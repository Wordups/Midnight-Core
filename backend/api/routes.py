"""
Midnight Core - Pipeline Routes
Takeoff LLC

POST /pipeline/migrate/preview   -> extract legacy policy into structured JSON
POST /pipeline/migrate/generate  -> render edited migrate JSON into .docx
POST /pipeline/migrate           -> legacy single-shot migrate
POST /pipeline/create/preview    -> create policy JSON from intake form
POST /pipeline/create/generate   -> render edited create JSON into .docx
POST /pipeline/create            -> legacy single-shot create
POST /pipeline/analyze           -> gap analysis on uploaded doc
POST /pipeline/birdsong          -> Bird Talk proxy
POST /pipeline/grc-summary       -> workspace GRC summary PDF
"""

import json
import os
import uuid
from io import BytesIO
from typing import Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from dotenv import load_dotenv
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.core.framework_layer import (
    build_framework_mapping_rules,
    build_framework_prompt_context,
)
from backend.renderers.pdf_renderer import build_grc_summary_pdf
from backend.storage.file_store import save_generated_document, list_generated_documents

try:
    import anthropic
except ImportError:  # pragma: no cover - handled at runtime when dependency is missing
    anthropic = None

load_dotenv()

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-opus-4-5"
SUPPORTED_EXTENSIONS = {".docx", ".txt", ".md"}


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
    lower = filename.lower()

    if lower.endswith(".docx"):
        doc = Document(BytesIO(file_bytes))
        lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                lines.append(text)
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    lines.append(" | ".join(cells))
        return "\n".join(lines)

    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


def _strip_json_fences(raw: str) -> str:
    return raw.replace("```json", "").replace("```", "").strip()


def _build_preview_text(policy_data: dict) -> str:
    for key in ("purpose", "scope", "policy_statement"):
        candidate = policy_data.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip().replace("\n", " ")[:280]
    return "Document generated successfully."


def _stream_docx_response(
    *,
    policy_data: dict,
    template_name: str,
    output_name: str,
    document_name: str,
    doc_type: str,
    source_name: str,
) -> StreamingResponse:
    try:
        docx_bytes = _build_docx(policy_data, template_name)
    except Exception as exc:  # pragma: no cover - runtime rendering failure
        raise HTTPException(status_code=500, detail=f"Document rendering error: {exc}") from exc

    preview_text = _build_preview_text(policy_data)
    record = save_generated_document(
        workspace_id=_get_workspace_id(),
        filename=output_name,
        document_name=document_name,
        doc_type=doc_type,
        preview=preview_text,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_bytes=docx_bytes,
        source_name=source_name,
    )

    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{output_name}"',
            "X-Midnight-Preview": preview_text,
            "X-Midnight-Document-Id": record["id"],
        },
    )


class BirdsongRequest(BaseModel):
    messages: list[dict]
    system: Optional[str] = None


@router.post("/birdsong")
async def birdsong(request: BirdsongRequest):
    try:
        client = _get_anthropic_client()
        system = request.system or (
            "You are Midnight, the AI compliance assistant for the Midnight compliance platform "
            "by Takeoff LLC. You are also known as Bird Talk, a chicken mascot who is the Chief "
            "Compliance Officer. Help users understand their compliance program, identify gaps, "
            "and guide them toward building the right policies and controls. "
            "Midnight covers HIPAA, HITRUST-aligned domains, PCI DSS, NIST CSF, and SOC 2. "
            "Philosophy: Handshake, not takeover - human-led, AI-accelerated. "
            "Keep responses short (3-5 sentences max). Warm, direct, expert tone."
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
    except Exception as exc:  # pragma: no cover - runtime provider failure
        raise HTTPException(status_code=500, detail=f"Bird Talk error: {exc}") from exc


MIGRATION_SYSTEM_PROMPT = """You are a policy reconstruction engine for Midnight, Takeoff LLC's enterprise compliance platform.

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
    "<framework>": ["<control>", "..."]
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
- Never invent content not in the source.
- Preserve the source meaning in plain business language.
- Map only to the provided framework controls or HITRUST-aligned domains.
- framework_map.gaps must list specific missing controls with risk level and remediation suggestion.
- quality_score is 0-100 based on completeness.
- Return only valid JSON, no markdown and no preamble."""


async def _extract_policy_data(
    *,
    file_bytes: bytes,
    filename: str,
    template_name: str,
    frameworks: list[str],
) -> dict:
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
        "Reconstruct this policy into the required JSON structure. Return only JSON."
    )

    client = _get_anthropic_client()
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=MIGRATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return json.loads(_strip_json_fences(message.content[0].text))


