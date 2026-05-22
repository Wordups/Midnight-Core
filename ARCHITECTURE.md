# ARCHITECTURE.md — Midnight Core Vertical Scope Audit

_Produced: 2026-05-21. Authoritative reference for what is wired, what is dangling, and what to wire next._

---

## 1. Vertical Layer Map

### Layer 1 — Frontend (frontend/)

| File | Purpose | Backend wired? |
|---|---|---|
| `midnight_dashboard.html` (4,854 lines) | SPA shell, 8 sidebar views | Yes — calls 15+ endpoints |
| `create_studio.html` / `create_studio.js` | 9 document-type lanes | **Only POLICY lane wired** |
| `bird_talk.html` / `bird_talk.js` | Bird Eye UI | Yes — /bird-eye/* |
| `smart_scan.js` | Smart Scan preflight | Yes — /api/smart-scan/preflight |
| `migrate_studio.html` | Doc migration UI | Yes — /pipeline/migrate/* |

**Studio lane wiring status:**

| Lane (`?type=`) | Generate Preview button | Generate Export button |
|---|---|---|
| `policy` | `POST /pipeline/create/preview` | `POST /pipeline/create/generate` |
| `procedure` | `workflowToast()` — no fetch | `workflowToast()` — no fetch |
| `standard` | `workflowToast()` — no fetch | `workflowToast()` — no fetch |
| `process_flow` | `workflowToast()` — no fetch | `workflowToast()` — no fetch |
| `training` | `workflowToast()` — no fetch | `workflowToast()` — no fetch |
| `incident_runbook` | `workflowToast()` — no fetch | `workflowToast()` — no fetch |
| `risk_assessment` | `workflowToast()` — no fetch | `workflowToast()` — no fetch |
| `audit_package` | `workflowToast()` — no fetch | `workflowToast()` — no fetch |
| `ai_governance` | `workflowToast()` — no fetch | `workflowToast()` — no fetch |

8 of 9 studio lanes call `workflowToast()` and never reach the backend.

---

### Layer 2 — API Routes (backend/api/)

| File | Router prefix | Key routes | Notes |
|---|---|---|---|
| `main.py` | — | App init, `verify_access()` auth | All routers except assessments require JWT cookie |
| `routes.py` | `/pipeline` | preview, generate, analyze, migrate, grc-summary, birdsong | Core pipeline; 2,793 lines |
| `dashboard.py` | `/dashboard` | summary, documents, activity, gaps | `get_gaps()` returns empty lists |
| `smart_scan.py` | `/api/smart-scan` | preflight | |
| `agent_ops.py` | `/agents` | Various agent ops | |
| `assessments.py` | (no auth) | Assessments | No `verify_access()` dependency |
| `bird_eye/routes.py` | `/bird-eye` | ingest, run, findings | |

**Dead / stub routes:**
- `GET /dashboard/gaps` → returns `GapsResponse()` with empty lists; gap_engine never called
- `POST /pipeline/analyze` → calls `_go_framework_coverage()` which POSTs to `GO_SERVICE_URL/analyze`; Go service is not in this repo and not in the Dockerfile

**Policy generation path (the one wired path):**
```
POST /pipeline/create/preview
  → _generate_policy_data()
    → 1 metadata Claude call (_call_model_json_object)
    → 10 per-slot Claude calls (POLICY_SLOT_SPECS)
  → returns AgentPolicyPayload JSON

POST /pipeline/create/generate
  → _build_docx()
    → python-docx (direct, no agent)
  → returns .docx bytes
```

No agent class is used. `CleanerAgent` is imported but only used as a post-processor inside `routes.py`. `PolicyAgent` is never called by any route.

---

### Layer 3 — Agent / Engine Layer (backend/agents/, backend/core/)

#### Agents

| Agent | File | Called by | Status |
|---|---|---|---|
| `BaseAgent` | `base.py` | Inherited by all agents | Live |
| `CleanerAgent` | `cleaner_agent.py` | `routes.py` (direct import) | Live — used in pipeline |
| `PolicyAgent` | `policy_agent.py` | Nothing | **Dangling** — no route calls it |
| `TraceAgent` | `trace_agent.py` | Nothing (docstring: "not wired to any HTTP route in this PR") | **Dangling** — no route calls it |
| `FrameworkMappingAgent` | `framework_mapping_agent.py` | `agent_ops.py` | Wired |
| `EvidenceAgent` | `evidence_agent.py` | `agent_ops.py` | Wired |
| `ExecutiveSummaryAgent` | `executive_summary_agent.py` | `agent_ops.py` | Wired |
| `SignalAgent` | `signal_agent.py` | `agent_ops.py` | Wired |
| `MigrationAgent` | `migration_agent.py` | `routes.py` | Wired |
| `BirdSongAgent` | `birdsong_agent.py` | `routes.py` | Wired |
| `SmartScanAgent` | `smart_scan.py` | `smart_scan.py` API file | Wired |

#### Core modules

| Module | File | Status |
|---|---|---|
| `gap_engine` | `gap_engine.py` | **Dangling** — `compute_gaps()` implemented, only called in `if __name__ == "__main__"` |
| `template_engine` | `template_engine.py` | **Stub** — 3-line TODO, never called |
| `extractor` | `extractor.py` | Used by migration pipeline |
| `transformer` | `transformer.py` | Used by migration pipeline |
| `classifier` | `classifier.py` | Used in pipeline |
| `framework_mapper` | `framework_mapper.py` | Used by FrameworkMappingAgent |
| `json_parser` | `json_parser.py` | Used everywhere (Claude output parsing) |
| `schema` | `schema.py` | Used |
| `validator` | `validator.py` | Used |

#### TraceAgent 16-step contract (step order must not change)

1. `load_intake` — reads `generation_intake` table
2. `plan` — LLM call to derive generation plan
3. `derive_questions` — derive clarifying questions
4. `load_answers` — check for existing answers
5. `freeze_assumptions` — lock declared_assumptions
6. `load_skill` — load domain skill/knowledge
7. `outline` — load YAML outline template or LLM fallback
8. `build_script` — LLM call → JSON spec for build_docx.js
9. `generate` — subprocess `node build_docx.js`
10. `validate_schema` — validate against AgentPolicyPayload
11. `spot_check` — LLM quality spot-check
12. `repair` — repair if spot-check fails
13. `rerun` — rerun generate after repair (up to MAX_REPAIR_ATTEMPTS=3)
14. `write_trace` — write process_trace.md
15. `verify_artifacts` — check .docx + .md exist
16. `return` — return GenerationResult

---

### Layer 4 — Data / Storage (backend/storage/, Supabase)

#### Supabase tables and their consumers

| Table | Written by | Read by | Notes |
|---|---|---|---|
| `policies` | `file_store.save_policy_draft` | `file_store`, dashboard routes | Core policy store |
| `policy_sections` | `file_store.save_policy_draft` | Bird Eye detectors, embeddings | Voyage AI 1024-dim embeddings stored here |
| `documents` | `file_store.save_generated_document` | dashboard routes | Generated .docx references |
| `activity_log` | `file_store.create_signal_activity_event`, TraceAgent | dashboard routes | TraceAgent writes one row per step |
| `tenants` | `file_store.create_tenant` | `verify_access()`, all routes | Multi-tenancy root |
| `profiles` | `file_store.update_profile_membership` | `verify_access()` | Links user → tenant |
| `enabled_modules` | Admin only | `verify_access()` | Feature flags per tenant |
| `onboarding_sessions` | `file_store` | assessments | |
| `policy_runs` (TABLE_RUNS) | routes.py pipeline | agent_ops routes | Generation run tracking |
| `policy_gaps` (TABLE_FINDINGS) | Bird Eye detectors | dashboard gaps route | Gap findings; dashboard returns empty list anyway |
| `generation_intake` | **Nothing in this repo** | TraceAgent `_select_intake()` | **Critical gap** — TraceAgent reads this table but nothing writes it |

---

### Layer 5 — Templates / Frameworks / Knowledge

#### midnight-template-build (external, `/c/Users/bword/Documents/midnight-template-build/`)

- 36 templates: 9 categories × 4 variants (formal, modern, detailed, executive)
- Categories: policy, procedure, standard, process_flow, training, incident_runbook, risk_assessment, audit_package, ai_governance
- Each template: `.docx` + `.md` source + `.png` preview
- Uses `{{MUSTACHE_STYLE}}` placeholders — 32 unique tokens across all templates

**Universal core tokens (all 36 templates):**
`{{ORGANIZATION_NAME}}`, `{{DOCUMENT_TITLE}}`, `{{EFFECTIVE_DATE}}`, `{{VERSION}}`, `{{APPROVER_NAME}}`, `{{APPROVER_TITLE}}`, `{{POLICY_OWNER}}`, `{{POLICY_OWNER_TITLE}}`, `{{NEXT_REVIEW_DATE}}`, `{{CLASSIFICATION}}`

**Doc-type-specific extras:** `{{SECURITY_CONTACT}}`, `{{AUTHOR_NAME}}`, `{{RISK_OWNER}}`, `{{TRAINING_COORDINATOR}}`, `{{INCIDENT_COMMANDER}}`, `{{AUDIT_SCOPE}}`, `{{AI_SYSTEM_NAME}}`, etc.

**No substitution code exists anywhere in the repo.** `template_engine.py` is a 3-line stub.

#### backend/templates/ (4 skeleton packs)

- `generic_policy/`, `generic_sop/`, `generic_playbook/`, `generic_plan/`
- Each has `manifest.json`, `schema.json`, `layout.json`, `mapping.json`
- `templates/registry.py` maps doc types → pack paths; called by nothing at runtime
- These are skeleton metadata packs, not `.docx` files — structurally incompatible with midnight-template-build format

#### TraceAgent outline templates (2 YAML files)

- `backend/agents/templates/outlines/hipaa_policy_HIPAA.yaml` — 11 sections
- `backend/agents/templates/outlines/soc_playbook_NIST_800_61.yaml` — 12 sections
- All other `(deliverable_type, framework)` combinations → LLM fallback

#### frameworks/ (control libraries)

- `hipaa.json`, `nist.json`, `pci.json`, `soc2.json` (+ iso27001, hitrust)
- Each has ~6 controls; used as context in LLM prompts via `framework_mapper.py`
- **Structural mismatch:** gap_engine.py has its own hardcoded CONTROL_REGISTRY with 24 controls (HIPAA×8, PCI×5, NIST×4, HITRUST×3, ISO×3, SOC2×3) — never reads these JSON files

#### knowledge/ (entirely unused at runtime)

- `template_definitions.json`, `framework_crosswalk.json`, `sectors/` (sector-specific knowledge)
- Zero runtime imports anywhere in the repo

---

### Layer 6 — Infrastructure / Ops

| File | Purpose | Issues |
|---|---|---|
| `config.py` | Pydantic-settings Settings; loaded at startup | **Voyage AI key missing** — `bird_eye/embeddings.py` requires it but it's not in Settings |
| `Dockerfile` | Container build | Go service (`GO_SERVICE_URL`) not included; will cause runtime 500s on `/pipeline/analyze` |
| `.env.example` | Key template | Voyage AI key not listed |
| `requirements.txt` | Python deps | `voyageai` listed but key not in config |
| `backend/agents/generators/package.json` | Node deps for `build_docx.js` | Must `npm install` before TraceAgent runs |

---

## 2. Dangling Components (19)

Components that exist in the codebase but are not connected to any live call path:

1. **`PolicyAgent`** — fully implemented agent, zero callers
2. **`TraceAgent`** — 16-step orchestrator, zero HTTP routes
3. **`gap_engine.compute_gaps()`** — deterministic engine, only in `__main__` self-test
4. **`template_engine.py`** — 3-line TODO stub
5. **`backend/templates/registry.py`** — maps doc types to packs; nothing calls it
6. **`backend/templates/generic_policy/`** — skeleton pack, no consumer
7. **`backend/templates/generic_sop/`** — skeleton pack, no consumer
8. **`backend/templates/generic_playbook/`** — skeleton pack, no consumer
9. **`backend/templates/generic_plan/`** — skeleton pack, no consumer
10. **36 midnight-template-build templates** — complete .docx library, no substitution engine
11. **`knowledge/template_definitions.json`** — zero imports
12. **`knowledge/framework_crosswalk.json`** — zero imports
13. **`knowledge/sectors/`** — zero imports
14. **`GET /dashboard/gaps`** — route exists but returns empty list; gap_engine never called
15. **`POST /pipeline/analyze`** — route exists; calls Go service that is not in repo
16. **8 of 9 studio lanes** — procedure, standard, process_flow, training, incident_runbook, risk_assessment, audit_package, ai_governance — all show toast, no backend calls
17. **`generation_intake` table** — consumed by TraceAgent; nothing in repo writes to it
18. **`frameworks/*.json` control defs** — used only for prompt context; gap_engine has its own registry
19. **`backend/agents/templates/outlines/` for non-HIPAA/non-SOC types** — LLM fallback for all other combinations; no additional YAML outlines exist

---

## 3. Gaps Between Layers

1. **Frontend → POLICY lane only**: 8 of 9 studio lanes never reach the backend. Users selecting Procedure, Standard, Training, etc. see a "staged" toast and get nothing.

2. **API → gap_engine**: `GET /dashboard/gaps` returns `GapsResponse()` with empty lists. `gap_engine.compute_gaps()` is fully implemented but the route never calls it.

3. **API → TraceAgent**: No HTTP route calls `TraceAgent.run()`. The `generation_intake` table has no writer anywhere in the repo; TraceAgent step 1 would fail with a Postgrest 404 for any intake_id.

4. **template_engine → midnight-template-build**: `template_engine.py` is a 3-line stub. 32 placeholder tokens across 36 templates have zero substitution logic.

5. **backend/templates packs → any consumer**: `templates/registry.py` maps doc types to skeleton packs; nothing imports or calls `get_template_path()`.

6. **knowledge/ → any prompt**: `knowledge/template_definitions.json`, `framework_crosswalk.json`, and all sector files are never loaded at runtime.

7. **Go microservice → Dockerfile**: `_go_framework_coverage()` in routes.py calls `GO_SERVICE_URL/analyze`. The Go service is not in this repo, not built by the Dockerfile, and not injected via docker-compose. Any call to `/pipeline/analyze` will 500 in production.

8. **gap_engine CONTROL_REGISTRY → frameworks/*.json**: Two independent control registries exist and are never synchronized. gap_engine hardcodes 24 controls; frameworks/ JSON files define ~6 controls each used only for prompt context.

9. **Voyage AI key → config.py**: `bird_eye/embeddings.py` requires a Voyage AI API key. It is not declared in `config.py` Settings, not in `.env.example`. Bird Eye will fail at runtime if the key is absent.

10. **midnight-template-build → backend/templates packs**: The external 36-template library uses `{{MUSTACHE}}` tokens in `.docx` files. The backend skeleton packs use `manifest.json`/`schema.json`/`layout.json` metadata. These are structurally incompatible; no bridge code exists.

---

## 4. Wiring Tasks — Ranked by Impact

### #1 — Wire gap_engine → /dashboard/gaps

**Impact:** Turns a dead route into a working feature; unlocks the Gap Analysis sidebar view.  
**Scope:** 1 focused session.  
**What to do:**
- In `dashboard.py::get_gaps()`, import `compute_gaps` from `gap_engine`
- Pull tenant's covered controls from `policy_sections` (or a new `covered_controls` table)
- Call `compute_gaps(document_name, doc_type, covered_control_ids, frameworks)`
- Return populated `GapsResponse`

**Blocker:** Need a source of `covered_control_ids` per tenant. Simplest: derive from policy_sections tags; more correct: add a `covered_controls` junction table.

---

### #2 — Wire 8 studio lanes to pipeline

**Impact:** Transforms 8 dead buttons into real generation flows; the product's core value prop.  
**Scope:** 2–3 days.  
**What to do:**
- In `create_studio.js`, replace `workflowToast()` with real fetch calls for each lane
- In `routes.py`, extend `_generate_policy_data()` or create `_generate_document_data()` with per-lane `SLOT_SPECS` (procedure slots, standard slots, etc.)
- Each lane maps to a POLICY_SLOT_SPECS equivalent for its doc type

**Blocker:** Slot specs for 8 doc types need to be defined. They don't exist yet — this is the bulk of the work.

---

### #3 — Implement template_engine + wire midnight-template-build templates

**Impact:** Generated documents use the 36 professionally designed Word templates instead of bare python-docx output. Dramatically improves output quality.  
**Scope:** Half day (template_engine) + 1 day (wiring into pipeline).  
**What to do:**
- Implement `template_engine.py::render(template_path, tokens: dict) -> bytes`
  - Load .docx template from midnight-template-build using `python-docx`
  - Replace `{{TOKEN}}` placeholders in paragraphs and table cells
  - Return bytes
- In `routes.py::_build_docx()`, call `template_engine.render()` with the token dict assembled from `AgentPolicyPayload`
- Token mapping: `ORGANIZATION_NAME` ← `payload.organization`, `DOCUMENT_TITLE` ← `payload.title`, etc.

**Blocker:** midnight-template-build lives outside the repo at `/c/Users/bword/Documents/midnight-template-build/`. Decision needed: copy into repo, or reference by absolute path + document the dependency.

---

### #4 — HTTP route + intake writer for TraceAgent

**Impact:** Makes TraceAgent callable from the product; enables the audit-ready batch generation flow.  
**Scope:** Half day (backend) + 1 day (UI).  
**What to do:**
- Add `POST /pipeline/trace/intake` route that writes a `generation_intake` row (the table TraceAgent reads in step 1)
- Add `POST /pipeline/trace/run` route that calls `TraceAgent(supabase_admin, anthropic_client).run(intake_id)`
- Add a UI entry point — simplest: a new studio lane (`?type=trace`) or a dedicated page
- Wire up polling / SSE for the 16-step progress (activity_log rows written per step)

**Blocker:** `generation_intake` table schema must match `TraceAgentIntake` Pydantic model exactly. Review all required fields (deliverable_type, framework_spine, scope_boundary, business_context, declared_assumptions, etc.) before writing the intake form.

---

### #5 — Bird Eye document upload UI

**Impact:** Bird Eye's 5 detectors are fully implemented but the only way to ingest documents is through `POST /bird-eye/ingest`, which has no frontend form.  
**Scope:** 1 focused session.  
**What to do:**
- Add a file upload form in `bird_talk.html` (or a new Bird Eye upload view in the dashboard)
- Call `POST /bird-eye/ingest` with the file and tenant context
- Surface ingestion status and trigger a detector run on success

**Blocker:** None — backend is complete.

---

### #6 — Load knowledge/ sector definitions into prompts

**Impact:** LLM generation calls gain sector-specific context (healthcare, finance, etc.) making output more accurate without any architectural change.  
**Scope:** 1 focused session.  
**What to do:**
- In `routes.py::_generate_policy_data()`, load `knowledge/sectors/{sector}.json` based on `tenant.industry` (or `business_context.sector`)
- Inject the sector profile as a system-prompt prefix
- Same injection point for `framework_crosswalk.json` to improve framework mapping quality

**Blocker:** Tenants need a `sector` / `industry` field in their profile. Check whether `profiles` table has this column.

---

### #7 — Sync gap_engine CONTROL_REGISTRY with frameworks/*.json

**Impact:** Eliminates two diverging control registries. Controls added to frameworks/*.json will automatically appear in gap analysis.  
**Scope:** Half day.  
**What to do:**
- Refactor `gap_engine.py` to load control definitions from `frameworks/*.json` at startup instead of using the hardcoded `CONTROL_REGISTRY`
- Add any controls present in CONTROL_REGISTRY but absent from frameworks/*.json into the JSON files
- Run existing gap_engine tests to verify equivalence

**Blocker:** None — pure refactor with no external dependencies.

---

### #8 — Expose /pipeline/analyze + Smart Scan from dashboard

**Impact:** Unlocks the framework coverage analysis feature and Smart Scan for all tenants.  
**Scope:** 1 focused session each.  
**What to do (analyze):**
- Either implement a Python-only fallback in `_go_framework_coverage()` that doesn't depend on the Go service, OR document and add the Go service to the Dockerfile
- Surface the analyze result in the dashboard (a "Framework Coverage" card)

**What to do (Smart Scan):**
- Add a Smart Scan trigger button to the dashboard (currently only accessible via direct API call)
- The backend route already exists at `POST /api/smart-scan/preflight`

**Blocker (analyze):** Go service architecture decision — implement in Python or add to infra.

---

## 5. Reading this document

- **"Dangling"** means the code exists but no live call path reaches it.
- **"Gap"** means a connection that should exist between two layers but doesn't.
- **"Wiring task"** means connecting existing code that already works in isolation.
- None of the 8 wiring tasks require new product features — they are all plumbing.

_Last updated: 2026-05-21._
