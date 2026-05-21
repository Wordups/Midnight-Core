"""Spot checker — extracts visible text from the generated .docx with
docx2txt and confirms every section heading from the outline is present.

Uses docx2txt (read-only, pure-Python) per the locked design — the
"do not use python-docx" rule applies to the generator, not the
validator. Spec originally called for pandoc, but pandoc isn't in the
prod Dockerfile and docx2txt is a 50 KB drop-in replacement for the
"docx -> plain text" job we need here.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import docx2txt

logger = logging.getLogger("midnight.trace_agent.spot_checker")


class SpotCheckResult:
    def __init__(
        self,
        ok: bool,
        error: str | None = None,
        missing_sections: list[str] | None = None,
        found_sections: list[str] | None = None,
        extracted_chars: int = 0,
    ):
        self.ok = ok
        self.error = error
        self.missing_sections = missing_sections or []
        self.found_sections = found_sections or []
        self.extracted_chars = extracted_chars

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "error": self.error,
            "missing_sections": self.missing_sections,
            "found_sections": self.found_sections,
            "extracted_chars": self.extracted_chars,
        }


# Dash variants we canonicalize before comparison. LLMs legitimately emit
# any of these in headings; our outline YAML uses U+2014 (em-dash) by
# convention but Claude routinely produces U+002D (hyphen) or U+2013
# (en-dash) instead — that's cosmetic Unicode variation, not a content
# defect, and the spot-checker should tolerate it.
#
# U+FFFD (REPLACEMENT CHARACTER) is included because pipeline encoding
# failures (e.g. cp1252 -> UTF-8 mismatches at subprocess boundaries) can
# corrupt a real dash into U+FFFD. The encoding fix in
# generators/docx_generator.py prevents that at the source, but we
# normalize U+FFFD here as defense-in-depth — a future encoding boundary
# upstream shouldn't be able to fail the spot-checker silently.
#
# All four characters collapse to U+2014 (em-dash) as the canonical form,
# so a heading rendered with any dash variant matches an outline heading
# written with any dash variant.
_DASH_VARIANTS = "-–—�"
_DASH_CANONICAL = "—"
_DASH_TRANSLATION = str.maketrans({c: _DASH_CANONICAL for c in _DASH_VARIANTS})


def _normalize(text: str) -> str:
    """Lowercase + collapse whitespace + strip leading numbering +
    canonicalize dash variants. Section headings come back from docx with
    variable spacing, dash characters, and our outline uses 'N. Heading'
    form; normalize both sides before comparison."""
    text = (text or "").lower().strip()
    text = text.translate(_DASH_TRANSLATION)
    text = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def spot_check(docx_path: str | Path, outline: dict[str, Any]) -> SpotCheckResult:
    """Render the .docx to text and confirm every outline section heading
    appears somewhere in the output.

    The outline shape is the YAML-loaded dict from
    backend/agents/templates/outlines/<key>.yaml or the LLM-fallback
    equivalent — both expose a `sections` list with `heading` fields.

    A section is "present" if its normalized heading appears as a
    substring of the normalized extracted text. We don't require
    paragraph-level structural match — Word readers handle the visual
    side; we just need text-level confirmation that the content didn't
    get dropped.
    """
    docx_path = Path(docx_path)
    if not docx_path.exists():
        return SpotCheckResult(False, f"File does not exist: {docx_path}")

    sections = outline.get("sections") or []
    if not sections:
        return SpotCheckResult(False, "Outline has no sections to spot-check against")

    try:
        text = docx2txt.process(str(docx_path)) or ""
    except Exception as exc:  # pragma: no cover - docx2txt raises generic Exceptions
        return SpotCheckResult(False, f"docx2txt extraction failed: {exc}")

    normalized_text = _normalize(text)
    extracted_chars = len(text)

    found: list[str] = []
    missing: list[str] = []
    for section in sections:
        heading = section.get("heading") if isinstance(section, dict) else None
        if not heading:
            continue
        target = _normalize(str(heading))
        if not target:
            continue
        if target in normalized_text:
            found.append(heading)
        else:
            missing.append(heading)

    if missing:
        return SpotCheckResult(
            False,
            error=f"{len(missing)} of {len(found) + len(missing)} sections missing from rendered text",
            missing_sections=missing,
            found_sections=found,
            extracted_chars=extracted_chars,
        )

    return SpotCheckResult(
        True,
        found_sections=found,
        extracted_chars=extracted_chars,
    )
