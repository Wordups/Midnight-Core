"""End-to-end test for Trace Agent.

No mocks. Inserts a real generation_intake row via service-role, runs
the agent, asserts the artifacts exist and validate, then asserts the
activity_log row count + rationale population.

Skipped if the generation_intake table is missing — that means the
migration hasn't been applied yet. The test prints the migration path
in the skip message so the operator knows what to do.

Runtime: ~60-120s due to two real Anthropic calls (build_script and
possibly outline if the template doesn't match) plus the docx-js
subprocess.
"""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

import pytest
import requests

# Env scaffolding before any backend imports.
REPO_ROOT = Path(__file__).resolve().parents[1]
from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env", override=True)

# These must be present for the e2e test to run.
TEST_TENANT_ID = os.environ.get("TEST_TENANT_ID", "").strip()
VOYAGE_KEY = os.environ.get("VOYAGE_API_KEY", "").strip()  # not used directly; signals dev env


def _service_headers() -> dict[str, str]:
    from config import settings
    return {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _rest_url(path: str) -> str:
    from config import settings
    return f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/{path.lstrip('/')}"


def _generation_intake_table_exists() -> bool:
    try:
        r = requests.get(_rest_url("generation_intake?limit=0&select=id"),
                         headers={"apikey": _service_headers()["apikey"],
                                  "Authorization": _service_headers()["Authorization"]},
                         timeout=10)
    except Exception:
        return False
    return r.status_code == 200


def _activity_log_has_rationale_column() -> bool:
    """We can't introspect schema via Postgrest, but we can probe by
    inserting a probe row that uses the new column and rolling it back."""
    try:
        r = requests.post(
            _rest_url("activity_log"),
            headers=_service_headers(),
            data=json.dumps({
                "tenant_id": TEST_TENANT_ID,
                "action": "_trace_agent_test_probe",
                "step_number": 0,
                "step_name": "probe",
                "rationale": "schema-existence probe; safe to delete",
            }),
            timeout=10,
        )
    except Exception:
        return False
    if r.status_code >= 400:
        return False
    rows = r.json() or []
    if rows:
        # Clean up the probe row immediately.
        probe_id = rows[0].get("id")
        if probe_id:
            requests.delete(
                _rest_url(f"activity_log?id=eq.{probe_id}"),
                headers={"apikey": _service_headers()["apikey"],
                         "Authorization": _service_headers()["Authorization"]},
                timeout=10,
            )
    return True


# Hardcoded test payload, exactly per Brian's spec.
def _build_test_intake_payload(tenant_id: str, created_by: str) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "deliverable_type": "soc_playbook",
        "audience": "both",
        "framework_spine": ["NIST_800_61"],
        "maturity_posture": "both",
        "scope_boundary": {"cyber": True, "physical": True},
        "business_context": {
            "company_name": "Poof E Gone",
            "industry": "ITAD",
            "region": "DMV",
            "team_size": "small",
            "data_types": ["PII", "asset_inventory", "chain_of_custody"],
            "tech_stack": ["Supabase", "FastAPI"],
        },
        "declared_assumptions": {
            "severity_tiers": 4,
            "regulators": ["MD_AG", "VA_AG", "DC_AG", "HHS_OCR", "FBI_IC3"],
            "runbook_count": 11,
        },
        "created_by": created_by,
        "approved_at": "2026-05-18T10:00:00+00:00",
    }


@pytest.fixture(scope="module")
def _prereq_check():
    if not TEST_TENANT_ID:
        pytest.skip("TEST_TENANT_ID not set in .env; cannot run Trace Agent e2e.")
    from config import settings
    if not settings.ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not configured.")
    if not _generation_intake_table_exists():
        pytest.skip(
            "Migration not applied: generation_intake table does not exist. "
            "Apply supabase/migrations/20260518_trace_agent_intake_and_activity_log.sql "
            "via the Supabase SQL Editor before running this test."
        )
    if not _activity_log_has_rationale_column():
        pytest.skip(
            "Migration not applied: activity_log is missing rationale/step_number/step_name columns. "
            "Apply supabase/migrations/20260518_trace_agent_intake_and_activity_log.sql first."
        )


@pytest.fixture
def inserted_intake(_prereq_check):
    """Insert a real generation_intake row for this test run; clean up
    the intake row + every activity_log row + the test user_id rows on
    teardown."""
    created_by = str(uuid.uuid4())
    payload = _build_test_intake_payload(TEST_TENANT_ID, created_by)
    resp = requests.post(
        _rest_url("generation_intake"),
        headers=_service_headers(),
        data=json.dumps(payload),
        timeout=30,
    )
    assert resp.status_code < 400, f"Intake insert failed {resp.status_code}: {resp.text[:500]}"
    rows = resp.json() or []
    assert rows, "Intake insert returned no rows"
    intake_id = rows[0]["id"]

    yield {"intake_id": intake_id, "created_by": created_by, "tenant_id": TEST_TENANT_ID}

    # Cleanup — remove the activity_log rows tied to this run + the intake row.
    requests.delete(
        _rest_url(
            f"activity_log?tenant_id=eq.{TEST_TENANT_ID}"
            f"&action=like.trace_step_*"
            f"&created_at=gte.{payload['approved_at']}"
        ),
        headers={"apikey": _service_headers()["apikey"],
                 "Authorization": _service_headers()["Authorization"]},
        timeout=15,
    )
    requests.delete(
        _rest_url(f"generation_intake?id=eq.{intake_id}"),
        headers={"apikey": _service_headers()["apikey"],
                 "Authorization": _service_headers()["Authorization"]},
        timeout=15,
    )


