alter table if exists public.policies
  add column if not exists document_type text,
  add column if not exists organization text,
  add column if not exists owner text,
  add column if not exists schema_version text,
  add column if not exists selected_frameworks jsonb default '[]'::jsonb;

create table if not exists public.policy_sections (
  id uuid primary key default gen_random_uuid(),
  policy_id uuid not null references public.policies(id) on delete cascade,
  tenant_id uuid not null references public.tenants(id) on delete cascade,
  slot_id text not null,
  heading text not null,
  content text not null,
  sort_order integer not null default 0,
  source_origin text,
  confidence_score double precision,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists idx_policy_sections_policy_id on public.policy_sections(policy_id);
create index if not exists idx_policy_sections_tenant_id on public.policy_sections(tenant_id);
create unique index if not exists idx_policy_sections_policy_slot on public.policy_sections(policy_id, slot_id);

alter table if exists public.policy_sections enable row level security;

drop policy if exists policy_sections_tenant_isolation on public.policy_sections;
create policy policy_sections_tenant_isolation
on public.policy_sections
for all
using (tenant_id = public.current_tenant_id())
with check (tenant_id = public.current_tenant_id());
