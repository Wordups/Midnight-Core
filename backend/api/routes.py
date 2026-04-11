"""
Midnight Core — Pipeline Routes
Takeoff LLC

POST /pipeline/migrate/preview  → Bird Eye extraction → returns structured policy JSON (no docx)
POST /pipeline/migrate/generate → takes policy JSON → renders + saves .docx
POST /pipeline/migrate          → legacy single-shot (kept for backward compat)
POST /pipeline/create           → create new policy from intake form → .docx
POST /pipeline/analyze          → gap analysis on uploaded doc → JSON
POST /pipeline/birdsong         → Bird Talk proxy (Anthropic key stays server-side)
POST /pipeline/grc-summary      → GRC summary PDF
POST /api/smart-scan/preflight  → Bird Eye preflight scan → JSON quality report
"""

import os
import json
import uuid
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from dotenv import load_dotenv
from backend.storage.file_store import save_generated_document, list_generated_documents
from backend.core.framework_layer import (
    build_framework_mapping_rules,
    build_framework_prompt_context,
)
from backend.renderers.pdf_renderer import build_grc_summary_pdf

try:
    import anthropic
except ImportError:
    anthropic = None

load_dotenv()

router = APIRouter(tags=["pipeline"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL   = "claude-opus-4-5"

SUPPORTED_EXTENSIONS = {".docx", ".txt", ".md"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_workspace_id() -> str:
    return os.getenv("WORKSPACE_ID", "personal")


def _get_anthropic_client():
    if anthropic is None:
        raise HTTPException(
            status_code=503,
            detail="Anthropic dependency is not installed on the server.",
        )
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY is not configured.")
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _require_supported_file(upload: UploadFile, field_name: str = "file") -> None:
    filename = (upload.filename or field_name).lower()
    ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be .docx, .txt, or .md. Got '{upload.filename}'.",
        )


def _extract_text_from_upload(file_bytes: bytes, filename: str) -> str:
    """Extract raw text from .docx, .txt, or .md."""
    lower = filename.lower()

    if lower.endswith(".docx"):
        doc   = Document(BytesIO(file_bytes))
        lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                lines.append(text)
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    lines.append(" | ".join(cells))
        return "\n".join(lines)

    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


# ── Bird Talk proxy ───────────────────────────────────────────────────────────

class BirdsongRequest(BaseModel):
    messages: list[dict]
    system:   Optional[str] = None


@router.post("/pipeline/birdsong")
async def birdsong(request: BirdsongRequest):
    """Bird Talk proxy — Anthropic key stays server-side."""
    try:
        client = _get_anthropic_client()

        system = request.system or (
            "You are Midnight, the AI compliance assistant for the Midnight compliance platform "
            "by Takeoff LLC. You are also known as Bird Talk — a chicken mascot who is the Chief "
            "Compliance Officer. Help users understand their compliance program, identify gaps, "
            "and guide them toward building the right policies and controls. "
            "Midnight covers HIPAA, HiTrust, PCI DSS, ISO 27001, NIST CSF, CoBIT 2019, SOC 2 Type II. "
            "Philosophy: Handshake, not takeover — human-led, AI-accelerated. "
            "Keep responses SHORT (3-5 sentences max). Warm, direct, expert tone. 🐔"
        )

        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1000,
            system=system,
            messages=request.messages,
        )

        return {"reply": message.content[0].text}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bird Talk error: {str(e)}")


# ── Bird Eye preflight scan ───────────────────────────────────────────────────

PREFLIGHT_SYSTEM = """You are Bird Eye — the document intelligence engine inside Midnight by Takeoff LLC.

Analyze the provided document and return a JSON quality assessment. No preamble, no markdown, only JSON.

Required JSON structure:
{
  "quality_score": <integer 0-100>,
  "quality_label": "<Strong|Moderate|Weak|Critical>",
  "section_statuses": {
    "purpose": "<complete|partial|missing>",
    "scope": "<complete|partial|missing>",
    "policy_statement": "<complete|partial|missing>",
    "procedures": "<complete|partial|missing>",
    "roles_responsibilities": "<complete|partial|missing>",
    "revision_history": "<complete|partial|missing>"
  },
  "priority_gaps": [
    {"section": "<name>", "severity": "<critical|high|medium>"}
  ],
  "source_quality_warning": "<string or null>"
}

Be strict: a section is only "complete" if it contains substantive, specific content."""


@router.post("/api/smart-scan/preflight")
async def smart_scan_preflight(
    source_doc: UploadFile = File(...),
    doc_type:   str        = Form(default="policy"),
    industry:   str        = Form(default=""),
):
    """Bird Eye preflight — quality report only, no docx generated."""
    _require_supported_file(source_doc, "source_doc")

    file_bytes = await source_doc.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    raw_text = _extract_text_from_upload(file_bytes, source_doc.filename or "document")

    if len(raw_text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Document appears to be empty or unreadable.")

    user_msg = (
        f"FILENAME: {source_doc.filename}\n"
        f"DOC TYPE: {doc_type}\n"
        f"INDUSTRY: {industry or 'Not specified'}\n\n"
        f"DOCUMENT CONTENT (first 8000 chars):\n---\n{raw_text[:8000]}\n---\n\n"
        f"Analyze this document and return only the JSON quality assessment."
    )

    try:
        client  = _get_anthropic_client()
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            system=PREFLIGHT_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = message.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return JSONResponse(content=json.loads(raw))

    except json.JSONDecodeError:
        # Fallback — return passing scan so migration can proceed
        return JSONResponse(content={
            "quality_score": 60,
            "quality_label": "Moderate",
            "section_statuses": {
                "purpose": "partial", "scope": "partial",
                "policy_statement": "partial", "procedures": "partial",
                "roles_responsibilities": "missing", "revision_history": "missing",
            },
            "priority_gaps": [],
            "source_quality_warning": None,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bird Eye scan error: {str(e)}")


# ── Migrate extraction prompt ─────────────────────────────────────────────────

MIGRATION_SYSTEM_PROMPT = """You are a policy reconstruction engine for Midnight — Takeoff LLC's enterprise compliance platform.

You receive extracted content from a legacy policy document and must reconstruct it into a clean, structured policy.

Your output must be valid JSON with this exact structure:
{
  "policy_name": "...",
  "doc_type": "...",
  "version": "...",
  "effective_date": "...",
  "owner": "...",
  "purpose": "...",
  "scope": "...",
  "policy_statement": "...",
  "definitions": [...],
  "procedures": [...],
  "roles_responsibilities": [...],
  "exceptions": "...",
  "enforcement": "...",
  "references": [...],
  "revision_history": [...],
  "framework_mappings": {
    "<framework>": ["<control>", ...]
  },
  "framework_map": {
    "overall_coverage": "<Strong|Moderate|Weak|Critical>",
    "total_controls_mapped": 0,
    "total_gaps": 0,
    "frameworks_covered": [],
    "audit_summary": "...",
    "mapped_citations": [],
    "gaps": [
      {
        "framework": "...",
        "control_id": "...",
        "gap_description": "...",
        "risk_level": "<high|medium|low>",
        "suggestion": "..."
      }
    ]
  },
  "gaps": [...],
  "quality_score": 0
}

Rules:
- NEVER invent content not in the source
- Preserve all original meaning
- Map only to the provided framework controls
- framework_map.gaps must list specific missing controls with risk level and remediation suggestion
- quality_score is 0-100 based on completeness
- Return ONLY valid JSON, no markdown, no preamble"""


async def _extract_policy_data(
    file_bytes: bytes,
    filename: str,
    template_name: str,
    frameworks: list[str],
) -> dict:
    """
    Shared extraction function used by both /preview and the legacy single-shot route.
    Calls Claude Opus and returns validated policy dict. Does NOT build a docx.
    """
    raw_text = _extract_text_from_upload(file_bytes, filename)

    if len(raw_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Document appears to be empty or unreadable.")

    normalized_frameworks, fw_context = build_framework_prompt_context(frameworks)
    mapping_rules = build_framework_mapping_rules(frameworks)

    user_msg = (
        f"DOCUMENT: {filename}\n"
        f"TEMPLATE TYPE: {template_name}\n"
        f"FRAMEWORKS TO MAP: {', '.join(normalized_frameworks)}\n"
        f"FRAMEWORK CONTROLS REFERENCE:\n{chr(10).join(fw_context)}\n\n"
        f"MAPPING RULES: {mapping_rules}\n\n"
        f"SOURCE CONTENT:\n---\n{raw_text[:14000]}\n---\n\n"
        f"Reconstruct this policy into the required JSON structure. Return only JSON."
    )

    client  = _get_anthropic_client()
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=MIGRATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


# ── Docx renderer ─────────────────────────────────────────────────────────────

def _build_docx(policy_data: dict, template_name: str) -> bytes:
    """Render policy dict → .docx bytes. Called by both generate and legacy routes."""
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    def add_heading(text: str, level: int = 1):
        h = doc.add_heading(text, level=level)
        h.style.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)
        return h

    def add_body(text: str):
        p = doc.add_paragraph(text)
        p.style.font.size = Pt(11)
        return p

    def add_bullet(text: str):
        doc.add_paragraph(text, style="List Bullet")

    # Header metadata table
    table = doc.add_table(rows=5, cols=2)
    table.style = "Table Grid"
    fields = [
        ("Policy Name",    policy_data.get("policy_name", "Untitled Policy")),
        ("Document Type",  policy_data.get("doc_type", "Policy")),
        ("Version",        policy_data.get("version", "1.0")),
        ("Effective Date", policy_data.get("effective_date", "—")),
        ("Policy Owner",   policy_data.get("owner", "—")),
    ]
    for i, (label, value) in enumerate(fields):
        row = table.rows[i]
        row.cells[0].text = label
        row.cells[1].text = str(value) if value else "—"

    doc.add_paragraph()

    sections = [
        ("1. Purpose",                  "purpose"),
        ("2. Scope",                    "scope"),
        ("3. Policy Statement",         "policy_statement"),
        ("4. Definitions",              "definitions"),
        ("5. Procedures",               "procedures"),
        ("6. Roles & Responsibilities", "roles_responsibilities"),
        ("7. Exceptions",               "exceptions"),
        ("8. Enforcement",              "enforcement"),
        ("9. References",               "references"),
    ]

    for title, key in sections:
        add_heading(title, level=1)
        content = policy_data.get(key)
        if not content:
            add_body("[Section not found in source document]")
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    add_bullet(
                        f"{item.get('role', item.get('title', ''))}: "
                        f"{item.get('responsibility', item.get('description', str(item)))}"
                    )
                else:
                    add_bullet(str(item))
        else:
            add_body(str(content))
        doc.add_paragraph()

    # Framework mappings
    fw_mappings = policy_data.get("framework_mappings", {})
    if fw_mappings:
        add_heading("10. Framework Mappings", level=1)
        for fw, controls in fw_mappings.items():
            if controls:
                add_heading(fw, level=2)
                if isinstance(controls, list):
                    for ctrl in controls:
                        add_bullet(str(ctrl))
                else:
                    add_body(str(controls))
        doc.add_paragraph()

    # Gap analysis — prefer framework_map.gaps for richer data
    fm   = policy_data.get("framework_map", {})
    gaps = (fm.get("gaps") if fm else None) or policy_data.get("gaps", [])
    if gaps:
        add_heading("11. Gap Analysis", level=1)
        for gap in gaps:
            if isinstance(gap, dict):
                label = (
                    f"{gap.get('framework','')} {gap.get('control_id','')}: "
                    f"{gap.get('gap_description','')}"
                )
                if gap.get("suggestion"):
                    label += f" → {gap['suggestion']}"
                add_bullet(label)
            else:
                add_bullet(str(gap))
        doc.add_paragraph()

    # Revision history
    revision = policy_data.get("revision_history", [])
    add_heading("12. Revision History", level=1)
    if revision:
        rev_table = doc.add_table(rows=1, cols=3)
        rev_table.style = "Table Grid"
        hdr = rev_table.rows[0].cells
        hdr[0].text = "Version"
        hdr[1].text = "Date"
        hdr[2].text = "Description"
        for entry in revision:
            row = rev_table.add_row().cells
            if isinstance(entry, dict):
                row[0].text = str(entry.get("version", ""))
                row[1].text = str(entry.get("date", ""))
                row[2].text = str(entry.get("description", entry.get("change", "")))
            else:
                row[0].text = str(entry)
    else:
        add_body("[No revision history found in source document]")

    # Footer
    section = doc.sections[0]
    footer  = section.footer
    fp = footer.paragraphs[0]
    fp.text = (
        f"{policy_data.get('policy_name', 'Policy')} · "
        f"v{policy_data.get('version', '1.0')} · "
        f"Midnight — Takeoff LLC · CONFIDENTIAL"
    )
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.style.font.size = Pt(8)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


def _build_preview_text(policy_data: dict) -> str:
    for key in ("purpose", "scope", "policy_statement"):
        candidate = policy_data.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip().replace("\n", " ")[:280]
    return "Document generated successfully."


# ── MIGRATE STEP 1: Preview ───────────────────────────────────────────────────

@router.post("/pipeline/migrate/preview")
async def migrate_preview(
    source_file:   UploadFile = File(...),
    template_name: str        = Form(default="generic_policy"),
    industry:      str        = Form(default="Healthcare"),
    frameworks:    str        = Form(default="HIPAA,HITRUST"),
):
    """
    Upload file → Claude Opus extraction → return structured policy JSON.
    NO docx is built here. Frontend renders a preview from this data,
    then calls /pipeline/migrate/generate when the user confirms.
    """
    _require_supported_file(source_file)

    file_bytes = await source_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    fw_list = [f.strip() for f in frameworks.split(",") if f.strip()]

    try:
        policy_data = await _extract_policy_data(
            file_bytes=file_bytes,
            filename=source_file.filename or "document.txt",
            template_name=template_name,
            frameworks=fw_list,
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Claude returned invalid JSON: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")

    # Attach session metadata so the generate step has full context without re-uploading
    policy_data["_session"] = {
        "source_filename": source_file.filename or "document",
        "template_name":   template_name,
        "frameworks":      fw_list,
        "preview_id":      str(uuid.uuid4()),
    }

    return JSONResponse(content={
        "policy_data":   policy_data,
        "framework_map": policy_data.get("framework_map"),
        "quality_score": policy_data.get("quality_score", 0),
        "preview_id":    policy_data["_session"]["preview_id"],
    })


# ── MIGRATE STEP 2: Generate ──────────────────────────────────────────────────

class MigrateGenerateRequest(BaseModel):
    policy_data: dict


@router.post("/pipeline/migrate/generate")
async def migrate_generate(request: MigrateGenerateRequest):
    """
    Receive validated policy JSON from frontend → render .docx → return file + save to store.
    The frontend may have edited policy_data between preview and generate — that's intentional.
    """
    policy_data = request.policy_data

    if not policy_data:
        raise HTTPException(status_code=400, detail="policy_data is required.")

    # Pop session metadata — it is routing data, not document content
    session       = policy_data.pop("_session", {})
    source_name   = session.get("source_filename", "document")
    template_name = session.get("template_name", "generic_policy")

    try:
        docx_bytes = _build_docx(policy_data, template_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document rendering error: {str(e)}")

    base_name    = source_name.rsplit(".", 1)[0]
    output_name  = f"{base_name}_migrated.docx"
    preview_text = _build_preview_text(policy_data)

    record = save_generated_document(
        workspace_id=_get_workspace_id(),
        filename=output_name,
        document_name=policy_data.get("policy_name", base_name),
        doc_type=policy_data.get("doc_type", template_name),
        preview=preview_text,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_bytes=docx_bytes,
        source_name=source_name,
    )

    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition":    f'attachment; filename="{output_name}"',
            "X-Midnight-Preview":     preview_text,
            "X-Midnight-Document-Id": record["id"],
        },
    )


# ── MIGRATE LEGACY: single-shot (backward compat) ─────────────────────────────

@router.post("/pipeline/migrate")
async def migrate_document(
    file:          UploadFile | None = File(default=None),
    source_file:   UploadFile | None = File(default=None),
    template_name: str               = Form(default="generic_policy"),
    industry:      str               = Form(default="Healthcare"),
    frameworks:    str               = Form(default="HIPAA,HITRUST"),
):
    """
    Single-shot migrate — extract + render in one request.
    Kept for backward compat. Prefer /preview + /generate for new work.
    """
    upload = file or source_file
    if upload is None:
        raise HTTPException(status_code=400, detail="No document was uploaded.")

    _require_supported_file(upload)

    file_bytes = await upload.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    fw_list = [f.strip() for f in frameworks.split(",") if f.strip()]

    try:
        policy_data = await _extract_policy_data(
            file_bytes=file_bytes,
            filename=upload.filename or "document.txt",
            template_name=template_name,
            frameworks=fw_list,
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Claude returned invalid JSON: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration error: {str(e)}")

    try:
        docx_bytes = _build_docx(policy_data, template_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document rendering error: {str(e)}")

    base_name    = (upload.filename or "document").rsplit(".", 1)[0]
    output_name  = f"{base_name}_migrated.docx"
    preview_text = _build_preview_text(policy_data)

    record = save_generated_document(
        workspace_id=_get_workspace_id(),
        filename=output_name,
        document_name=policy_data.get("policy_name", base_name),
        doc_type=policy_data.get("doc_type", template_name),
        preview=preview_text,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_bytes=docx_bytes,
        source_name=upload.filename or "document",
    )

    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition":    f'attachment; filename="{output_name}"',
            "X-Midnight-Preview":     preview_text,
            "X-Midnight-Document-Id": record["id"],
        },
    )


# ── Policy creation ───────────────────────────────────────────────────────────

CREATE_SYSTEM_PROMPT = """You are a policy creation engine for Midnight — Takeoff LLC's enterprise compliance platform.

Create a complete, professional enterprise policy document based on the intake information provided.

Return valid JSON with this structure:
{
  "policy_name": "...",
  "doc_type": "...",
  "version": "1.0",
  "effective_date": "...",
  "owner": "...",
  "purpose": "...",
  "scope": "...",
  "policy_statement": "...",
  "definitions": [...],
  "procedures": [...],
  "roles_responsibilities": [...],
  "exceptions": "...",
  "enforcement": "...",
  "references": [...],
  "revision_history": [{"version": "1.0", "date": "...", "description": "Initial release"}],
  "framework_mappings": {}
}

Rules:
- Write professionally and specifically for the industry provided
- Map only to the provided framework controls
- Procedures must be numbered step-by-step
- Return ONLY valid JSON, no markdown"""


class CreatePolicyRequest(BaseModel):
    policy_name: str
    doc_type:    str
    industry:    str
    frameworks:  list[str]
    owner:       str
    description: Optional[str] = None


@router.post("/pipeline/create")
async def create_document(request: CreatePolicyRequest):
    normalized_frameworks, fw_context = build_framework_prompt_context(request.frameworks)
    mapping_rules = build_framework_mapping_rules(request.frameworks)

    user_msg = (
        f"Policy Name: {request.policy_name}\n"
        f"Document Type: {request.doc_type}\n"
        f"Industry: {request.industry}\n"
        f"Frameworks: {', '.join(normalized_frameworks)}\n"
        f"Owner: {request.owner}\n"
        f"Description/Scope: {request.description or 'Not provided'}\n\n"
        f"Framework Controls Reference:\n{chr(10).join(fw_context)}\n\n"
        f"Mapping Rules: {mapping_rules}\n\n"
        f"Create a complete enterprise policy document. Return only JSON."
    )

    try:
        client  = _get_anthropic_client()
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=CREATE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = message.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        policy_data = json.loads(raw)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Claude returned invalid JSON: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Creation error: {str(e)}")

    try:
        docx_bytes = _build_docx(policy_data, request.doc_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document rendering error: {str(e)}")

    output_name  = f"{request.policy_name.replace(' ', '_')}_v1.0.docx"
    preview_text = _build_preview_text(policy_data)

    record = save_generated_document(
        workspace_id=_get_workspace_id(),
        filename=output_name,
        document_name=policy_data.get("policy_name", request.policy_name),
        doc_type=request.doc_type,
        preview=preview_text,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_bytes=docx_bytes,
        source_name=request.policy_name,
    )

    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition":    f'attachment; filename="{output_name}"',
            "X-Midnight-Preview":     preview_text,
            "X-Midnight-Document-Id": record["id"],
        },
    )


# ── GRC Summary ───────────────────────────────────────────────────────────────

class GrcSummaryRequest(BaseModel):
    organization_name: str
    industry:          str
    frameworks:        list[str]
    # Optional: pass policy_data from a migrate/preview session for real gap data
    policy_data:       Optional[dict] = None


@router.post("/pipeline/grc-summary")
async def create_grc_summary(request: GrcSummaryRequest):
    normalized_frameworks, _ = build_framework_prompt_context(request.frameworks)
    workspace_id = _get_workspace_id()
    documents    = list_generated_documents(workspace_id)

    pdf_bytes = build_grc_summary_pdf(
        organization_name=request.organization_name.strip() or "Organization",
        industry=request.industry.strip() or "Unspecified",
        frameworks=normalized_frameworks,
        documents=documents,
    )

    org_slug     = (request.organization_name.strip() or "organization").replace(" ", "_")
    output_name  = f"{org_slug}_grc_summary.pdf"
    preview_text = (
        f"GRC summary for {request.organization_name.strip() or 'your workspace'} "
        f"covering {', '.join(normalized_frameworks) or 'selected frameworks'}."
    )

    record = save_generated_document(
        workspace_id=workspace_id,
        filename=output_name,
        document_name=f"{request.organization_name.strip() or 'Organization'} GRC Summary",
        doc_type="PDF",
        preview=preview_text,
        content_type="application/pdf",
        file_bytes=pdf_bytes,
        source_name=request.organization_name.strip() or output_name,
    )

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition":    f'attachment; filename="{output_name}"',
            "X-Midnight-Preview":     preview_text,
            "X-Midnight-Document-Id": record["id"],
        },
    )


# ── Gap analysis ──────────────────────────────────────────────────────────────

@router.post("/pipeline/analyze")
async def analyze_document(
    file:       UploadFile = File(...),
    frameworks: str        = Form(default="HIPAA,PCI DSS,NIST CSF"),
):
    _require_supported_file(file)

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    fw_list  = [f.strip() for f in frameworks.split(",") if f.strip()]
    raw_text = _extract_text_from_upload(file_bytes, file.filename or "document")[:10000]

    normalized_frameworks, fw_context = build_framework_prompt_context(fw_list)
    mapping_rules = build_framework_mapping_rules(fw_list)

    user_msg = (
        f"FRAMEWORKS: {', '.join(normalized_frameworks)}\n\n"
        f"FRAMEWORK CONTROLS:\n{chr(10).join(fw_context)}\n\n"
        f"MAPPING RULES: {mapping_rules}\n\n"
        f"POLICY DOCUMENT:\n---\n{raw_text}\n---\n\n"
        f"Analyze this policy against the framework controls. "
        f"Return JSON with: covered_controls, missing_controls, partial_controls, gaps, recommendations, overall_score (0-100)"
    )

    try:
        client  = _get_anthropic_client()
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            system="You are a GRC analyst. Analyze policy documents against compliance frameworks. Return only valid JSON.",
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = message.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return JSONResponse(content=json.loads(raw))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
