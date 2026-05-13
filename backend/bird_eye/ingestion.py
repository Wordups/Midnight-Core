"""Document ingestion pipeline for Bird Eye Review.

Pipeline:
1. Save raw bytes to Supabase Storage
2. Extract text from .docx/.pdf/.md/.txt
3. Single Claude Opus 4.5 call extracts ALL metadata: title, owner, version, dates,
   framework tags, artifact type, and numeric requirements per section.
4. Detect sections by heading regex (structural, separate from metadata)
5. Insert policy row in `policies`, insert section rows in `policy_sections` with embeddings
"""
from __future__ import annotations

import io
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from .db import (
    TABLE_DOCUMENTS,
    TABLE_CHUNKS,
    delete as db_delete,
    insert as db_insert,
    select as db_select,
    storage_upload,
)
from .embeddings import embed_chunks
from .metadata_llm import extract_metadata as llm_extract_metadata
from .tenant_guard import require_tenant

logger = logging.getLogger("midnight.bird_eye.ingestion")

ARTIFACT_TYPES = {"policy", "procedure", "standard", "runbook", "risk_assessment", "training", "vendor"}


def _extract_text_md(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def _extract_text_docx(content: bytes) -> str:
    from docx import Document  # type: ignore
    doc = Document(io.BytesIO(content))
    lines: list[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def _extract_text_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        from PyPDF2 import PdfReader  # type: ignore
    reader = PdfReader(io.BytesIO(content))
    chunks: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def extract_text(filename: str, content: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".docx"):
        return _extract_text_docx(content)
    if lower.endswith(".pdf"):
        return _extract_text_pdf(content)
    return _extract_text_md(content)


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
NUMBERED_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+([A-Z].{1,120})$")


def split_sections(raw_text: str) -> list[dict[str, str]]:
    """Split into section dicts with heading + content. Only main numbered sections (## ...) and their 4.x subsections."""
    sections: list[dict[str, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for raw_line in raw_text.splitlines():
        line = raw_line.rstrip()
        m = HEADING_RE.match(line.strip())
        if m:
            level = len(m.group(1))
            heading_text = m.group(2).strip()
            if level >= 2:
                if current_heading is not None:
                    sections.append({"heading": current_heading, "content": "\n".join(current_lines).strip()})
                current_heading = heading_text
                current_lines = []
                continue
        if current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections.append({"heading": current_heading, "content": "\n".join(current_lines).strip()})

    # Drop sections with empty content (just a sub-heading container) but keep their content rolled into next
    return [s for s in sections if s["content"] or s["heading"]]


# Mapping of section heading -> slot_id used in existing schema. Falls back to slugified heading.
SLOT_ALIASES = {
    "purpose": "purpose",
    "scope": "scope",
    "definitions": "definitions",
    "policy statements": "policy_statements",
    "standard requirements": "standard_requirements",
    "roles and responsibilities": "roles_and_responsibilities",
    "enforcement": "enforcement",
    "review cadence": "review_cadence",
}


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "section"


def _section_slot(heading: str) -> str:
    cleaned = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", heading).strip().lower()
    return SLOT_ALIASES.get(cleaned, _slug(cleaned)[:60])


def _normalize_heading_key(heading: str) -> str:
    return re.sub(r"\s+", " ", heading.strip().lower())


def _match_section_numerics(
    section_heading: str,
    llm_section_numerics: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Match a section heading produced by our structural split to the LLM's section list.

    Tolerates small differences (e.g. extra section numbering) via normalized substring match.
    """
    if not llm_section_numerics:
        return {}
    key = _normalize_heading_key(section_heading)
    if not key:
        return {}
    # Exact match
    for heading, reqs in llm_section_numerics.items():
        if _normalize_heading_key(heading) == key and reqs:
            return reqs
    # Substring match (either direction)
    for heading, reqs in llm_section_numerics.items():
        if not reqs:
            continue
        norm = _normalize_heading_key(heading)
        if norm in key or key in norm:
            return reqs
    return {}


def ingest_document(
    tenant_id: str,
    *,
    filename: str,
    file_bytes: bytes,
    artifact_type: str | None = None,
    title_override: str | None = None,
    skip_storage: bool = False,
    delete_existing_with_doc_id: bool = True,
) -> dict[str, Any]:
    """End-to-end ingestion. Returns the new policy row + chunk count."""
    require_tenant(tenant_id)

    text = extract_text(filename, file_bytes)
    if not text.strip():
        raise ValueError(f"No extractable text in {filename}")

    # Single Claude Opus 4.5 call extracts ALL metadata (title, owner, dates, frameworks,
    # artifact_type, per-section numeric requirements). No regex fallback by spec.
    metadata = llm_extract_metadata(text, default_title=title_override or filename)
    doc_id_external = metadata.get("document_id")
    title = metadata.get("title") or title_override or filename
    detected_type = artifact_type or metadata.get("artifact_type") or "policy"

    # Build a lookup from LLM-derived section heading -> numeric_requirements dict.
    # Headings may not match split_sections exactly, so we match best-effort by normalized substring.
    llm_section_numerics: dict[str, dict[str, Any]] = {}
    for s in metadata.get("sections") or []:
        heading = (s.get("heading") or "").strip()
        if heading:
            llm_section_numerics[heading] = s.get("numeric_requirements") or {}

    if delete_existing_with_doc_id and doc_id_external:
        from .db import TABLE_FINDINGS as _TF
        existing = db_select(
            TABLE_DOCUMENTS,
            tenant_id=tenant_id,
            columns="id",
            filters={"policy_number": f"eq.{doc_id_external}"},
        )
        for row in existing:
            pid = row.get("id")
            if pid:
                db_delete(_TF, tenant_id=tenant_id, filters={"policy_id": f"eq.{pid}"})
                db_delete(_TF, tenant_id=tenant_id, filters={"related_policy_id": f"eq.{pid}"})
                db_delete(TABLE_CHUNKS, tenant_id=tenant_id, filters={"policy_id": f"eq.{pid}"})
                db_delete(TABLE_DOCUMENTS, tenant_id=tenant_id, filters={"id": f"eq.{pid}"})

    new_id = str(uuid.uuid4())

    storage_path: str | None = None
    if not skip_storage:
        try:
            storage_path = storage_upload(tenant_id, new_id, filename, file_bytes)
        except Exception as exc:
            logger.warning("storage upload failed for %s: %s", filename, exc)
            storage_path = None

    doc_row = {
        "id": new_id,
        "tenant_id": tenant_id,
        "policy_name": title,
        "policy_number": doc_id_external,
        "version": metadata.get("version"),
        "status": metadata.get("status") or "Active",
        "document_type": detected_type,
        "organization": "Takeoff LLC",
        "owner": metadata.get("owner"),
        "selected_frameworks": metadata.get("frameworks") or [],
        "last_reviewed_at": metadata.get("last_reviewed_at"),
        "next_review_at": metadata.get("next_review_at"),
        "effective_date": metadata.get("effective_date"),
    }
    inserted = db_insert(TABLE_DOCUMENTS, doc_row)
    policy_id = inserted[0]["id"] if inserted else new_id

    # Chunks
    sections = split_sections(text)
    if not sections:
        sections = [{"heading": "Document", "content": text}]

    chunk_texts = [f"{s['heading']}\n{s['content']}" for s in sections]
    try:
        vectors = embed_chunks(chunk_texts, input_type="document")
    except Exception as exc:
        logger.warning("voyage embedding failed (%s); inserting chunks without vectors", exc)
        vectors = [[] for _ in chunk_texts]

    now_iso = datetime.now(timezone.utc).isoformat()
    chunk_rows: list[dict[str, Any]] = []
    for idx, section in enumerate(sections):
        vec = vectors[idx] if idx < len(vectors) else []
        numeric = _match_section_numerics(section["heading"], llm_section_numerics)
        embedding_payload = vec if vec else None
        chunk_rows.append(
            {
                "tenant_id": tenant_id,
                "policy_id": policy_id,
                "slot_id": _section_slot(section["heading"]),
                "heading": section["heading"],
                "content": section["content"],
                "sort_order": idx,
                "source_origin": "bird_eye_ingest",
                "embedding": embedding_payload,
                "numeric_requirements": numeric or None,
                "embedded_at": now_iso if vec else None,
            }
        )
    if chunk_rows:
        db_insert(TABLE_CHUNKS, chunk_rows)

    return {
        "policy_id": policy_id,
        "policy_number": doc_id_external,
        "title": title,
        "artifact_type": detected_type,
        "section_count": len(sections),
        "storage_path": storage_path,
        "metadata": metadata,
    }