CREATE_SYSTEM_PROMPT = """You are a policy creation engine for Midnight, Takeoff LLC's enterprise compliance platform.

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
  "framework_mappings": {
    "<framework>": ["<control>", "..."]
  },
  "framework_map": {
    "overall_coverage": "Strong",
    "total_controls_mapped": 0,
    "total_gaps": 0,
    "frameworks_covered": [],
    "audit_summary": "...",
    "mapped_citations": [],
    "gaps": []
  }
}

Rules:
- Write professionally and specifically for the industry provided.
- Map only to the provided framework controls or HITRUST-aligned domains.
- Procedures must be written step-by-step when procedural detail is appropriate.
- Return only valid JSON, no markdown."""


class CreatePolicyRequest(BaseModel):
    policy_name: str
    doc_type: str
    industry: str
    frameworks: list[str]
    owner: str
    description: Optional[str] = None


async def _generate_policy_data(request: CreatePolicyRequest) -> dict:
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
        "Create a complete enterprise policy document. Return only JSON."
    )

    client = _get_anthropic_client()
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=CREATE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return json.loads(_strip_json_fences(message.content[0].text))


def _build_docx(policy_data: dict, template_name: str) -> bytes:
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    def add_heading(text: str, level: int = 1):
        heading = doc.add_heading(text, level=level)
        heading.style.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
        return heading

    def add_body(text: str):
        paragraph = doc.add_paragraph(text)
        paragraph.style.font.size = Pt(11)
        return paragraph

    def add_bullet(text: str):
        doc.add_paragraph(text, style="List Bullet")

    table = doc.add_table(rows=5, cols=2)
    table.style = "Table Grid"
    fields = [
        ("Policy Name", policy_data.get("policy_name", "Untitled Policy")),
        ("Document Type", policy_data.get("doc_type", "Policy")),
        ("Version", policy_data.get("version", "1.0")),
        ("Effective Date", policy_data.get("effective_date", "-")),
        ("Policy Owner", policy_data.get("owner", "-")),
    ]
    for index, (label, value) in enumerate(fields):
        row = table.rows[index]
        row.cells[0].text = label
        row.cells[1].text = str(value) if value else "-"

    doc.add_paragraph()

    sections = [
        ("1. Purpose", "purpose"),
        ("2. Scope", "scope"),
        ("3. Policy Statement", "policy_statement"),
        ("4. Definitions", "definitions"),
        ("5. Procedures", "procedures"),
        ("6. Roles & Responsibilities", "roles_responsibilities"),
        ("7. Exceptions", "exceptions"),
        ("8. Enforcement", "enforcement"),
        ("9. References", "references"),
    ]

    for title, key in sections:
        add_heading(title, level=1)
        content = policy_data.get(key)
        if not content:
            add_body("[Section not found in source document]")
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    label = item.get("role") or item.get("title") or ""
                    desc = item.get("responsibility") or item.get("description") or str(item)
                    add_bullet(f"{label}: {desc}" if label else desc)
                else:
                    add_bullet(str(item))
        else:
            add_body(str(content))
        doc.add_paragraph()

    framework_mappings = policy_data.get("framework_mappings", {})
    if framework_mappings:
        add_heading("10. Framework Mappings", level=1)
        for framework, controls in framework_mappings.items():
            if not controls:
                continue
            add_heading(framework, level=2)
            if isinstance(controls, list):
                for control in controls:
                    add_bullet(str(control))
            else:
                add_body(str(controls))
        doc.add_paragraph()

    framework_map = policy_data.get("framework_map", {}) or {}
    gaps = framework_map.get("gaps") or policy_data.get("gaps", [])
    if gaps:
        add_heading("11. Gap Analysis", level=1)
        for gap in gaps:
            if isinstance(gap, dict):
                label = (
                    f"{gap.get('framework', '')} {gap.get('control_id', '')}: "
                    f"{gap.get('gap_description', '')}"
                ).strip()
                if gap.get("suggestion"):
                    label = f"{label} -> {gap['suggestion']}"
                add_bullet(label)
            else:
                add_bullet(str(gap))
        doc.add_paragraph()

    revision_history = policy_data.get("revision_history", [])
    add_heading("12. Revision History", level=1)
    if revision_history:
        rev_table = doc.add_table(rows=1, cols=3)
        rev_table.style = "Table Grid"
        header = rev_table.rows[0].cells
        header[0].text = "Version"
        header[1].text = "Date"
        header[2].text = "Description"
        for entry in revision_history:
            row = rev_table.add_row().cells
            if isinstance(entry, dict):
                row[0].text = str(entry.get("version", ""))
                row[1].text = str(entry.get("date", ""))
                row[2].text = str(entry.get("description", entry.get("change", "")))
            else:
                row[0].text = str(entry)
    else:
        add_body("[No revision history found in source document]")

    footer = doc.sections[0].footer.paragraphs[0]
    footer.text = (
        f"{policy_data.get('policy_name', 'Policy')} · "
        f"v{policy_data.get('version', '1.0')} · "
        "Midnight - Takeoff LLC · CONFIDENTIAL"
    )
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.style.font.size = Pt(8)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


