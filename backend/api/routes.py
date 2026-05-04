"""
Midnight Core - Pipeline Routes
Takeoff LLC
"""

import json
import os
import re
import tempfile
import uuid
from io import BytesIO
from typing import Optional

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from dotenv import load_dotenv
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.core.framework_layer import (
    build_framework_mapping_rules,
    build_framework_prompt_context,
)
from backend.renderers.pdf_renderer import build_grc_summary_pdf
from backend.storage.file_store import save_generated_document, list_generated_documents

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None

try:
    import requests as _requests
except ImportError:  # pragma: no cover
    _requests = None

load_dotenv()

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
router = APIRouter(prefix="/pipeline", tags=["pipeline"])

GO_SERVICE_URL = os.getenv("GO_SERVICE_URL", "http://localhost:8080")

_FW_TO_GO = {
    "HIPAA": "HIPAA",
    "PCI DSS": "PCI_DSS",
    "NIST CSF": "NIST_CSF",
    "SOC 2": "SOC2",
    "HITRUST": "HITRUST",
    "ISO 27001": "ISO_27001",
}


def _go_framework_coverage(document: str, frameworks: list[str], title: str = "") -> list | None:
    if _requests is None:
        return None
    go_frameworks = [_FW_TO_GO[f] for f in frameworks if f in _FW_TO_GO]
    if not go_frameworks:
        return None
    try:
        resp = _requests.post(
            f"{GO_SERVICE_URL}/analyze",
            json={"title": title, "document": document, "frameworks": go_frameworks},
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json().get("frameworks", [])
    except Exception:
        return None


@router.get("/smoke-docx")
async def smoke_docx():
    path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.docx")

    doc = Document()
    doc.add_paragraph("Hello world")
    doc.save(path)

    return FileResponse(
        path=path,
        filename="smoke_test.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-opus-4-5"
SUPPORTED_EXTENSIONS = {".docx", ".txt", ".md"}

MIGRATE_SECTION_ALIASES = {
    "purpose": ["Purpose", "Purpose and Scope", "Background", "Overview", "Objective", "Introduction"],
    "definitions": ["Glossary", "Key Terms", "Definitions", "Terminology"],
    "policy_statement": [
        "Policy Statement",
        "Policy Body",
        "Policy Details",
        "Policy Content",
        "Policy Requirements",
        "Rules",
    ],
    "procedures": ["Procedures", "Process Steps", "Controls", "Implementation", "Guidelines"],
    "related_policies": ["Related Policies", "See Also", "References", "Associated Documents"],
    "citations_references": [
        "Citations / References",
        "Standards",
        "Regulatory References",
        "Citations",
        "Compliance References",
    ],
    "revision_history": ["Revision History", "Change Log", "Document History", "Version History"],
}

MIGRATE_HEADER_ALIASES = {
    "policy_name": ["Policy Name"],
    "policy_number": ["Policy Number"],
    "version": ["Version"],
    "grc_id": ["GRC ID"],
    "effective_date": ["Effective Date"],
    "supersedes_policy": ["Supersedes Policy"],
    "last_reviewed_date": ["Last Reviewed Date", "Last Reviewed"],
    "last_revised_date": ["Last Revised Date", "Last Revised"],
    "policy_custodian": ["Policy Custodian"],
    "policy_owner": ["Policy Owner"],
    "policy_approver": ["Policy Approver"],
}


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
        lines: list[str] = []

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


def _iter_docx_blocks(doc: Document):
    for child in doc.element.body.iterchildren():
        if child.tag.endswith("}p"):
            yield "paragraph", Paragraph(child, doc)
        elif child.tag.endswith("}tbl"):
            yield "table", Table(child, doc)


def _table_rows_to_lists(table: Table) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.rows:
        values = [cell.text or "" for cell in row.cells]
        if any(value.strip() for value in values):
            rows.append(values)
    return rows


def _extract_source_blocks(file_bytes: bytes, filename: str) -> list[dict]:
    lower = filename.lower()
    blocks: list[dict] = []

    if lower.endswith(".docx"):
        doc = Document(BytesIO(file_bytes))
        for kind, item in _iter_docx_blocks(doc):
            if kind == "paragraph":
                blocks.append({"kind": "paragraph", "text": item.text or ""})
            else:
                rows = _table_rows_to_lists(item)
                if rows:
                    blocks.append(
                        {
                            "kind": "table",
                            "rows": rows,
                            "text": "\n".join(" | ".join(row) for row in rows),
                        }
                    )
        return blocks

    text = _extract_text_from_upload(file_bytes, filename)
    for line in text.splitlines():
        blocks.append({"kind": "paragraph", "text": line})
    return blocks


def _normalize_source_label(text: str) -> str:
    normalized = re.sub(r"^[#>\-\*\s]+", "", str(text or "").strip())
    normalized = normalized.rstrip(":").strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _split_semicolons(value: str) -> str:
    return str(value or "").replace(";", "\n")


def _match_header_value(text: str) -> tuple[Optional[str], Optional[str]]:
    raw = str(text or "").strip()
    if not raw:
        return None, None

    for output_key, aliases in MIGRATE_HEADER_ALIASES.items():
        for alias in aliases:
            match = re.match(
                rf"^\s*{re.escape(alias)}\s*[:\-–]\s*(.+?)\s*$",
                raw,
                flags=re.IGNORECASE,
            )
            if match:
                return output_key, match.group(1)
    return None, None


def _match_section_heading(text: str) -> tuple[Optional[str], Optional[str]]:
    raw = str(text or "").strip()
    if not raw:
        return None, None

    normalized = _normalize_source_label(raw)
    for output_key, aliases in MIGRATE_SECTION_ALIASES.items():
        for alias in aliases:
            alias_normalized = _normalize_source_label(alias)
            if normalized == alias_normalized:
                return output_key, None

            match = re.match(
                rf"^\s*{re.escape(alias)}\s*[:\-–]\s*(.+?)\s*$",
                raw,
                flags=re.IGNORECASE,
            )
            if match:
                return output_key, match.group(1)
    return None, None


def _capture_header_rows(rows: list[list[str]], header_values: dict) -> bool:
    captured = False
    for row in rows:
        if len(row) < 2:
            continue
        key, value = _match_header_value(f"{row[0]}: {row[1]}")
        if key and value and not header_values.get(key):
            header_values[key] = value
            captured = True
    return captured


def _looks_like_revision_history_header(row: list[str]) -> bool:
    normalized = [_normalize_source_label(cell) for cell in row if str(cell or "").strip()]
    if not normalized:
        return False
    header_tokens = {"version", "date", "description", "change", "change log", "history"}
    return sum(token in header_tokens for token in normalized) >= 2


def _build_revision_history(rows: list[list[str]]) -> list[dict]:
    entries: list[dict] = []
    filtered_rows = [row for row in rows if any(str(cell or "").strip() for cell in row)]
    if filtered_rows and _looks_like_revision_history_header(filtered_rows[0]):
        filtered_rows = filtered_rows[1:]

    for row in filtered_rows:
        cleaned = [_split_semicolons(cell).strip() for cell in row]
        if not any(cleaned):
            continue
        entries.append(
            {
                "version": cleaned[0] if len(cleaned) > 0 else "",
                "date": cleaned[1] if len(cleaned) > 1 else "",
                "description": " | ".join(cell for cell in cleaned[2:] if cell) if len(cleaned) > 2 else "",
            }
        )
    return entries


def _join_verbatim_content(parts: list[str]) -> str:
    if not parts:
        return ""
    text = "\n".join(parts)
    return text.strip("\n")


def _map_migrate_source(file_bytes: bytes, filename: str) -> dict:
    blocks = _extract_source_blocks(file_bytes, filename)
    header_values: dict[str, str] = {}
    section_parts: dict[str, list[str]] = {key: [] for key in MIGRATE_SECTION_ALIASES}
    revision_rows: list[list[str]] = []
    current_section: Optional[str] = None

    for block in blocks:
        if block["kind"] == "paragraph":
            text = str(block.get("text", ""))
            if not text.strip():
                if current_section and current_section != "revision_history" and section_parts[current_section]:
                    section_parts[current_section].append("")
                continue

            header_key, header_value = _match_header_value(text)
            if header_key and header_value and not header_values.get(header_key):
                header_values[header_key] = header_value
                continue

            section_key, inline_value = _match_section_heading(text)
            if section_key:
                current_section = section_key
                if inline_value:
                    if section_key == "revision_history":
                        revision_rows.append([_split_semicolons(inline_value)])
                    else:
                        section_parts[section_key].append(_split_semicolons(inline_value))
                continue

            if current_section == "revision_history":
                revision_rows.append([_split_semicolons(text)])
            elif current_section:
                section_parts[current_section].append(_split_semicolons(text))
            continue

        rows = block.get("rows", [])
        if not rows:
            continue

        if _capture_header_rows(rows, header_values) and current_section is None:
            continue

        if current_section == "revision_history":
            revision_rows.extend(rows)
        elif current_section:
            for row in rows:
                section_parts[current_section].append(_split_semicolons(" | ".join(row)))

    related_policies = _join_verbatim_content(section_parts["related_policies"])
    citations_references = _join_verbatim_content(section_parts["citations_references"])
    combined_references_parts = []
    if related_policies:
        combined_references_parts.append(f"Related Policies\n{related_policies}")
    if citations_references:
        combined_references_parts.append(f"Citations / References\n{citations_references}")

    return {
        "headers": header_values,
        "purpose": _join_verbatim_content(section_parts["purpose"]),
        "definitions": _join_verbatim_content(section_parts["definitions"]),
        "policy_statement": _join_verbatim_content(section_parts["policy_statement"]),
        "procedures": _join_verbatim_content(section_parts["procedures"]),
        "related_policies": related_policies,
        "citations_references": citations_references,
        "combined_references": "\n\n".join(part for part in combined_references_parts if part),
        "revision_history": _build_revision_history(revision_rows),
    }


def _build_migrate_mapping_context(mapped_source: dict) -> str:
    header_lines = []
    for key in (
        "policy_name",
        "policy_number",
        "version",
        "grc_id",
        "effective_date",
        "supersedes_policy",
        "last_reviewed_date",
        "last_revised_date",
        "policy_custodian",
        "policy_owner",
        "policy_approver",
    ):
        value = mapped_source.get("headers", {}).get(key)
        if value:
            header_lines.append(f"{key}: {value}")

    section_lines = []
    for key in (
        "purpose",
        "definitions",
        "policy_statement",
        "procedures",
        "related_policies",
        "citations_references",
    ):
        value = mapped_source.get(key)
        if value:
            section_lines.append(f"{key.upper()}:\n{value}")

    revision_history = mapped_source.get("revision_history") or []
    if revision_history:
        revision_lines = ["REVISION_HISTORY:"]
        for entry in revision_history:
            revision_lines.append(
                f"{entry.get('version', '')} | {entry.get('date', '')} | {entry.get('description', '')}"
            )
        section_lines.append("\n".join(revision_lines))

    return "\n\n".join(
        part for part in ["\n".join(header_lines).strip(), "\n\n".join(section_lines).strip()] if part
    )


def _apply_migrate_source_mapping(policy_data: dict, mapped_source: dict) -> dict:
    updated = dict(policy_data or {})
    headers = mapped_source.get("headers", {}) or {}

    if headers.get("policy_name"):
        updated["policy_name"] = headers["policy_name"]
    if headers.get("version"):
        updated["version"] = headers["version"]
    if headers.get("effective_date"):
        updated["effective_date"] = headers["effective_date"]
    if headers.get("policy_owner"):
        updated["owner"] = headers["policy_owner"]

    for field in (
        "policy_number",
        "grc_id",
        "supersedes_policy",
        "last_reviewed_date",
        "last_revised_date",
        "policy_custodian",
        "policy_owner",
        "policy_approver",
    ):
        if headers.get(field):
            updated[field] = headers[field]

    if mapped_source.get("purpose"):
        updated["purpose"] = mapped_source["purpose"]
    if mapped_source.get("definitions"):
        updated["definitions"] = mapped_source["definitions"]
    if mapped_source.get("policy_statement"):
        updated["policy_statement"] = mapped_source["policy_statement"]
    if mapped_source.get("procedures"):
        updated["procedures"] = mapped_source["procedures"]
    if mapped_source.get("related_policies"):
        updated["related_policies"] = mapped_source["related_policies"]
    if mapped_source.get("citations_references"):
        updated["citations_references"] = mapped_source["citations_references"]
    if mapped_source.get("combined_references"):
        updated["references"] = mapped_source["combined_references"]
    if mapped_source.get("revision_history"):
        updated["revision_history"] = mapped_source["revision_history"]

    return updated


def _strip_json_fences(raw: str) -> str:
    return raw.replace("```json", "").replace("```", "").strip()


def _build_preview_text(policy_data: dict) -> str:
    for key in ("purpose", "scope", "policy_statement"):
        candidate = policy_data.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip().replace("\n", " ")[:280]
    return "Document generated successfully."


def _safe_text(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _write_temp_docx(docx_bytes: bytes) -> str:
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"{uuid.uuid4()}.docx")
    with open(output_path, "wb") as f:
        f.write(docx_bytes)
    return output_path


def _file_docx_response(
    *,
    policy_data: dict,
    template_name: str,
    output_name: str,
    document_name: str,
    doc_type: str,
    source_name: str,
) -> FileResponse:
    try:
        docx_bytes = _build_docx(policy_data, template_name)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Document rendering error: {exc}") from exc

    if not docx_bytes:
        raise HTTPException(status_code=500, detail="Document rendering produced an empty file.")

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

    temp_path = _write_temp_docx(docx_bytes)

    return FileResponse(
        path=temp_path,
        filename=output_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "X-Midnight-Preview": preview_text,
            "X-Midnight-Document-Id": record["id"],
        },
    )


class BirdsongRequest(BaseModel):
    messages: list[dict]
    system: Optional[str] = None


@router.get("/smoke-docx")
async def smoke_docx():
    doc = Document()
    doc.add_paragraph("Hello world from Midnight Core")
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    temp_path = _write_temp_docx(buffer.read())

    return FileResponse(
        path=temp_path,
        filename="smoke_test.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


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
            max_tokens=8096,
            system=system,
            messages=request.messages,
        )
        return {"reply": message.content[0].text}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
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
- For mapped source sections and header fields, copy content verbatim.
- Never paraphrase or summarize mapped source sections.
- Preserve bullets, indentation, and numbered lists exactly for mapped source sections.
- Replace semicolons in mapped body content with line breaks.
- Never append unmapped content to the end of the document.
- Do not restructure source tables.
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
    mapped_source = _map_migrate_source(file_bytes, filename)
    mapped_context = _build_migrate_mapping_context(mapped_source)

    normalized_frameworks, fw_context = build_framework_prompt_context(frameworks)
    mapping_rules = build_framework_mapping_rules(frameworks)

    user_msg = (
        f"DOCUMENT: {filename}\n"
        f"TEMPLATE TYPE: {template_name}\n"
        f"FRAMEWORKS TO MAP: {', '.join(normalized_frameworks)}\n"
        f"FRAMEWORK CONTROLS REFERENCE:\n{chr(10).join(fw_context)}\n\n"
        f"MAPPING RULES: {mapping_rules}\n\n"
        f"VERBATIM SOURCE MAPPING:\n---\n{mapped_context or 'No deterministic section matches found.'}\n---\n\n"
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
    policy_data = json.loads(_strip_json_fences(message.content[0].text))
    return _apply_migrate_source_mapping(policy_data, mapped_source)


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
        return heading

    def add_body(text: str):
        paragraph = doc.add_paragraph(_safe_text(text))
        return paragraph

    def add_bullet(text: str):
        doc.add_paragraph(_safe_text(text), style="List Bullet")

    fields = [
        ("Policy Name", policy_data.get("policy_name", "Untitled Policy")),
        ("Document Type", policy_data.get("doc_type", "Policy")),
        ("Version", policy_data.get("version", "1.0")),
        ("Effective Date", policy_data.get("effective_date", "-")),
        ("Policy Owner", policy_data.get("owner", "-")),
    ]

    table = doc.add_table(rows=len(fields), cols=2)
    table.style = "Table Grid"

    for index, (label, value) in enumerate(fields):
        row = table.rows[index]
        row.cells[0].text = _safe_text(label)
        row.cells[1].text = _safe_text(value)

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
                    desc = item.get("responsibility") or item.get("description") or item
                    text = f"{label}: {desc}" if label else _safe_text(desc)
                    add_bullet(text)
                else:
                    add_bullet(item)
        else:
            add_body(content)

        doc.add_paragraph()

    framework_mappings = policy_data.get("framework_mappings", {})
    if framework_mappings:
        add_heading("10. Framework Mappings", level=1)
        for framework, controls in framework_mappings.items():
            if not controls:
                continue
            add_heading(_safe_text(framework), level=2)
            if isinstance(controls, list):
                for control in controls:
                    add_bullet(control)
            else:
                add_body(controls)
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
                add_bullet(gap)
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
                row[0].text = _safe_text(entry.get("version", ""))
                row[1].text = _safe_text(entry.get("date", ""))
                row[2].text = _safe_text(entry.get("description", entry.get("change", "")))
            else:
                row[0].text = _safe_text(entry)
                row[1].text = ""
                row[2].text = ""
    else:
        add_body("[No revision history found in source document]")

    footer = doc.sections[0].footer.paragraphs[0]
    footer.text = (
        f"{policy_data.get('policy_name', 'Policy')} · "
        f"v{policy_data.get('version', '1.0')} · "
        "Midnight - Takeoff LLC · CONFIDENTIAL"
    )
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

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
    except Exception as exc:  # pragma: no cover
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

    return _file_docx_response(
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
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Migration error: {exc}") from exc

    base_name = (upload.filename or "document").rsplit(".", 1)[0]
    return _file_docx_response(
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
    except Exception as exc:  # pragma: no cover
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

    return _file_docx_response(
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
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Creation error: {exc}") from exc

    output_name = f"{request.policy_name.replace(' ', '_')}_v1.0.docx"
    return _file_docx_response(
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
        result = json.loads(_strip_json_fences(message.content[0].text))
        go_coverage = _go_framework_coverage(raw_text, normalized_frameworks, file.filename or "")
        if go_coverage:
            result["framework_coverage"] = go_coverage
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Analysis error: {exc}") from exc
