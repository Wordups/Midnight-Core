# Phase 1 Wiring List — 2026-05-23

**70 sessions estimated. 17.5 weeks at 4/wk. Demo-ready ~2026-06-14. Launch-ready ~2026-09-27 to 2026-10-25. On track for STRATEGY §XVI Q4 2026 target.**

Produced from a read-only audit of the codebase at HEAD (ceb3066) against
STRATEGY.md §IX and §XVI, LAUNCH_READY.md, MULTI_TENANT_SPEC.md §6,
ARCHITECTURE.md (2026-05-21), and VERTICAL_AUDIT_2026-05-23.md.

**Corrections to the vertical audit:** Several audit claims are now stale.
`/pipeline/analyze` uses a direct Claude call as the primary path; the Go
service is an optional enhancement silently caught on failure — this route
is functional without it. `VOYAGE_API_KEY` is present in `config.py:26`
and `.env.example:14`, not missing as the audit claimed. `GET /dashboard/gaps`
does call `run_program_gap_analysis()` — but only returns data for policies
with non-empty `covered_control_ids`, which only the AI generation path
(`POST /pipeline/create/generate`) populates. Uploaded documents have
`covered_control_ids = []` and are excluded from gap analysis entirely.
These corrections change the wiring status of ARCH tasks #1 and #8.

---

## Loose Wiring (right now)

### BLOCKS — Prevents any non-TKO self-onboarding

These six filter lines make Bird Eye produce zero findings for any non-TKO
tenant. Until they're removed, the free tier is worthless and the Logic
and Wedge stages of the demo break.