@router.post("/migrate/preview")
async def migrate_preview(
    source_file: UploadFile = File(...),
    template_name: str = Form(default="generic_policy"),
    industry: str = Form(default="Healthcare"),
    frameworks: str = Form(default="HIPAA,HITRUST"),
):
    _require_supported_file(source_file, "source_file")
    file_bytes = await source_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    framework_list = [item.strip() for item in frameworks.split(",") if item.strip()]

    try:
        policy_data = await _extract_policy_data(
            file_bytes=file_bytes,
            filename=source_file.filename or "document.txt",
            template_name=template_name,
            frameworks=framework_list,
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Claude returned invalid JSON: {exc}") from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - runtime provider failure
        raise HTTPException(status_code=500, detail=f"Extraction error: {exc}") from exc

    policy_data["_session"] = {
        "source_filename": source_file.filename or "document",
        "template_name": template_name,
        "frameworks": framework_list,
        "industry": industry,
        "preview_id": str(uuid.uuid4()),
    }

    return JSONResponse(
        content={
            "policy_data": policy_data,
            "framework_map": policy_data.get("framework_map"),
            "quality_score": policy_data.get("quality_score", 0),
            "preview_id": policy_data["_session"]["preview_id"],
        }
    )


class MigrateGenerateRequest(BaseModel):
    policy_data: dict


@router.post("/migrate/generate")
async def migrate_generate(request: MigrateGenerateRequest):
    policy_data = dict(request.policy_data or {})
    if not policy_data:
        raise HTTPException(status_code=400, detail="policy_data is required.")

    session = policy_data.pop("_session", {})
    source_name = session.get("source_filename", "document")
    template_name = session.get("template_name", "generic_policy")
    base_name = source_name.rsplit(".", 1)[0]
    output_name = f"{base_name}_migrated.docx"

    return _stream_docx_response(
        policy_data=policy_data,
        template_name=template_name,
        output_name=output_name,
        document_name=policy_data.get("policy_name", base_name),
        doc_type=policy_data.get("doc_type", template_name),
        source_name=source_name,
    )


@router.post("/migrate")
async def migrate_document(
    file: UploadFile | None = File(default=None),
    source_file: UploadFile | None = File(default=None),
    template_name: str = Form(default="generic_policy"),
    industry: str = Form(default="Healthcare"),
    frameworks: str = Form(default="HIPAA,HITRUST"),
):
    upload = file or source_file
    if upload is None:
        raise HTTPException(status_code=400, detail="No document was uploaded.")

    _require_supported_file(upload)
    file_bytes = await upload.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    framework_list = [item.strip() for item in frameworks.split(",") if item.strip()]

    try:
        policy_data = await _extract_policy_data(
            file_bytes=file_bytes,
            filename=upload.filename or "document.txt",
            template_name=template_name,
            frameworks=framework_list,
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Claude returned invalid JSON: {exc}") from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - runtime provider failure
        raise HTTPException(status_code=500, detail=f"Migration error: {exc}") from exc

    base_name = (upload.filename or "document").rsplit(".", 1)[0]
    return _stream_docx_response(
        policy_data=policy_data,
        template_name=template_name,
        output_name=f"{base_name}_migrated.docx",
        document_name=policy_data.get("policy_name", base_name),
        doc_type=policy_data.get("doc_type", template_name),
        source_name=upload.filename or "document",
    )


@router.post("/create/preview")
async def create_preview(request: CreatePolicyRequest):
    try:
        policy_data = await _generate_policy_data(request)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Claude returned invalid JSON: {exc}") from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - runtime provider failure
        raise HTTPException(status_code=500, detail=f"Creation error: {exc}") from exc

    policy_data["_session"] = {
        "doc_type": request.doc_type,
        "industry": request.industry,
        "frameworks": request.frameworks,
        "source_name": request.policy_name,
        "preview_id": str(uuid.uuid4()),
    }

    return JSONResponse(
        content={
            "policy_data": policy_data,
            "framework_map": policy_data.get("framework_map"),
            "preview_id": policy_data["_session"]["preview_id"],
        }
    )


class CreateGenerateRequest(BaseModel):
    policy_data: dict


@router.post("/create/generate")
async def create_generate(request: CreateGenerateRequest):
    policy_data = dict(request.policy_data or {})
    if not policy_data:
        raise HTTPException(status_code=400, detail="policy_data is required.")

    session = policy_data.pop("_session", {})
    policy_name = policy_data.get("policy_name", session.get("source_name", "Policy"))
    doc_type = policy_data.get("doc_type", session.get("doc_type", "POLICY"))
    output_name = f"{policy_name.replace(' ', '_')}_v{policy_data.get('version', '1.0')}.docx"

    return _stream_docx_response(
        policy_data=policy_data,
        template_name=str(doc_type).lower(),
        output_name=output_name,
        document_name=policy_name,
        doc_type=doc_type,
        source_name=session.get("source_name", policy_name),
    )


@router.post("/create")
async def create_document(request: CreatePolicyRequest):
    try:
        policy_data = await _generate_policy_data(request)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Claude returned invalid JSON: {exc}") from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - runtime provider failure
        raise HTTPException(status_code=500, detail=f"Creation error: {exc}") from exc

    output_name = f"{request.policy_name.replace(' ', '_')}_v1.0.docx"
    return _stream_docx_response(
        policy_data=policy_data,
        template_name=request.doc_type,
        output_name=output_name,
        document_name=policy_data.get("policy_name", request.policy_name),
        doc_type=request.doc_type,
        source_name=request.policy_name,
    )


class GrcSummaryRequest(BaseModel):
    organization_name: str
    industry: str
    frameworks: list[str]
    policy_data: Optional[dict] = None


@router.post("/grc-summary")
async def create_grc_summary(request: GrcSummaryRequest):
    normalized_frameworks, _ = build_framework_prompt_context(request.frameworks)
    workspace_id = _get_workspace_id()
    documents = list_generated_documents(workspace_id)

    pdf_bytes = build_grc_summary_pdf(
        organization_name=request.organization_name.strip() or "Organization",
        industry=request.industry.strip() or "Unspecified",
        frameworks=normalized_frameworks,
        documents=documents,
    )

    org_slug = (request.organization_name.strip() or "organization").replace(" ", "_")
    output_name = f"{org_slug}_grc_summary.pdf"
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
            "Content-Disposition": f'attachment; filename="{output_name}"',
            "X-Midnight-Preview": preview_text,
            "X-Midnight-Document-Id": record["id"],
        },
    )


