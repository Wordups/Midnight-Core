"""Bird Eye HTTP endpoints. Tenant id always comes from the authenticated session."""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from .db import (
    TABLE_DOCUMENTS,
    TABLE_FINDINGS,
    TABLE_RUNS,
    select as db_select,
    update as db_update,
)
from .ingestion import ingest_document
from .orchestrator import run_bird_eye
from .tenant_guard import require_tenant

logger = logging.getLogger("midnight.bird_eye.api")

router = APIRouter(prefix="/bird-eye", tags=["bird-eye"])


def _tenant_from_request(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authenticated tenant context is missing.")
    return require_tenant(tenant_id)


class PatchFindingBody(BaseModel):
    status: Literal["open", "dismissed", "resolved"]


@router.post("/ingest")
async def ingest_endpoint(
    request: Request,
    file: UploadFile = File(...),
    artifact_type: str | None = Form(default=None),
    title: str | None = Form(default=None),
    auto_run: bool = Form(default=True),
):
    tenant_id = _tenant_from_request(request)
    content = await file.read()
    try:
        result = ingest_document(
            tenant_id,
            filename=file.filename or "upload.txt",
            file_bytes=content,
            artifact_type=artifact_type,
            title_override=title,
        )
    except Exception as exc:
        logger.exception("Bird Eye ingest failed")
        raise HTTPException(status_code=400, detail=str(exc))

    run_summary: dict[str, Any] | None = None
    if auto_run:
        try:
            run_summary = run_bird_eye(tenant_id, triggered_by="upload", trigger_document_id=result["policy_id"])
        except Exception as exc:
            logger.exception("Bird Eye auto-run failed after ingest")
            run_summary = {"status": "failed", "error": str(exc)}
    return {"ingest": result, "run": run_summary}


@router.post("/runs")
async def trigger_run(request: Request):
    tenant_id = _tenant_from_request(request)
    try:
        return run_bird_eye(tenant_id, triggered_by="manual")
    except Exception as exc:
        logger.exception("Bird Eye manual run failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/runs/{run_id}")
async def get_run(request: Request, run_id: str):
    tenant_id = _tenant_from_request(request)
    rows = db_select(TABLE_RUNS, tenant_id=tenant_id, columns="*", filters={"id": f"eq.{run_id}"}, limit=1)
    if not rows:
        raise HTTPException(status_code=404, detail="Run not found.")
    return rows[0]


@router.get("/runs")
async def list_runs(request: Request, limit: int = 10):
    tenant_id = _tenant_from_request(request)
    return db_select(
        TABLE_RUNS,
        tenant_id=tenant_id,
        columns="*",
        filters={"run_type": "eq.bird_eye_review"},
        limit=max(1, min(limit, 50)),
        order="created_at.desc",
    )


@router.get("/findings")
async def list_findings(request: Request, run_id: str | None = None, status: str | None = None):
    tenant_id = _tenant_from_request(request)
    filters: dict[str, str] = {}
    if run_id:
        filters["run_id"] = f"eq.{run_id}"
    if status:
        filters["status"] = f"eq.{status}"
    findings = db_select(
        TABLE_FINDINGS,
        tenant_id=tenant_id,
        columns="*",
        filters=filters or None,
        order="created_at.desc",
        limit=500,
    )
    return _hydrate_findings(tenant_id, findings)


@router.patch("/findings/{finding_id}")
async def patch_finding(request: Request, finding_id: str, body: PatchFindingBody):
    tenant_id = _tenant_from_request(request)
    rows = db_update(
        TABLE_FINDINGS,
        tenant_id=tenant_id,
        filters={"id": f"eq.{finding_id}"},
        patch={"status": body.status},
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Finding not found.")
    return rows[0]


@router.get("/library-summary")
async def library_summary(request: Request):
    tenant_id = _tenant_from_request(request)
    docs = db_select(
        TABLE_DOCUMENTS,
        tenant_id=tenant_id,
        columns="id,policy_name,policy_number,document_type,status",
        filters={"policy_number": "like.TKO-*"},
    )
    runs = db_select(
        TABLE_RUNS,
        tenant_id=tenant_id,
        columns="id,status,documents_reviewed,findings_count,completed_at,created_at",
        filters={"run_type": "eq.bird_eye_review"},
        order="created_at.desc",
        limit=1,
    )
    last_run = runs[0] if runs else None
    findings: list[dict[str, Any]] = []
    if last_run:
        findings = db_select(
            TABLE_FINDINGS,
            tenant_id=tenant_id,
            columns="finding_type,severity,status",
            filters={"run_id": f"eq.{last_run['id']}"},
            limit=500,
        )
    severity_counts = Counter(f.get("severity") for f in findings if f.get("status") == "open")
    type_counts = Counter(f.get("finding_type") for f in findings if f.get("status") == "open")
    open_count = sum(1 for f in findings if f.get("status") == "open")
    merge_opportunities = type_counts.get("duplicate", 0)
    return {
        "documents_reviewed": len(docs),
        "issues_open": open_count,
        "merge_opportunities": merge_opportunities,
        "severity_breakdown": dict(severity_counts),
        "type_breakdown": dict(type_counts),
        "last_run": last_run,
    }


def _hydrate_findings(tenant_id: str, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not findings:
        return []
    doc_ids: set[str] = set()
    for f in findings:
        if f.get("policy_id"):
            doc_ids.add(f["policy_id"])
        if f.get("related_policy_id"):
            doc_ids.add(f["related_policy_id"])
    docs = (
        db_select(
            TABLE_DOCUMENTS,
            tenant_id=tenant_id,
            columns="id,policy_name,policy_number",
            filters={"id": "in.(" + ",".join(doc_ids) + ")"} if doc_ids else None,
        )
        if doc_ids
        else []
    )
    doc_lookup = {d["id"]: d for d in docs}
    for f in findings:
        f["primary_document"] = doc_lookup.get(f.get("policy_id"))
        f["related_document"] = doc_lookup.get(f.get("related_policy_id"))
        f["summary"] = f.get("description")  # alias for UI
    return findings
