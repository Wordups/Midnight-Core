"""Claude Opus 4.5 metadata extractor.

Single LLM call per ingested document. Returns a structured payload with:
- title, document_id, version, owner, status
- last_reviewed_at, next_review_at, effective_date (ISO-8601 strings)
- frameworks (list of canonical framework tags)
- numeric_requirements (dict[section_heading -> dict[key -> int|str])

This is the ONLY metadata extractor for Bird Eye. There is no regex fallback.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from backend.core.json_parser import ParsedModelOutputError, parse_model_json
from config import settings

logger = logging.getLogger("midnight.bird_eye.metadata_llm")

CLAUDE_MODEL = "claude-opus-4-5"
MAX_TEXT_CHARS = 60_000

FRAMEWORK_CANONICAL = {
    "soc 2": "SOC 2",
    "soc2": "SOC 2",
    "soc 2 type i": "SOC 2",
    "soc 2 type ii": "SOC 2",
    "hipaa": "HIPAA",
    "nist csf": "NIST CSF",
    "nist csf 2.0": "NIST CSF",
    "nist cybersecurity framework": "NIST CSF",
    "nist 800-53": "NIST 800-53",
    "nist 800-63b": "NIST 800-63B",
    "iso 27001": "ISO 27001",
    "iso/iec 27001": "ISO 27001",
    "iso27001": "ISO 27001",
    "pci dss": "PCI DSS",
    "pci-dss": "PCI DSS",
    "pci": "PCI DSS",
    "hitrust": "HITRUST",
}

NUMERIC_KEYS = {
    "password_min_length",
    "password_rotation_days",
    "password_reuse_count",
    "lockout_failed_attempts",
    "lockout_window_minutes",
    "lockout_duration_minutes",
    "session_idle_timeout_minutes",
    "session_max_duration_hours",
    "service_account_rotation_days",
    "customer_doc_retention_days",
    "breach_notification_hours",
    "tls_min_version",
    "aes_key_bits",
    "kms_key_rotation_days",
}


_PROMPT = """You are extracting structured metadata from a governance document (policy, standard, procedure, or runbook).

Return STRICT JSON only. No prose, no markdown fences. Schema:

{{
  "title": "string - the document title (e.g. 'Access Control Policy'). Required.",
  "document_id": "string|null - the external doc identifier if present (e.g. 'POL-001').",
  "version": "string|null - version identifier as written (e.g. '1.0', '0.9').",
  "owner": "string|null - the named owner. Return null if marked unassigned, TBD, '[unassigned]', or absent.",
  "status": "string|null - e.g. 'Active', 'Draft', 'Retired'.",
  "effective_date": "YYYY-MM-DD|null",
  "last_reviewed_at": "YYYY-MM-DD|null",
  "next_review_at": "YYYY-MM-DD|null",
  "frameworks": ["array of compliance frameworks declared in the front matter. Use canonical names: SOC 2, HIPAA, NIST CSF, NIST 800-53, NIST 800-63B, ISO 27001, PCI DSS, HITRUST. Empty array if none declared."],
  "artifact_type": "one of: policy | procedure | standard | runbook | risk_assessment | training | vendor",
  "sections": [
    {{
      "heading": "section heading exactly as it appears (e.g. '4.2 Password Requirements')",
      "numeric_requirements": {{
        // ONLY include keys for values explicitly present in the section. Omit keys that aren't stated.
        // Allowed keys:
        // password_min_length (integer characters)
        // password_rotation_days (integer days)
        // password_reuse_count (integer)
        // lockout_failed_attempts (integer)
        // lockout_window_minutes (integer)
        // lockout_duration_minutes (integer)
        // session_idle_timeout_minutes (integer)
        // session_max_duration_hours (integer)
        // service_account_rotation_days (integer)
        // customer_doc_retention_days (integer)
        // breach_notification_hours (integer)
        // tls_min_version (string like '1.2' or '1.3')
        // aes_key_bits (integer like 256)
        // kms_key_rotation_days (integer)
      }}
    }}
  ]
}}

Rules:
- Use the document body's own front matter for dates, version, owner, frameworks. Do not invent values.
- For owner, treat '[unassigned]', '_[unassigned]_', 'TBD', '—', '-', or empty as null.
- For frameworks, ONLY include those explicitly listed. Do not infer from body content.
- For numeric_requirements, ONLY include numeric / version values clearly stated in that section's body. Do not transcribe values from prose elsewhere.
- For password_rotation_days, only set it where the section is describing USER password rotation, not service-account rotation.
- For service_account_rotation_days, only set it where the section is describing service-account credential rotation.
- Return only the JSON object. No commentary.

