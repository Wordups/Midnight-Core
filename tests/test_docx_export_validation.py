"""C4 regression: the export path must validate the .docx and reject silent
section holes before serving. Before this gate, a document containing
'[Section not found in source document]' was stored status='ready' and handed
to the customer — an incomplete policy presented as complete."""

import io

import pytest
from docx import Document
from fastapi import HTTPException

from backend.agents.validators.schema_validator import validate_schema_bytes
from backend.api import routes


def _docx(*paragraphs: str) -> bytes:
    d = Document()
    for p in paragraphs:
        d.add_paragraph(p)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def test_valid_docx_passes_schema():
    r = validate_schema_bytes(_docx("Purpose", "Scope"))
    assert r.ok is True
    assert r.body_paragraphs >= 2


def test_garbage_and_empty_fail_schema():
    assert validate_schema_bytes(b"not a docx").ok is False
    assert validate_schema_bytes(b"").ok is False


def test_export_gate_rejects_section_holes():
    holed = _docx("Purpose", "[Section not found in source document]")
    assert routes._missing_section_count(holed) >= 1
    with pytest.raises(HTTPException) as ei:
        routes._assert_export_docx_ok(holed)
    assert ei.value.status_code == 422


def test_export_gate_passes_complete_doc():
    good = _docx("Purpose", "Scope", "Roles and responsibilities")
    assert routes._missing_section_count(good) == 0
    routes._assert_export_docx_ok(good)  # must not raise


def test_export_gate_rejects_corrupt_bytes():
    with pytest.raises(HTTPException) as ei:
        routes._assert_export_docx_ok(b"corrupt-not-a-zip")
    assert ei.value.status_code == 500
