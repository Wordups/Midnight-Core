-- AUDIT TRAIL: migration drift incident 2026-05-23
-- 20260505_phase_14_branded_interactive.sql already adds these columns.
-- This file was written before that migration was discovered, making it a
-- duplicate. Retained as an explicit record of the drift; all four ALTER
-- statements are idempotent (IF NOT EXISTS) and safe to re-run.
ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS brand_logo_url TEXT,
  ADD COLUMN IF NOT EXISTS brand_primary_color TEXT,
  ADD COLUMN IF NOT EXISTS brand_secondary_color TEXT,
  ADD COLUMN IF NOT EXISTS brand_footer_text TEXT;
