-- Corpus + Answer Engine: questionnaire runs answered from the compliance corpus.
-- See docs/superpowers/specs/2026-08-12-corpus-answer-engine-design.md.

create table if not exists public.corpus_runs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references public.tenants(id),
  use_case text not null default 'questionnaire',
  question_count integer not null default 0,
  satisfied_count integer not null default 0,
  partial_count integer not null default 0,
  not_satisfied_count integer not null default 0,
  insufficient_count integer not null default 0,
  not_applicable_count integer not null default 0,
  model text,
  input_tokens integer not null default 0,
  output_tokens integer not null default 0,
  created_at timestamptz default now()
);

create index if not exists corpus_runs_tenant_id_idx on public.corpus_runs (tenant_id);
create index if not exists corpus_runs_created_at_idx on public.corpus_runs (created_at desc);

create table if not exists public.corpus_answers (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references public.corpus_runs(id) on delete cascade,
  tenant_id uuid references public.tenants(id),
  position integer not null default 0,
  question text not null,
  status text not null default 'insufficient_evidence',
  answer_text text,
  citations jsonb default '[]'::jsonb,
  control_ids text[] default '{}',
  confidence text,
  followup_question text,
  provenance text not null default 'ai_assisted',
  created_at timestamptz default now()
);

create index if not exists corpus_answers_run_id_idx on public.corpus_answers (run_id);
create index if not exists corpus_answers_tenant_id_idx on public.corpus_answers (tenant_id);

alter table public.corpus_runs enable row level security;
alter table public.corpus_answers enable row level security;

do $$
declare
  tenant_table text;
begin
  foreach tenant_table in array array[
    'corpus_runs',
    'corpus_answers'
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
