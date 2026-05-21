-- Trace Agent — batch-intake orchestrator support
--
-- Adds the generation_intake table that holds a populated intake row
-- (the unit of work Trace Agent runs against) and extends activity_log
-- with rationale + step ordering columns so the 16-step trace is
-- queryable from the database, not just the logs.
--
-- RLS pattern matches policies / policy_sections (tenant-scoped, service
-- role bypasses). Applied via Supabase SQL Editor or `supabase db push`.

BEGIN;

-- ── generation_intake ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.generation_intake (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    policy_id uuid,
    deliverable_type text NOT NULL,
    audience text NOT NULL CHECK (audience IN ('ops', 'auditor', 'both')),
    framework_spine text[] NOT NULL,
    maturity_posture text NOT NULL CHECK (maturity_posture IN ('current', 'target', 'both')),
    scope_boundary jsonb NOT NULL,
    business_context jsonb NOT NULL,
    declared_assumptions jsonb,
    created_by uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    approved_at timestamptz
);

CREATE INDEX IF NOT EXISTS idx_generation_intake_tenant
    ON public.generation_intake (tenant_id);
CREATE INDEX IF NOT EXISTS idx_generation_intake_tenant_created_at
    ON public.generation_intake (tenant_id, created_at DESC);

ALTER TABLE public.generation_intake ENABLE ROW LEVEL SECURITY;

-- Tenant isolation: service_role bypasses; authenticated reads/writes
-- are scoped to the caller's tenant. Same shape as the policies table.
DROP POLICY IF EXISTS generation_intake_tenant_select ON public.generation_intake;
CREATE POLICY generation_intake_tenant_select
    ON public.generation_intake
    FOR SELECT
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);

DROP POLICY IF EXISTS generation_intake_tenant_insert ON public.generation_intake;
CREATE POLICY generation_intake_tenant_insert
    ON public.generation_intake
    FOR INSERT
    WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);

DROP POLICY IF EXISTS generation_intake_tenant_update ON public.generation_intake;
CREATE POLICY generation_intake_tenant_update
    ON public.generation_intake
    FOR UPDATE
    USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid)
    WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);

-- ── activity_log extensions ──────────────────────────────────────────────────
ALTER TABLE public.activity_log
    ADD COLUMN IF NOT EXISTS rationale text,
    ADD COLUMN IF NOT EXISTS step_number int,
    ADD COLUMN IF NOT EXISTS step_name text;

COMMENT ON COLUMN public.activity_log.rationale IS
    'Free-text explanation of WHY this row was emitted given the inputs the agent saw. Trace Agent writes one row per step with a populated rationale.';
COMMENT ON COLUMN public.activity_log.step_number IS
    'Ordinal of the step within a single agent run. NULL for events emitted outside a stepped flow.';
COMMENT ON COLUMN public.activity_log.step_name IS
    'Human-readable step identifier (e.g. "load_intake", "outline", "validate_schema").';

CREATE INDEX IF NOT EXISTS idx_activity_log_step_number
    ON public.activity_log (tenant_id, step_number)
    WHERE step_number IS NOT NULL;

COMMIT;
