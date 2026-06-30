"""
Midnight — PM layer router.

The request/task workflow that makes Midnight a program-management system:
GRC analysts create requests, assign them to SMEs, and track status; SMEs see
their assigned work and respond. Plus SME invites and pre-built request
templates. All data is tenant-scoped in code via the service-role client.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.notifications import email as mailer
from backend.storage.supabase_client import supabase_admin

logger = logging.getLogger("midnight.pm")

router = APIRouter(prefix="/pm", tags=["pm"])

_VALID_STATUS = {"open", "in_review", "complete"}
_TRANSITIONS = {
    "open": {"in_review", "complete"},
    "in_review": {"open", "complete"},
    "complete": {"in_review"},
}


# ── helpers ──────────────────────────────────────────────────────────────────

def _ctx(request: Request) -> tuple[str, str, dict]:
    tenant_id = getattr(request.state, "tenant_id", None)
    user_id = getattr(request.state, "user_id", None)
    if not tenant_id or not user_id:
        raise HTTPException(status_code=401, detail="Authenticated tenant context is missing.")
    return tenant_id, user_id, getattr(request.state, "auth_context", {}) or {}


def _row(data: Any) -> Optional[dict]:
    if isinstance(data, list):
        return data[0] if data else None
    return data if isinstance(data, dict) else None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _audit(tenant_id: str, actor_id: str, actor_name: str, action: str, detail: str) -> None:
    try:
        supabase_admin.table("activity_log").insert({
            "tenant_id": tenant_id,
            "actor_id": actor_id,
            "actor_name": actor_name,
            "action": action,
            "detail": detail,
        }).execute()
    except Exception:
        logger.warning("activity_log_write_failed", exc_info=True)


def _profile(tenant_id: str, user_id: str) -> Optional[dict]:
    try:
        res = supabase_admin.table("profiles").select("id,email,name,role,tenant_id").eq("id", user_id).limit(1).execute()
        return _row(res.data)
    except Exception:
        logger.warning("profile_lookup_failed", exc_info=True)
        return None


# ── models ───────────────────────────────────────────────────────────────────

class RequestCreate(BaseModel):
    title: str = Field(min_length=2)
    description: str | None = None
    framework: str | None = None
    control_id: str | None = None
    assignee_id: str | None = None
    due_date: str | None = None


class RequestUpdate(BaseModel):
    status: str | None = None
    assignee_id: str | None = None
    response: str | None = None
    due_date: str | None = None
    title: str | None = None
    description: str | None = None


class InviteCreate(BaseModel):
    email: str
    role: str = "sme"


class InviteAccept(BaseModel):
    token: str


# ── request templates (pre-built, per launch framework) ──────────────────────

_TEMPLATES = [
    {"id": "soc2-access-review", "framework": "SOC 2", "control_id": "SOC2-CC6.3",
     "title": "Quarterly user access review",
     "description": "Review all user access against least-privilege for in-scope systems; document approvals and removals."},
    {"id": "soc2-vendor-risk", "framework": "SOC 2", "control_id": "SOC2-CC9.2",
     "title": "Vendor risk assessment",
     "description": "Collect SOC 2 / security documentation for a critical vendor and record the risk decision."},
    {"id": "hipaa-risk-analysis", "framework": "HIPAA", "control_id": "HIPAA-164.308(a)(1)",
     "title": "Security risk analysis",
     "description": "Perform and document a risk analysis of systems handling ePHI, with remediation owners and dates."},
    {"id": "hipaa-workforce-training", "framework": "HIPAA", "control_id": "HIPAA-164.308(a)(5)",
     "title": "Workforce security awareness training",
     "description": "Deliver and record completion of the periodic HIPAA security awareness training."},
    {"id": "iso-access-control", "framework": "ISO 27001", "control_id": "ISO-A.5.15",
     "title": "Access control policy review",
     "description": "Review the access control policy against ISO 27001:2022 A.5.15 and update where needed."},
    {"id": "iso-supplier", "framework": "ISO 27001", "control_id": "ISO-A.5.19",
     "title": "Supplier information security review",
     "description": "Assess information security in a key supplier relationship per A.5.19/A.5.20."},
]


@router.get("/templates")
async def list_templates(request: Request):
    _ctx(request)
    return {"templates": _TEMPLATES}


# ── requests CRUD ────────────────────────────────────────────────────────────

@router.post("/requests")
async def create_request(request: Request, payload: RequestCreate):
    tenant_id, user_id, auth = _ctx(request)
    now = _now().isoformat()
    row = {
        "tenant_id": tenant_id,
        "creator_id": user_id,
        "assignee_id": payload.assignee_id,
        "title": payload.title.strip(),
        "description": (payload.description or "").strip() or None,
        "framework": payload.framework,
        "control_id": payload.control_id,
        "due_date": payload.due_date or None,
        "status": "open",
        "created_at": now,
        "updated_at": now,
    }
    res = supabase_admin.table("requests").insert(row).execute()
    created = _row(res.data) or row
    actor_name = auth.get("display_name") or auth.get("email") or "A user"
    _audit(tenant_id, user_id, actor_name, "request_created", f"Created request: {row['title']}")

    if payload.assignee_id:
        _notify_assignee(tenant_id, payload.assignee_id, created)
    return created


@router.get("/requests")
async def list_requests(request: Request, status: Optional[str] = None, assignee_id: Optional[str] = None):
    tenant_id, _, _ = _ctx(request)
    q = supabase_admin.table("requests").select("*").eq("tenant_id", tenant_id)
    if status:
        q = q.eq("status", status)
    if assignee_id:
        q = q.eq("assignee_id", assignee_id)
    res = q.execute()
    items = res.data or []
    items.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return {"total": len(items), "items": items}


@router.get("/requests/{request_id}")
async def get_request(request: Request, request_id: str):
    tenant_id, _, _ = _ctx(request)
    res = supabase_admin.table("requests").select("*").eq("tenant_id", tenant_id).eq("id", request_id).limit(1).execute()
    row = _row(res.data)
    if not row:
        raise HTTPException(status_code=404, detail="Request not found.")
    return row


@router.patch("/requests/{request_id}")
async def update_request(request: Request, request_id: str, payload: RequestUpdate):
    tenant_id, user_id, auth = _ctx(request)
    current = _row(
        supabase_admin.table("requests").select("*").eq("tenant_id", tenant_id).eq("id", request_id).limit(1).execute().data
    )
    if not current:
        raise HTTPException(status_code=404, detail="Request not found.")

    patch: dict[str, Any] = {"updated_at": _now().isoformat()}
    if payload.title is not None:
        patch["title"] = payload.title.strip()
    if payload.description is not None:
        patch["description"] = payload.description.strip() or None
    if payload.response is not None:
        patch["response"] = payload.response
    if payload.due_date is not None:
        patch["due_date"] = payload.due_date or None

    newly_assigned = False
    if payload.assignee_id is not None and payload.assignee_id != current.get("assignee_id"):
        patch["assignee_id"] = payload.assignee_id
        newly_assigned = bool(payload.assignee_id)

    if payload.status is not None:
        new_status = payload.status.strip().lower()
        if new_status not in _VALID_STATUS:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {sorted(_VALID_STATUS)}.")
        cur_status = current.get("status", "open")
        if new_status != cur_status and new_status not in _TRANSITIONS.get(cur_status, set()):
            raise HTTPException(status_code=400, detail=f"Cannot move a request from {cur_status} to {new_status}.")
        patch["status"] = new_status

    res = supabase_admin.table("requests").update(patch).eq("tenant_id", tenant_id).eq("id", request_id).execute()
    updated = _row(res.data) or {**current, **patch}
    actor_name = auth.get("display_name") or auth.get("email") or "A user"

    if patch.get("status") == "complete":
        _audit(tenant_id, user_id, actor_name, "task_complete", f"Completed: {updated.get('title')}")
        _notify_creator_complete(tenant_id, current, updated)
    elif "status" in patch:
        _audit(tenant_id, user_id, actor_name, "request_status", f"{updated.get('title')} → {patch['status']}")
    if newly_assigned:
        _audit(tenant_id, user_id, actor_name, "request_assigned", f"Assigned: {updated.get('title')}")
        _notify_assignee(tenant_id, payload.assignee_id, updated)
    return updated


@router.delete("/requests/{request_id}")
async def delete_request(request: Request, request_id: str):
    tenant_id, user_id, auth = _ctx(request)
    current = _row(
        supabase_admin.table("requests").select("title").eq("tenant_id", tenant_id).eq("id", request_id).limit(1).execute().data
    )
    if not current:
        raise HTTPException(status_code=404, detail="Request not found.")
    supabase_admin.table("requests").delete().eq("tenant_id", tenant_id).eq("id", request_id).execute()
    actor_name = auth.get("display_name") or auth.get("email") or "A user"
    _audit(tenant_id, user_id, actor_name, "request_deleted", f"Deleted: {current.get('title')}")
    return {"deleted": True}


# ── SME directory ────────────────────────────────────────────────────────────

@router.get("/smes")
async def list_smes(request: Request):
    tenant_id, _, _ = _ctx(request)
    res = supabase_admin.table("profiles").select("id,email,name,role").eq("tenant_id", tenant_id).eq("role", "sme").execute()
    return {"smes": res.data or []}


# ── invites ──────────────────────────────────────────────────────────────────

@router.post("/invites")
async def create_invite(request: Request, payload: InviteCreate):
    tenant_id, user_id, auth = _ctx(request)
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="A valid email is required.")
    token = secrets.token_urlsafe(32)
    expires_at = (_now() + timedelta(days=7)).isoformat()
    row = {
        "tenant_id": tenant_id,
        "email": email,
        "role": payload.role if payload.role in {"sme", "analyst"} else "sme",
        "token": token,
        "invited_by": user_id,
        "accepted": False,
        "expires_at": expires_at,
        "created_at": _now().isoformat(),
    }
    supabase_admin.table("invites").insert(row).execute()

    org_name = auth.get("organization_name") or "your team"
    accept_url = f"{mailer.app_base_url()}/login.html?invite={token}" if mailer.app_base_url() else f"/login.html?invite={token}"
    emailed = mailer.send_invite_email(to=email, org_name=org_name, accept_url=accept_url)
    actor_name = auth.get("display_name") or auth.get("email") or "A user"
    _audit(tenant_id, user_id, actor_name, "invite_sent", f"Invited {email} as {row['role']}")
    return {"sent": emailed, "email": email, "expires_at": expires_at,
            "email_configured": mailer.is_configured(),
            "accept_token": token if not mailer.is_configured() else None}


@router.get("/invites")
async def list_invites(request: Request):
    tenant_id, _, _ = _ctx(request)
    res = supabase_admin.table("invites").select("id,email,role,accepted,expires_at,created_at").eq("tenant_id", tenant_id).execute()
    items = res.data or []
    items.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return {"invites": items}


@router.post("/invites/accept")
async def accept_invite(request: Request, payload: InviteAccept):
    _, user_id, auth = _ctx(request)
    user_email = (getattr(request.state, "user_email", "") or auth.get("email") or "").strip().lower()
    res = supabase_admin.table("invites").select("*").eq("token", payload.token).limit(1).execute()
    invite = _row(res.data)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found.")
    if invite.get("accepted"):
        raise HTTPException(status_code=400, detail="This invite has already been accepted.")
    try:
        expired = datetime.fromisoformat(invite["expires_at"]) < _now()
    except Exception:
        expired = False
    if expired:
        raise HTTPException(status_code=400, detail="This invite has expired.")
    if user_email and invite["email"].strip().lower() != user_email:
        raise HTTPException(status_code=403, detail="This invite was issued to a different email address.")

    # Move the accepting user into the inviting tenant as the invited role.
    supabase_admin.table("profiles").update(
        {"tenant_id": invite["tenant_id"], "role": invite.get("role", "sme")}
    ).eq("id", user_id).execute()
    supabase_admin.table("invites").update({"accepted": True}).eq("id", invite["id"]).execute()
    _audit(invite["tenant_id"], user_id, user_email or "New member",
           "invite_accepted", f"{user_email or 'A user'} joined as {invite.get('role', 'sme')}")
    return {"accepted": True, "tenant_id": invite["tenant_id"], "role": invite.get("role", "sme")}


# ── notification helpers (best-effort; email may be unconfigured) ─────────────

def _assignee_email(tenant_id: str, assignee_id: str) -> Optional[str]:
    try:
        res = supabase_admin.table("profiles").select("email").eq("tenant_id", tenant_id).eq("id", assignee_id).limit(1).execute()
        row = _row(res.data)
        return row.get("email") if row else None
    except Exception:
        return None


def _notify_assignee(tenant_id: str, assignee_id: str, req: dict) -> None:
    to = _assignee_email(tenant_id, assignee_id)
    if not to:
        return
    link = f"{mailer.app_base_url()}/midnight_dashboard.html" if mailer.app_base_url() else "/midnight_dashboard.html"
    mailer.send_task_assigned_email(
        to=to, title=req.get("title", "New task"),
        description=req.get("description", "") or "", due_date=req.get("due_date"), link=link,
    )


def _notify_creator_complete(tenant_id: str, current: dict, updated: dict) -> None:
    creator_id = current.get("creator_id")
    if not creator_id:
        return
    to = _assignee_email(tenant_id, creator_id)  # same lookup, by id
    if not to:
        return
    link = f"{mailer.app_base_url()}/midnight_dashboard.html" if mailer.app_base_url() else "/midnight_dashboard.html"
    mailer.send_task_complete_email(to=to, title=updated.get("title", "Task"), link=link)
