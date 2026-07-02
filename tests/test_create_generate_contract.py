"""C1 regression: /pipeline/create/generate must return JSON (with a download
URL) when the Create Policy Studio asks for it (Accept: application/json), and
binary .docx for the dashboard/migrate blob callers. Before the fix it always
returned binary, so the Studio's response.json() threw and every successful
generation showed 'generation failed'."""

import types

import pytest
from fastapi.testclient import TestClient

from backend.api import routes
from backend.api.main import app, verify_access


BODY = {
    "policy_data": {
        "policy_name": "Access Control Policy",
        "version": "1.0",
        "doc_type": "POLICY",
        "_session": {"frameworks": ["HIPAA"], "policy_id": "p1", "source_name": "src"},
    }
}


@pytest.fixture
def client(monkeypatch):
    app.dependency_overrides[verify_access] = lambda: {"authenticated": True}
    # Stub out the heavy collaborators so we exercise only the response contract.
    monkeypatch.setattr(routes, "_tenant_context_from_request",
                        lambda request: {"id": "t1", "name": "Acme", "plan_type": "pro"})
    monkeypatch.setattr(routes, "_merge_sections_from_top_level", lambda pd: pd)
    monkeypatch.setattr(routes, "_normalize_policy_payload_or_400", lambda pd, **k: pd)
    monkeypatch.setattr(routes, "_ensure_required_slots_or_400", lambda pd: pd)
    monkeypatch.setattr(routes, "save_policy_draft", lambda **k: {"policy": {"id": "p1"}})
    monkeypatch.setattr(routes, "_identify_covered_controls", lambda **k: [])
    monkeypatch.setattr(routes, "update_policy_covered_controls", lambda *a, **k: None)
    monkeypatch.setattr(routes, "EVIDENCE_AGENT",
                        types.SimpleNamespace(run=lambda payload: types.SimpleNamespace(
                            evidence_requirements=[], readiness_summary="")))
    monkeypatch.setattr(routes, "_emit_signal", lambda *a, **k: None)
    # Avoid real docx build + Supabase storage; return a fake stored record.
    monkeypatch.setattr(routes, "_render_and_store_docx",
                        lambda **k: ({"id": "doc123"}, b"PKfakedocxbytes", "preview text"))
    tc = TestClient(app)
    yield tc
    app.dependency_overrides.clear()


def test_studio_gets_json_with_download_url(client):
    r = client.post("/pipeline/create/generate", json=BODY, headers={"Accept": "application/json"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    data = r.json()
    assert data["download"]["url"] == "/dashboard/documents/doc123/download"
    assert data["document_id"] == "doc123"
    assert data["policy_data"]["policy_name"] == "Access Control Policy"


def test_dashboard_still_gets_binary_docx(client):
    r = client.post("/pipeline/create/generate", json=BODY, headers={"Accept": "*/*"})
    assert r.status_code == 200
    assert r.headers["content-type"] == routes.DOCX_MIME
