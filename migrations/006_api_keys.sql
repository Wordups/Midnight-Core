-- Midnight Core — per-tenant API keys for the remote MCP gateway.
-- The full key is shown once at mint time and stored only as a sha256 hash;
-- key_prefix (mk_xxxxxxxx…) is what the UI lists. Revocation is a timestamp
-- so keys are auditable after death.

create table if not exists api_keys (
    id           uuid primary key default gen_random_uuid(),
    tenant_id    uuid not null references tenants(id) on delete cascade,
    name         text not null default 'AI connector',
    key_hash     text not null unique,
    key_prefix   text not null,
    created_at   timestamptz not null default now(),
    last_used_at timestamptz,
    revoked_at   timestamptz
);

create index if not exists api_keys_tenant_idx on api_keys (tenant_id);
alter table api_keys enable row level security;
