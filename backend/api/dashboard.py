"""
Midnight - Dashboard Router
Takeoff LLC

Minimal personal-workspace dashboard backed by the local file store.
"""

from __future__ import annotations

from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Optional
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.storage.file_store import (
    get_generated_document,
    list_generated_documents,
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


class DocumentItem(BaseModel):
    id: str
    name: str
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


def _get_workspace_id() -> str:
    return os.getenv("WORKSPACE_ID", "personal")


def _format_initials(name: str) -> str:
    parts = [part[0] for part in name.split() if part]
    return "".join(parts[:2]).upper() or "ME"


def _documents() -> list[dict]:
    return list_generated_documents(_get_workspace_id())


def _summary() -> SummaryResponse:
    documents = _documents()
    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    recent_count = sum(
        1 for record in documents if datetime.fromisoformat(record["timestamp"]) >= seven_days_ago
    )
    ready_count = sum(1 for record in documents if record["status"] == "ready")
    return SummaryResponse(
        policies_processed=len(documents),
        policies_last_7_days=recent_count,
        gaps_total=0,
        gaps_critical=0,
        gaps_medium=0,
        needs_review_total=max(0, len(documents) - ready_count),
        needs_review_critical=0,
        overall_coverage_pct=100 if documents else 0,
        frameworks=[],
    )


def _gaps() -> GapsResponse:
    return GapsResponse(total=0, critical=0, medium=0, low=0, items=[])


def _documents_response() -> DocumentsResponse:
    owner_name = "Workspace Owner"
    owner_initials = _format_initials(owner_name)
    items = [
        DocumentItem(
            id=record["id"],
            name=record["name"],
            doc_type=record["doc_type"],
            status=record["status"],
            owner_name=owner_name,
            owner_initials=owner_initials,
            framework_tags=[],
            last_updated=record["timestamp"],
            download_path=f"/dashboard/documents/{record['id']}/download",
            preview=record.get("preview", ""),
        )
        for record in _documents()
    ]
    return DocumentsResponse(total=len(items), items=items)


def _activity(limit: int = 10) -> ActivityResponse:
    items = [ActivityItem(**item) for item in list_recent_activity(_get_workspace_id(), limit)]
    return ActivityResponse(items=items)


@router.get("/summary", response_model=SummaryResponse)
async def get_summary():
    return _summary()


@router.get("/gaps", response_model=GapsResponse)
async def get_gaps(severity: Optional[str] = None, framework: Optional[str] = None):
    data = _gaps()
    items = data.items
    if severity:
        items = [g for g in items if g.severity == severity.lower()]
    if framework:
        items = [g for g in items if framework.upper() in g.affected_frameworks]
    return GapsResponse(total=len(items), critical=0, medium=0, low=0, items=items)


@router.get("/documents", response_model=DocumentsResponse)
async def get_documents(status: Optional[str] = None, doc_type: Optional[str] = None):
    data = _documents_response()
    items = data.items
    if status:
        items = [item for item in items if item.status == status.lower()]
    if doc_type:
        items = [item for item in items if item.doc_type == doc_type.upper()]
    return DocumentsResponse(total=len(items), items=items)


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    record = get_generated_document(_get_workspace_id(), document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    path = Path(record["stored_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Stored artifact is missing.")

    return FileResponse(path, media_type=record["content_type"], filename=record["filename"])


@router.get("/activity", response_model=ActivityResponse)
async def get_activity(limit: int = 10):
    return _activity(limit)
