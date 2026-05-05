from __future__ import annotations

import json
import re
from typing import Any


SMART_QUOTES = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
)

_TRAILING_COMMAS_RE = re.compile(r",(\s*[}\]])")
_BARE_KEY_RE = re.compile(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)')
_PYTHON_LITERAL_REPLACEMENTS = (
    (re.compile(r"\bNone\b"), "null"),
    (re.compile(r"\bTrue\b"), "true"),
    (re.compile(r"\bFalse\b"), "false"),
)


class ParsedModelOutputError(ValueError):
    """Raised when model output cannot be normalized into valid JSON."""


class PolicySchemaError(ValueError):
    """Raised when structured policy JSON is missing required shape."""


def strip_markdown_fences(raw_text: str) -> str:
    text = str(raw_text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        while lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def extract_first_complete_json(raw_text: str) -> str:
    text = strip_markdown_fences(raw_text)
    start = -1
    opening = ""
    for idx, char in enumerate(text):
        if char in "{[":
            start = idx
            opening = char
            break
    if start < 0:
        raise ParsedModelOutputError("No JSON object or array found in model output.")

    closing = "}" if opening == "{" else "]"
    depth = 0
    in_string = False
    escaped = False

    for idx in range(start, len(text)):
        char = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return text[start : idx + 1]

    raise ParsedModelOutputError("Incomplete JSON object or array in model output.")


def _cleanup_candidate(json_text: str) -> str:
    candidate = json_text.translate(SMART_QUOTES)
    candidate = candidate.replace("\ufeff", "").replace("\u200b", "").strip()
    candidate = _TRAILING_COMMAS_RE.sub(r"\1", candidate)
    candidate = _BARE_KEY_RE.sub(r'\1"\2"\3', candidate)
    for pattern, replacement in _PYTHON_LITERAL_REPLACEMENTS:
        candidate = pattern.sub(replacement, candidate)
    return candidate


def parse_model_json(raw_text: str) -> Any:
    extracted = extract_first_complete_json(raw_text)
    candidates = []
    for candidate in (extracted, _cleanup_candidate(extracted)):
        if candidate not in candidates:
            candidates.append(candidate)

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc

    detail = str(last_error) if last_error else "Unable to decode model JSON."
    raise ParsedModelOutputError(detail)


def _coerce_section_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        lines: list[str] = []
        for item in value:
            if isinstance(item, dict):
                label = str(item.get("role") or item.get("title") or item.get("heading") or "").strip()
                body = str(
                    item.get("responsibility")
                    or item.get("description")
                    or item.get("content")
                    or item.get("body")
                    or ""
                ).strip()
                text = f"{label}: {body}".strip(": ").strip()
                if text:
                    lines.append(text)
            else:
                text = str(item).strip()
                if text:
                    lines.append(text)
        return "\n".join(lines).strip()
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def normalize_policy_payload(
    payload: dict[str, Any],
    *,
    organization_hint: str = "",
    required_frameworks: list[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise PolicySchemaError("Policy output must be a JSON object.")

    normalized = dict(payload)
    title = str(normalized.get("title") or normalized.get("policy_name") or "").strip()
    if not title:
        raise PolicySchemaError("Policy output is missing a title.")

    organization = str(normalized.get("organization") or organization_hint or "").strip()
    if not organization:
        raise PolicySchemaError("Policy output is missing an organization.")

    status = str(normalized.get("status") or "Draft").strip() or "Draft"
    metadata = normalized.get("metadata")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise PolicySchemaError("Policy metadata must be an object when provided.")

    sections = normalized.get("sections")
    if sections is None:
        sections = []
        inferred_sections = (
            ("purpose", "Purpose", normalized.get("purpose")),
            ("scope", "Scope", normalized.get("scope")),
            ("definitions", "Definitions", normalized.get("definitions")),
            ("roles_responsibilities", "Roles & Responsibilities", normalized.get("roles_responsibilities")),
            ("policy_statement", "Policy Statement", normalized.get("policy_statement")),
            ("procedures", "Procedures", normalized.get("procedures")),
            ("exceptions", "Exceptions", normalized.get("exceptions")),
            ("enforcement", "Enforcement", normalized.get("enforcement")),
            ("references", "References", normalized.get("references")),
            ("revision_history", "Revision History", normalized.get("revision_history")),
        )
        for slot_id, heading, content in inferred_sections:
            body = _coerce_section_text(content)
            if body:
                sections.append(
                    {
                        "slot_id": slot_id,
                        "heading": heading,
                        "content": body,
                    }
                )

    if not isinstance(sections, list) or not sections:
        raise PolicySchemaError("Policy sections must be a non-empty list.")

    normalized_sections: list[dict[str, str]] = []
    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            raise PolicySchemaError(f"Policy section {idx + 1} must be an object.")
        slot_id = str(section.get("slot_id") or "").strip()
        heading = str(section.get("heading") or section.get("title") or "").strip()
        content = _coerce_section_text(section.get("content") if "content" in section else section.get("body"))
        if not heading:
            raise PolicySchemaError(f"Policy section {idx + 1} is missing a heading.")
        if not content:
            raise PolicySchemaError(f"Policy section {idx + 1} is missing content.")
        normalized_sections.append(
            {
                "slot_id": slot_id or heading.lower().replace("&", "and").replace(" ", "_"),
                "heading": heading,
                "content": content,
            }
        )

    framework_mappings = normalized.get("framework_mappings")
    if framework_mappings is None:
        framework_mappings = {}
    if required_frameworks and not isinstance(framework_mappings, dict):
        raise PolicySchemaError("framework_mappings must be an object when frameworks are selected.")
    if not isinstance(framework_mappings, dict):
        raise PolicySchemaError("framework_mappings must be an object.")

    normalized["title"] = title
    normalized["policy_name"] = normalized.get("policy_name") or title
    normalized["organization"] = organization
    normalized["status"] = status
    normalized["metadata"] = metadata
    normalized["sections"] = normalized_sections
    normalized["framework_mappings"] = framework_mappings
    return normalized