| # | file:line | What it is | What it's missing | Smallest action | Maps to |
|---|---|---|---|---|---|
| B1 | `detectors.py:130` | `detect_duplicates` fetches docs | Filters by `policy_number like TKO-*`; excludes every non-TKO doc | Remove the filter; `tenant_id` scoping already isolates the tenant | MTS §6 BLOCK |
| B2 | `detectors.py:252` | `detect_conflicts` fetches docs | Same filter as B1 | Same fix | MTS §6 BLOCK |
| B3 | `detectors.py:415` | `detect_stale_governance` fetches docs | Same filter | Same fix | MTS §6 BLOCK |
| B4 | `detectors.py:520` | `detect_framework_gaps` fetches docs | Same filter | Same fix | MTS §6 BLOCK |
| B5 | `detectors.py:621` | `detect_orphans` fetches docs | Same filter | Same fix | MTS §6 BLOCK |
| B6 | `orchestrator.py:61` | Counts `documents_reviewed` | Same filter; count is always 0 for non-TKO tenants | Remove filter | MTS §6 BLOCK |
| B7 | `detectors.py:567` | AUP framework-gap check | Special-cases `number == "TKO-POL-004"`; every other tenant's AUP is missed unless it has "acceptable use" in the title | Remove the hardcode; `"acceptable use" in title` already covers it generically | MTS §6 BLOCK |
| B8 | `detectors.py:589–612` | `ORPHAN_CUES` table | Uses `TKO-POL-003`, `TKO-POL-005`, `TKO-POL-006` policy numbers; no non-TKO doc can trigger an orphan finding | Rewrite as content-based matching on document type + keywords per MTS §6 design | MTS §6 BLOCK |
| B9 | `ingestion.py:359` | Doc row insert | `"organization": "Takeoff LLC"` hardcoded; every non-TKO tenant's doc shows wrong org name | Fetch `tenant.name` from tenants table and use it here | MTS §6 BLOCK, LAUNCH_READY #2 |
| B10 | `metadata_llm.py:72` | LLM extraction prompt | Example uses `TKO-POL-002`; minor anchoring risk toward TKO naming | Replace with `POL-001` | MTS §6 COSMETIC |
| B11 | `main.py:837–839` | `/onboarding/plan` route | Is a 307 redirect back to `/login.html?mode=signup`; new users loop back to signup | Build 3-question wizard; write to `onboarding_sessions`; redirect to dashboard | MTS §6 BLOCK, LAUNCH_READY #3 |
| B12 | `main.py:65` / `verify_access()` | Trial seat cap | `TRIAL_MAX_USERS = 1`; a B2B buyer who tries to add a teammate hits a 403 before seeing value | Raise trial cap to 3 (one-line change) as an interim fix; wire a paywall prompt at invite time when the invite flow is built (LAUNCH_READY #11) | MTS §6 BLOCK |

---

### Not wired — Component exists, no live call path reaches it

| # | file:line | What it is | What it's missing | Smallest action | Maps to |
|---|---|---|---|---|---|
| W1 | `agents/trace_agent.py` | 16-step batch policy orchestrator | No HTTP route; `generation_intake` table has no writer anywhere in the repo; step 1 would fail immediately for any intake_id | Add `POST /pipeline/trace/intake` (writes intake row) + `POST /pipeline/trace/run` (calls `TraceAgent.run(intake_id)`) | ARCH task #4, uncatalogued in LAUNCH_READY |
| W2 | `core/template_engine.py` | Template substitution engine | 3-line TODO stub; no implementation; 36 professional .docx templates in `midnight-template-build/` have `{{TOKEN}}` placeholders with no substitution code | Implement `render(template_path, tokens) → bytes` using python-docx; replace `{{TOKEN}}` in paragraphs and table cells | ARCH task #3, uncatalogued in LAUNCH_READY |
| W3 | `create_studio.js:432,487` | 8 of 9 Create Studio lanes (SOP, STANDARD, PROCESS_FLOW, TRAINING_MODULE, INCIDENT_RUNBOOK, RISK_ASSESSMENT, AUDIT_PACKAGE, AI_GOVERNANCE) | `runPolicyPreview()` and `runPolicyGenerate()` both check `if (workflowState.lane !== 'POLICY')` and show toast; no backend call for any non-Policy lane | Define slot specs per doc type; extend `_generate_policy_data()` or create `_generate_document_data()`; wire fetch calls in JS per lane | ARCH task #2, uncatalogued in LAUNCH_READY |
| W4 | `agents/policy_agent.py` | PolicyAgent class | Fully implemented; `agent_ops.py` references `"policy_agent"` only as an activity-log label, not as a call to the class; routes.py uses direct LLM calls instead | Either wire PolicyAgent into the generation path or acknowledge it as redundant and remove | Uncatalogued |
| W5 | `knowledge/` (entire directory) | Sector knowledge base + framework crosswalk | Zero runtime imports; `template_definitions.json`, `framework_crosswalk.json`, all sector files are never loaded | In `routes.py::_generate_policy_data()`, load sector JSON from `knowledge/sectors/{sector}.json` and inject as system-prompt prefix | ARCH task #6 |
| W6 | `core/gap_engine.py:96` | `CONTROL_REGISTRY` | 24 hardcoded controls; gap_engine never reads `frameworks/*.json` (which have their own control definitions); two independent registries diverge silently | Refactor gap_engine to load from `frameworks/*.json` at startup instead of hardcoded list | ARCH task #7, uncatalogued in LAUNCH_READY |
| W7 | `agents/evidence_agent.py` + `agents/executive_summary_agent.py` | Two Output-stage agents fully implemented | No UI trigger reaches either; both stay silent while the other five agents fire | Wire `ExecutiveSummaryAgent` into Z4 (GRC Card distribution) and `EvidenceAgent` into a future Audit Package export action | Uncatalogued in LAUNCH_READY |

---

### Returns empty or wrong — Route exists, data path is broken

| # | file:line | What it is | What it's missing | Smallest action | Maps to |
|---|---|---|---|---|---|
| M1 | `file_store.py:845` | `list_policies_for_gap_analysis()` | Filters `covered_control_ids neq []`; `POST /pipeline/create/generate` populates this field, but `POST /bird-eye/ingest` does not; any tenant who uploads existing docs gets an empty gap analysis | After Bird Eye ingest, run `FrameworkMappingAgent` and call `update_policy_covered_controls()` with the result, or remove the filter and treat uploaded docs as entirely uncovered (simpler, less accurate) | ARCH task #1 (partially done), LAUNCH_READY #14 (GRC Card coverage %) |
| M2 | `pdf_renderer.py:11–60` | `build_grc_summary_pdf()` | Produces a document-list PDF (artifact name, type, status, timestamp); no gap coverage %, no Bird Eye findings count, no pending task count; this is a receipt, not a GRC Card | No fix until GRC Card UI (Z3) is built; this function will be replaced, not extended | LAUNCH_READY #14, STRATEGY §XII |
| M3 | `dashboard.py:227–241` | `GET /dashboard/gaps` | Calls gap engine correctly but returns empty for tenants with only uploaded docs (M1); returns 0 gaps for fresh tenants | Depends on M1 fix | LAUNCH_READY #14 |

---

### Zero code — New build, no existing scaffold

| # | What it is | What's needed | Maps to |
|---|---|---|---|
| Z1 | Stripe checkout | Checkout session creation, webhook handler to update `plan_type`, subscription management, per-tier feature gates for non-trial plans. Zero Stripe imports anywhere in backend. | LAUNCH_READY #6 |
| Z2 | PM layer (requests, tasks, SME workspace) | DB schema for requests table; CRUD API; GRC analyst task queue UI; SME workspace UI (task list, response form, mark-complete); email notifications on assign + complete; invite flow (email → accept link → profile row with `role = "sme"`); request templates; audit log UI surface | LAUNCH_READY #7–13 |
| Z3 | GRC Card as live analytics view | Dashboard view showing: gap coverage % (from gap engine), open Bird Eye findings count by severity, pending SME task count (from Z2), recent activity feed. Depends on M1, W6, and Z2 task count. | LAUNCH_READY #14 |
| Z4 | GRC Card distribution | Email send infrastructure (SES or SendGrid), cadence configuration UI, distro list management, HTML email body, PDF attachment (generated from Z3 view), Midnight watermark in footer | LAUNCH_READY #16 |
| Z5 | Onboarding wizard UI | 3-question frontend at `/onboarding/plan`; writes `frameworks`, `primary_objective`, `build_method` to `onboarding_sessions`; sets `completed = true`; redirects to dashboard; empty-state reads `frameworks` for first-doc suggestions | LAUNCH_READY #3, MTS §6 BLOCK |
| Z6 | Template engine implementation | Replace stub in `template_engine.py`; requires midnight-template-build templates to be accessible at deploy time (see I2) | ARCH task #3 |
| Z7 | `generation_intake` writer | `POST /pipeline/trace/intake` route writes intake row in schema matching `TraceAgentIntake` model; without this, TraceAgent step 1 fails with a DB 404 for any intake_id | ARCH task #4, uncatalogued in LAUNCH_READY |
| Z8 | Excel / CSV import | Column-mapping UI, import logic routing rows to tasks (PM layer) or policy library; depends on Z2 schema | LAUNCH_READY #15 |
| Z9 | PDF export (GRC Card, Bird Eye findings) | "Export PDF" action on GRC Card view and Bird Eye findings panel; Midnight header, tenant name, date, content, footer watermark | LAUNCH_READY #17 |

---

### Infrastructure / config

| # | file:line | What it is | What it's missing | Smallest action | Maps to |
|---|---|---|---|---|---|
| I1 | `config.py:26` | `VOYAGE_API_KEY` | Defined and in `.env.example`; defaults to empty string; if not set in production, all Bird Eye ingestion fails (embeddings call) | Confirm key is set in ECS task definition / Secrets Manager | LAUNCH_READY #5 |
| I2 | `ARCHITECTURE.md:146` | `midnight-template-build` templates | Live at `/c/Users/bword/Documents/midnight-template-build/` — outside repo; path will not exist in ECS | Copy into repo under `backend/templates/docx/` or mount via EFS; decision required before template_engine is implemented | ARCH task #3, uncatalogued in LAUNCH_READY |

---

## Sequenced Execution Order

**Dependencies drive the first two tiers. Items without dependencies come last, ordered by blast radius.**

---

### Tier 1 — Prerequisite for everything else (do these first)

These unblock the demo, the free tier, and all downstream builds. Nothing external
can be shown until Tier 1 is complete.

**1.1 — TKO filter removal + org name fix + ORPHAN_CUES generalization (B1–B9)**
- Estimated: 2 sessions
- Dependencies: none
- What it unblocks: Bird Eye Logic stage, free-tier value, demo stages 1–3
- Risk: ORPHAN_CUES rewrite needs validation against TKO corpus. Run
  `files/00_VALIDATION_KEY.md` comparison after the fix. If findings regress,
  detection logic needs adjustment before marking complete.

**1.2 — Trial user cap raised to 3 (B12 interim fix)**
- Estimated: 0.25 sessions
- Dependencies: none
- What it unblocks: B2B team evaluation, Sam demo with multiple stakeholders
- Risk: none. One-line change to `TRIAL_MAX_USERS` in `main.py:65`.
  Full invite flow comes later (Z2).

**1.3 — Onboarding wizard + redirect fix (B11 + Z5)**
- Estimated: 3 sessions
- Dependencies: 1.1 (Bird Eye must work before the wizard redirects to a useful product)
- What it unblocks: self-serve signup, LAUNCH_READY #3 DoD
- Risk: `onboarding_sessions` table schema must be confirmed against MTS §4 column
  list before building the form. If `primary_objective` or `build_method` columns
  don't exist in the migration, schema work is needed first.

**1.4 — Gap analysis for uploaded docs (M1)**
- Estimated: 1 session
- Dependencies: 1.1 (Bird Eye must produce findings before framework mapping of
  uploaded docs is useful)
- What it unblocks: Wedge stage of the demo for fresh tenants; `/dashboard/gaps`
  returning non-empty for any tenant with uploaded docs; LAUNCH_READY #14 GRC
  Card coverage metric
- Approach decision needed: (a) run lightweight framework mapping after Bird Eye
  ingest and write `covered_control_ids`, or (b) remove the filter in
  `list_policies_for_gap_analysis` and treat uploaded docs as uncovered against
  all controls. Option (a) produces more accurate gap output but adds a Claude
  call on every ingest. Option (b) is one-line but changes semantics. Recommend
  (b) first; (a) can be added in a later session.

---

### Tier 2 — Required for the §IX demo (5-stage ILWAO)

With Tier 1 done, stages 1–3 (Input, Logic, Wedge) are demoable. Stages 4–5
still break. These items close the remaining demo gaps.

**2.1 — Basic GRC Card dashboard view (subset of Z3)**
- Estimated: 3 sessions
- Dependencies: 1.1 (Bird Eye findings), 1.4 (gap coverage %)
- Scope: a single dashboard view showing gap coverage %, Bird Eye findings count
  by severity, and recent activity feed. Not the full GRC Card (no task count,
  no distribution). Enough to demonstrate Stage 5 of the demo.
- Risk: This is a new UI surface — requires design decisions on layout and data
  display. If it reads AI-generated or placeholder, it fails the demo. Allocate
  0.5 sessions for design before implementation.

**2.2 — TraceAgent HTTP route + intake writer (W1 + Z7)**
- Estimated: 2 sessions
- Dependencies: 1.1 (Bird Eye), but not strictly blocking the demo since Policy
  lane can substitute for Stage 4
- Note: Stage 4 of the demo can use `POST /pipeline/create/generate` (Policy lane)
  as a substitute for Trace Agent. TraceAgent wiring is more impressive for the
  demo but not required to show "Automate." Prioritize here if the Sam demo is
  imminent; otherwise move to Tier 4.
- Risk: `TraceAgentIntake` Pydantic model must be read carefully before writing
  the intake form — all required fields must be present. `generation_intake` table
  schema must match exactly.

---

### Tier 3 — Required for self-serve signup (Principle 1)

With Tiers 1–2 done, the demo works. Self-serve requires paying customers to be
able to sign up, set up, and hit value without a human in the loop.

**3.1 — Stripe checkout end-to-end (Z1)**
- Estimated: 5 sessions
- Dependencies: 1.3 (onboarding wizard — Stripe needs a destination after payment)
- Scope: Starter, Professional, Team, Enterprise tiers. Webhook to update
  `plan_type`. Per-tier feature gate code for non-trial plans. Cancellation
  handling.
- Risk: Stripe integration is the largest single-task risk. Webhook handler
  security (signature verification), idempotency, and testing across all tiers
  add sessions. The 5-session estimate assumes no billing edge cases surface;
  treat it as a floor.

**3.2 — PM layer: requests/tasks schema + API (first half of Z2)**
- Estimated: 2 sessions
- Dependencies: 3.1 (Stripe — some PM features are paid-tier only)
- Scope: DB schema for requests table, CRUD API (`POST /requests`, `GET /requests`,
  `PATCH /requests/{id}/status`, `DELETE /requests/{id}`). No UI yet.
- Risk: schema must account for `tenant_id`, `assignee_id` (SME), `control_id`
  (optional), `framework`. Design this once — changing the schema after the UI
  is built is expensive.

**3.3 — PM layer: GRC analyst workspace UI (second half, part 1)**
- Estimated: 2 sessions
- Dependencies: 3.2
- Scope: task queue in dashboard (open requests, filterable by status + framework),
  request creation form (title, description, framework, assignee, due date),
  SME directory (list of profiles with role="sme").
- Risk: SME directory requires invite flow (3.5) to populate. Build the UI with
  empty-state handling.

**3.4 — PM layer: SME workspace UI (second half, part 2)**
- Estimated: 2 sessions
- Dependencies: 3.2
- Scope: separate route for SMEs (not the full dashboard); assigned tasks list
  with context (title, description, due date); response submission form (text +
  optional file); mark-complete action.
- Risk: SME workspace must be a distinct surface — not the analyst's dashboard
  with sections hidden. Different route, different shell.

**3.5 — PM layer: invite flow + email notifications (Z2 remainder)**
- Estimated: 3 sessions
- Dependencies: 3.2, 3.3, 3.4 (invite flow needs the SME workspace to land in)
- Scope: invite endpoint (sends email with accept link); accept link creates
  `profiles` row with `role = "sme"`, token expires after 7 days; analyst
  gets email when SME marks task complete; SME gets email when assigned.
  Email infrastructure decision: SES or SendGrid.
- Risk: transactional email is always harder than expected. 7-day token expiry,
  deduplication on duplicate invites, and email deliverability (SPF/DKIM) add
  time. 3 sessions is aggressive if email infra is new.

---

### Tier 4 — Required for tier enforcement (Principle 4: Demo-free/Stripe)

**4.1 — Per-tier feature gates (non-trial plan enforcement)**
- Estimated: 1 session
- Dependencies: 3.1 (Stripe, so plan_type is actually being set by real upgrades)
- Scope: Add `plan_type` checks for non-trial tiers in `verify_access()` and
  relevant routes (e.g., Starter unlocks unlimited uploads, Professional unlocks
  3 frameworks, Team unlocks all). Currently no non-trial gate logic exists.
- Risk: Low. The enforcement pattern from trial limits is already in place.

**4.2 — Paywall UX (upgrade prompts at choke points)**
- Estimated: 1 session
- Dependencies: 3.1, 4.1
- Scope: Paywall prompts at (1) 4th upload, (2) 2nd framework, (3) invite attempt.
  Link to Stripe checkout from each prompt.
- Risk: Low if Stripe checkout session creation is already wired (3.1).

---

### Tier 5 — Everything else, smallest blast radius first

**5.1 — gap_engine CONTROL_REGISTRY → frameworks/*.json (W6)**
- Estimated: 1 session
- Dependencies: none (pure refactor)
- Risk: run existing gap_engine tests to verify equivalence before marking done.

**5.2 — Secrets hygiene: VOYAGE_API_KEY in production (I1)**
- Estimated: 0.5 sessions
- Dependencies: none
- Scope: confirm VOYAGE_API_KEY is in ECS task definition via Secrets Manager.
  Update LAUNCH_READY #5 DoD to include Voyage AI key verification.

**5.3 — midnight-template-build repo inclusion strategy (I2)**
- Estimated: 0.5 sessions for the decision + 0.5 to execute
- Dependencies: none; must be resolved before W2 is implemented
- Scope: decision only — copy into repo under `backend/templates/docx/` or mount
  via EFS. Copying is simpler and avoids EFS cost; it adds ~36 .docx files to
  the repo. Recommend copying.

**5.4 — Template engine implementation (W2 + Z6)**
- Estimated: 3 sessions
- Dependencies: 5.3 (templates must be in repo before engine can reference them)
- Risk: python-docx token replacement across paragraph runs is the hard part.
  Word splits text across `<w:r>` XML runs; a token that spans two runs won't be
  found by simple string replace. Test with real .docx templates from
  midnight-template-build before declaring working.

**5.5 — 8 studio lanes wired to backend (W3)**
- Estimated: 5 sessions
- Dependencies: none for backend work; template_engine (5.4) for professional output
- Scope: define slot specs for 8 doc types (procedure, standard, process_flow,
  training, incident_runbook, risk_assessment, audit_package, ai_governance);
  extend `_generate_policy_data()` or create per-type equivalents; wire fetch
  calls in `create_studio.js` per lane.
- Risk: slot spec definition is the bulk of the work (what sections does each
  doc type have, what prompts generate each section?). 5 sessions assumes 2–3
  lanes per session. If quality review per lane is included, estimate climbs.

**5.6 — Full GRC Card with live metrics (Z3 remainder)**
- Estimated: 2 sessions (beyond the 3 already in 2.1)
- Dependencies: 3.2–3.5 (PM layer — pending task count), 1.4 (gap coverage %)
- Scope: Add pending SME task count (from PM layer) and audit calendar to the
  basic GRC Card built in 2.1. Wire all metrics to live data.

**5.7 — GRC Card distribution (Z4)**
- Estimated: 4 sessions
- Dependencies: 5.6 (full GRC Card must exist before distributing it)
- Scope: cadence configuration UI, distro list management, scheduled send
  infrastructure (cron or background job), HTML email body, PDF attachment,
  Midnight watermark in footer.
- Risk: scheduled send requires a persistent job runner (not just FastAPI
  BackgroundTasks, which doesn't survive restarts). Either an ECS scheduled
  task, a database-backed job queue, or a cron endpoint polled by a scheduler
  are all valid approaches. Decision adds a session.

**5.8 — PDF export for Bird Eye findings and GRC Card (Z9)**
- Estimated: 2 sessions
- Dependencies: 5.6 (GRC Card view must exist to export)
- Scope: "Export PDF" action on GRC Card view and Bird Eye findings panel.
  Midnight header, tenant name, date, content, footer watermark. The existing
  `pdf_renderer.py` can be extended.

**5.9 — Excel / CSV import (Z8)**
- Estimated: 4 sessions
- Dependencies: 3.2 (requests schema must exist for imported tasks)
- Risk: column-mapping UI is UX-heavy. The import logic itself is moderate; the
  UI where a user maps "Status" to one of the system fields is the time sink.

**5.10 — Knowledge sectors into prompts (W5)**
- Estimated: 1 session
- Dependencies: check `profiles` table for `industry`/`sector` column; if absent,
  use `tenants.industry` captured at signup
- Risk: low. Read a JSON file, inject into system prompt. If industry field
  doesn't exist, this becomes 0.5 sessions to add + 0.5 to inject.

**5.11 — Framework deep coverage: SOC 2, HIPAA, ISO 27001 (LAUNCH_READY #22–24)**
- Estimated: 6 sessions
- Dependencies: 5.1 (gap_engine reads from frameworks/*.json, so control additions
  go into JSON files, not hardcoded list)
- Scope: review current control counts (HIPAA: 8, SOC 2: 3, ISO 27001: 3 in
  current CONTROL_REGISTRY); ISO 27001:2022 has 93 Annex A controls — 3 is not
  "deep". Research each framework's audit evidence requirements; add controls
  until coverage is audit-representative; founder review against known audit
  evidence requirements.
- Risk: this is judgment-heavy, not code-heavy. 6 sessions is for a founder with
  GRC domain knowledge doing the review and the implementation together. If
  framework-specific research takes longer than expected, this estimate doubles.

**5.12 — Dashboard visual design pass (LAUNCH_READY #18)**
- Estimated: 6 sessions
- Dependencies: Z3 (GRC Card must be built first — design should reflect final
  data surfaces, not current state)
- Risk: this is a sequential workflow: references → mocks → approval →
  implementation. Design sessions are harder to time-box than code sessions.
  6 sessions assumes the founder is doing design. If a designer is involved,
  coordination adds time.

**5.13 — Status page (LAUNCH_READY #19)**
- Estimated: 1 session
- Dependencies: none

**5.14 — Customer-facing documentation (LAUNCH_READY #20)**
- Estimated: 4 sessions
- Dependencies: complete product (self-serve, Bird Eye, PM layer, policy
  generation must all work before documenting them)
- Scope: 5 topics per spec. Good docs take longer than code.

**5.15 — Landing page copy (LAUNCH_READY #21)**
- Estimated: 2 sessions
- Dependencies: none (can be done any time; copy doesn't require the product
  to be complete)

---

## Phase 1 Completion Math

**Session count by tier:**

| Tier | Description | Sessions |
|---|---|---|
| 1 | Prerequisites | 1.1 (2) + 1.2 (0.25) + 1.3 (3) + 1.4 (1) = **6.25** |
| 2 | Demo-ready | 2.1 (3) + 2.2 (2) = **5** |
| 3 | Self-serve signup | 3.1 (5) + 3.2 (2) + 3.3 (2) + 3.4 (2) + 3.5 (3) = **14** |
| 4 | Tier enforcement | 4.1 (1) + 4.2 (1) = **2** |
| 5 | Everything else | 5.1 (1) + 5.2 (0.5) + 5.3 (1) + 5.4 (3) + 5.5 (5) + 5.6 (2) + 5.7 (4) + 5.8 (2) + 5.9 (4) + 5.10 (1) + 5.11 (6) + 5.12 (6) + 5.13 (1) + 5.14 (4) + 5.15 (2) = **42.5** |

**Total: 69.75 sessions. Call it 70.**

**At 4 sessions/week** (W-2 + family + recovery — more realistic pacing):
70 ÷ 4 = 17.5 weeks → start 2026-05-24 → **complete approximately 2026-09-27**

**At 6 sessions/week** (high-output, no recovery buffer):
70 ÷ 6 = 11.7 weeks → **complete approximately 2026-08-16**

**STRATEGY §XVI target: Q4 2026 / Q1 2027** (October 2026 – March 2027)

**Verdict: on track.** At 4 sessions/week, completion is late September 2026 — just
ahead of Q4. At 3 sessions/week (realistic minimum with W-2, family, and unexpected
obstacles), completion is 23 weeks → **2026-10-25**, which is mid-Q4. The range is
late September to late October 2026. The strategy target of Q4 2026 is achievable
without padding.

**Three largest session-count items:**

1. **PM layer (Tiers 3.1–3.5): 15 sessions combined (Stripe + all PM layer)**
   Deferral candidate for V2: No. The PM layer is the product — requests, SME
   coordination, invite flow. The GRC Card depends on it. Without it, Midnight
   is Bird Eye + policy generation, not a program management system. STRATEGY §XII
   makes clear the GRC Card is the retention artifact; the GRC Card's pending-task
   metric requires the PM layer. Deferring the PM layer defers the entire product.

2. **Dashboard visual design pass: 6 sessions**
   Deferral candidate: Partial. The design pass could be scoped to the primary
   user-facing surfaces (GRC Card, Bird Eye findings, request list) and deferred
   for lower-traffic surfaces (framework coverage view, migrate UI). The
   LAUNCH_READY #18 DoD says "no element reads AI-generated or placeholder" — this
   is a launch blocker, not a nice-to-have. But the scope could be narrowed.

3. **Framework deep coverage (SOC 2, HIPAA, ISO 27001): 6 sessions**
   Deferral candidate: Partial. SOC 2 and HIPAA are the primary launch frameworks
   and cannot be deferred without breaking the launch value prop. ISO 27001 is the
   third launch framework per STRATEGY §XVI. Deferring ISO 27001 to V2 saves 2
   sessions and narrows the launch to SOC 2 + HIPAA only. STRATEGY §III says
   "three frameworks done thoroughly at launch is better than seven done partially"
   — so dropping to two is against the strategic intent, but might be the right
   trade if the founder's GRC depth in ISO 27001 isn't as strong as in SOC 2 and
   HIPAA.

---

## Honest Gaps

**Items that need founder judgment, not code reading:**

1. **What "deep" means for framework coverage.** The LAUNCH_READY #22–24 DoD says
   "founder reviews output against known audit evidence requirements." The gap
   engine currently has 8 HIPAA, 3 SOC 2, and 3 ISO 27001 controls. ISO 27001:2022
   has 93 Annex A controls. Whether 3 is "deep enough" for launch or whether the
   number needs to reach 30+ is a judgment call that only someone who has run a
   real ISO 27001 audit can make. The 6-session estimate above assumes the founder
   has that judgment and can execute both the research and the implementation.

2. **midnight-template-build repo strategy.** The 36 .docx templates at
   `/c/Users/bword/Documents/midnight-template-build/` need to be in the
   production environment. Copying into repo is simple; it adds binary files
   to git history permanently. Mounting via EFS adds operational complexity.
   Decision is infrastructure + philosophy (do binary assets belong in the repo?),
   not code.

3. **Stripe tier differentiation.** STRATEGY §XV defines 5 pricing tiers.
   Item 4.1 is scoped to adding non-trial gates, but the exact per-tier
   capabilities (how many GRC seats at Team vs Professional? which features
   gate at Professional vs Team?) require a product decision before implementation.
   The pricing table in STRATEGY §XV has a start but doesn't map cleanly to
   every feature.

4. **Demo readiness date.** Items 1.1, 1.2, 1.3, 1.4, and 2.1 must be complete
   before any external demo. At 4 sessions/week, that's 12.25 sessions → 3 weeks
   from 2026-05-24 → **demo-ready approximately 2026-06-14**. Whether this is
   fast enough for a specific Sam demo or other planned external show is a founder
   schedule call, not a code call.

**Items where the estimate is a guess, not a calculation:**

- **5.11 (framework deep coverage): 6 sessions.** This estimate assumes domain
  knowledge is already in the founder's head and the work is mostly writing
  control definitions + testing output. If research is required first, add
  sessions. If the current 8 HIPAA controls are substantially wrong (not just
  incomplete), add more.

- **3.5 (PM layer invite flow + email): 3 sessions.** Email deliverability
  (SPF, DKIM, DMARC, domain reputation) and transactional email provider
  setup (SES/SendGrid account, templates, bounced-email handling) can blow
  a session estimate. 3 is the best case; 5 is the realistic worst case if
  email infra is new.

- **5.7 (GRC Card distribution): 4 sessions.** The scheduled-send mechanism
  doesn't exist in the codebase. Whether a cron endpoint, ECS scheduled task,
  or a job table with a polling loop is chosen changes both the implementation
  complexity and the estimate. The decision itself is a session.

**Items where launch criteria are genuinely ambiguous:**

- **LAUNCH_READY #18 (dashboard visual polish):** The DoD says "reviewed by
  at least one person outside the build process before signing off." If no
  external reviewer is involved, this DoD can't be met by the founder alone.
  Is the design partner cohort (3–5 practitioners per STRATEGY §XVI) the
  review pool? That's not stated in the DoD.

- **LAUNCH_READY #4 (real auth):** The TOOL_PASSWORD bug is not in the
  codebase (audit §7 confirmed). The DoD (`grep -r "TOOL_PASSWORD" backend/`)
  passes today. But the DoD also says "all authenticated routes require a
  valid Supabase JWT cookie." Whether that's fully enforced or whether any
  admin/dev routes bypass it is not verified in this audit. The DoD may
  already pass; it may have a hidden failure. A 30-minute code grep would
  confirm. Not scheduled because it's likely not blocking.

---

*Produced: 2026-05-23. Read-only audit. No files modified.*
*Sources: codebase at HEAD (ceb3066), STRATEGY.md, LAUNCH_READY.md,*
*MULTI_TENANT_SPEC.md, ARCHITECTURE.md, VERTICAL_AUDIT_2026-05-23.md.*