@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    frameworks: str = Form(default="HIPAA,PCI DSS,NIST CSF"),
):
    _require_supported_file(file)

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    framework_list = [item.strip() for item in frameworks.split(",") if item.strip()]
    raw_text = _extract_text_from_upload(file_bytes, file.filename or "document")[:10000]

    normalized_frameworks, fw_context = build_framework_prompt_context(framework_list)
    mapping_rules = build_framework_mapping_rules(framework_list)

    user_msg = (
        f"FRAMEWORKS: {', '.join(normalized_frameworks)}\n\n"
        f"FRAMEWORK CONTROLS:\n{chr(10).join(fw_context)}\n\n"
        f"MAPPING RULES: {mapping_rules}\n\n"
        f"POLICY DOCUMENT:\n---\n{raw_text}\n---\n\n"
        "Analyze this policy against the framework controls. "
        "Return JSON with: covered_controls, missing_controls, partial_controls, gaps, recommendations, overall_score (0-100)"
    )

    try:
        client = _get_anthropic_client()
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            system="You are a GRC analyst. Analyze policy documents against compliance frameworks. Return only valid JSON.",
            messages=[{"role": "user", "content": user_msg}],
        )
        return JSONResponse(content=json.loads(_strip_json_fences(message.content[0].text)))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - runtime provider failure
        raise HTTPException(status_code=500, detail=f"Analysis error: {exc}") from exc
