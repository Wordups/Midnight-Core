-- Midnight Core — give the audit trail room to say what happened.
--
-- activity_log currently stores tenant_id, action, and policy_id. That is enough
-- to prove an AI assistant called the connector, but not enough to say which
-- capability it used — the tool name only ever reached the application log,
-- which evaporates when the instance restarts.
--
-- For a compliance product the difference matters: "an assistant acted on your
-- program" is an incident report, "an assistant read your posture at 22:51" is
-- an audit record.
--
-- Safe to run twice. Additive, nullable, no backfill: existing rows keep a null
-- metadata and stay valid.

alter table activity_log
    add column if not exists metadata jsonb;

comment on column activity_log.metadata is
    'Structured detail about the action — e.g. {"tool": "get_posture", "error": false} for connector calls.';

-- Actions are queried by exact match and by prefix; keep both cheap.
create index if not exists activity_log_tenant_action_idx
    on activity_log (tenant_id, action, created_at desc);
