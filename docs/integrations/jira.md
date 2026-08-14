# Jira integration

Midnight connects to Jira Cloud in two directions, against the Jira REST API v3.

## Two projects, two purposes
- **Midnight Shift (`MS`)** — compliance. Detected gaps / remediation items are
  pushed here by the product as Jira Tasks: `[control] summary`, the source
  document ID in the body, framework + severity labels.
- **Night Shift (`SCRUM`)** — engineering. The nightly scheduler reports its own
  completed work here (one Task per merged PR).

> Only classic Jira projects (Software / Work Management) are REST-addressable.
> Projects created in **Atlassian Home** (`home.atlassian.net`) are a different
> product and cannot receive issues via the API.

## Compliance push (layer 2 — the product)
Backend: `backend/integrations/jira_client.py` (REST v3, Basic auth, ADF),
`backend/integrations/jira_config.py` (per-tenant config + env fallback),
`backend/api/integrations.py` (`/api/v1/integrations/jira/*`).

Per-tenant config is set in the dashboard **Integrations** screen (site URL,
project key, email, API token — token stored server-side, masked in the UI).
An env fallback (`JIRA_SITE_URL` / `JIRA_EMAIL` / `JIRA_API_TOKEN` /
`JIRA_PROJECT_KEY`) covers the demo tenant.

Endpoints: `GET/PUT /config`, `POST /test`, `POST /push-gap`,
`GET /issues/{key}`, `GET /links`.

## Automation (scheduler + alerts)
`backend/core/scheduler.py` starts an in-process loop on app startup
(`AUTOMATION_INTERVAL_MINUTES`, default 60; disable with
`AUTOMATION_SCHEDULER=0`). Each pass runs `backend/integrations/jira_sync.py`
per Jira-enabled tenant:

1. **Sync-back** — refresh open `jira_issue_links`; a Jira issue reaching a
   done status category stamps `resolved_at` and alerts. The Midnight gap
   itself closes only when re-ingested evidence covers the control.
2. **Auto-push** (opt-in per tenant, `auto_push`) — recompute program gaps and
   file every unlinked critical/medium gap as a Jira issue. Dedupe is by
   `control_id` against `jira_issue_links`, so re-runs never double-file.
3. **Readiness cadence** — every 30 days (`last_readiness_at`), snapshot
   coverage + open gaps and alert with the summary.

Alerts land in the tenant's activity feed (signals) and, when
`alert_webhook_url` is set, POST a Slack-compatible `{"text"}` payload.
`POST /sync` is the one-click version (sync-back + push-all), wired to the
dashboard's **Sync now** button. Requires migration `005_automation.sql`.

## Engineering report (CI)
`.github/workflows/jira-report.yml` runs on PR merge and records the completed
work as a Night Shift Task. It runs on a GitHub runner because the Claude
routine sandbox has no Jira egress. Requires repo secrets `JIRA_BASE_URL`,
`JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_AGENT_PROJECT_KEY`; it no-ops if unset and
never fails a merge.
