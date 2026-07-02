"""Multi-tenant isolation: a document fetch must always be scoped to the
authenticated tenant, so tenant A can never read tenant B's policy by id.
Catches the IDOR class (a dropped tenant_id filter)."""

from backend.storage import file_store as fs


def _capture(monkeypatch):
    captured = {}

    def fake_postgrest(method, table, params=None, **kwargs):
        captured["table"] = table
        captured["params"] = params or {}
        return []  # simulate: no row matches (cross-tenant → not found)

    monkeypatch.setattr(fs, "_postgrest", fake_postgrest)
    return captured


def test_get_document_is_tenant_scoped(monkeypatch):
    captured = _capture(monkeypatch)
    # Tenant A tries to read a document that belongs to tenant B.
    result = fs.get_generated_document("tenant-A", "doc-owned-by-B")
    assert result is None  # the tenant filter yields no row
    assert captured["table"] == "documents"
    assert captured["params"].get("tenant_id") == "eq.tenant-A"
    assert captured["params"].get("id") == "eq.doc-owned-by-B"


def test_download_raises_not_found_cross_tenant(monkeypatch):
    _capture(monkeypatch)
    try:
        fs.download_generated_document("tenant-A", "doc-owned-by-B")
    except fs.SupabaseStoreError as exc:
        assert "not found" in str(exc).lower()
    else:
        raise AssertionError("cross-tenant download should raise, not return a doc")
