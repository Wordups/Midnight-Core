"""
Per-tenant Jira configuration: load / save / resolve.

Resolution order: the tenant's stored row in `jira_integrations`, then an env
fallback (JIRA_SITE_URL / JIRA_EMAIL / JIRA_API_TOKEN / JIRA_PROJECT_KEY) so the
demo tenant works before anyone opens the settings UI. Returns None when neither
is configured — callers fail closed.
"""
from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

from backend.bird_eye.db import insert as db_insert
from backend.bird_eye.db import select as db_select
from backend.bird_eye.db import update as db_update
from backend.integrations.jira_client import JiraConfig

logger = logging.getLogger("midnight.jira.config")

_TABLE = "jira_integrations"


def _from_env() -> JiraConfig | None:
    site = os.getenv("JIRA_SITE_URL", "").strip()
    email = os.getenv("JIRA_EMAIL", "").strip()
    token = os.getenv("JIRA_API_TOKEN", "").strip()
    if not (site and email and token):
        return None
    return JiraConfig(
        site_url=site, email=email, api_token=token,
        project_key=os.getenv("JIRA_PROJECT_KEY", "GRC").strip() or "GRC",
    )


def load_config(tenant_id: str) -> JiraConfig | None:
    """Resolved Jira config for a tenant, or None if unconfigured/disabled."""
    try:
        rows = db_select(_TABLE, tenant_id=tenant_id, columns="*")
    except Exception as exc:  # table missing / db down → fall back to env
        logger.warning("jira config load failed (%s); trying env", exc)
        rows = []
    if rows:
        row = rows[0]
        if not row.get("enabled", True):
            return None
        if row.get("site_url") and row.get("auth_email") and row.get("api_token"):
            return JiraConfig(
                site_url=row["site_url"], email=row["auth_email"],
                api_token=row["api_token"],
                project_key=row.get("project_key") or "GRC",
            )
    return _from_env()


def save_config(tenant_id: str, *, site_url: str, email: str, api_token: str,
                project_key: str = "GRC", enabled: bool = True) -> None:
    """Upsert a tenant's Jira config. Never logs the token."""
    now = datetime.now(UTC).isoformat()
    existing = db_select(_TABLE, tenant_id=tenant_id, columns="tenant_id")
    payload = {
        "site_url": site_url.strip(),
        "project_key": (project_key or "GRC").strip() or "GRC",
        "auth_email": email.strip(),
        "api_token": api_token,
        "enabled": enabled,
        "updated_at": now,
    }
    if existing:
        db_update(_TABLE, tenant_id=tenant_id,
                  filters={"tenant_id": f"eq.{tenant_id}"}, patch=payload)
    else:
        db_insert(_TABLE, {**payload, "tenant_id": tenant_id, "created_at": now})


def public_config(tenant_id: str) -> dict:
    """Config safe to return to the client — token masked, never raw."""
    try:
        rows = db_select(_TABLE, tenant_id=tenant_id, columns="*")
    except Exception:
        rows = []
    if rows:
        row = rows[0]
        return {
            "configured": True,
            "source": "tenant",
            "site_url": row.get("site_url"),
            "project_key": row.get("project_key"),
            "auth_email": row.get("auth_email"),
            "enabled": row.get("enabled", True),
            "api_token": _mask(row.get("api_token")),
        }
    env = _from_env()
    if env:
        return {
            "configured": True, "source": "env",
            "site_url": env.site_url, "project_key": env.project_key,
            "auth_email": env.email, "enabled": True,
            "api_token": _mask(env.api_token),
        }
    return {"configured": False}


def _mask(token: str | None) -> str | None:
    if not token:
        return None
    return f"••••{token[-4:]}" if len(token) > 4 else "••••"
