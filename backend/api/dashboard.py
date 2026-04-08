"""
Midnight — Dashboard Router
Takeoff LLC

Endpoints:
  GET /dashboard/summary    → metric cards (policies, gaps, needs review)
  GET /dashboard/gaps       → framework gap list with severity + control IDs
  GET /dashboard/documents  → policy library with status + owner
  GET /dashboard/activity   → recent activity feed

Swap the _mock_* functions for real Supabase calls in Phase 2.
Every response shape matches exactly what midnight_dashboard.html expects.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ── Response models ────────────────────────────────────────────────────────────

class SummaryResponse(BaseModel):
    policies_processed: int
    policies_last_7_days: int
    gaps_total: int
    gaps_critical: int
    gaps_medium: int
    needs_review_total: int
    needs_review_critical: int
    overall_coverage_pct: int
    frameworks: list[dict]          # [{name, coverage_pct}]


class GapItem(BaseModel):
    id: str
    control_id: str                 # e.g. "NIST PR.DS-5"
    framework: str                  # e.g. "NIST"
    description: str
    severity: str                   # "critical" | "medium" | "low"
    affected_frameworks: list[str]  # ["HIPAA", "HITRUST", "NIST"]
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
    doc_type: str       # POLICY | SOP | PLAYBOOK | STANDARD | PLAN | PROCEDURE
    status: str         # ready | review | draft | progress
    owner_name: str
    owner_initials: str
    framework_tags: list[str]
    last_updated: str   # ISO date string


class DocumentsResponse(BaseModel):
    total: int
    items: list[DocumentItem]


class ActivityItem(BaseModel):
    id: str
    timestamp: str
    user_name: str
    user_initials: str
    action: str         # "Uploaded" | "Transformed" | "Downloaded" | "Assigned reviewer" etc.
    target: str         # policy/document name
    result: str         # "audit-ready" | "needs-review" | "complete" | "failed"


class ActivityResponse(BaseModel):
    items: list[ActivityItem]


# ── Mock data (replace with Supabase queries) ──────────────────────────────────

def _mock_summary() -> SummaryResponse:
    return SummaryResponse(
        policies_processed=98,
        policies_last_7_days=12,
        gaps_total=24,
        gaps_critical=8,
        gaps_medium=11,
        needs_review_total=7,
        needs_review_critical=3,
        overall_coverage_pct=61,
        frameworks=[
            {"name": "HIPAA",    "coverage_pct": 78},
            {"name": "HITRUST",  "coverage_pct": 52},
            {"name": "PCI DSS",  "coverage_pct": 44},
            {"name": "NIST CSF", "coverage_pct": 65},
            {"name": "SOC 2",    "coverage_pct": 30},
        ]
    )


def _mock_gaps() -> GapsResponse:
    items = [
        GapItem(
            id="gap-001",
            control_id="NIST PR.DS-5",
            framework="NIST",
            description="No incident response plan detected",
            severity="critical",
            affected_frameworks=["HIPAA", "HITRUST", "NIST"],
            suggested_action="Build incident response plan",
        ),
        GapItem(
            id="gap-002",
            control_id="PCI DSS 3.5.1",
            framework="PCI DSS",
            description="Vendor risk management policy missing",
            severity="critical",
            affected_frameworks=["PCI DSS", "HITRUST"],
            suggested_action="Generate vendor risk management policy",
        ),
        GapItem(
            id="gap-003",
            control_id="HIPAA 164.308(a)(5)",
            framework="HIPAA",
            description="Security awareness training gap detected",
            severity="critical",
            affected_frameworks=["HIPAA", "ISO 27001"],
            suggested_action="Build security awareness training policy",
        ),
        GapItem(
            id="gap-004",
            control_id="ISO 27001 A.8.1",
            framework="ISO 27001",
            description="Lacks clear user responsibility definition",
            severity="medium",
            affected_frameworks=["ISO 27001", "NIST AC-2"],
            suggested_action="Update access control policy with user responsibilities",
        ),
        GapItem(
            id="gap-005",
            control_id="PCI DSS 7.1",
            framework="PCI DSS",
            description="Access control review procedure missing",
            severity="medium",
            affected_frameworks=["PCI DSS", "NIST AC-2"],
            suggested_action="Create access control review SOP",
        ),
        GapItem(
            id="gap-006",
            control_id="HIPAA 164.312(a)(2)",
            framework="HIPAA",
            description="Encryption policy out of date",
            severity="medium",
            affected_frameworks=["HIPAA", "PCI DSS"],
            suggested_action="Update encryption policy to current standards",
        ),
        GapItem(
            id="gap-007",
            control_id="NIST PR.IP-9",
            framework="NIST",
            description="No business continuity plan on record",
            severity="medium",
            affected_frameworks=["NIST", "ISO 27001"],
            suggested_action="Build business continuity plan",
        ),
        GapItem(
            id="gap-008",
            control_id="SOC 2 CC6.1",
            framework="SOC 2",
            description="Logical access controls not documented",
            severity="low",
            affected_frameworks=["SOC 2"],
            suggested_action="Document logical access controls",
        ),
    ]
    return GapsResponse(
        total=len(items),
        critical=sum(1 for g in items if g.severity == "critical"),
        medium=sum(1 for g in items if g.severity == "medium"),
        low=sum(1 for g in items if g.severity == "low"),
        items=items,
    )


def _mock_documents() -> DocumentsResponse:
    items = [
        DocumentItem(
            id="doc-001",
            name="Information Security Policy",
            doc_type="POLICY",
            status="ready",
            owner_name="Joe Bailey",
            owner_initials="JB",
            framework_tags=["HIPAA", "NIST", "ISO 27001"],
            last_updated="2026-04-02",
        ),
        DocumentItem(
            id="doc-002",
            name="Access Control Policy",
            doc_type="POLICY",
            status="progress",
            owner_name="Joe Bailey",
            owner_initials="JB",
            framework_tags=["HIPAA", "PCI DSS", "NIST AC-2"],
            last_updated="2026-04-01",
        ),
        DocumentItem(
            id="doc-003",
            name="Incident Response Plan",
            doc_type="PLAN",
            status="review",
            owner_name="Sari Patel",
            owner_initials="SP",
            framework_tags=["HIPAA", "NIST", "HITRUST"],
            last_updated="2026-03-28",
        ),
        DocumentItem(
            id="doc-004",
            name="Daily Log Review SOP",
            doc_type="SOP",
            status="ready",
            owner_name="Andrew Hoffman",
            owner_initials="AH",
            framework_tags=["NIST", "SOC 2"],
            last_updated="2026-04-01",
        ),
        DocumentItem(
            id="doc-005",
            name="Phishing Response Playbook",
            doc_type="PLAYBOOK",
            status="draft",
            owner_name="Joe Bailey",
            owner_initials="JB",
            framework_tags=["HIPAA", "NIST"],
            last_updated="2026-04-05",
        ),
        DocumentItem(
            id="doc-006",
            name="Password & MFA Standard",
            doc_type="STANDARD",
            status="ready",
            owner_name="Andrew Hoffman",
            owner_initials="AH",
            framework_tags=["PCI DSS", "NIST", "HITRUST"],
            last_updated="2026-03-30",
        ),
        DocumentItem(
            id="doc-007",
            name="Vendor Management Policy",
            doc_type="POLICY",
            status="progress",
            owner_name="Joe Bailey",
            owner_initials="JB",
            framework_tags=["PCI DSS", "HITRUST"],
            last_updated="2026-03-25",
        ),
        DocumentItem(
            id="doc-008",
            name="Business Continuity Plan",
            doc_type="PLAN",
            status="review",
            owner_name="Sari Patel",
            owner_initials="SP",
            framework_tags=["NIST", "ISO 27001"],
            last_updated="2026-02-12",
        ),
    ]
    return DocumentsResponse(total=len(items), items=items)


def _mock_activity() -> ActivityResponse:
    now = datetime.utcnow()
    items = [
        ActivityItem(
            id="act-001",
            timestamp=(now - timedelta(minutes=2)).isoformat(),
            user_name="Joe Bailey",
            user_initials="JB",
            action="Uploaded",
            target="Incident Response Plan",
            result="audit-ready",
        ),
        ActivityItem(
            id="act-002",
            timestamp=(now - timedelta(minutes=8)).isoformat(),
            user_name="Sari Patel",
            user_initials="SP",
            action="Transformed Policy",
            target="Access Control Policy",
            result="audit-ready",
        ),
        ActivityItem(
            id="act-003",
            timestamp=(now - timedelta(minutes=14)).isoformat(),
            user_name="Andrew Hoffman",
            user_initials="AH",
            action="Downloaded GRC Summary",
            target="Access Control Policy",
            result="complete",
        ),
        ActivityItem(
            id="act-004",
            timestamp=(now - timedelta(minutes=32)).isoformat(),
            user_name="Joe Bailey",
            user_initials="JB",
            action="Assigned reviewer",
            target="Vendor Management Policy",
            result="needs-review",
        ),
        ActivityItem(
            id="act-005",
            timestamp=(now - timedelta(hours=1)).isoformat(),
            user_name="Andrew Hoffman",
            user_initials="AH",
            action="Gap analysis run",
            target="Full program",
            result="complete",
        ),
        ActivityItem(
            id="act-006",
            timestamp=(now - timedelta(hours=3)).isoformat(),
            user_name="Sari Patel",
            user_initials="SP",
            action="Downloaded PDF Output",
            target="Incident Response Plan",
            result="audit-ready",
        ),
    ]
    return ActivityResponse(items=items)


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=SummaryResponse)
async def get_summary():
    """
    Metric cards + framework coverage bars.
    Replace _mock_summary() with:
        supabase.table("documents").select("*").execute()
        supabase.table("gaps").select("*").execute()
    """
    return _mock_summary()


@router.get("/gaps", response_model=GapsResponse)
async def get_gaps(severity: Optional[str] = None, framework: Optional[str] = None):
    """
    Gap panel — all gaps with optional severity/framework filter.
    ?severity=critical  →  only critical gaps
    ?framework=HIPAA    →  only gaps affecting HIPAA

    Replace _mock_gaps() with:
        supabase.table("gaps").select("*").order("severity").execute()
    """
    data = _mock_gaps()
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
    )


@router.get("/documents", response_model=DocumentsResponse)
async def get_documents(status: Optional[str] = None, doc_type: Optional[str] = None):
    """
    Policy library — all documents with optional status/type filter.
    ?status=review     →  documents needing review
    ?doc_type=PLAYBOOK →  only playbooks

    Replace _mock_documents() with:
        supabase.table("documents").select("*").order("last_updated", desc=True).execute()
    """
    data = _mock_documents()
    items = data.items

    if status:
        items = [d for d in items if d.status == status.lower()]
    if doc_type:
        items = [d for d in items if d.doc_type == doc_type.upper()]

    return DocumentsResponse(total=len(items), items=items)


@router.get("/activity", response_model=ActivityResponse)
async def get_activity(limit: int = 10):
    """
    Recent activity feed — most recent first.
    ?limit=20  →  return up to 20 items

    Replace _mock_activity() with:
        supabase.table("activity").select("*").order("timestamp", desc=True).limit(limit).execute()
    """
    data = _mock_activity()
    return ActivityResponse(items=data.items[:limit])
