"""Tier restructure fences (The Angle §4): FREE is one watermarked,
preview-only generation; STARTER caps documents per month and cannot see the
gap list; PRO unlocks the list and export. Every fence returns a 403 whose
detail carries code=upgrade_required so the UI can render the upsell."""

import types

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from backend.api import dashboard, routes
from backend.api.main import app, verify_access


BODY = {
    "policy_data": {
        "policy_name": "Access Control Policy",
        "version": "1.0",
        "doc_type": "POLICY",
        "_session": {"frameworks": ["HIPAA"], "policy_id": "p1", "source_name": "src"},
    }
}


def _stub_generate_collaborators(monkeypatch, plan_type: str, generated_count: int):
    monkeypatch.setattr(routes, "_tenant_context_from_request",
                        lambda request: {"id": "t1", "name": "Acme", "plan_type": plan_type})
    monkeypatch.setattr(routes, "count_activity_for_tenant",
                        lambda tenant_id, **k: generated_count)
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
    calls = {}

    def fake_render(**kwargs):
        calls["watermark_exports"] = kwargs.get("watermark_exports")
        return {"id": "doc123"}, b"PKfakedocxbytes", "preview text"

    monkeypatch.setattr(routes, "_render_and_store_docx", fake_render)
    return calls


@pytest.fixture
def client():
    app.dependency_overrides[verify_access] = lambda: {"authenticated": True}
    tc = TestClient(app)
    yield tc
    app.dependency_overrides.clear()


def _assert_upgrade_403(response):
    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["code"] == "upgrade_required"
    assert detail["message"]


# ── Free plan: one generation, watermarked, export locked ─────────────────────

def test_free_first_generation_is_watermarked_and_export_locked(client, monkeypatch):
    calls = _stub_generate_collaborators(monkeypatch, "free", generated_count=0)
    r = client.post("/pipeline/create/generate", json=BODY, headers={"Accept": "application/json"})
    assert r.status_code == 200
    data = r.json()
    assert data["export_locked"] is True
    assert data["download"] is None
    assert calls["watermark_exports"] is True


def test_free_second_generation_is_fenced(client, monkeypatch):
    _stub_generate_collaborators(monkeypatch, "free", generated_count=1)
    r = client.post("/pipeline/create/generate", json=BODY, headers={"Accept": "application/json"})
    _assert_upgrade_403(r)


def test_free_binary_download_path_is_fenced(client, monkeypatch):
    _stub_generate_collaborators(monkeypatch, "free", generated_count=0)
    r = client.post("/pipeline/create/generate", json=BODY, headers={"Accept": "*/*"})
    _assert_upgrade_403(r)


# ── Starter: export unlocked, ten documents a month, no watermark ─────────────

def test_starter_generation_exports_clean(client, monkeypatch):
    calls = _stub_generate_collaborators(monkeypatch, "starter", generated_count=3)
    r = client.post("/pipeline/create/generate", json=BODY, headers={"Accept": "application/json"})
    assert r.status_code == 200
    data = r.json()
    assert data["export_locked"] is False
    assert data["download"]["url"] == "/dashboard/documents/doc123/download"
    assert calls["watermark_exports"] is False


def test_starter_monthly_cap_is_fenced(client, monkeypatch):
    _stub_generate_collaborators(monkeypatch, "starter", generated_count=10)
    r = client.post("/pipeline/create/generate", json=BODY, headers={"Accept": "application/json"})
    _assert_upgrade_403(r)


def test_legacy_trial_rows_behave_as_free(client, monkeypatch):
    _stub_generate_collaborators(monkeypatch, "trial", generated_count=1)
    r = client.post("/pipeline/create/generate", json=BODY, headers={"Accept": "application/json"})
    _assert_upgrade_403(r)


# ── Model routing: free is Haiku-only ─────────────────────────────────────────

def test_free_routes_every_slot_to_structural_model():
    from backend.billing_plans import limits_for
    assert routes._model_for_slot("procedures", limits_for("free")) == routes.STRUCTURAL_MODEL
    assert routes._model_for_slot("procedures", limits_for("starter")) == routes.CREATIVE_MODEL
    assert routes._model_for_slot("procedures", limits_for("pro")) == routes.CREATIVE_MODEL
    assert routes._model_for_slot("definitions", limits_for("pro")) == routes.STRUCTURAL_MODEL


# ── Dashboard fences: gap list lock, gaps PDF, document download ──────────────

_FAKE_GAP_RESULT = {
    "total_gaps": 2,
    "gaps_critical": 1,
    "gaps_medium": 1,
    "gaps_low": 0,
    "overall_coverage_pct": 61,
    "frameworks_checked": ["HIPAA"],
    "coverage_by_framework": {"HIPAA": 61},
    "gaps": [
        {"control_id": "AC-1", "framework": "HIPAA", "description": "d",
         "severity": "critical", "affected_frameworks": ["HIPAA"], "suggested_action": "a"},
        {"control_id": "AC-2", "framework": "HIPAA", "description": "d",
         "severity": "medium", "affected_frameworks": ["HIPAA"], "suggested_action": "a"},
    ],
}


@pytest.fixture
def dash_client(monkeypatch):
    plan_holder = {"plan": "free"}

    def override(request: Request):
        request.state.tenant_id = "t1"
        request.state.plan_type = plan_holder["plan"]
        request.state.auth_context = {"tenant_id": "t1", "plan_type": plan_holder["plan"],
                                      "organization_name": "Acme"}
        return request.state.auth_context

    app.dependency_overrides[verify_access] = override
    monkeypatch.setattr(dashboard, "_gap_result", lambda request: dict(_FAKE_GAP_RESULT))
    tc = TestClient(app)
    yield tc, plan_holder
    app.dependency_overrides.clear()


def test_gap_list_locked_below_pro(dash_client):
    tc, plan = dash_client
    for tier in ("free", "starter"):
        plan["plan"] = tier
        data = tc.get("/dashboard/gaps").json()
        assert data["locked"] is True, tier
        assert data["items"] == [], tier
        assert data["total"] == 2, tier
        assert data["overall_coverage_pct"] == 61, tier


def test_gap_list_full_on_pro(dash_client):
    tc, plan = dash_client
    plan["plan"] = "pro"
    data = tc.get("/dashboard/gaps").json()
    assert data["locked"] is False
    assert len(data["items"]) == 2
    assert data["items"][0]["control_id"] == "AC-1"


def test_gaps_pdf_fenced_below_pro(dash_client):
    tc, plan = dash_client
    plan["plan"] = "starter"
    _assert_upgrade_403(tc.get("/dashboard/gaps/pdf"))


def test_document_download_fenced_on_free(dash_client):
    tc, plan = dash_client
    plan["plan"] = "free"
    _assert_upgrade_403(tc.get("/dashboard/documents/doc123/download"))
