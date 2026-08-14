"""
Midnight Core — jira_sync.py

The Jira automation layer: everything that runs without a person clicking.

- auto_push_gaps: recompute the tenant's program gaps and push every material
  (critical/medium) gap that isn't already linked to a Jira issue. Dedupe is by
  control_id against jira_issue_links, so re-running never double-files.
- sync_back: read status for open links; when Jira reaches a done category,
  stamp resolved_at and alert. The Midnight gap itself only closes when
  re-ingested evidence covers the control — sync-back records remediation,
  the next readiness run confirms it.
- run_readiness_check: program-level gap snapshot + alert, stamped on the
  tenant row so the scheduler knows when the next monthly run is due.
- run_tick: one scheduler pass for one tenant (sync → auto-push → readiness).

Every step is fail-safe: one tenant's broken Jira config never stops the tick,
and alerts (activity signal + optional webhook) never raise.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import requests

from backend.bird_eye.db import _rest_url, _service_headers
from backend.bird_eye.db import select as db_select
from backend.bird_eye.db import update as db_update
from backend.core.gap_engine import run_program_gap_analysis
from backend.integrations.jira_client import JiraClient, JiraError
from backend.integrations.jira_config import load_config, load_settings
from backend.storage.file_store import (
    create_signal_activity_event,
    list_policies_for_gap_analysis,
)

logger = logging.getLogger("midnight.jira.sync")

_LINKS = "jira_issue_links"
_INTEGRATIONS = "jira_integrations"

MATERIAL_SEVERITIES = {"critical", "medium"}
READINESS_INTERVAL_DAYS = 30
_WEBHOOK_TIMEOUT = 10.0


# ── alerts ───────────────────────────────────────────────────────────────────

def alert(tenant_id: str, *, event_type: str, summary: str,
          metadata: dict[str, Any] | None = None) -> None:
    """Record an alert in the tenant's activity feed and, when a webhook URL is
    configured, POST a Slack-compatible {"text": ...} payload. Never raises."""
    try:
        create_signal_activity_event(
            tenant_id=tenant_id, event_type=event_type,
            source="jira.automation", summary=summary, metadata=metadata or {},
        )
    except Exception as exc:
        logger.warning("alert signal failed for %s: %s", tenant_id, exc)
    try:
        webhook = (load_settings(tenant_id) or {}).get("alert_webhook_url")
        if webhook:
            httpx.post(webhook, json={"text": f"Midnight: {summary}"},
                       timeout=_WEBHOOK_TIMEOUT)
    except Exception as exc:
        logger.warning("alert webhook failed for %s: %s", tenant_id, exc)


# ── gap detection (tenant-scoped, no Request needed) ─────────────────────────

def detect_gaps(tenant_id: str) -> dict:
    """Program-level gap analysis for a tenant. Same computation the dashboard
    shows; {} when there is nothing to analyze."""
    policies = list_policies_for_gap_analysis(tenant_id)
    if not policies:
        return {}
    documents = [
        {
            "name": p["policy_name"],
            "doc_type": (p.get("document_type") or "POLICY").upper(),
            "covered_control_ids": p.get("covered_control_ids") or [],
        }
        for p in policies
    ]
    frameworks = list({fw for p in policies for fw in (p.get("selected_frameworks") or [])})
    if not frameworks:
        return {}
    return run_program_gap_analysis(documents=documents, frameworks=frameworks)


# ── auto-push on detection (SCRUM-12) ────────────────────────────────────────

def _linked_control_ids(tenant_id: str) -> set[str]:
    rows = db_select(_LINKS, tenant_id=tenant_id, columns="control_id")
    return {r["control_id"] for r in rows if r.get("control_id")}


def auto_push_gaps(tenant_id: str, gaps: list[dict] | None = None) -> dict:
    """Push every material gap that has no Jira link yet. Returns
    {pushed: [...], skipped_linked: n, skipped_severity: n}."""
    config = load_config(tenant_id)
    if config is None:
        return {"pushed": [], "skipped_linked": 0, "skipped_severity": 0,
                "detail": "Jira not configured."}

    if gaps is None:
        gaps = (detect_gaps(tenant_id) or {}).get("gaps", [])

    already = _linked_control_ids(tenant_id)
    client = JiraClient(config)
    pushed: list[dict] = []
    skipped_linked = skipped_severity = 0

    for gap in gaps:
        control_id = gap.get("control_id") or ""
        severity = str(gap.get("severity", "")).lower()
        if severity not in MATERIAL_SEVERITIES:
            skipped_severity += 1
            continue
        if control_id and control_id in already:
            skipped_linked += 1
            continue
        summary = f"[{control_id}] {gap.get('name') or 'Compliance gap'}" \
            if control_id else (gap.get("name") or "Compliance gap")
        description = "\n".join(filter(None, [
            "Source: Midnight Core — automated gap detection",
            f"Framework / Control: {gap.get('framework', '')} {control_id}".strip(),
            f"Severity: {severity}",
            "",
            "Finding",
            gap.get("description") or gap.get("reason") or "Control not covered by any ingested document.",
            "",
            "Suggested remediation",
            gap.get("suggested_action") or "",
        ]))
        try:
            issue = client.create_issue(
                summary=summary, description=description,
                labels=["midnight", "gap-remediation", "auto-pushed",
                        gap.get("framework") or "", f"severity-{severity}"],
            )
        except JiraError as exc:
            logger.warning("auto-push failed for %s %s: %s", tenant_id, control_id, exc)
            continue
        _record_link(tenant_id, issue, control_id)
        if control_id:
            already.add(control_id)
        pushed.append({"control_id": control_id, "key": issue.get("key"),
                       "url": issue.get("url")})

    if pushed:
        keys = ", ".join(p["key"] for p in pushed if p.get("key"))
        alert(tenant_id, event_type="jira_gaps_auto_pushed",
              summary=f"Auto-pushed {len(pushed)} compliance gap(s) to Jira: {keys}.",
              metadata={"pushed": pushed})
    return {"pushed": pushed, "skipped_linked": skipped_linked,
            "skipped_severity": skipped_severity}


def _record_link(tenant_id: str, issue: dict, control_id: str) -> None:
    now = datetime.now(UTC).isoformat()
    try:
        requests.post(
            _rest_url(_LINKS), headers=_service_headers(),
            json=[{
                "tenant_id": tenant_id,
                "issue_key": issue.get("key"),
                "issue_url": issue.get("url"),
                "control_id": control_id or None,
                "last_status": "To Do",
                "last_synced_at": now,
                "created_at": now,
            }],
            timeout=30,
        )
    except Exception as exc:  # the issue exists either way; linking is best-effort
        logger.warning("auto-push link record failed: %s", exc)


# ── status sync-back (SCRUM-13) ──────────────────────────────────────────────

def sync_back(tenant_id: str) -> dict:
    """Refresh status for unresolved links; stamp resolved_at + alert on newly
    done issues. Returns {synced: n, newly_done: [...]}."""
    config = load_config(tenant_id)
    if config is None:
        return {"synced": 0, "newly_done": [], "detail": "Jira not configured."}

    rows = db_select(_LINKS, tenant_id=tenant_id, columns="*",
                     filters={"resolved_at": "is.null"})
    if not rows:
        return {"synced": 0, "newly_done": []}

    client = JiraClient(config)
    newly_done: list[dict] = []
    synced = 0
    for row in rows:
        key = row.get("issue_key")
        if not key:
            continue
        try:
            status = client.get_issue_status(key)
        except JiraError as exc:
            logger.warning("sync-back status failed for %s: %s", key, exc)
            continue
        patch: dict[str, Any] = {
            "last_status": status.get("status"),
            "last_synced_at": datetime.now(UTC).isoformat(),
        }
        if status.get("done"):
            patch["resolved_at"] = datetime.now(UTC).isoformat()
            newly_done.append({"key": key, "control_id": row.get("control_id")})
        try:
            db_update(_LINKS, tenant_id=tenant_id,
                      filters={"issue_key": f"eq.{key}"}, patch=patch)
            synced += 1
        except Exception as exc:
            logger.warning("sync-back update failed for %s: %s", key, exc)

    for done in newly_done:
        control = f" ({done['control_id']})" if done.get("control_id") else ""
        alert(tenant_id, event_type="jira_issue_done",
              summary=f"Jira {done['key']} is Done{control} — remediation complete. "
                      "Re-ingest the updated evidence to confirm closure.",
              metadata=done)
    return {"synced": synced, "newly_done": newly_done}


# ── recurring readiness cadence (SCRUM-24) ───────────────────────────────────

def readiness_due(tenant_id: str, *, now: datetime | None = None) -> bool:
    rows = db_select(_INTEGRATIONS, tenant_id=tenant_id, columns="last_readiness_at")
    last = (rows[0].get("last_readiness_at") if rows else None)
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
    except ValueError:
        return True
    return (now or datetime.now(UTC)) - last_dt >= timedelta(days=READINESS_INTERVAL_DAYS)


def run_readiness_check(tenant_id: str) -> dict:
    """Snapshot the tenant's compliance posture, alert with the summary, and
    stamp last_readiness_at so the scheduler knows the next run date."""
    result = detect_gaps(tenant_id) or {}
    total = result.get("total_gaps", 0)
    coverage = result.get("overall_coverage_pct", 0)
    alert(tenant_id, event_type="readiness_run_completed",
          summary=(f"Scheduled readiness check: {coverage}% overall coverage, "
                   f"{total} open gap(s) "
                   f"({result.get('gaps_critical', 0)} critical, "
                   f"{result.get('gaps_medium', 0)} medium)."),
          metadata={k: result.get(k) for k in (
              "total_gaps", "gaps_critical", "gaps_medium", "gaps_low",
              "overall_coverage_pct", "coverage_by_framework")})
    try:
        db_update(_INTEGRATIONS, tenant_id=tenant_id,
                  filters={"tenant_id": f"eq.{tenant_id}"},
                  patch={"last_readiness_at": datetime.now(UTC).isoformat()})
    except Exception as exc:
        logger.warning("readiness stamp failed for %s: %s", tenant_id, exc)
    return result


# ── one scheduler pass for one tenant ────────────────────────────────────────

def run_tick(tenant_id: str, *, force_readiness: bool = False) -> dict:
    """sync-back → auto-push (if enabled) → readiness (monthly or forced).
    Each stage is independent; a failure in one never blocks the next."""
    out: dict[str, Any] = {"tenant_id": tenant_id}
    try:
        out["sync"] = sync_back(tenant_id)
    except Exception as exc:
        logger.warning("tick sync-back failed for %s: %s", tenant_id, exc)
        out["sync"] = {"error": str(exc)}

    try:
        settings = load_settings(tenant_id) or {}
        if settings.get("auto_push"):
            out["auto_push"] = auto_push_gaps(tenant_id)
        else:
            out["auto_push"] = {"skipped": "auto_push disabled"}
    except Exception as exc:
        logger.warning("tick auto-push failed for %s: %s", tenant_id, exc)
        out["auto_push"] = {"error": str(exc)}

    try:
        if force_readiness or readiness_due(tenant_id):
            out["readiness"] = {
                "ran": True,
                "total_gaps": (run_readiness_check(tenant_id) or {}).get("total_gaps", 0),
            }
        else:
            out["readiness"] = {"ran": False}
    except Exception as exc:
        logger.warning("tick readiness failed for %s: %s", tenant_id, exc)
        out["readiness"] = {"error": str(exc)}
    return out


def list_automation_tenants() -> list[str]:
    """Tenant ids with an enabled Jira integration row. This is the one
    deliberate cross-tenant read in the module — scheduler enumeration only,
    service-role, ids only."""
    try:
        resp = requests.get(
            _rest_url(_INTEGRATIONS), headers=_service_headers(),
            params={"select": "tenant_id", "enabled": "eq.true"}, timeout=30,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}")
        return [r["tenant_id"] for r in (resp.json() or []) if r.get("tenant_id")]
    except Exception as exc:
        logger.warning("automation tenant enumeration failed: %s", exc)
        return []
