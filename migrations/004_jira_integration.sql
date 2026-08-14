-- Midnight Core — Jira integration (layer 2)
-- Per-tenant Jira connection: where remediation issues are pushed and synced.
-- api_token is a tenant secret — service-role access only; never returned to
-- the client in plaintext (the API masks it). Consider column-level encryption
-- (pgcrypto / Vault) before onboarding external tenants.

create table if not exists jira_integrations (
    tenant_id   uuid primary key references tenants(id) on delete cascade,
    site_url    text not null,                       -- https://acme.atlassian.net
    project_key text not null default 'GRC',
    auth_email  text not null,
    api_token   text not null,
    enabled     boolean not null default true,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

-- Link a pushed Jira issue back to the Midnight gap/request that created it, so
-- status sync knows which posture item to update.
create table if not exists jira_issue_links (
    id             uuid primary key default gen_random_uuid(),
    tenant_id      uuid not null references tenants(id) on delete cascade,
    issue_key      text not null,                    -- e.g. GRC-14
    issue_url      text,
    control_id     text,                             -- e.g. SOC2-CC6.1
    document_id    text,                             -- e.g. PFI-SEC-014
    request_id     uuid,                             -- optional: PM Requests inbox item
    last_status    text,
    last_synced_at timestamptz,
    created_at     timestamptz not null default now(),
    unique (tenant_id, issue_key)
);

create index if not exists jira_issue_links_tenant_idx on jira_issue_links (tenant_id);
