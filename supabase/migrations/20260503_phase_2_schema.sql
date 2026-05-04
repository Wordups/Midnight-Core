begin;

create extension if not exists pgcrypto;

create or replace function public.slugify(input text)
returns text
language sql
immutable
as $$
  select nullif(trim(both '-' from regexp_replace(lower(coalesce(input, '')), '[^a-z0-9]+', '-', 'g')), '');
$$;

create or replace function public.current_tenant_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select p.tenant_id
  from public.profiles as p
  where p.id = auth.uid()
  limit 1;
$$;

grant execute on function public.current_tenant_id() to authenticated, service_role;

-- Step 1: tenants table completion
alter table public.tenants add column if not exists slug text;
alter table public.tenants add column if not exists industry text;
alter table public.tenants add column if not exists plan_type text default 'trial';
alter table public.tenants add column if not exists region text;
alter table public.tenants add column if not exists employee_count text;

update public.tenants
set slug = coalesce(public.slugify(name), 'tenant-' || left(id::text, 8))
where slug is null or btrim(slug) = '';

with ranked as (
  select
    id,
    slug,
    row_number() over (partition by slug order by created_at nulls last, id) as rn
  from public.tenants
)
update public.tenants as t
set slug = ranked.slug || '-' || ranked.rn
from ranked
where t.id = ranked.id
  and ranked.rn > 1;

alter table public.tenants alter column slug set not null;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.tenants'::regclass
      and conname = 'tenants_slug_key'
  ) then
    alter table public.tenants add constraint tenants_slug_key unique (slug);
  end if;
end $$;

-- Step 2: activity_log tenant_id
alter table public.activity_log add column if not exists tenant_id uuid references public.tenants(id);

update public.activity_log as al
set tenant_id = p.tenant_id
from public.policies as p
where al.policy_id = p.id
  and (al.tenant_id is null or al.tenant_id <> p.tenant_id);

create index if not exists activity_log_tenant_id_idx on public.activity_log (tenant_id);

-- Step 3: merge organizations into tenants, then drop organizations
update public.tenants as t
set
  industry = coalesce(t.industry, o.industry),
  employee_count = coalesce(t.employee_count, o.size),
  region = coalesce(t.region, o.state)
from public.organizations as o
where lower(btrim(t.name)) = lower(btrim(o.name));

with org_rows as (
  select
    o.id,
    o.name,
    o.industry,
    o.state,
    o.size,
    coalesce(public.slugify(o.name), 'tenant-' || left(o.id::text, 8)) as base_slug,
    row_number() over (
      partition by coalesce(public.slugify(o.name), 'tenant-' || left(o.id::text, 8))
      order by o.created_at nulls last, o.id
    ) as rn
  from public.organizations as o
  left join public.tenants as t
    on lower(btrim(t.name)) = lower(btrim(o.name))
  where t.id is null
),
prepared as (
  select
    name,
    industry,
    state,
    size,
    case
      when rn = 1 then base_slug
      else base_slug || '-' || rn
    end as slug
  from org_rows
)
insert into public.tenants (id, name, slug, industry, region, employee_count, plan_type, created_at)
select
  gen_random_uuid(),
  p.name,
  p.slug,
  p.industry,
  p.state,
  p.size,
  'trial',
  now()
from prepared as p
on conflict (slug) do update
set
  industry = coalesce(public.tenants.industry, excluded.industry),
  region = coalesce(public.tenants.region, excluded.region),
  employee_count = coalesce(public.tenants.employee_count, excluded.employee_count);

drop table if exists public.organizations;

-- Step 4: policy_gaps tenant_id
alter table public.policy_gaps add column if not exists tenant_id uuid references public.tenants(id);

update public.policy_gaps as pg
set tenant_id = p.tenant_id
from public.policies as p
where pg.policy_id = p.id
  and (pg.tenant_id is null or pg.tenant_id <> p.tenant_id);

create index if not exists policy_gaps_tenant_id_idx on public.policy_gaps (tenant_id);

-- Step 5: policy_runs tenant_id
alter table public.policy_runs add column if not exists tenant_id uuid references public.tenants(id);

update public.policy_runs as pr
set tenant_id = p.tenant_id
from public.policies as p
where pr.policy_id = p.id
  and (pr.tenant_id is null or pr.tenant_id <> p.tenant_id);

create index if not exists policy_runs_tenant_id_idx on public.policy_runs (tenant_id);

-- Step 6: missing tables
create table if not exists public.onboarding_sessions (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references public.tenants(id),
  current_step text default 'plan',
  progress integer default 0,
  build_method text,
  primary_objective text,
  frameworks jsonb default '[]'::jsonb,
  enabled_modules jsonb default '[]'::jsonb,
  completed boolean default false,
  created_at timestamptz default now()
);

create index if not exists onboarding_sessions_tenant_id_idx on public.onboarding_sessions (tenant_id);

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references public.tenants(id),
  policy_id uuid references public.policies(id),
  file_path text,
  file_type text,
  file_name text,
  storage_url text,
  created_at timestamptz default now()
);

create index if not exists documents_tenant_id_idx on public.documents (tenant_id);
create index if not exists documents_policy_id_idx on public.documents (policy_id);

create table if not exists public.enabled_modules (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references public.tenants(id),
  module_key text not null,
  enabled boolean default true,
  created_at timestamptz default now()
);

create unique index if not exists enabled_modules_tenant_module_key_idx
  on public.enabled_modules (tenant_id, module_key);

-- Step 8: profiles table completion
alter table public.profiles add column if not exists name text;
alter table public.profiles add column if not exists organization_name text;

update public.profiles as p
set organization_name = t.name
from public.tenants as t
where p.tenant_id = t.id
  and (p.organization_name is null or btrim(p.organization_name) = '');

-- Step 7: Row Level Security
alter table public.tenants enable row level security;
alter table public.profiles enable row level security;
alter table public.policies enable row level security;
alter table public.activity_log enable row level security;
alter table public.policy_gaps enable row level security;
alter table public.policy_runs enable row level security;
alter table public.onboarding_sessions enable row level security;
alter table public.documents enable row level security;
alter table public.enabled_modules enable row level security;

do $$
begin
  if not exists (
    select 1 from pg_policies
    where schemaname = 'public' and tablename = 'tenants' and policyname = 'tenants_isolation'
  ) then
    create policy tenants_isolation
      on public.tenants
      for all
      using (id = public.current_tenant_id())
      with check (id = public.current_tenant_id());
  end if;
end $$;

do $$
declare
  tenant_table text;
begin
  foreach tenant_table in array array[
    'profiles',
    'policies',
    'activity_log',
    'policy_gaps',
    'policy_runs',
    'onboarding_sessions',
    'documents',
    'enabled_modules'
  ]
  loop
    if not exists (
      select 1 from pg_policies
      where schemaname = 'public'
        and tablename = tenant_table
        and policyname = tenant_table || '_tenant_isolation'
    ) then
      execute format(
        'create policy %I on public.%I for all using (tenant_id = public.current_tenant_id()) with check (tenant_id = public.current_tenant_id())',
        tenant_table || '_tenant_isolation',
        tenant_table
      );
    end if;
  end loop;
end $$;

commit;
