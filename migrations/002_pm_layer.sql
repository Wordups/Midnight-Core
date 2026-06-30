-- Midnight — PM layer migration (requests/tasks, SME invites, roles, audit columns)
-- Run in the Supabase SQL editor. Safe to re-run (idempotent).
--
-- The backend reaches these tables with the service-role client and scopes every
-- query by tenant_id in code, so RLS is enabled (service role bypasses it) with
-- no client policies — the anon key can never read PM data directly.

-- ── requests (the GRC analyst's task/request entity) ─────────────────────────
create table if not exists public.requests (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null,
  creator_id  uuid,
  assignee_id uuid,
  title       text not null,
  description text,
  framework   text,
  control_id  text,
  due_date    date,
  status      text not null default 'open' check (status in ('open', 'in_review', 'complete')),
  response    text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists requests_tenant_created_idx on public.requests (tenant_id, created_at desc);
create index if not exists requests_assignee_idx on public.requests (assignee_id);
alter table public.requests enable row level security;

-- ── profiles.role (owner | analyst | sme) ────────────────────────────────────
alter table public.profiles add column if not exists role text default 'owner';

-- ── invites (invite an SME by email; token-based accept, 7-day expiry) ────────
create table if not exists public.invites (
  id          uuid primary key default gen_random_uuid(),
  tenant_id   uuid not null,
  email       text not null,
  role        text not null default 'sme',
  token       text not null unique,
  invited_by  uuid,
  accepted    boolean not null default false,
  expires_at  timestamptz not null,
  created_at  timestamptz not null default now()
);
create index if not exists invites_token_idx on public.invites (token);
create index if not exists invites_tenant_idx on public.invites (tenant_id, created_at desc);
alter table public.invites enable row level security;

-- ── activity_log: actor + detail columns (richer audit trail) ────────────────
alter table public.activity_log add column if not exists actor_id   uuid;
alter table public.activity_log add column if not exists actor_name text;
alter table public.activity_log add column if not exists detail     text;
-- Existing schema requires policy_id on some installs; make it nullable so PM
-- events (which have no policy) can be logged.
alter table public.activity_log alter column policy_id drop not null;
