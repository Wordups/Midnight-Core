"""
Midnight Core — Pipeline Routes
Takeoff LLC

POST /pipeline/migrate   → Bird Eye scan + semantic reconstruct + .docx output
POST /pipeline/create    → create new policy from intake form
POST /pipeline/analyze   → gap analysis on uploaded doc
POST /pipeline/birdsong  → Bird Talk proxy (Anthropic key stays server-side)
"""

import os
import json
import asyncio
from io import BytesIO
from typing import Optional

import anthropic
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL   = "claude-opus-4-5"

# ── Framework control mappings ────────────────────────────────────────────────

FRAMEWORK_CONTROLS = {
    "HIPAA": [
        "164.308(a)(1) — Risk Analysis",
        "164.308(a)(3) — Workforce Access Management",
        "164.308(a)(5) — Security Awareness Training",
        "164.310(a)(1) — Facility Access Controls",
        "164.312(a)(1) — Access Control",
        "164.312(e)(1) — Transmission Security",
    ],
    "HiTrust": [
        "01.a — Access Control Policy",
        "06.d — Information Classification",
        "09.ab — Monitoring System Use",
        "10.b — Input Data Validation",
    ],
    "PCI DSS": [
        "1.1 — Firewall Configuration Standards",
        "7.1 — Limit Access to System Components",
        "8.3 — Secure Individual Authentication",
        "10.1 — Audit Logs",
        "12.8 — Third Party Risk Management",
    ],
    "ISO 27001": [
        "A.5 — Information Security Policies",
        "A.6 — Organization of Information Security",
        "A.9 — Access Control",
        "A.12 — Operations Security",
        "A.15 — Supplier Relationships",
        "A.16 — Information Security Incident Management",
    ],
    "NIST CSF": [
        "ID.AM — Asset Management",
        "ID.SC — Supply Chain Risk Management",
        "PR.AC — Identity Management and Access Control",
        "PR.DS — Data Security",
        "DE.CM — Security Continuous Monitoring",
        "RS.RP — Response Planning",
    ],
    "SOC 2": [
        "CC1.1 — Control Environment",
        "CC6.1 — Logical Access Controls",
        "CC6.6 — External Access Controls",
        "CC7.1 — System Monitoring",
        "CC9.2 — Vendor Risk Management",
    ],
}


# ── Bird Talk proxy ───────────────────────────────────────────────────────────

class BirdsongRequest(BaseModel):
    messages: list[dict]
    system:   Optional[str] = None


@router.post("/birdsong")
async def birdsong(request: BirdsongRequest):
    """
    Bird Talk proxy — Anthropic key stays server-side.
    Frontend calls this instead of hitting Anthropic directly.
    """
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bird Talk error: {str(e)}")


# ── Policy migration ──────────────────────────────────────────────────────────

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
    "HIPAA": [...],
    "PCI DSS": [...],
    "ISO 27001": [...],
    "NIST CSF": [...],
    "SOC 2": [...]
  },
  "gaps": [...],
  "quality_score": 0
}

