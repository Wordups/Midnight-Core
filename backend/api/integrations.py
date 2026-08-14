"""
Jira integration API (layer 2).

Per-tenant: configure a Jira connection, push a compliance gap as a Jira issue,
and read status back. Auth (verify_access) is attached at registration; every
call is tenant-scoped and fails closed when Jira isn't configured.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.bird_eye.db import insert as db_insert
from backend.bird_eye.db import select as db_select
from backend.bird_eye.db import update as db_update
from backend.core.ratelimit import allow as rate_allow
from backend.integrations.jira_client import JiraClient, JiraError
from backend.integrations.jira_config import load_config, public_config, save_config

logger = logging.getLogger("midnight.integrations.api")

router = APIRouter(prefix="/api/v1/integrations/jira", tags=["integrations"])

_LINKS = "jira_issue_links"


def _tenant_id(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return tenant_id


def _client(tenant_id: str) -> JiraClient:
    config = load_config(tenant_id)
    if config is None:
        raise HTTPException(
            status_code=409,
            detail="Jira is not connected. Add your site, email, and API token first.",
        )
    try:
        return JiraClient(config)
    except JiraError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# ── config ───────────────────────────────────────────────────────────────────
class JiraConfigRequest(BaseModel):
    site_url: str = Field(min_length=4)
    auth_email: str = Field(min_length=3)
    # Empty token on an already-configured tenant means "keep the stored one" —
    # so settings like auto_push can be toggled without re-entering the secret.
    api_token: str = Field(default="", max_length=500)
    project_key: str = Field(default="GRC", min_length=1, max_length=20)
    enabled: bool = True
    auto_push: bool = False
    alert_webhook_url: str = Field(default="", max_length=500)


@router.get("/config")
def get_config(request: Request) -> dict:
    return public_config(_tenant_id(request))


@router.put("/config")
def put_config(payload: JiraConfigRequest, request: Request) -> dict:
    tenant_id = _tenant_id(request)
    api_token = payload.api_token.strip()
    if not api_token:
        existing = load_config(tenant_id)
        if existing is None:
            raise HTTPException(status_code=422, detail="An API token is required to connect Jira.")
        api_token = existing.api_token
    elif len(api_token) < 8:
        raise HTTPException(status_code=422, detail="That API token looks too short.")
    save_config(
        tenant_id,
        site_url=payload.site_url, email=payload.auth_email,
        api_token=api_token, project_key=payload.project_key,
        enabled=payload.enabled, auto_push=payload.auto_push,
        alert_webhook_url=payload.alert_webhook_url,
    )
    # Verify the credentials immediately so the user gets instant feedback.
    try:
        who = _client(tenant_id).test_connection()
    except (HTTPException, JiraError) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        return {"saved": True, "connection_ok": False, "detail": detail}
    return {"saved": True, "connection_ok": True, "connected_as": who}


@router.post("/test")
def test_connection(request: Request) -> dict:
    try:
        return {"connection_ok": True, "connected_as": _client(_tenant_id(request)).test_connection()}
    except JiraError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ── push a gap → Jira issue ──────────────────────────────────────────────────
class PushGapRequest(BaseModel):
    control_id: str = Field(default="", max_length=60)
    framework: str = Field(default="", max_length=40)
    title: str = Field(min_length=3, max_length=200)
    finding: str = Field(default="", max_length=8000)
    remediation: str = Field(default="", max_length=8000)
    severity: str = Field(default="Medium", max_length=20)
    document_id: str = Field(default="", max_length=60)
    request_id: str | None = None


def _build_summary(p: PushGapRequest) -> str:
    return f"[{p.control_id}] {p.title}" if p.control_id else p.title


def _build_description(p: PushGapRequest) -> str:
    lines = ["Source: Midnight Core — compliance gap"]
    if p.document_id:
        lines.append(f"Document ID: {p.document_id}")
    if p.framework or p.control_id:
        lines.append(f"Framework / Control: {p.framework} {p.control_id}".strip())
    if p.severity:
        lines.append(f"Severity: {p.severity}")
    if p.finding:
        lines += ["", "Finding", p.finding]
    if p.remediation:
        lines += ["", "Suggested remediation", p.remediation]
    return "\n".join(lines)


@router.post("/push-gap")
def push_gap(payload: PushGapRequest, request: Request) -> dict:
    tenant_id = _tenant_id(request)
    if not rate_allow(f"jira-push:{tenant_id}", max_hits=30, window_seconds=300):
        raise HTTPException(status_code=429, detail="Too many Jira pushes — wait a few minutes.")
    client = _client(tenant_id)
    labels = [x for x in ["midnight", "gap-remediation", payload.framework,
                          f"severity-{payload.severity.lower()}" if payload.severity else ""] if x]
    try:
        issue = client.create_issue(
            summary=_build_summary(payload),
            description=_build_description(payload),
            labels=labels,
        )
    except JiraError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Record the link so status sync can find the source item later.
    try:
        db_insert(_LINKS, {
            "tenant_id": tenant_id,
            "issue_key": issue.get("key"),
            "issue_url": issue.get("url"),
            "control_id": payload.control_id or None,
            "document_id": payload.document_id or None,
            "request_id": payload.request_id or None,
            "last_status": "To Do",
            "last_synced_at": datetime.now(UTC).isoformat(),
            "created_at": datetime.now(UTC).isoformat(),
        })
    except Exception as exc:  # linking is best-effort; the issue already exists
        logger.warning("jira link record failed: %s", exc)
    return issue


@router.get("/issues/{issue_key}")
def issue_status(issue_key: str, request: Request) -> dict:
    tenant_id = _tenant_id(request)
    try:
        status = _client(tenant_id).get_issue_status(issue_key)
    except JiraError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    # Keep the local link row in sync (best-effort).
    try:
        db_update(_LINKS, tenant_id=tenant_id,
                  filters={"issue_key": f"eq.{issue_key}"},
                  patch={"last_status": status.get("status"),
                         "last_synced_at": datetime.now(UTC).isoformat()})
    except Exception:
        pass
    return status


# ── one-click sync: sync-back + push all unlinked material gaps ──────────────
@router.post("/sync")
def sync_now(request: Request) -> dict:
    """The 'Sync now' button: refresh Jira statuses (Done stamps the link
    resolved), then push every material gap that isn't filed yet — regardless
    of the auto_push setting, since the click is the consent."""
    tenant_id = _tenant_id(request)
    if not rate_allow(f"jira-sync:{tenant_id}", max_hits=6, window_seconds=300):
        raise HTTPException(status_code=429, detail="Sync already running — wait a few minutes.")
    _client(tenant_id)  # fail closed (409) before doing any work
    from backend.integrations.jira_sync import auto_push_gaps, sync_back

    result = {"sync": sync_back(tenant_id), "push": auto_push_gaps(tenant_id)}
    logger.info("manual jira sync for %s: %d synced, %d pushed", tenant_id,
                result["sync"].get("synced", 0), len(result["push"].get("pushed", [])))
    return result


@router.get("/links")
def list_links(request: Request) -> dict:
    tenant_id = _tenant_id(request)
    rows = db_select(_LINKS, tenant_id=tenant_id, columns="*",
                     order="created_at.desc", limit=50)
    return {"links": rows}
