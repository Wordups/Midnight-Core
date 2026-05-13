"""Bird Eye orchestrator - runs all five detectors and persists run status."""
from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from .db import TABLE_DOCUMENTS, TABLE_FINDINGS, TABLE_RUNS, insert as db_insert, select as db_select, update as db_update
from .detectors import (
    detect_conflicts,
    detect_duplicates,
    detect_framework_gaps,
    detect_orphans,
    detect_stale_governance,
)
from .tenant_guard import require_tenant

logger = logging.getLogger("midnight.bird_eye.orchestrator")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_run(tenant_id: str, *, triggered_by: str, trigger_document_id: str | None = None) -> dict[str, Any]:
    require_tenant(tenant_id)
    row = {
        "tenant_id": tenant_id,
        "run_type": "bird_eye_review",
        "triggered_by": triggered_by,
        "policy_id": trigger_document_id,
        "status": "running",
        "documents_reviewed": 0,
        "findings_count": 0,
    }
    inserted = db_insert(TABLE_RUNS, row)
    return inserted[0] if inserted else row


def finalize_run(tenant_id: str, run_id: str, *, status: str, documents_reviewed: int, findings_count: int, error: str | None = None) -> None:
    patch = {
        "status": status,
        "documents_reviewed": documents_reviewed,
        "findings_count": findings_count,
        "completed_at": _now(),
    }
    if error:
        patch["error_message"] = error[:500]
    db_update(TABLE_RUNS, tenant_id=tenant_id, filters={"id": f"eq.{run_id}"}, patch=patch)


def run_bird_eye(tenant_id: str, *, triggered_by: str = "manual", trigger_document_id: str | None = None) -> dict[str, Any]:
    require_tenant(tenant_id)
    run = create_run(tenant_id, triggered_by=triggered_by, trigger_document_id=trigger_document_id)
    run_id = run["id"]
    docs = db_select(
        TABLE_DOCUMENTS,
        tenant_id=tenant_id,
        columns="id",
        filters={"policy_number": "like.TKO-*"},
    )
    documents_reviewed = len(docs)
    findings_total = 0
    try:
        findings_total += detect_duplicates(tenant_id, run_id)
        findings_total += detect_conflicts(tenant_id, run_id)
        findings_total += detect_stale_governance(tenant_id, run_id)
        findings_total += detect_framework_gaps(tenant_id, run_id)
        findings_total += detect_orphans(tenant_id, run_id)
        finalize_run(tenant_id, run_id, status="complete", documents_reviewed=documents_reviewed, findings_count=findings_total)
    except Exception as exc:
        logger.exception("Bird Eye run failed")
        finalize_run(
            tenant_id,
            run_id,
            status="failed",
            documents_reviewed=documents_reviewed,
            findings_count=findings_total,
            error=f"{exc.__class__.__name__}: {exc}",
        )
        raise
    return {
        "run_id": run_id,
        "tenant_id": tenant_id,
        "documents_reviewed": documents_reviewed,
        "findings_count": findings_total,
        "status": "complete",
    }
