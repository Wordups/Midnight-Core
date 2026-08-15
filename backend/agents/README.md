# Agents

Each module under `backend/agents/` exposes a single agent class. All inherit
`BaseAgent` (in `base.py`): override `_run(data)` for logic; `run()` wraps it
with `validate_input` / `validate_output`. Every agent declares `name`,
`role`, `allowed_actions`, and `forbidden_actions` as class attributes — the
forbidden list is an explicit, enforced boundary (e.g. no agent may claim
compliance certification or bypass tenant isolation).

(The batch-orchestrator agent that used to live here, Trace Agent, was
deleted 2026-08-13 as dead code — no route, no caller. Document generation
now runs through the Studio path: `create_generate()` in `backend/api/routes.py`
calling `backend/core/master_template.py` + `template_voice.py` +
`template_engine.py`.)

## Current agents

| Agent | Role |
|---|---|
| `policy_agent.py::PolicyAgent` | Handles policy creation and policy improvement workflows |
| `cleaner_agent.py::CleanerAgent` | Quality control and governance enforcement — sanitizes/validates LLM JSON output before it's trusted |
| `evidence_agent.py::EvidenceAgent` | Tracks audit readiness and evidence needs |
| `executive_summary_agent.py::ExecutiveSummaryAgent` | Creates leadership-facing GRC summaries |
| `framework_mapping_agent.py::FrameworkMappingAgent` | Maps content to framework controls (HIPAA, NIST CSF, PCI DSS, SOC 2, ISO 27001, HITRUST, HITRUST Domains) |
| `signal_manager.py::SignalManagerAgent` | Collects and classifies user/system events into structured signals |
| `tenant_manager.py::TenantManagerAgent` | Enforces tenant-scoped access; rejects cross-tenant payloads |

`schemas.py` holds the shared Pydantic I/O models; `validators/schema_validator.py`
holds `validate_schema_bytes`, the live export integrity check.
