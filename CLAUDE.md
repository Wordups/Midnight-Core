# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

Note: `test_trace_agent.py` makes real Anthropic API calls and takes 60–120s. Most other tests are unit tests that do not require live services.

## Architecture

### Request flow
Every authenticated request goes through `verify_access()` in `backend/api/main.py`, which validates the Supabase JWT cookie (`midnight_session`) and injects `tenant_id`, `user_id`, `plan_type`, etc. into `request.state`. All routers except `assessments_router` require this dependency.

### Module layout

| Package | Responsibility |
|---|---|
| `backend/api/` | HTTP layer — `main.py` (auth + app init), `routes.py` (core pipeline), `dashboard.py`, `smart_scan.py`, `agent_ops.py`, `assessments.py` |
| `backend/core/` | Pure engine — `extractor`, `transformer`, `classifier`, `framework_mapper`, `gap_engine`, `json_parser`, `schema`, `validator`, `template_engine` |
| `backend/agents/` | AI agent layer — `base.py` (ABC), specialized agents, `trace_agent.py` (16-step batch orchestrator), `validators/`, `generators/` |
| `backend/bird_eye/` | Autonomous document review — `orchestrator.py` runs 5 detectors (conflicts, duplicates, gaps, orphans, stale governance); `ingestion.py` + `embeddings.py` handle document indexing |
| `backend/renderers/` | Output — `docx_renderer.py`, `pdf_renderer.py` |
| `backend/storage/` | Persistence — `supabase_client.py` (two clients: anon + service-role admin), `file_store.py` (all DB helpers) |
| `backend/templates/` | Template packs — each pack has `manifest.json`, `schema.json`, `layout.json`, `mapping.json` |
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

### Trace Agent
`backend/agents/trace_agent.py` is a fixed 16-step autonomous batch orchestrator. The step order is a contract — do not reorder. Each step appends an `activity_log` row explaining the WHY. Produces a `.docx` + `process_trace.md`.

### Agents base class
All agents inherit from `backend/agents/base.py::BaseAgent`. Override `_run()` for logic; `run()` wraps it with `validate_input` / `validate_output`.

## Repo rules (from README)
- One responsibility per module — no giant service files
- Template logic belongs in template packs, not in the core engine
- Every generated output is a "draft" / "prepared" — never claim "compliant"
- No client data in this repo
