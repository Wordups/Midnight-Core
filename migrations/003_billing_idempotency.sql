-- Midnight — billing webhook idempotency ledger (C2)
-- Run in the Supabase SQL editor. Idempotent, additive, no data touched.
--
-- Stripe delivers webhook events at-least-once. Plan activation is already
-- idempotent (setting the same plan_type twice is harmless), so this table is
-- a hardening layer that lets the webhook skip a replayed event outright.
-- Service-role only (RLS enabled, no client policies).

create table if not exists public.processed_stripe_events (
  event_id     text primary key,
  event_type   text,
  processed_at timestamptz not null default now()
);

alter table public.processed_stripe_events enable row level security;
