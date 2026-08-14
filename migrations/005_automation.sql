-- Midnight Core — Jira automation (SCRUM-12 / SCRUM-13 / SCRUM-24)
-- Auto-push on detection, status sync-back, and the recurring readiness cadence.

alter table jira_integrations
    add column if not exists auto_push boolean not null default false,
    add column if not exists alert_webhook_url text,
    add column if not exists last_readiness_at timestamptz;

-- Sync-back marks a link resolved when its Jira issue reaches a done status
-- category. The Midnight gap itself only closes when re-ingested evidence
-- covers the control — resolved_at records that remediation finished in Jira.
alter table jira_issue_links
    add column if not exists resolved_at timestamptz;
