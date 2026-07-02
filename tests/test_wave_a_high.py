"""Wave A HIGH regressions: H3 (download by path, not expiring signed URL),
H4 (framework citations grounded in the registry), H5 (ISO 27001 reaches
the generator)."""

from backend.storage import file_store as fs
from backend.api import routes
from backend.core import framework_layer as fl


# ── H3: download by storage path (never expires), not the stored signed URL ──

def test_download_prefers_storage_path(monkeypatch):
    calls = {}
    monkeypatch.setattr(fs, "get_generated_document",
                        lambda w, d: {"id": d, "stored_path": "t/p/doc.docx", "storage_url": "https://signed"})
    monkeypatch.setattr(fs, "_download_storage_object_by_path",
                        lambda p: calls.__setitem__("by_path", p) or b"BYTES")
    monkeypatch.setattr(fs, "_download_storage_object",
                        lambda u: calls.__setitem__("by_url", u) or b"URLBYTES")
    _rec, data = fs.download_generated_document("t", "doc1")
    assert calls.get("by_path") == "t/p/doc.docx"
    assert "by_url" not in calls        # the expiring signed URL is not used
    assert data == b"BYTES"


def test_download_falls_back_to_signed_url_when_no_path(monkeypatch):
    monkeypatch.setattr(fs, "get_generated_document",
                        lambda w, d: {"id": d, "stored_path": "", "storage_url": "https://signed"})
    monkeypatch.setattr(fs, "_download_storage_object_by_path", lambda p: b"BYPATH")
    monkeypatch.setattr(fs, "_download_storage_object", lambda u: b"BYURL")
    _rec, data = fs.download_generated_document("t", "doc1")
    assert data == b"BYURL"


# ── H4: framework mappings rendered only from registry-valid controls ────────

def test_grounded_mappings_drops_hallucinated_ids():
    grouped = routes._grounded_framework_mappings(
        ["SOC2-CC6.1", "ISO-A.5.15", "FAKE-999", "HIPAA-164.308(a)(1)"]
    )
    # Real controls are grouped by framework; the fabricated id is dropped.
    assert "SOC 2" in grouped and any("SOC2-CC6.1" in x for x in grouped["SOC 2"])
    assert "ISO 27001" in grouped and any("ISO-A.5.15" in x for x in grouped["ISO 27001"])
    assert "HIPAA" in grouped
    flat = [x for v in grouped.values() for x in v]
    assert not any("FAKE-999" in x for x in flat)


def test_grounded_mappings_empty_for_all_invalid():
    assert routes._grounded_framework_mappings(["NOPE-1", "BOGUS-2"]) == {}


# ── H5: ISO 27001 library is wired into the generation prompt context ────────

def test_iso_in_public_framework_files():
    assert "ISO 27001" in fl.PUBLIC_FRAMEWORK_FILES
    loaded = fl.load_public_frameworks()
    assert len(loaded.get("ISO 27001", [])) >= 90  # full 2022 Annex A


def test_iso_aliases_resolve():
    assert fl.FRAMEWORK_ALIASES.get("ISO 27001:2022") == "ISO 27001"
    assert fl.FRAMEWORK_ALIASES.get("ISO27001") == "ISO 27001"
