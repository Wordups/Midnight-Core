"""
Midnight - Dashboard Router
Takeoff LLC

Minimal personal-workspace dashboard backed by the local file store.
"""

from __future__ import annotations

from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from backend.core.gap_engine import run_program_gap_analysis
from backend.storage.file_store import (
    SupabaseStoreError,
    download_generated_document,
    get_generated_document,
    list_generated_documents,
    list_policies_for_gap_analysis,
    list_recent_activity,
)


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class SummaryResponse(BaseModel):
    policies_processed: int
    policies_last_7_days: int
    gaps_total: int
    gaps_critical: int
    gaps_medium: int
    needs_review_total: int
    needs_review_critical: int
    overall_coverage_pct: int
    frameworks: list[dict]


class GapItem(BaseModel):
    id: str
    control_id: str
    framework: str
    description: str
    severity: str
    affected_frameworks: list[str]
    suggested_action: str


class GapsResponse(BaseModel):
    total: int
    critical: int
    medium: int
    low: int
    items: list[GapItem]
    overall_coverage_pct: int = 0


class DocumentItem(BaseModel):
    id: str
    name: str
    filename: str
    doc_type: str
    status: str
    owner_name: str
    owner_initials: str
    framework_tags: list[str]
    last_updated: str
    download_path: str
    preview: str


class DocumentsResponse(BaseModel):
    total: int
    items: list[DocumentItem]


class ActivityItem(BaseModel):
    id: str
    timestamp: str
    user_name: str
    user_initials: str
    action: str
    target: str
    result: str


class ActivityResponse(BaseModel):
    items: list[ActivityItem]

def _format_initials(name: str) -> str:
    parts = [part[0] for part in name.split() if part]
    return "".join(parts[:2]).upper() or "ME"


def _tenant_id(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authenticated tenant context is missing.")
    return tenant_id


def _documents(request: Request) -> list[dict]:
    try:
        return list_generated_documents(_tenant_id(request))
    except SupabaseStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _summary(request: Request) -> SummaryResponse:
    documents = _documents(request)
    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    recent_count = sum(
        1 for record in documents if datetime.fromisoformat(record["timestamp"]) >= seven_days_ago
    )
    ready_count = sum(1 for record in documents if record["status"] == "ready")

    try:
        gap_data = _gaps(request)
    except HTTPException:
        gap_data = GapsResponse(total=0, critical=0, medium=0, low=0, items=[])

    return SummaryResponse(
        policies_processed=len(documents),
        policies_last_7_days=recent_count,
        gaps_total=gap_data.total,
        gaps_critical=gap_data.critical,
        gaps_medium=gap_data.medium,
        needs_review_total=max(0, len(documents) - ready_count),
        needs_review_critical=0,
        overall_coverage_pct=gap_data.overall_coverage_pct,
        frameworks=[],
    )


def _gaps(request: Request) -> GapsResponse:
    tenant_id = _tenant_id(request)
    try:
        policies = list_policies_for_gap_analysis(tenant_id)
    except SupabaseStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not policies:
        return GapsResponse(total=0, critical=0, medium=0, low=0, items=[])

    documents = [
        {
            "name": p["policy_name"],
            "doc_type": (p.get("document_type") or "POLICY").upper(),
            "covered_control_ids": p.get("covered_control_ids") or [],
        }
        for p in policies
    ]

    all_frameworks: list[str] = list({
        fw for p in policies for fw in (p.get("selected_frameworks") or [])
    })

    if not all_frameworks:
        return GapsResponse(total=0, critical=0, medium=0, low=0, items=[])

    result = run_program_gap_analysis(documents=documents, frameworks=all_frameworks)

    items = [
        GapItem(
            id=g["control_id"],
            control_id=g["control_id"],
            framework=g["framework"],
            description=g["description"],
            severity=g["severity"],
            affected_frameworks=g.get("affected_frameworks", [g["framework"]]),
            suggested_action=g["suggested_action"],
        )
        for g in result.get("gaps", [])
    ]

    return GapsResponse(
        total=result["total_gaps"],
        critical=result["gaps_critical"],
        medium=result["gaps_medium"],
        low=result["gaps_low"],
        items=items,
        overall_coverage_pct=result.get("overall_coverage_pct", 0),
    )


def _documents_response(request: Request) -> DocumentsResponse:
    auth_context = getattr(request.state, "auth_context", {}) or {}
    owner_name = auth_context.get("display_name") or "Workspace Owner"
    owner_initials = _format_initials(owner_name)
    items = [
        DocumentItem(
            id=record["id"],
            name=record["name"],
            filename=record["filename"],
            doc_type=record["doc_type"],
            status=record["status"],
            owner_name=owner_name,
            owner_initials=owner_initials,
            framework_tags=[],
            last_updated=record["timestamp"],
            download_path=f"/dashboard/documents/{record['id']}/download",
            preview=record.get("preview", ""),
        )
        for record in _documents(request)
    ]
    return DocumentsResponse(total=len(items), items=items)


def _activity(request: Request, limit: int = 10) -> ActivityResponse:
    try:
        items = [ActivityItem(**item) for item in list_recent_activity(_tenant_id(request), limit)]
    except SupabaseStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ActivityResponse(items=items)


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(request: Request):
    return _summary(request)


@router.get("/gaps", response_model=GapsResponse)
async def get_gaps(request: Request, severity: Optional[str] = None, framework: Optional[str] = None):
    data = _gaps(request)
    items = data.items
    if severity:
        items = [g for g in items if g.severity == severity.lower()]
    if framework:
        items = [g for g in items if framework.upper() in g.affected_frameworks]
    return GapsResponse(
        total=len(items),
        critical=sum(1 for g in items if g.severity == "critical"),
        medium=sum(1 for g in items if g.severity == "medium"),
        low=sum(1 for g in items if g.severity == "low"),
        items=items,
        overall_coverage_pct=data.overall_coverage_pct,
    )


@router.get("/documents", response_model=DocumentsResponse)
async def get_documents(request: Request, status: Optional[str] = None, doc_type: Optional[str] = None):
    data = _documents_response(request)
    items = data.items
    if status:
        items = [item for item in items if item.status == status.lower()]
    if doc_type:
        items = [item for item in items if item.doc_type == doc_type.upper()]
    return DocumentsResponse(total=len(items), items=items)


@router.get("/documents/{document_id}/download")
async def download_document(request: Request, document_id: str):
    try:
        record, file_bytes = download_generated_document(_tenant_id(request), document_id)
    except SupabaseStoreError as exc:
        message = str(exc)
        if "Document not found" in message:
            raise HTTPException(status_code=404, detail="Document not found.") from exc
        raise HTTPException(status_code=503, detail=message) from exc

    headers = {"Content-Disposition": f'attachment; filename="{record["filename"]}"'}
    return Response(content=file_bytes, media_type=record["content_type"], headers=headers)


@router.get("/activity", response_model=ActivityResponse)
async def get_activity(request: Request, limit: int = 10):
    return _activity(request, limit)
