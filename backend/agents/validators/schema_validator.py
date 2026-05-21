"""Schema validator — confirms the file the docx-js subprocess produced
is a real, well-formed .docx.

We do NOT use python-docx here (its read path drifts from Word's
behavior on edge cases). Instead: open the file as a zip archive,
confirm the canonical OOXML parts are present, and parse the main
document XML to make sure it's not empty.
"""
from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

logger = logging.getLogger("midnight.trace_agent.schema_validator")

# Canonical parts of an OOXML word document.
REQUIRED_PARTS = (
    "[Content_Types].xml",
    "word/document.xml",
)

DOCUMENT_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class SchemaValidationResult:
    def __init__(self, ok: bool, error: str | None = None, body_paragraphs: int = 0):
        self.ok = ok
        self.error = error
        self.body_paragraphs = body_paragraphs

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "error": self.error,
            "body_paragraphs": self.body_paragraphs,
        }


def validate_schema(docx_path: str | Path) -> SchemaValidationResult:
    """Open the .docx as a zip, confirm required parts exist, parse the
    main document XML, count body paragraphs. Returns a result object
    rather than raising — TraceAgent's repair loop wants the failure
    reason as text."""
    docx_path = Path(docx_path)
    if not docx_path.exists():
        return SchemaValidationResult(False, f"File does not exist: {docx_path}")
    if docx_path.stat().st_size == 0:
        return SchemaValidationResult(False, "File is zero bytes")

    try:
        with zipfile.ZipFile(docx_path) as zf:
            names = set(zf.namelist())
            missing = [p for p in REQUIRED_PARTS if p not in names]
            if missing:
                return SchemaValidationResult(
                    False,
                    f"Missing required OOXML parts: {', '.join(missing)}",
                )
            with zf.open("word/document.xml") as f:
                document_xml = f.read()
    except zipfile.BadZipFile as exc:
        return SchemaValidationResult(False, f"Not a valid .docx (zip parse failed): {exc}")
    except KeyError as exc:
        return SchemaValidationResult(False, f"OOXML structure incomplete: {exc}")

    try:
        root = ET.fromstring(document_xml)
    except ET.ParseError as exc:
        return SchemaValidationResult(False, f"document.xml is not valid XML: {exc}")

    body = root.find(f"{DOCUMENT_NAMESPACE}body")
    if body is None:
        return SchemaValidationResult(False, "document.xml has no <w:body> element")

    paragraphs = body.findall(f"{DOCUMENT_NAMESPACE}p")
    if not paragraphs:
        return SchemaValidationResult(False, "document.xml body has zero paragraphs")

    return SchemaValidationResult(True, None, body_paragraphs=len(paragraphs))
