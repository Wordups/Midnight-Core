# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Strategic Posture

[ARCHITECTURE.md](./ARCHITECTURE.md) is a **superseded, historical** self-audit from 2026-05-21 — useful for the reasoning behind old decisions, not for current state. Its wiring-status tables and numbered task list are stale; several were finished, several were replaced by a different approach.

**[docs/BUILD_QUEUE.md](./docs/BUILD_QUEUE.md) is the current source of truth for active work.** It's worked one item at a time by the nightly build agent, delivered as a PR against `master` — never pushed to `master` directly. The owner reorders it to reprioritize.

The earlier "no new features for 3 weeks" freeze (dated from the May audit) has long since lapsed and is no longer in effect. Large, unplanned product decisions (pricing, new integrations, new auth surfaces) are still worth a stop-and-confirm if a session finds itself adding one outside of BUILD_QUEUE.md — not because of a standing freeze, but because those are the owner's calls to make.

## Escape hatch for all sessions

If you hit a real dead end in any task, stopping and asking is a valid successful outcome. Treat the following as equally legitimate completions:

1. Clean success — task complete, tests pass, here's what I did.
2. Blocker surfaced — I hit a design decision or missing piece. Here's the blocker, here are 2-3 options I see, which do you want?
3. Assumption flagged — I implemented this, but had to assume X to keep moving. Here's the assumption and why, want me to revise?

What is NEVER acceptable:

- Silently swallowing errors so tests pass
- Returning hardcoded, mocked, or sample data in place of real computation
- Adding TODO comments and moving on as if shipped
- Marking a task complete when a partial fallback was actually shipped
- Inventing "reasonable inference" logic where the underlying data doesn't exist

If you find yourself reaching for any of the unacceptable patterns, stop and use option 2 or 3 instead. Surfacing a real blocker is more valuable than a hidden one.

One fully-wired task beats three half-wired tasks with silent gotchas.

Known dead ends still live in the current code (re-verified 2026-08-15):

- **`template_engine.py`'s placeholder substitution is per-run, not per-paragraph.** `fill_paragraph()` only replaces a `{{token}}` that lands inside a single `<w:r>` run; Word routinely splits a token across runs (autocorrect, paste, manual edits), and a split token silently fails to substitute — no error, just a literal `{{token}}` left in the output. If you're touching this path and hit a token that won't substitute, that's why — don't paper over it with a narrower regex, surface it.
- **Only the POLICY lane in Create Studio has a real slot spec and live generate/export calls.** The other seven lanes in `create_studio.js` (procedure, standard, process_flow, training, incident_runbook, risk_assessment, audit_package) still gate their buttons behind `workflowToast(IN_DEV_MESSAGE)` — "In Development." Template *packs* now exist on disk for most of these doc types (`backend/templates/packs/`), but that's output examples, not the same thing as a wired Studio lane. Don't assume a pack's existence means the lane is live; check `create_studio.js` for `live` / real `fetch()` calls before claiming a lane works.

(The gap_engine `covered_control_ids` dead end from the original audit is resolved — it's populated in both the generation path (`backend/api/routes.py`, `_identify_covered_controls`) and Bird Eye ingestion (`backend/bird_eye/api.py::_map_controls_at_ingest`) and stored via `update_policy_covered_controls`.)

## Commands

**Setup**
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
cp .env.example .env            # fill in all keys
```

**Run locally** (from repo root)
```bash
uvicorn backend.api.main:app --reload --port 8000
```
Dashboard: `http://localhost:8000/midnight_dashboard.html`

**Tests** (from repo root)
```bash
pytest tests/
pytest tests/test_gap_engine.py          # single file
pytest tests/test_gap_engine.py::test_fn # single test
```

Note: `test_tenant_isolation.py` and `test_document_isolation.py` need a live Supabase instance; the CI workflow (`.github/workflows/tests.yml`) skips them. Most other tests are unit tests that do not require live services.

## Architecture

### Request flow
Every authenticated request goes through `verify_access()` in `backend/api/main.py`, which validates the Supabase JWT cookie (`midnight_session`) and injects `tenant_id`, `user_id`, `plan_type`, etc. into `request.state`. All routers except `assessments_router` require this dependency.

### Module layout

| Package | Responsibility |
|---|---|
| `backend/api/` | HTTP layer — `main.py` (auth + app init), `routes.py` (core pipeline), `dashboard.py`, `smart_scan.py`, `agent_ops.py`, `assessments.py`, `corpus.py` (questionnaire answer engine), `integrations.py` + `mcp_gateway.py` + `api_keys_router.py` + `stripe_router.py` + `pm.py` |
| `backend/core/` | Pure engine — `gap_engine`, `json_parser`, `framework_mapper`, `framework_layer`, `template_engine` + `master_template` + `template_voice` (docx generation), `corpus.py` (retrieval), `smart_scan_engine`, `beta_access`, `public_artifacts`, `ratelimit`, `scheduler` |
| `backend/agents/` | AI agent layer — `base.py` (ABC), specialized agents (`policy_agent`, `cleaner_agent`, `evidence_agent`, `executive_summary_agent`, `framework_mapping_agent`, `signal_manager`, `tenant_manager`), `validators/` |
| `backend/bird_eye/` | Autonomous document review — `orchestrator.py` runs detectors (`detectors.py`); `ingestion.py` + `embeddings.py` handle document indexing; `tenant_guard.py` enforces tenant scoping |
| `backend/integrations/` | Third-party wiring — `jira_client.py` + `jira_config.py` + `jira_sync.py` (auto-push/sync-back), `api_keys.py` (per-tenant `mk_` keys for the MCP gateway) |
| `backend/renderers/` | Output — `docx_renderer.py`, `pdf_renderer.py` |
| `backend/storage/` | Persistence — `supabase_client.py` (two clients: anon + service-role admin), `file_store.py` (all DB helpers) |
| `backend/templates/` | Template packs — each pack has `manifest.json`, `schema.json`, `layout.json`, `mapping.json` |
| `mcp_server/` | Standalone local MCP server (own venv — its SDK deps conflict with the pinned FastAPI). Separate from `backend/api/mcp_gateway.py`, which is the hosted per-tenant remote gateway mounted in the main app. |
| `frameworks/` | JSON control libraries — hipaa, nist, pci, soc2 |
| `knowledge/` | Sector knowledge base — used by framework mapping |
| `frontend/` | Static files served by FastAPI at `/` |
| `config.py` | `pydantic-settings` `Settings` class — loaded at startup; lives at repo root, not inside `backend/` |

### Multi-tenancy
Every user belongs to a `tenant` (row in `tenants` table) via a `profile` row. All data queries must be scoped to `tenant_id`. The `bird_eye/tenant_guard.py` enforces this at the Bird Eye layer.

### AI / model output
All Claude API responses go through `backend/core/json_parser.py` (`parse_model_json`) before use. This is the two-pass safe parser that handles smart quotes, trailing commas, Python literals, and bare keys. Use it at every model-output callsite.

### Gap engine
Deterministic — no AI. `backend/core/gap_engine.py` computes required controls minus covered controls. Framework control definitions live in `frameworks/*.json`.

### Agents base class
All agents inherit from `backend/agents/base.py::BaseAgent`. Override `_run()` for logic; `run()` wraps it with `validate_input` / `validate_output`.

## Repo rules (from README)
- One responsibility per module — no giant service files
- Template logic belongs in template packs, not in the core engine
- Every generated output is a "draft" / "prepared" — never claim "compliant"
- No client data in this repo
