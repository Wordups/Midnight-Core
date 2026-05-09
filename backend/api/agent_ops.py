"""
Midnight Core - Agent Ops Center.

Exposes read-only telemetry derived from the existing activity_log table.
Does not introduce new persistence; every status field is computed on demand
from the rows already written by signal_manager / save_generated_document.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
import logging
import os

from fastapi import APIRouter, HTTPException, Request, status
import requests


logger = logging.getLogger("midnight.agent_ops")

agent_ops_router = APIRouter(prefix="/api/agents", tags=["agent-ops"])


AGENT_CATALOG: list[dict[str, str]] = [
    {
        "id": "signal_manager",
        "name": "Signal Manager",
        "role": "Classifies and persists every system event into activity_log.",
    },
    {
        "id": "policy_agent",
        "name": "Policy Agent",
        "role": "Generates and updates policy drafts and sections.",
    },
    {
        "id": "cleaner_agent",
        "name": "Cleaner Agent",
        "role": "Cleans and migrates legacy documents into the canonical schema.",
    },
    {
        "id": "framework_mapping_agent",
        "name": "Framework Mapping Agent",
        "role": "Maps policy content to compliance frameworks and surfaces gaps.",
    },
    {
        "id": "tenant_manager",
        "name": "Tenant Manager",
        "role": "Provisions tenants and manages onboarding and invites.",
    },
    {
        "id": "evidence_agent",
        "name": "Evidence Agent",
        "role": "Collects and links supporting evidence for controls.",
    },
    {
        "id": "executive_summary_agent",
        "name": "Executive Summary Agent",
        "role": "Produces executive-level summaries of policy posture.",
    },
]

_AGENT_BY_ID: dict[str, dict[str, str]] = {a["id"]: a for a in AGENT_CATALOG}

ACTIVE_WINDOW = timedelta(hours=24)
DEFAULT_EVENT_LIMIT = 50
MAX_EVENT_LIMIT = 200
STATUS_QUERY_LIMIT = 500


def _classify_action(action: str) -> str:
    """Map an activity_log.action string to a responsible agent id."""
    a = (action or "").lower()
    if not a:
        return "signal_manager"
    if "policy" in a or a == "generated":
        return "policy_agent"
    if "migration" in a or "clean" in a:
        return "cleaner_agent"
    if "framework" in a:
        return "framework_mapping_agent"
    if "invite" in a or "onboarding" in a or "signup" in a or "tenant" in a or "membership" in a:
        return "tenant_manager"
    if "evidence" in a:
        return "evidence_agent"
    if "summary" in a or "executive" in a:
        return "executive_summary_agent"
    return "signal_manager"


def _humanize_action(action: str) -> str:
    return str(action or "activity").replace("_", " ").title()


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _supabase_config() -> tuple[str, str]:
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
    if not url or not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured for agent ops telemetry.",
        )
    return url, key


def _fetch_activity_rows(tenant_id: str, *, limit: int) -> list[dict[str, Any]]:
    url, key = _supabase_config()
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    params = {
        "select": "id,action,policy_id,created_at,tenant_id",
        "tenant_id": f"eq.{tenant_id}",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    try:
        response = requests.get(
            f"{url}/rest/v1/activity_log",
            headers=headers,
            params=params,
            timeout=15,
        )
    except requests.RequestException as exc:
        logger.exception("agent_ops_activity_fetch_failed", extra={"tenant_id": tenant_id})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach activity_log.",
        ) from exc

    if response.status_code >= 400:
        logger.warning(
            "agent_ops_activity_fetch_status",
            extra={
                "tenant_id": tenant_id,
                "status_code": response.status_code,
                "body": response.text[:500],
            },
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="activity_log query failed.",
        )

    payload = response.json() if response.content else []
    return payload if isinstance(payload, list) else []


def _fetch_policies(tenant_id: str, policy_ids: set[str]) -> dict[str, dict[str, Any]]:
    if not policy_ids:
        return {}
    url, key = _supabase_config()
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    ids_csv = ",".join(sorted(p for p in policy_ids if p))
    if not ids_csv:
        return {}
    params = {
        "select": "id,policy_name,status",
        "tenant_id": f"eq.{tenant_id}",
        "id": f"in.({ids_csv})",
    }
    try:
        response = requests.get(
            f"{url}/rest/v1/policies",
            headers=headers,
            params=params,
            timeout=15,
        )
    except requests.RequestException:
        logger.exception("agent_ops_policy_lookup_failed", extra={"tenant_id": tenant_id})
        return {}
    if response.status_code >= 400 or not response.content:
        return {}
    rows = response.json()
    if not isinstance(rows, list):
        return {}
    return {row["id"]: row for row in rows if isinstance(row, dict) and row.get("id")}


def _require_tenant_id(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant scope is required for agent ops telemetry.",
        )
    return str(tenant_id)


@agent_ops_router.get("/status")
async def agents_status(request: Request) -> dict[str, Any]:
    tenant_id = _require_tenant_id(request)
    rows = _fetch_activity_rows(tenant_id, limit=STATUS_QUERY_LIMIT)
    now = datetime.now(UTC)
    cutoff = now - ACTIVE_WINDOW

    per_agent: dict[str, dict[str, Any]] = {
        a["id"]: {
            "id": a["id"],
            "name": a["name"],
            "role": a["role"],
            "last_event_at": None,
            "last_action": None,
            "last_action_label": None,
            "event_count_24h": 0,
            "event_count_total": 0,
            "status": "no_data",
        }
        for a in AGENT_CATALOG
    }

    for row in rows:
        agent_id = _classify_action(row.get("action") or "")
        bucket = per_agent.get(agent_id) or per_agent["signal_manager"]
        bucket["event_count_total"] += 1
        ts = _parse_timestamp(row.get("created_at"))
        if ts is not None and ts >= cutoff:
            bucket["event_count_24h"] += 1
        if bucket["last_event_at"] is None and row.get("created_at"):
            bucket["last_event_at"] = row.get("created_at")
            bucket["last_action"] = row.get("action")
            bucket["last_action_label"] = _humanize_action(row.get("action") or "")

    for bucket in per_agent.values():
        if bucket["event_count_24h"] > 0:
            bucket["status"] = "active"
        elif bucket["event_count_total"] > 0:
            bucket["status"] = "idle"
        else:
            bucket["status"] = "no_data"

    return {
        "tenant_id": tenant_id,
        "fetched_at": now.isoformat(),
        "active_window_hours": int(ACTIVE_WINDOW.total_seconds() // 3600),
        "agents": [per_agent[a["id"]] for a in AGENT_CATALOG],
        "total_events": len(rows),
    }


@agent_ops_router.get("/events")
async def agents_events(request: Request, limit: int = DEFAULT_EVENT_LIMIT) -> dict[str, Any]:
    tenant_id = _require_tenant_id(request)
    bounded_limit = max(1, min(int(limit or DEFAULT_EVENT_LIMIT), MAX_EVENT_LIMIT))
    rows = _fetch_activity_rows(tenant_id, limit=bounded_limit)

    policy_ids = {str(row.get("policy_id")) for row in rows if row.get("policy_id")}
    policy_map = _fetch_policies(tenant_id, policy_ids)

    events: list[dict[str, Any]] = []
    for row in rows:
        action = row.get("action") or ""
        agent_id = _classify_action(action)
        agent = _AGENT_BY_ID.get(agent_id, _AGENT_BY_ID["signal_manager"])
        policy = policy_map.get(str(row.get("policy_id") or "")) if row.get("policy_id") else None
        events.append(
            {
                "id": row.get("id"),
                "timestamp": row.get("created_at"),
                "action": action,
                "action_label": _humanize_action(action),
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "policy_id": row.get("policy_id"),
                "policy_name": (policy or {}).get("policy_name"),
                "policy_status": (policy or {}).get("status"),
            }
        )

    return {
        "tenant_id": tenant_id,
        "fetched_at": datetime.now(UTC).isoformat(),
        "limit": bounded_limit,
        "count": len(events),
        "events": events,
    }
