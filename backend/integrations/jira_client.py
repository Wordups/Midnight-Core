"""
Midnight Core — jira_client.py

A thin, fail-closed client for Jira Cloud's REST API v3. Midnight uses it to push
compliance gaps into a tenant's Jira project as issues and to read their status
back, so remediation is tracked where the team already works.

Auth is Basic (Atlassian account email + API token) — the standard way a backend
service talks to Jira Cloud. The token is a tenant secret: it is never logged and
never returned to the client (see api/integrations.py for masking).

Descriptions are Atlassian Document Format (ADF) — v3 rejects plain strings.
"""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("midnight.jira")

_TIMEOUT = 15.0


class JiraError(Exception):
    """A Jira API call failed. Message is safe to surface (no secrets)."""


def _adf(text: str) -> dict[str, Any]:
    """Wrap plain text (newline-separated) into a minimal ADF document. Blank
    lines separate paragraphs; a leading '- ' / '* ' becomes a bullet list."""
    blocks: list[dict[str, Any]] = []
    bullets: list[str] = []

    def flush_bullets() -> None:
        if bullets:
            blocks.append({
                "type": "bulletList",
                "content": [
                    {"type": "listItem", "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": b}]}
                    ]}
                    for b in bullets
                ],
            })
            bullets.clear()

    for line in (text or "").split("\n"):
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            bullets.append(stripped[2:].strip())
            continue
        flush_bullets()
        if stripped:
            blocks.append({"type": "paragraph", "content": [{"type": "text", "text": stripped}]})
    flush_bullets()
    if not blocks:
        blocks = [{"type": "paragraph", "content": []}]
    return {"type": "doc", "version": 1, "content": blocks}


@dataclass
class JiraConfig:
    site_url: str          # e.g. https://midnightgrc.atlassian.net
    email: str
    api_token: str
    project_key: str = "GRC"

    def normalized_site(self) -> str:
        site = (self.site_url or "").strip().rstrip("/")
        if not site.startswith(("http://", "https://")):
            site = "https://" + site
        return site


class JiraClient:
    def __init__(self, config: JiraConfig, transport: "httpx.BaseTransport | None" = None):
        if not (config.site_url and config.api_token) or (transport is None and not config.email):
            raise JiraError("Jira is not configured (site, email, and API token are required).")
        self._config = config
        # transport is a dependency-injection seam for tests/demos (httpx
        # MockTransport); None means real network.
        self._transport = transport
        token = base64.b64encode(f"{config.email}:{config.api_token}".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._base = config.normalized_site() + "/rest/api/3"

    def _http(self) -> "httpx.Client":
        return httpx.Client(timeout=_TIMEOUT, transport=self._transport)

    # ── operations ──────────────────────────────────────────────────────────
    def test_connection(self) -> dict[str, Any]:
        """Verify credentials by fetching the current user. Never raises the
        raw token; returns a small dict on success."""
        try:
            with self._http() as client:
                resp = client.get(f"{self._base}/myself", headers=self._headers)
        except httpx.HTTPError as exc:
            raise JiraError(f"Could not reach Jira: {exc.__class__.__name__}") from exc
        if resp.status_code == 401:
            raise JiraError("Jira rejected the credentials (check email + API token).")
        if resp.status_code >= 400:
            raise JiraError(f"Jira connection failed (HTTP {resp.status_code}).")
        data = resp.json()
        return {"account_id": data.get("accountId"), "email": data.get("emailAddress"),
                "display_name": data.get("displayName")}

    def create_issue(self, *, summary: str, description: str,
                     issue_type: str = "Task", labels: list[str] | None = None,
                     project_key: str | None = None) -> dict[str, Any]:
        fields: dict[str, Any] = {
            "project": {"key": project_key or self._config.project_key},
            "issuetype": {"name": issue_type},
            "summary": summary[:250],
            "description": _adf(description),
        }
        if labels:
            # Jira labels can't contain spaces.
            fields["labels"] = [l.replace(" ", "-") for l in labels if l]
        try:
            with self._http() as client:
                resp = client.post(f"{self._base}/issue", headers=self._headers,
                                   json={"fields": fields})
        except httpx.HTTPError as exc:
            raise JiraError(f"Could not reach Jira: {exc.__class__.__name__}") from exc
        if resp.status_code == 401:
            raise JiraError("Jira rejected the credentials (check email + API token).")
        if resp.status_code >= 400:
            # Surface Jira's field errors without leaking auth.
            detail = ""
            try:
                body = resp.json()
                detail = "; ".join(str(v) for v in (body.get("errors") or {}).values()) \
                    or "; ".join(body.get("errorMessages") or [])
            except Exception:
                pass
            raise JiraError(f"Jira rejected the issue (HTTP {resp.status_code}). {detail}".strip())
        data = resp.json()
        key = data.get("key")
        return {"key": key, "id": data.get("id"),
                "url": f"{self._config.normalized_site()}/browse/{key}" if key else None}

    def get_issue_status(self, issue_key: str) -> dict[str, Any]:
        try:
            with self._http() as client:
                resp = client.get(f"{self._base}/issue/{issue_key}",
                                  headers=self._headers,
                                  params={"fields": "status,summary"})
        except httpx.HTTPError as exc:
            raise JiraError(f"Could not reach Jira: {exc.__class__.__name__}") from exc
        if resp.status_code == 404:
            raise JiraError(f"Jira issue {issue_key} not found.")
        if resp.status_code >= 400:
            raise JiraError(f"Jira status lookup failed (HTTP {resp.status_code}).")
        f = resp.json().get("fields", {})
        status = (f.get("status") or {})
        category = (status.get("statusCategory") or {})
        return {
            "key": issue_key,
            "summary": f.get("summary"),
            "status": status.get("name"),
            "status_category": category.get("key"),  # new | indeterminate | done
            "done": category.get("key") == "done",
            "url": f"{self._config.normalized_site()}/browse/{issue_key}",
        }
