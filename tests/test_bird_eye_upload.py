"""
Structural tests for Bird Eye upload routes.

These tests verify that routes exist, require authentication, and reject
malformed requests. They do NOT require live Supabase or Voyage AI keys —
no embeddings are generated, no rows are written.
"""

import io

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_ingest_requires_file(client):
    """POST /bird-eye/ingest without a file body → 401 or 422.

    Auth middleware fires before body validation, so an unauthenticated request
    without a file body returns 401. Either 401 or 422 indicates the route
    rejects the bad request for the right reason.
    """
    response = client.post("/bird-eye/ingest")
    assert response.status_code in (401, 422)


def test_ingest_requires_auth(client):
    """POST /bird-eye/ingest with a valid file but no session cookie → 401."""
    file_bytes = io.BytesIO(b"Sample policy content for testing.")
    response = client.post(
        "/bird-eye/ingest",
        files={"file": ("test_policy.txt", file_bytes, "text/plain")},
    )
    assert response.status_code == 401


def test_library_summary_requires_auth(client):
    """GET /bird-eye/library-summary without a session cookie → 401."""
    response = client.get("/bird-eye/library-summary")
    assert response.status_code == 401


def test_findings_requires_auth(client):
    """GET /bird-eye/findings without a session cookie → 401."""
    response = client.get("/bird-eye/findings")
    assert response.status_code == 401


def test_map_controls_at_ingest_persists_ids(monkeypatch):
    """Uploaded docs get control mapping at ingest (previously always [])."""
    from backend.bird_eye import api as be_api

    monkeypatch.setattr(
        be_api, "db_select",
        lambda *a, **k: [{"heading": "Authentication", "content": "MFA required"}],
    )
    captured = {}

    def fake_identify(*, sections, doc_type, frameworks):
        captured["doc_type"] = doc_type
        captured["frameworks"] = frameworks
        return ["SOC2-CC6.1"]

    def fake_update(policy_id, covered):
        captured["persisted"] = (policy_id, covered)

    import backend.api.routes as routes
    import backend.storage.file_store as fs
    monkeypatch.setattr(routes, "_identify_covered_controls", fake_identify)
    monkeypatch.setattr(fs, "update_policy_covered_controls", fake_update)

    covered = be_api._map_controls_at_ingest(
        "tenant-1",
        {"policy_id": "pol-9", "artifact_type": "runbook", "metadata": {"frameworks": ["SOC 2"]}},
    )
    assert covered == ["SOC2-CC6.1"]
    assert captured["doc_type"] == "INCIDENT_RUNBOOK"
    assert captured["frameworks"] == ["SOC 2"]
    assert captured["persisted"] == ("pol-9", ["SOC2-CC6.1"])


def test_map_controls_at_ingest_no_sections_noop(monkeypatch):
    from backend.bird_eye import api as be_api

    monkeypatch.setattr(be_api, "db_select", lambda *a, **k: [])
    assert be_api._map_controls_at_ingest("tenant-1", {"policy_id": "pol-9"}) == []
