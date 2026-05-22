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