Rules:
- NEVER invent content not in the source
- Preserve all original meaning
- Map to framework controls where content clearly applies
- List gaps where required sections are missing or weak
- quality_score is 0-100 based on completeness
- Return ONLY valid JSON, no markdown, no preamble"""


async def _extract_and_reconstruct(
    file_bytes: bytes,
    filename: str,
    template_name: str,
    frameworks: list[str],
) -> dict:
    """Extract content from docx and reconstruct via Claude Opus."""

    # Extract raw text from docx
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

    raw_text = "\n".join(lines)

    if len(raw_text) < 50:
        raise HTTPException(status_code=400, detail="Document appears to be empty or unreadable.")

    # Build framework context
    fw_context = []
    for fw in frameworks:
        if fw in FRAMEWORK_CONTROLS:
            fw_context.append(f"{fw}: {', '.join(FRAMEWORK_CONTROLS[fw][:3])}")

    user_msg = (
        f"DOCUMENT: {filename}\n"
        f"TEMPLATE TYPE: {template_name}\n"
        f"FRAMEWORKS TO MAP: {', '.join(frameworks)}\n"
        f"FRAMEWORK CONTROLS REFERENCE:\n{chr(10).join(fw_context)}\n\n"
        f"SOURCE CONTENT:\n---\n{raw_text[:14000]}\n---\n\n"
        f"Reconstruct this policy into the required JSON structure. Return only JSON."
    )

    client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=MIGRATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def _build_docx(policy_data: dict, template_name: str) -> bytes:
    """Render reconstructed policy data into a clean .docx file."""
    doc = Document()

    # ── Styles ───────────────────────────────────────────────────────────────
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

    # ── Header metadata table ─────────────────────────────────────────────────
    table = doc.add_table(rows=5, cols=2)
    table.style = "Table Grid"
    fields = [
        ("Policy Name",     policy_data.get("policy_name", "Untitled Policy")),
        ("Document Type",   policy_data.get("doc_type", "Policy")),
        ("Version",         policy_data.get("version", "1.0")),
        ("Effective Date",  policy_data.get("effective_date", "—")),
        ("Policy Owner",    policy_data.get("owner", "—")),
    ]
    for i, (label, value) in enumerate(fields):
        row = table.rows[i]
        row.cells[0].text = label
        row.cells[1].text = str(value) if value else "—"

    doc.add_paragraph()

    # ── Sections ──────────────────────────────────────────────────────────────
    sections = [
        ("1. Purpose",               "purpose"),
        ("2. Scope",                 "scope"),
        ("3. Policy Statement",      "policy_statement"),
        ("4. Definitions",           "definitions"),
        ("5. Procedures",            "procedures"),
        ("6. Roles & Responsibilities", "roles_responsibilities"),
        ("7. Exceptions",            "exceptions"),
        ("8. Enforcement",           "enforcement"),
        ("9. References",            "references"),
    ]

    for title, key in sections:
        add_heading(title, level=1)
        content = policy_data.get(key)
        if not content:
            add_body("[Section not found in source document]")
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    add_bullet(f"{item.get('role', item.get('title', ''))}: {item.get('responsibility', item.get('description', str(item)))}")
                else:
                    add_bullet(str(item))
        else:
            add_body(str(content))
        doc.add_paragraph()

    # ── Framework mappings ────────────────────────────────────────────────────
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

    # ── Gaps ──────────────────────────────────────────────────────────────────
    gaps = policy_data.get("gaps", [])
    if gaps:
        add_heading("11. Gap Analysis", level=1)
        for gap in gaps:
            add_bullet(str(gap))
        doc.add_paragraph()

    # ── Revision history ──────────────────────────────────────────────────────
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

    # ── Footer ────────────────────────────────────────────────────────────────
    section = doc.sections[0]
    footer  = section.footer
    footer_para = footer.paragraphs[0]
    footer_para.text = f"{policy_data.get('policy_name', 'Policy')} · v{policy_data.get('version', '1.0')} · Midnight — Takeoff LLC · CONFIDENTIAL"
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_para.style.font.size = Pt(8)

    # ── Save to bytes ─────────────────────────────────────────────────────────
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


@router.post("/migrate")
async def migrate_document(
    file:          UploadFile = File(...),
    template_name: str        = Form(default="generic_policy"),
    industry:      str        = Form(default="Healthcare"),
    frameworks:    str        = Form(default="HIPAA,HiTrust"),
):
    """
    Full migration pipeline:
    upload .docx → Bird Eye extraction → Claude Opus reconstruction → .docx output
    """
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured on server.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    fw_list = [f.strip() for f in frameworks.split(",") if f.strip()]

    try:
        policy_data = await _extract_and_reconstruct(
            file_bytes=file_bytes,
            filename=file.filename,
            template_name=template_name,
            frameworks=fw_list,
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Claude returned invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration error: {str(e)}")

    # Build the output docx
    try:
        docx_bytes = _build_docx(policy_data, template_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document rendering error: {str(e)}")

    # Return as downloadable file
    output_name = file.filename.replace(".docx", "") + "_migrated.docx"
    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{output_name}"'},
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
- Map to applicable framework controls
- Procedures must be numbered step-by-step
- Return ONLY valid JSON, no markdown"""


class CreatePolicyRequest(BaseModel):
    policy_name: str
    doc_type:    str
    industry:    str
    frameworks:  list[str]
    owner:       str
    description: Optional[str] = None


@router.post("/create")
async def create_document(request: CreatePolicyRequest):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured on server.")

    fw_context = []
    for fw in request.frameworks:
        if fw in FRAMEWORK_CONTROLS:
            fw_context.append(f"{fw}: {', '.join(FRAMEWORK_CONTROLS[fw][:3])}")

    user_msg = (
        f"Policy Name: {request.policy_name}\n"
        f"Document Type: {request.doc_type}\n"
        f"Industry: {request.industry}\n"
        f"Frameworks: {', '.join(request.frameworks)}\n"
        f"Owner: {request.owner}\n"
        f"Description/Scope: {request.description or 'Not provided'}\n\n"
        f"Framework Controls Reference:\n{chr(10).join(fw_context)}\n\n"
        f"Create a complete enterprise policy document. Return only JSON."
    )

    try:
        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Creation error: {str(e)}")

    try:
        docx_bytes = _build_docx(policy_data, request.doc_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document rendering error: {str(e)}")

    output_name = f"{request.policy_name.replace(' ', '_')}_v1.0.docx"
    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{output_name}"'},
    )


# ── Gap analysis ──────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_document(
    file:       UploadFile = File(...),
    frameworks: str        = Form(default="HIPAA,PCI DSS,NIST CSF"),
):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured on server.")

    file_bytes = await file.read()
    fw_list    = [f.strip() for f in frameworks.split(",") if f.strip()]

    doc   = Document(BytesIO(file_bytes))
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    text  = "\n".join(lines)[:10000]

    fw_context = []
    for fw in fw_list:
        if fw in FRAMEWORK_CONTROLS:
            fw_context.append(f"{fw}: {', '.join(FRAMEWORK_CONTROLS[fw])}")

    user_msg = (
        f"FRAMEWORKS: {', '.join(fw_list)}\n\n"
        f"FRAMEWORK CONTROLS:\n{chr(10).join(fw_context)}\n\n"
        f"POLICY DOCUMENT:\n---\n{text}\n---\n\n"
        f"Analyze this policy against the framework controls. "
        f"Return JSON with: covered_controls, missing_controls, partial_controls, gaps, recommendations, overall_score (0-100)"
    )

    try:
        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            system="You are a GRC analyst. Analyze policy documents against compliance frameworks. Return only valid JSON.",
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = message.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return JSONResponse(content=json.loads(raw))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
