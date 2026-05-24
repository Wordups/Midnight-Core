"""
Midnight Platform Admin — cross-tenant telemetry for the platform operator.

Gated by PLATFORM_ADMIN_EMAILS env var (comma-separated). All queries use the
service_role key and bypass RLS intentionally — this is the operator view.
"""
from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import requests
from fastapi import APIRouter, HTTPException, Request, status

from backend.api.agent_ops import _AGENT_BY_ID, _classify_action, _humanize_action

logger = logging.getLogger("midnight.admin_ops")

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

ACTIVE_WINDOW = timedelta(hours=24)
MAX_EVENT_ROWS = 2000
MAX_PROFILE_ROWS = 5000


def _supabase_config() -> tuple[str, str]:
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not url or not key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Supabase not configured.")
    return url, key


def _require_platform_admin(request: Request) -> str:
    """Raise 403 unless the authenticated user's email is in PLATFORM_ADMIN_EMAILS."""
    email = str(getattr(request.state, "user_email", "") or "").strip().lower()
    allowed = {
        e.strip().lower()
        for e in (os.getenv("PLATFORM_ADMIN_EMAILS") or "").split(",")
        if e.strip()
    }
    if not allowed:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="PLATFORM_ADMIN_EMAILS is not configured.")
    if email not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Platform admin access required.")
    return email


def _sb_get(url: str, key: str, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    try:
        r = requests.get(f"{url}/rest/v1/{table}", headers=headers,
                         params=params, timeout=20)
    except requests.RequestException as exc:
        logger.exception("admin_sb_fetch_failed", extra={"table": table})
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Supabase fetch failed: {table}") from exc
    if r.status_code >= 400:
        logger.warning("admin_sb_fetch_status", extra={"table": table,
                                                        "status_code": r.status_code})
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Supabase error {r.status_code} on {table}.")
    payload = r.json() if r.content else []
    return payload if isinstance(payload, list) else []


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


@admin_router.get("/tenants")
async def admin_tenants(request: Request) -> dict[str, Any]:
    _require_platform_admin(request)
    url, key = _supabase_config()

    tenants = _sb_get(url, key, "tenants", {
        "select": "id,slug,industry,plan_type,created_at",
        "order": "created_at.desc",
        "limit": "500",
    })
    profiles = _sb_get(url, key, "profiles", {
        "select": "tenant_id,organization_name,role",
        "limit": str(MAX_PROFILE_ROWS),
    })

    org_map: dict[str, str] = {}
    profile_count: dict[str, int] = {}
    for p in profiles:
        tid = str(p.get("tenant_id") or "")
        if not tid:
            continue
        profile_count[tid] = profile_count.get(tid, 0) + 1
        if not org_map.get(tid) and p.get("organization_name"):
            org_map[tid] = str(p["organization_name"])

    result = []
    for t in tenants:
        tid = str(t.get("id") or "")
        result.append({
            "id": tid,
            "slug": t.get("slug") or "—",
            "organization_name": org_map.get(tid) or t.get("slug") or "—",
            "industry": t.get("industry") or "—",
            "plan_type": t.get("plan_type") or "trial",
            "created_at": t.get("created_at"),
            "profile_count": profile_count.get(tid, 0),
        })

    return {
        "fetched_at": datetime.now(UTC).isoformat(),
        "count": len(result),
        "tenants": result,
    }


@admin_router.get("/agents")
async def admin_agents(request: Request) -> dict[str, Any]:
    _require_platform_admin(request)
    url, key = _supabase_config()
    now = datetime.now(UTC)
    cutoff = now - ACTIVE_WINDOW

    rows = _sb_get(url, key, "activity_log", {
        "select": "tenant_id,action,created_at",
        "order": "created_at.desc",
        "limit": str(MAX_EVENT_ROWS),
    })

    per_tenant: dict[str, dict[str, Any]] = {}
    for row in rows:
        tid = str(row.get("tenant_id") or "")
        if not tid:
            continue
        if tid not in per_tenant:
            per_tenant[tid] = {"total": 0, "count_24h": 0, "last_event_at": None}
        s = per_tenant[tid]
        s["total"] += 1
        ts = _parse_ts(row.get("created_at"))
        if ts is not None:
            if ts >= cutoff:
                s["count_24h"] += 1
            if s["last_event_at"] is None:
                s["last_event_at"] = row.get("created_at")

    active_tenants = sum(1 for s in per_tenant.values() if s["count_24h"] > 0)
    total_events_24h = sum(s["count_24h"] for s in per_tenant.values())

    return {
        "fetched_at": now.isoformat(),
        "tenant_count": len(per_tenant),
        "active_tenants_24h": active_tenants,
        "total_events_24h": total_events_24h,
        "total_events": len(rows),
        "per_tenant": per_tenant,
    }


@admin_router.get("/events")
async def admin_events(request: Request, limit: int = 50) -> dict[str, Any]:
    _require_platform_admin(request)
    url, key = _supabase_config()
    bounded = max(1, min(int(limit), 200))

    rows = _sb_get(url, key, "activity_log", {
        "select": "id,tenant_id,action,created_at",
        "order": "created_at.desc",
        "limit": str(bounded),
    })

    events = []
    for row in rows:
        action = row.get("action") or ""
        agent_id = _classify_action(action)
        agent = _AGENT_BY_ID.get(agent_id, _AGENT_BY_ID["signal_manager"])
        events.append({
            "id": row.get("id"),
            "tenant_id": row.get("tenant_id"),
            "timestamp": row.get("created_at"),
            "action": action,
            "action_label": _humanize_action(action),
            "agent_id": agent["id"],
            "agent_name": agent["name"],
        })

    return {
        "fetched_at": datetime.now(UTC).isoformat(),
        "count": len(events),
        "events": events,
    }
