"""
Midnight Core — scheduler.py

The in-process automation clock. Started from the FastAPI startup hook, it
ticks every AUTOMATION_INTERVAL_MINUTES (default 60) and runs the Jira
automation pass (jira_sync.run_tick) for every tenant with an enabled Jira
integration: status sync-back, auto-push of newly detected gaps, and the
monthly readiness check when one is due.

The loop is deliberately boring: pure asyncio, no external scheduler dep, and
one tenant's failure never stops the tick. Disable entirely with
AUTOMATION_SCHEDULER=0 (tests set this; so does any deploy that prefers an
external cron hitting POST /api/v1/integrations/jira/sync).
"""
from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger("midnight.scheduler")

_task: asyncio.Task | None = None


def _interval_seconds() -> float:
    try:
        minutes = float(os.getenv("AUTOMATION_INTERVAL_MINUTES", "60"))
    except ValueError:
        minutes = 60.0
    return max(60.0, minutes * 60.0)


def enabled() -> bool:
    return os.getenv("AUTOMATION_SCHEDULER", "1").strip().lower() not in {"0", "false", "off"}


def run_pass() -> list[dict]:
    """One synchronous automation pass over every automation-enabled tenant.
    Also callable directly (tests, scripts, a one-off ops run)."""
    from backend.integrations.jira_sync import list_automation_tenants, run_tick

    results = []
    for tenant_id in list_automation_tenants():
        try:
            results.append(run_tick(tenant_id))
        except Exception as exc:  # never let one tenant kill the pass
            logger.warning("automation tick failed for %s: %s", tenant_id, exc)
            results.append({"tenant_id": tenant_id, "error": str(exc)})
    return results


async def _loop() -> None:
    interval = _interval_seconds()
    logger.info("automation scheduler running (every %.0f s)", interval)
    # First pass is delayed so app startup (and short-lived test clients)
    # never fires network calls the moment the process boots.
    await asyncio.sleep(min(120.0, interval))
    while True:
        try:
            results = await asyncio.to_thread(run_pass)
            if results:
                logger.info("automation pass complete: %d tenant(s)", len(results))
        except Exception as exc:
            logger.warning("automation pass errored: %s", exc)
        await asyncio.sleep(interval)


def start() -> None:
    """Idempotent; call from the FastAPI startup hook."""
    global _task
    if not enabled():
        logger.info("automation scheduler disabled (AUTOMATION_SCHEDULER=0)")
        return
    if _task is None or _task.done():
        _task = asyncio.get_event_loop().create_task(_loop())


def stop() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
