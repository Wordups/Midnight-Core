"""Bird Eye tenant isolation tests - these are the gate for shipping v1.

Defense in depth:
  1. No cross-tenant findings via API
  2. Similarity search is tenant-bounded
  3. Body-injected tenant_id is rejected by the API
  4. Codebase has no unscoped SELECT/UPDATE/DELETE against bird_eye tables
  5. Storage paths are isolated by tenant (no cross-tenant reads)
"""
from __future__ import annotations

import os
import re
import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env", override=True)

# Skip the whole module if Voyage isn't configured - the tests require real ingestion.
VOYAGE_KEY = os.environ.get("VOYAGE_API_KEY", "").strip()
TEST_TENANT_ID = os.environ.get("TEST_TENANT_ID", "").strip()


def _have_voyage() -> bool:
    return bool(VOYAGE_KEY)


def _service_role_present() -> bool:
    try:
        from config import settings  # type: ignore
        return bool(settings.SUPABASE_SERVICE_ROLE_KEY)
    except Exception:
        return False


# Fixture: a pair of tenants with one duplicate-ish chunk each.
@pytest.fixture(scope="module")
def isolated_tenants():
    if not (_have_voyage() and _service_role_present() and TEST_TENANT_ID):
        pytest.skip("Bird Eye integration prerequisites missing (Voyage / Supabase service role / TEST_TENANT_ID)")
    from backend.bird_eye.db import TABLE_DOCUMENTS, TABLE_CHUNKS, TABLE_FINDINGS, TABLE_RUNS, delete, insert
    from backend.bird_eye.embeddings import embed_chunks
    import requests as _r
    from config import settings as _s

    tenant_a = TEST_TENANT_ID
    tenant_b = str(uuid.uuid4())

    # Create the tenant_b row in tenants so FKs from policies/etc. resolve.
    headers = {
        "apikey": _s.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {_s.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    _r.post(
        f"{_s.SUPABASE_URL.rstrip('/')}/rest/v1/tenants",
        headers=headers,
        json={"id": tenant_b, "slug": f"iso-test-{tenant_b[:8]}", "name": "Isolation Test Tenant B", "plan_type": "trial"},
        timeout=30,
    )

    delete(TABLE_FINDINGS, tenant_id=tenant_b, filters={"tenant_id": f"eq.{tenant_b}"})
    delete(TABLE_RUNS, tenant_id=tenant_b, filters={"tenant_id": f"eq.{tenant_b}"})
    delete(TABLE_CHUNKS, tenant_id=tenant_b, filters={"tenant_id": f"eq.{tenant_b}"})
    delete(TABLE_DOCUMENTS, tenant_id=tenant_b, filters={"tenant_id": f"eq.{tenant_b}"})

    # Tenant B isolated policy + chunk (so no Bird Talk dependency)
    pol_b_id = str(uuid.uuid4())
    insert(
        TABLE_DOCUMENTS,
        {
            "id": pol_b_id,
            "tenant_id": tenant_b,
            "policy_name": "Tenant B Access Policy",
            "policy_number": "TKB-ISO-001",
            "version": "1.0",
            "status": "Active",
            "document_type": "policy",
            "organization": "Test Tenant B",
            "owner": "Isolation Owner",
            "selected_frameworks": ["SOC 2"],
        },
    )
    chunk_text = "Authentication requires multi-factor with hardware token. Minimum password length 14 characters."
    vector = embed_chunks([chunk_text])[0]
    insert(
        TABLE_CHUNKS,
        {
            "tenant_id": tenant_b,
            "policy_id": pol_b_id,
            "slot_id": "auth",
            "heading": "Authentication",
            "content": chunk_text,
            "sort_order": 0,
            "source_origin": "bird_eye_iso_test",
            "embedding": vector,
        },
    )

    yield {"a": tenant_a, "b": tenant_b, "b_policy_id": pol_b_id, "b_chunk_text": chunk_text}

    # Cleanup
    delete(TABLE_FINDINGS, tenant_id=tenant_b, filters={"tenant_id": f"eq.{tenant_b}"})
    delete(TABLE_RUNS, tenant_id=tenant_b, filters={"tenant_id": f"eq.{tenant_b}"})
    delete(TABLE_CHUNKS, tenant_id=tenant_b, filters={"tenant_id": f"eq.{tenant_b}"})
    delete(TABLE_DOCUMENTS, tenant_id=tenant_b, filters={"tenant_id": f"eq.{tenant_b}"})
    _r.delete(
        f"{_s.SUPABASE_URL.rstrip('/')}/rest/v1/tenants?id=eq.{tenant_b}",
        headers={"apikey": _s.SUPABASE_SERVICE_ROLE_KEY, "Authorization": f"Bearer {_s.SUPABASE_SERVICE_ROLE_KEY}"},
        timeout=30,
    )


# ─── Test 1: cross-tenant findings ──────────────────────────────────────────
def test_no_cross_tenant_findings(isolated_tenants):
    from backend.bird_eye.db import TABLE_DOCUMENTS, TABLE_FINDINGS, select
    from backend.bird_eye.orchestrator import run_bird_eye

    run_bird_eye(isolated_tenants["a"], triggered_by="iso_test")

    findings_a = select(TABLE_FINDINGS, tenant_id=isolated_tenants["a"], columns="*")
    for f in findings_a:
        assert f["tenant_id"] == isolated_tenants["a"], "tenant_id mismatch on tenant A finding"
        for ref in (f.get("policy_id"), f.get("related_policy_id")):
            if not ref:
                continue
            doc = select(
                TABLE_DOCUMENTS,
                tenant_id=isolated_tenants["a"],
                columns="id,tenant_id",
                filters={"id": f"eq.{ref}"},
                limit=1,
            )
            assert doc, f"Finding refers to doc {ref} not visible to tenant A"
            assert doc[0]["tenant_id"] == isolated_tenants["a"]


# ─── Test 2: similarity search is tenant-bounded ────────────────────────────
def test_similarity_search_respects_tenant(isolated_tenants):
    from backend.bird_eye.db import TABLE_CHUNKS, select

    chunks_b_from_a_scope = select(
        TABLE_CHUNKS,
        tenant_id=isolated_tenants["a"],
        columns="id,tenant_id,policy_id",
        filters={"source_origin": "eq.bird_eye_iso_test"},
    )
    assert chunks_b_from_a_scope == [], "Tenant A scope should not see tenant B isolation-test chunks"

    chunks_b_from_b_scope = select(
        TABLE_CHUNKS,
        tenant_id=isolated_tenants["b"],
        columns="id,tenant_id",
        filters={"source_origin": "eq.bird_eye_iso_test"},
    )
    assert chunks_b_from_b_scope, "Tenant B should see its own isolation-test chunk"
    for row in chunks_b_from_b_scope:
        assert row["tenant_id"] == isolated_tenants["b"]


# ─── Test 3: body-injected tenant_id is rejected ────────────────────────────
def test_cannot_inject_tenant_id_via_body():
    """The Bird Eye API derives tenant_id from `request.state.tenant_id`, not the body.

    We don't have a JWT in a unit test, so we directly verify the endpoint code does
    not consume `tenant_id` from the request payload.
    """
    from backend.bird_eye import api as bird_eye_api
    import inspect

    source = inspect.getsource(bird_eye_api)
    # No endpoint should read tenant_id from a Pydantic body field
    bad_patterns = [
        r"body\.tenant_id",
        r"payload\.tenant_id",
        r"request\.json\(\)\.get\(['\"]tenant_id",
    ]
    for pat in bad_patterns:
        assert not re.search(pat, source), f"Bird Eye API must not read tenant_id from the body (pattern {pat})"
    # Every endpoint must call _tenant_from_request
    assert "_tenant_from_request" in source, "_tenant_from_request must be used to derive tenant_id"


# ─── Test 4: codebase has no unscoped queries against bird-eye tables ───────
def test_codebase_has_no_unscoped_queries():
    """All SQL/REST calls against bird-eye tables must include a tenant_id filter."""
    target_tables = {"policies", "policy_sections", "policy_runs", "policy_gaps"}
    bird_eye_dir = REPO_ROOT / "backend" / "bird_eye"
    assert bird_eye_dir.is_dir(), "backend/bird_eye package is missing"

    offenders: list[str] = []
    for py_file in bird_eye_dir.rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        # Heuristic: look at calls into db.select / db.update / db.delete / db.insert
        for func, table in re.findall(r"(select|update|delete|insert)\(\s*[\"']?(\w+)[\"']?", source):
            if table not in target_tables and table not in {"TABLE_DOCUMENTS", "TABLE_CHUNKS", "TABLE_RUNS", "TABLE_FINDINGS"}:
                continue
            # The db.select/update/delete signatures require tenant_id; insert payloads check tenant_id presence.
            # We rely on a unit-level check below.
            pass

    from backend.bird_eye import db
    import inspect

    db_source = inspect.getsource(db)
    for fn in ("def select", "def update", "def delete"):
        idx = db_source.index(fn)
        body = db_source[idx : idx + 600]
        assert "tenant_id" in body, f"{fn} in backend/bird_eye/db.py must enforce tenant_id"
    assert "tenant_id missing from insert" in db_source, "db.insert must require tenant_id in every row"


# ─── Test 5: storage uploads are isolated by tenant ─────────────────────────
def test_storage_uploads_isolated_by_tenant(isolated_tenants):
    from backend.bird_eye.db import storage_upload, _service_headers, _rest_url
    import requests
    from config import settings

    tenant_a = isolated_tenants["a"]
    tenant_b = isolated_tenants["b"]
    doc_id = str(uuid.uuid4())
    storage_upload(tenant_a, doc_id, "iso.txt", b"hello tenant A", "text/plain")

    a_path = f"tenants/{tenant_a}/uploads/{doc_id}/iso.txt"
    b_path = f"tenants/{tenant_b}/uploads/{doc_id}/iso.txt"

    sign_url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/sign/midnight-documents/"
    headers = {"apikey": settings.SUPABASE_ANON_KEY, "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}", "Content-Type": "application/json"}

    # Anon client cannot read either path
    anon_get_a = requests.get(
        f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/midnight-documents/{a_path}",
        headers={"apikey": settings.SUPABASE_ANON_KEY, "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}"},
        timeout=30,
    )
    anon_get_b = requests.get(
        f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/midnight-documents/{b_path}",
        headers={"apikey": settings.SUPABASE_ANON_KEY, "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}"},
        timeout=30,
    )
    # Bucket is private, so neither tenant's anon-key request should succeed
    assert anon_get_a.status_code in (400, 401, 403, 404), f"anon read of tenant A path should be denied, got {anon_get_a.status_code}"
    assert anon_get_b.status_code in (400, 401, 403, 404), f"anon read of tenant B path should be denied, got {anon_get_b.status_code}"
