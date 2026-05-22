-- Sprint 1 / Task 1: Add coverage tracking column to policies.
-- Run in Supabase SQL Editor before deploying the gap-engine wiring changes.
-- Safe to re-run (IF NOT EXISTS guard).

ALTER TABLE policies
  ADD COLUMN IF NOT EXISTS covered_control_ids JSONB DEFAULT '[]'::jsonb;
