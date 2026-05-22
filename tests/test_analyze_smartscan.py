"""
Structural tests for /pipeline/analyze and /api/smart-scan/* routes.

Verifies route existence, auth enforcement, and basic request validation.
No live Supabase or Anthropic API calls are made.
"""

import io

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_analyze_requires_file(client):
    """POST /pipeline/analyze without a file → 401 (auth fires first) or 422.

    The auth middleware runs before FastAPI body validation, so an unauthenticated
    request without a file returns 401. Either status indicates the route rejects
    the bad request correctly.
    """
    response = client.post("/pipeline/analyze")
    assert response.status_code in (401, 422)


def test_analyze_requires_auth(client):
    """POST /pipeline/analyze with a valid file but no session cookie → 401."""
    file_bytes = io.BytesIO(b"Sample policy document for framework coverage analysis.")
    response = client.post(
        "/pipeline/analyze",
        data={"frameworks": "HIPAA,SOC 2"},
        files={"file": ("policy.txt", file_bytes, "text/plain")},
    )
    assert response.status_code == 401


def test_smartscan_run_requires_files(client):
    """POST /api/smart-scan/run without files → 401 (auth fires first) or 422."""
    response = client.post("/api/smart-scan/run")
    assert response.status_code in (401, 422)


def test_smartscan_preflight_requires_auth(client):
    """POST /api/smart-scan/preflight with a file but no session cookie → 401."""
    file_bytes = io.BytesIO(b"PK\x03\x04")  # minimal docx-like bytes
    response = client.post(
        "/api/smart-scan/preflight",
        files={"source_doc": ("policy.docx", file_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 401
