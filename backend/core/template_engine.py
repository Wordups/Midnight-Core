"""
Midnight Core — template_engine.py
Takeoff LLC

Real template engine: doc_type + variant → a styled DOCX shell from
backend/templates/packs/ (36 shells: 9 categories × 4 variants, imported from
the midnight-template-build collection). The shell's body is cleared but its
styles, fonts, headers, and section setup survive — so everything rendered
into it (headings, body, bullets) inherits the pack's typography.

Fail-open by design: a missing pack or unreadable shell falls back to a blank
python-docx Document, which is exactly the pre-template-engine behavior.
"""
from __future__ import annotations

import copy
import logging
from pathlib import Path

from docx import Document
from docx.shared import RGBColor

logger = logging.getLogger("midnight.template_engine")

PACKS_DIR = Path(__file__).resolve().parent.parent / "templates" / "packs"

VARIANTS = ("formal", "modern", "detailed", "executive")
DEFAULT_VARIANT = "modern"

# Studio doc types → pack category directories.
DOC_TYPE_TO_CATEGORY = {
    "POLICY": "policy",
    "STANDARD": "standard",
    "SOP": "procedure",
    "PROCEDURE": "procedure",
    "INCIDENT_RUNBOOK": "incident_runbook",
    "PLAYBOOK": "incident_runbook",
    "PROCESS_FLOW": "process_flow",
    "TRAINING": "training",
    "RISK_ASSESSMENT": "risk_assessment",
    "AUDIT_PACKAGE": "audit_package",
    "AI_GOVERNANCE": "ai_governance",
}

# Placeholder tokens the shells carry in headers/footers.
_PLACEHOLDERS = ("{{CLASSIFICATION}}", "{{ORG}}", "{{ORGANIZATION}}", "{{TITLE}}")


def normalize_variant(variant: str | None) -> str:
    v = str(variant or "").strip().lower()
    return v if v in VARIANTS else DEFAULT_VARIANT


def shell_path(doc_type: str, variant: str | None = None) -> Path | None:
    category = DOC_TYPE_TO_CATEGORY.get(str(doc_type or "").strip().upper())
    if not category:
        return None
    v = normalize_variant(variant)
    path = PACKS_DIR / category / v / f"{category}_{v}.docx"
    return path if path.exists() else None


_BUILTIN_STYLE_NAMES = (
    "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3", "Heading 4",
    "Heading 5", "Heading 6", "List Paragraph", "Strong", "Quote",
)


def _normalize_builtin_style_names(doc) -> None:
    """Pandoc-built shells store UI style names ("Heading 1") where python-docx
    expects internal names ("heading 1"), so styles["Heading 1"] — and
    doc.add_heading — KeyError even though iteration shows the style.
    Reassigning the name through python-docx's setter writes the internal
    form and makes lookups (and rendering) work."""
    from docx.styles import BabelFish

    for style in doc.styles:
        if style.name in _BUILTIN_STYLE_NAMES:
            try:
                # Write the internal form (e.g. "heading 1") — the getter
                # translates it back to the UI form, and lookups resolve.
                style.name = BabelFish.ui2internal(style.name)
            except Exception:
                continue


def _clear_body(doc) -> None:
    """Remove all body content, keeping section properties (headers/margins)."""
    body = doc.element.body
    for child in list(body):
        if child.tag.endswith("}sectPr"):
            continue
        body.remove(child)


def _replace_placeholder_text(doc, replacements: dict[str, str]) -> None:
    for section in doc.sections:
        for container in (section.header, section.footer):
            for paragraph in container.paragraphs:
                for token, value in replacements.items():
                    if token in paragraph.text:
                        for run in paragraph.runs:
                            if token in run.text:
                                run.text = run.text.replace(token, value)
                        # Token may span runs; last resort rebuilds the text.
                        if token in paragraph.text:
                            paragraph.text = paragraph.text.replace(token, value)


def _parse_hex_color(value: str | None) -> RGBColor | None:
    raw = str(value or "").strip().lstrip("#")
    if len(raw) != 6:
        return None
    try:
        return RGBColor(int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))
    except ValueError:
        return None


def apply_branding(doc, *, organization: str = "", title: str = "", primary_color: str | None = None,
                   classification: str = "Internal") -> None:
    """Tenant branding: header placeholders + brand color on Title/Heading styles."""
    _replace_placeholder_text(doc, {
        "{{CLASSIFICATION}}": classification or "Internal",
        "{{ORG}}": organization or "",
        "{{ORGANIZATION}}": organization or "",
        "{{TITLE}}": title or "",
    })
    color = _parse_hex_color(primary_color)
    if color is not None:
        for style_name in ("Title", "Heading 1", "Heading 2"):
            try:
                doc.styles[style_name].font.color.rgb = color
            except (KeyError, AttributeError):
                continue


def load_template_shell(doc_type: str, variant: str | None = None, *, branding: dict | None = None):
    """Return a python-docx Document ready to render into.

    Styled shell when a pack exists for (doc_type, variant); blank Document
    otherwise. Never raises — the export path must not fail on styling.
    """
    path = shell_path(doc_type, variant)
    if path is None:
        doc = Document()
        doc.is_template_shell = False
        return doc
    try:
        doc = Document(str(path))
        _normalize_builtin_style_names(doc)
        _clear_body(doc)
        doc.is_template_shell = True
        if branding:
            apply_branding(
                doc,
                organization=str(branding.get("organization") or ""),
                title=str(branding.get("title") or ""),
                primary_color=branding.get("primary_color"),
                classification=str(branding.get("classification") or "Internal"),
            )
        return doc
    except Exception as exc:
        logger.warning("template shell %s unusable (%s); falling back to blank", path, exc)
        doc = Document()
        doc.is_template_shell = False
        return doc