Document text:
---
{text}
---
"""


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _strip_fences(s: str) -> str:
    return _FENCE_RE.sub("", s).strip()


def _normalize_framework(value: str) -> str:
    cleaned = value.strip().strip("`").strip()
    key = cleaned.lower()
    return FRAMEWORK_CANONICAL.get(key, cleaned)


def _coerce_iso_date(value: Any) -> str | None:
    if not value or not isinstance(value, str):
        return None
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", value.strip())
    if not m:
        return None
    try:
        from datetime import datetime, timezone
        dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        return None


def _coerce_numeric_requirements(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, Any] = {}
    for key, value in raw.items():
        if key not in NUMERIC_KEYS:
            continue
        if key == "tls_min_version":
            s = str(value).strip()
            if re.match(r"^\d+\.\d+$", s):
                out[key] = s
        else:
            try:
                out[key] = int(value)
            except (TypeError, ValueError):
                continue
    return out


def extract_metadata(raw_text: str, *, default_title: str | None = None) -> dict[str, Any]:
    """Call Claude Opus 4.5 once and parse its JSON response into our metadata shape.

    Raises RuntimeError on missing key, network failure, malformed JSON, or schema failure.
    There is no regex fallback by design - the spec says Claude Opus 4.5 only.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured; cannot run metadata extraction.")

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    truncated = raw_text[:MAX_TEXT_CHARS]
    prompt = _PROMPT.format(text=truncated)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    if not text.strip():
        raise RuntimeError("Claude metadata extractor returned an empty response")
    try:
        parsed = parse_model_json(text)
    except ParsedModelOutputError as exc:
        # Log a bounded preview of the raw output so the failure is
        # debuggable in CloudWatch without leaking arbitrary length.
        logger.warning(
            "metadata_llm_parse_failed",
            extra={"error": str(exc), "raw_output": text[:2000]},
        )
        raise RuntimeError(f"Claude metadata extractor returned unparseable JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("Claude metadata extractor returned non-object JSON")

    title = (parsed.get("title") or "").strip() or default_title
    if not title:
        raise RuntimeError("Claude metadata extractor did not return a title")

    frameworks_raw = parsed.get("frameworks") or []
    if not isinstance(frameworks_raw, list):
        frameworks_raw = []
    frameworks: list[str] = []
    seen: set[str] = set()
    for f in frameworks_raw:
        if not isinstance(f, str):
            continue
        norm = _normalize_framework(f)
        if norm not in seen:
            seen.add(norm)
            frameworks.append(norm)

    owner = parsed.get("owner")
    if isinstance(owner, str):
        owner_clean = owner.strip().strip("`").strip("*_")
        if owner_clean.lower() in {"[unassigned]", "_[unassigned]_", "unassigned", "tbd", "—", "-", "none", ""}:
            owner = None
        else:
            owner = owner_clean

    sections_payload = parsed.get("sections") or []
    if not isinstance(sections_payload, list):
        sections_payload = []
    sections: list[dict[str, Any]] = []
    for s in sections_payload:
        if not isinstance(s, dict):
            continue
        heading = (s.get("heading") or "").strip()
        if not heading:
            continue
        sections.append(
            {
                "heading": heading,
                "numeric_requirements": _coerce_numeric_requirements(s.get("numeric_requirements")),
            }
        )

    artifact_type = (parsed.get("artifact_type") or "").strip().lower()
    if artifact_type not in {"policy", "procedure", "standard", "runbook", "risk_assessment", "training", "vendor"}:
        artifact_type = "policy"

    return {
        "title": title.strip(),
        "document_id": (parsed.get("document_id") or None) or None,
        "version": (parsed.get("version") or None) or None,
        "owner": owner,
        "status": (parsed.get("status") or None) or None,
        "effective_date": _coerce_iso_date(parsed.get("effective_date")),
        "last_reviewed_at": _coerce_iso_date(parsed.get("last_reviewed_at")),
        "next_review_at": _coerce_iso_date(parsed.get("next_review_at")),
        "frameworks": frameworks,
        "artifact_type": artifact_type,
        "sections": sections,
    }