def test_trace_agent_end_to_end(inserted_intake, tmp_path):
    """Hardcoded SOC playbook scenario; everything below is real I/O."""
    from backend.agents.trace_agent import TraceAgent

    intake_id = inserted_intake["intake_id"]
    agent = TraceAgent(output_dir=tmp_path)
    result = agent.run(intake_id)

    # ── Result invariants ────────────────────────────────────────────────
    assert result.intake_id == intake_id, f"intake_id mismatch: {result.intake_id} vs {intake_id}"
    assert result.status in {"complete", "draft"}, (
        f"Expected complete or draft, got {result.status}. Error: {result.error}"
    )
    assert result.outline_source == "template", (
        f"soc_playbook + NIST_800_61 should hit the template registry, got source={result.outline_source}"
    )

    # ── Artifacts exist + non-zero ───────────────────────────────────────
    assert result.docx_path, "docx_path is empty"
    assert result.trace_path, "trace_path is empty"
    docx_p = Path(result.docx_path)
    trace_p = Path(result.trace_path)
    assert docx_p.exists() and docx_p.stat().st_size > 0, f"docx missing or empty: {docx_p}"
    assert trace_p.exists() and trace_p.stat().st_size > 0, f"trace missing or empty: {trace_p}"

    # ── Validators run cleanly against the produced .docx ────────────────
    from backend.agents.validators.schema_validator import validate_schema
    from backend.agents.validators.spot_checker import spot_check
    schema = validate_schema(docx_p)
    assert schema.ok, f"Schema validator rejected the produced docx: {schema.error}"
    assert schema.body_paragraphs > 0, "Docx has no body paragraphs"

    # Use the actual outline that was loaded to spot-check.
    from backend.agents.trace_agent import OUTLINE_DIR
    import yaml
    with (OUTLINE_DIR / "soc_playbook_NIST_800_61.yaml").open("r", encoding="utf-8") as f:
        outline = yaml.safe_load(f)
    spot = spot_check(docx_p, outline)
    # Spot-check might find missing sections if Claude trimmed a heading.
    # That's a 'draft' outcome, not a test failure — but we DO assert the
    # extraction produced text.
    assert spot.extracted_chars > 1000, (
        f"Generated docx text is suspiciously short ({spot.extracted_chars} chars). "
        f"Sample first 200 chars: {(spot.found_sections or spot.missing_sections)[:200]}"
    )

    # ── activity_log row count + rationale population ────────────────────
    log_resp = requests.get(
        _rest_url(
            f"activity_log?tenant_id=eq.{TEST_TENANT_ID}"
            f"&action=like.trace_step_*"
            f"&order=created_at.asc,step_number.asc"
            f"&select=id,action,step_number,step_name,rationale,created_at"
        ),
        headers={"apikey": _service_headers()["apikey"],
                 "Authorization": _service_headers()["Authorization"]},
        timeout=30,
    )
    assert log_resp.status_code == 200, f"activity_log read failed: {log_resp.status_code}"
    rows = log_resp.json() or []

    # Filter to rows from THIS run by matching against returned activity_log_ids.
    expected_ids = set(result.activity_log_ids)
    this_run_rows = [r for r in rows if r.get("id") in expected_ids]
    assert len(this_run_rows) >= 16, (
        f"Expected >=16 activity_log rows for this run, got {len(this_run_rows)}. "
        f"Returned activity_log_ids: {len(expected_ids)}"
    )

    # Every row must have rationale populated.
    missing_rationale = [r for r in this_run_rows if not (r.get("rationale") or "").strip()]
    assert not missing_rationale, (
        f"{len(missing_rationale)} activity_log row(s) have empty rationale: "
        f"{[r.get('step_name') for r in missing_rationale]}"
    )

    # Step numbers should cover 1..16 (a row per step). Repair can fire more.
    step_numbers = {r.get("step_number") for r in this_run_rows}
    for required_n in range(1, 17):
        assert required_n in step_numbers, (
            f"step_number {required_n} missing from activity_log. "
            f"Step numbers present: {sorted(s for s in step_numbers if s is not None)}"
        )

    # step_name on each row must be set and look like one of the canonical names.
    from backend.agents.trace_agent import STEP_DEFINITIONS
    canonical_names = {name for _, name in STEP_DEFINITIONS}
    bad_names = [
        r for r in this_run_rows
        if (r.get("step_name") or "") not in canonical_names
    ]
    assert not bad_names, (
        f"{len(bad_names)} rows have non-canonical step_name: "
        f"{[r.get('step_name') for r in bad_names[:5]]}"
    )

    # The trace markdown should reference the docx path AND the intake id.
    trace_text = trace_p.read_text(encoding="utf-8")
    assert str(docx_p) in trace_text, "trace markdown does not reference the docx path"
    assert intake_id in trace_text, "trace markdown does not reference the intake id"
    assert "16-step trace" in trace_text, "trace markdown missing the 16-step section"
