# Midnight — Multi-Tenant Readiness Spec

**Target:** 100 tenants by EOY 2026 (32 weeks)
**Scope:** Scale-readiness, not sales motion. Self-serve onboarding, any tenant, no manual intervention.
**Constraint:** Solo founder, W-2 day job. Every section is sized to that reality.
**CLAUDE.md freeze:** This spec describes wiring and correction work — no new product capability.

---

## 1. SELF-SERVE SIGNUP

### What happens between "hits signup" and "tenant is usable"

**Auth flow (already built)**

1. User opens `/login.html`
2. Chooses one of: email/password, Google OAuth, Microsoft OAuth, Magic Link
3. On email/password: POST `/auth/signup` with `{ email, password, company_name, name, industry, region, employee_count }`
4. On OAuth: `/auth/oauth/{google|microsoft}` → Supabase → redirect → `/auth/exchange` → cookie set
5. Backend (`main.py`) auto-provisions:
   - `tenants` row: `slug` (unique), `name`, `industry`, `region`, `employee_count`, `plan_type = "trial"`
   - `profiles` row: links Supabase auth user → tenant, `role = "owner"`
   - `onboarding_sessions` row: `current_step = "plan"`, `progress = 0`, `completed = false`
6. Redirect to `/onboarding/plan`

**Critical gap: `/onboarding/plan` is broken**

`GET /onboarding/plan` in `main.py:837` is a 307 redirect back to `/login.html?mode=signup`.
New users who complete signup are immediately looped back to the signup form. There is no onboarding
page. The `onboarding_sessions` table, the `frameworks`, `primary_objective`, and `build_method`
columns, and the `completed` flag — all exist in the schema but are never written to from the product.

Until this is fixed, self-serve onboarding does not exist. The fix is to build a 3-step wizard at
`/onboarding/plan` (or a modal in `login.html`) and redirect to `/midnight_dashboard.html` on complete.

**Onboarding session design (table confirmed, UI to build)**

The onboarding wizard writes these columns in `onboarding_sessions` (all exist in the migration):
- `frameworks` (JSONB array) — which frameworks the tenant cares about
- `primary_objective` (text) — one of: audit_prep, continuous_monitoring, gap_closure, policy_creation
- `build_method` (text) — one of: upload_existing, start_from_scratch, hybrid
- `current_step` → `"complete"`, `completed = true`

Recommended industry → framework defaults (pre-populate if industry was captured at signup):

| Industry | Default frameworks |
|---|---|
| Healthcare | HIPAA, SOC 2 |
| Finance / Fintech | PCI DSS, SOC 2 |
| General SaaS | SOC 2, ISO 27001 |
| Government contractor | NIST CSF, NIST 800-53 |
| Other | SOC 2 |

**Default state of a new tenant**

| Table | State |
|---|---|
| tenants | 1 row, plan_type=trial |
| profiles | 1 row, role=owner |
| policies (documents) | empty |
| policy_sections (chunks) | empty |
| bird_eye_runs | empty |
| bird_eye_findings | empty |
| onboarding_sessions | 1 row, completed=false (never written to today) |
| enabled_modules | empty (all modules accessible by default) |

**What is seeded:** Nothing. No demo documents are pre-loaded. The tenant starts with a clean library.
TKO corpus is TKO's data, not a template every tenant gets.

**Trial constraints (already enforced in routes.py):**
- 1 user per tenant (enforced in `verify_access()` — see §6 BLOCKS)
- 3 document upload limit (`TRIAL_MAX_UPLOADS = 3`)
- 1 framework (`TRIAL_MAX_FRAMEWORKS = 1`)

These limits gate the free tier. Paid upgrade removes them. See §8 for paywall design.

---

## 2. FIRST-UPLOAD UX

### Empty library state

A tenant with 0 documents sees:
- Overview: 0 Policies, 0 Gaps, 0 Frameworks, empty activity feed
- Policy Library: empty table, "No generated outputs yet — run Migrate or Create to get started"
- Bird Eye tab: upload form visible, "Waiting for workspace activity" status bar
- Gap Analysis: empty

**First-run guidance gap:** There is no wizard or next-action prompt explaining what to upload first.
This is a UX gap for self-serve (see §4 Smart Onboarding).

### Upload → ingestion

1. Tenant opens Bird Eye tab, drags or selects a `.docx`, `.pdf`, `.md`, or `.txt` file
2. POST `/bird-eye/ingest` with file + optional `artifact_type` and `title`
3. Backend pipeline (all in `bird_eye/ingestion.py`):
   - Text extraction: `_iter_paragraphs_in_order()` for .docx (includes table cells), pypdf for .pdf
   - If `text.strip()` is empty → 400 "No extractable text" returned to UI
   - LLM metadata extraction (1 Claude Opus call): title, owner, version, dates, frameworks, artifact_type, per-section numeric requirements
   - Section splitting: heading-regex walk of extracted text → list of `{heading, content}` dicts
   - Voyage AI embedding (batch): 1024-dim vector per section
   - DB write: 1 row in `policies` (TABLE_DOCUMENTS) + N rows in `policy_sections` (TABLE_CHUNKS)
4. Auto Bird Eye run triggers immediately after ingest (`auto_run=True` default)

**Note:** The ingest + run is synchronous — the POST response does not return until Bird Eye finishes.
This is a scale concern (see §7) but acceptable for fewer than 20 tenants.

### Bird Eye on a 1-doc library

What fires with a single document:

| Detector | Result |
|---|---|
| detect_duplicates | 0 findings (need 2+ docs to compare) |
| detect_conflicts | 0 findings (need 2+ docs with overlapping numeric keys) |
| detect_stale_governance | 1-3 findings if doc has no owner, overdue review, or pre-release version marked Active |
| detect_framework_gaps | 0-2 findings if doc body mentions framework keywords not in its `selected_frameworks` tag |
| detect_orphans | 0-1 findings if doc references a runbook/procedure that doesn't exist in the library |

**What the tenant sees after first upload:**
- Library summary: "1 document reviewed · N issues open"
- Findings panel: actionable items like "This policy has no assigned owner" or "This policy references HIPAA but is not tagged for HIPAA"
- Section count displayed next to document in library
- These are genuinely useful findings on a 1-doc library — no "nothing to show yet" dead ends

### 1-doc library states to handle explicitly in the UI

- `documents_reviewed = 1, findings_count = 0` → "Your document looks clean. Upload more to find cross-document issues."
- `documents_reviewed = 1, findings_count > 0` → show findings, no "compare to other docs" CTAs
- Upload in progress (auto_run running) → "Bird Eye Scanning" overlay state (already in UI)
- Ingest failed (extraction error) → 400 response, UI shows error toast

---

## 3. STEADY-STATE UX

### Tenant has 15 docs, mixed naming, mixed types

**After TKO-* filters are removed** (§6 Inventory, BLOCKS section), this works:

**Bird Eye output at 15 docs:**
- Conflict detector: compares `numeric_requirements` across all docs in the tenant's library — finds password length conflicts, session timeout mismatches, breach notification window discrepancies
- Duplicate detector: cosine similarity across all section embeddings — finds near-duplicate policy sections (common when policies overlap with standards)
- Stale governance: audits every doc for missing owner, overdue review date, pre-release version
- Framework gaps: checks all docs for body→tag mismatches
- Orphan detector (after fix): checks if any policy referencing runbook/procedure keywords has a matching artifact type in the library

**Gap engine output:**
- `/dashboard/gaps` calls `run_program_gap_analysis()` once policies exist
- Returns control-by-control gap list: which HIPAA/SOC 2/NIST/PCI controls are covered vs. missing
- Coverage percentage per framework
- Recommended action per gap ("Add section covering AC-2 Account Management to your Access Control Policy")
- **Note:** Per ARCHITECTURE.md, `/dashboard/gaps` currently returns empty lists — gap_engine is never called. This is a known wiring gap.

**Framework mapping output:**
- `/pipeline/analyze` maps documents to framework control IDs via Go service
- **Note:** Per ARCHITECTURE.md, the Go service is not in this repo and not in the Dockerfile — this route is currently dead. Framework coverage via this path requires the Go service to be deployed.

**Dashboard at 15 docs (with gaps noted above fixed):**
- Overview: real metrics — X policies, Y gaps, Z% coverage
- Policy Library: document table with type, version, owner, status columns
- Bird Eye: findings list sorted by severity; library summary shows merge opportunities
- Gap Analysis: framework breakdown, critical/high/medium/low gap counts
- GRC Summary: executive report on demand

**Document naming freedom:**
Any `policy_number` value extracted by the LLM metadata call (or `null`) works. The detectors operate
on `tenant_id` scope only — no naming scheme required. A tenant can use `ACME-POL-001`, `IR-2024`, or
leave the field null. All documents are analyzed.

### Wow Moment Design Target

**The constraint that drives the rest of the work:** Without a defined quality bar, "scale-readiness"
optimizes for availability, not value. Here is the target:

**Time-to-first-finding:** A new tenant uploads their first real policy document and sees at least one
actionable Bird Eye finding within 5 minutes of signup. This is achievable because stale governance
and framework gap detectors fire on a 1-doc library.

**Output quality bar:**
- The finding must name a specific issue in the tenant's own document, not a generic message
- "This document references HIPAA but is not tagged for HIPAA" beats "No findings yet"
- The stale governance detector is the most reliable source for first findings — almost every
  real-world policy document lacks an assigned owner or has no review date set

**Shareable artifact target:**
- The immediate shareable is the Bird Eye findings panel — a numbered list of issues with severity
- The higher-value shareable is a GRC Summary export (PDF/docx) the owner can forward to their CISO,
  auditor, or board. This requires the GRC Summary lane to work for any tenant's documents.
- Target: within the first session, a new tenant can download one artifact they'd actually send to
  someone. If they can't, the wow moment didn't land.

**Wow moment failure modes to watch:**
- Ingest fails with "no extractable text" (table-heavy docx — fixed in cc830b6 but validate)
- Bird Eye runs but returns 0 findings on a real policy (likely means TKO-* filter still blocking)
- Findings are present but reference the wrong organization name ("Takeoff LLC" instead of theirs)
- Dashboard shows correct data but the export/share path is broken

---

## 4. SMART ONBOARDING

### Design (no code implementation yet; wizard to be built)

The goal: a new tenant who doesn't know where to start gets to their first useful finding in under
10 minutes. Currently there is no onboarding flow — signup loops users back to the signup form
(see §1). The wizard must be built before any external tenant signs up.

**Onboarding wizard (post-signup, at `/onboarding/plan`)**

3-question flow, writes to `onboarding_sessions`. All columns exist in the migration:

1. **"What are you working toward?"** → maps to `primary_objective`
   - Getting ready for a SOC 2 audit
   - Maintaining ongoing compliance
   - Closing a specific gap
   - Building our policy library from scratch

2. **"Which frameworks matter to you?"** → maps to `frameworks` (JSONB array, multi-select)
   - SOC 2 / SOC 2 Type II
   - HIPAA / HITECH
   - PCI DSS
   - ISO 27001
   - NIST CSF
   - NIST 800-53
   - Pre-populate based on `industry` captured at signup (see defaults table in §1)

3. **"Do you have existing policies?"** → maps to `build_method`
   - Yes, I'll upload them → redirect to dashboard, Bird Eye tab focused, upload prompt visible
   - No, I'll start from scratch → redirect to dashboard, Create tab focused, Policy lane open
   - A mix of both → redirect to dashboard overview with both CTAs

On completion: write `current_step = "complete"`, `completed = true`, redirect to
`/midnight_dashboard.html`.

**In-product next-action prompts (empty state enhancements)**

After onboarding completes, the empty library state reads `onboarding_sessions.frameworks` and shows:
- "Start with your Access Control Policy — covers SOC 2 CC6.1, HIPAA 164.312(a)"
- "Upload your Incident Response Policy — addresses SOC 2 CC7.3 and NIST IR-1"
- "No frameworks selected yet — complete your setup to get personalized suggestions →"

These are static lookup entries (`framework → top 3 suggested first documents`), not AI-generated.
No new backend needed — read `frameworks` from the onboarding_session at dashboard load.

---

## 5. TKO'S ROLE

### TKO becomes one of N tenants

TKO (Takeoff LLC) was the only tenant during development. Going forward:

**What changes:**
- Bird Eye detectors no longer filter by `policy_number like 'TKO-*'`. TKO's documents are found by
  `tenant_id` like any other tenant's.
- `ORPHAN_CUES` in `detectors.py` is generalized from TKO-POL-xxx policy numbers to document-type-based
  matching (see §6). TKO's orphan findings are re-derived from its actual document types.
- The `"organization": "Takeoff LLC"` hardcode in `ingestion.py` is replaced with the tenant's `name` field.
- Scripts (`ingest_bird_eye_corpus.py`, `backfill_embeddings.py`, `render_bird_eye_screenshots.py`)
  keep their TKO-* filters — they are TKO-specific utilities, not production code.

**What stays the same:**
- TKO's `files/` corpus (the 8 demo policy documents) remains in the repo as validation fixtures.
- TKO remains the dogfood tenant for testing Bird Eye output quality.
- `files/00_VALIDATION_KEY.md` stays as the expected-findings reference for TKO runs.
- TKO tenant_id is the value used in `tests/` where a fixed tenant is needed.

**TKO-specific validation post-fix:**
After removing TKO-* filters, run the TKO corpus through Bird Eye and compare output to
`files/00_VALIDATION_KEY.md`. If findings are preserved, the fix is correct. If findings regress,
the generalized detection logic needs adjustment.

---

## 6. INVENTORY: GAPS FROM TODAY TO DESTINATION

### BLOCKS any non-TKO self-onboarding

These prevent self-onboarding from working. Fix before first external tenant.

| Location | Issue | Fix direction |
|---|---|---|
| `detectors.py:130` | `detect_duplicates` fetches docs with `"policy_number": "like.TKO-*"` | Remove filter; docs already scoped to tenant_id |
| `detectors.py:252` | `detect_conflicts` same filter | Same |
| `detectors.py:415` | `detect_stale_governance` same filter | Same |
| `detectors.py:520` | `detect_framework_gaps` same filter | Same |
| `detectors.py:621` | `detect_orphans` same filter | Same |
| `orchestrator.py:61` | `documents_reviewed` count uses same filter | Remove filter; count all tenant docs |
| `detectors.py:592,599,606` | `ORPHAN_CUES` checks `TKO-POL-003`, `TKO-POL-005`, `TKO-POL-006` by policy number | Generalize: match by document content type, not policy number (see below) |
| `detectors.py:567` | `detect_framework_gaps` special-cases `number == "TKO-POL-004"` for AUP | Remove; `"acceptable use" in title` already covers it generically |
| `main.py:837` | `/onboarding/plan` is a 307 redirect back to `/login.html?mode=signup` — new users loop back to signup after registering | Build 3-question wizard; write to onboarding_sessions; redirect to dashboard |
| `verify_access()` | Trial cap: 1 user per tenant. B2B compliance buyers add teammates within the first hour. If they can't add a second user, they churn before they see value. | Wire a paid-tier check; `profiles` table already supports multiple users per tenant_id |

**ORPHAN_CUES generalization design:**

Replace the policy-number-based table with a content-based pattern:
- If any `document_type = 'policy'` contains incident response keywords (`incident response`, `runbook`, `playbook`) AND no `document_type = 'runbook'` exists in the tenant library → flag orphan
- If any `document_type = 'policy'` contains vendor management keywords AND no `document_type = 'procedure'` exists → flag orphan
- If any `document_type = 'policy'` contains data disposal keywords AND no `document_type = 'procedure'` with matching content exists → flag orphan

This is entirely data-driven — works for any tenant's naming scheme.

### PRODUCES WRONG OUTPUT for non-TKO tenant

These don't block Bird Eye but produce incorrect or misleading output.

| Location | Issue |
|---|---|
| `ingestion.py:359` | `"organization": "Takeoff LLC"` hardcoded on every doc insert. Non-TKO tenant documents show wrong org name. Fix: fetch `tenant.name` from the tenants table and use it here. |
| `metadata_llm.py:72` | LLM extraction prompt example says `"e.g. 'TKO-POL-002'"`. Minor anchoring risk — may bias model toward TKO naming scheme. Replace with `"e.g. 'POL-001'"`. |
| `dashboard.py` (gap engine) | Per ARCHITECTURE.md, `/dashboard/gaps` returns empty lists — gap_engine is never called. Gap Analysis view is dead for all tenants. Wiring task exists in ARCHITECTURE.md. |
| `/pipeline/analyze` | Per ARCHITECTURE.md, the Go service backing this route is not deployed. Framework coverage via this path is dead. |
| Create studio lanes | 8 of 9 doc types (Procedure, Standard, Runbook, Training, Process Flow, Risk Assessment, Audit Package, AI Governance) show `workflowToast("coming soon")`. Tenants who try to create anything other than a Policy hit a dead end. |

### DEGRADES at scale (> 20 tenants)

Flag before 20 active tenants, not at 100.

| Component | Issue |
|---|---|
| Bird Eye auto-run | Synchronous inside POST `/bird-eye/ingest`. Response blocks until all 5 detectors complete. At 20 concurrent uploads, 20 Bird Eye runs compete on 1 ECS task. |
| Python cosine (detect_duplicates) | O(n²) comparison. At 15 docs × 20 sections = 300 chunks → 90K pairs. At 50 docs × 20 = 1000 chunks → 1M pairs. Grows quadratically with library size. |
| No pagination | `/dashboard/documents` fetches all docs. At 100+ docs/tenant the payload grows unbounded. |
| No async job queue | All processing is in-band on the FastAPI event loop (no Celery, no Redis). Long Bird Eye runs block other requests. |
| ECS single task | No auto-scaling policy. At 100 active concurrent tenants, the single task is the bottleneck. |

### COSMETIC

Low priority; fix opportunistically.

| Location | Issue |
|---|---|
| `routes.py:1364` | Bird Talk system prompt: "Midnight by Takeoff LLC" — branding issue, not a data leak |
| `ingestion.py:359` | Wrong org name for non-Takeoff tenants (also listed in WRONG OUTPUT; fix once) |
| `metadata_llm.py:72` | TKO-POL-002 example in LLM prompt |
| `scripts/` | TKO-* filters in backfill_embeddings.py, ingest_bird_eye_corpus.py, render_bird_eye_screenshots.py — scripts only |

---

## 7. 100-TENANT LOAD CONSIDERATIONS

Inventory only. Do not solve here.

**LLM cost**
- 1 Claude Opus call per document upload (metadata extraction)
- At 100 tenants × 20 docs avg = 2,000 calls total for initial ingestion
- Each call ~2K tokens in + ~1K out ≈ $0.18/call → ~$360 one-time ingestion cost
- Ongoing cost is new uploads only. Not a blocker but worth monitoring.

**Embedding cost**
- Voyage AI voyage-3: ~$0.06/1M tokens
- 100 tenants × 20 docs × 50 chunks × 200 tokens/chunk = 20M tokens ≈ $1.20 one-time
- Not a cost concern.

**Embedding storage**
- 1024 floats × 4 bytes = 4KB per chunk
- 100 tenants × 20 docs × 50 chunks = 100K chunks × 4KB = 400MB in Supabase
- Acceptable at current scale.

**Python cosine similarity**
- `detect_duplicates` runs an O(n²) loop in pure Python
- 100 chunks: ~10K comparisons, ~0.1s — fine
- 500 chunks: ~250K comparisons, ~2-5s — slow
- 2000 chunks (large library): ~4M comparisons, ~40s — timeout risk
- Flag for vectorized computation (numpy) before any tenant reaches 100 docs.

**Bird Eye synchronous execution**
- Today: upload request blocks until full Bird Eye run completes
- At 10+ concurrent uploads: queue builds on the single ECS task
- Move Bird Eye run to background task (FastAPI BackgroundTasks or a job table + polling) before reaching 20 tenants with active uploads.

**ECS task sizing**
- Single task, no auto-scaling policy in place
- At 100 tenants with occasional concurrent use: needs at minimum 2 vCPU / 4GB memory
- Auto-scaling policy needed: scale out on CPU > 60% for 3 consecutive minutes.

**Supabase REST connection pattern**
- All Bird Eye DB calls go through HTTP REST (not pgbouncer)
- 5 detectors × ~3 queries each = 15+ REST calls per Bird Eye run
- At 20 concurrent runs: 300+ simultaneous HTTP calls to Supabase
- Verify against Supabase plan tier connection limits before scaling.

**Dashboard query patterns**
- `/dashboard/documents` has no pagination — fetches all docs for the tenant
- At 100 docs/tenant: acceptable payload
- At 500 docs/tenant: add `limit` + `offset` pagination.

**Multi-user per tenant**
- Once trial cap is removed for paid tenants, multiple users per tenant will generate concurrent
  requests against the same tenant's data. The data plane handles this correctly (tenant_id-scoped
  everywhere); the load concern is ECS task capacity, not data correctness.

**Onboarding session completeness**
- `onboarding_sessions` table exists; `completed` flag is not checked during normal product use
- At scale, stale incomplete sessions from abandoned signups accumulate
- Low priority; add a cleanup cron or TTL once real signups are flowing.

---

## 8. FREE TIER & PAYWALL DESIGN

### What the trial includes (already enforced)

| Capability | Trial limit | Enforced in |
|---|---|---|
| Document uploads | 3 (`TRIAL_MAX_UPLOADS = 3`) | `routes.py` |
| Frameworks | 1 (`TRIAL_MAX_FRAMEWORKS = 1`) | `routes.py` |
| Users per tenant | 1 | `verify_access()` |
| Bird Eye scans | Unlimited (runs on every upload) | Not gated |
| Policy creation | 1 lane (Policy only) | `workflowToast()` gates others |
| Bird Talk | Unlimited | Not gated |

### What's free forever (never locked)

- Signup and tenant provisioning
- Uploading up to 3 documents
- Bird Eye analysis on those 3 documents (all 5 detectors)
- Viewing all findings from those 3 documents
- Policy creation (the one wired lane)
- Bird Talk (AI compliance chat)

The free tier is valuable enough to demonstrate the product — a user can upload their Access Control
Policy, see Bird Eye flag the stale governance issues, and understand the value proposition before
upgrading.

### What triggers the paywall

Three natural choke points exist in the current enforcement logic:

**1. 4th document upload**
- `routes.py` checks `TRIAL_MAX_UPLOADS` before ingestion
- Response: HTTP 403, upgrade prompt
- UX target: show findings from the 3 uploaded docs + "Upload unlimited documents with a paid plan"

**2. 2nd framework selection**
- `routes.py` checks `TRIAL_MAX_FRAMEWORKS` before framework-scoped operations
- Response: HTTP 403, upgrade prompt
- UX target: show coverage for the 1 selected framework + "Add HIPAA, PCI DSS, ISO 27001 with a paid plan"

**3. Team invite (2nd user)**
- `verify_access()` enforces 1-user cap on trial tenants
- Currently no invite UI exists (known gap in §6 BLOCKS)
- Response: should surface a paywall at invite time, not at login of the second user
- UX target: owner sees "Invite teammates" CTA → hits paywall before the invite is sent

### What paid unlocks

| Capability | Change |
|---|---|
| Document uploads | Unlimited |
| Frameworks | Unlimited |
| Users per tenant | Up to plan tier (e.g., 5 for SMB, unlimited for enterprise) |
| Create studio lanes | Remaining 8 lanes (Procedure, Standard, Runbook, etc.) as they are wired |
| Export / share | GRC Summary export; shareable Bird Eye report links |

### Alignment with §6 severity tiers

- The 6 TKO-* filter bugs in BLOCKS must be fixed before the free tier is meaningful — currently
  Bird Eye produces 0 findings for any non-TKO document, making the free tier worthless
- The broken `/onboarding/plan` redirect in BLOCKS must be fixed before trial conversion is possible
- The 1-user cap in BLOCKS is the biggest conversion risk — B2B buyers evaluate with a team
- The 8 unwired Create lanes in WRONG OUTPUT are a paywall problem: if the upgrade promise
  includes those lanes, they must be wired or removed from the upgrade pitch

### What to not design into the free tier

- The free tier should not feel crippled on first use. 3 docs is enough to generate real Bird Eye
  output. The limit hits at the 4th upload, after the user has already seen value.
- Do not gate Bird Talk. It is the fastest path to first value for users who don't have docs ready.
- Do not gate Bird Eye runs. The trial's 3-doc library produces useful findings. Gating scans
  would eliminate the demo value of the free tier.

---

## APPENDIX: FUTURE ENHANCEMENTS (post-freeze)

These ideas are outside the CLAUDE.md freeze. Captured here to avoid losing them; not scheduled.

**Bird Talk as onboarding guide**

Bird Talk's system prompt could be extended to read `onboarding_sessions.completed` and `frameworks`.
If onboarding is not complete, Bird Talk's first response leads with contextual guidance:
"I see you haven't set your compliance frameworks yet — want me to help you figure out which ones
apply to your business? That'll make my answers a lot more specific."
This is new product behavior — not wiring — and belongs after the freeze lifts.

**Tenant-configurable ORPHAN_CUES**

Once the generic content-based orphan detection is in place, a future improvement is letting tenants
define their own "expected artifact" rules: "we require a Runbook for every policy in the IR domain."
This is a configuration UI + a new table — new product capability, post-freeze.

**Multi-user invite flow**

Once the 1-user trial cap is replaced with a paid-tier check, a full invite flow (email invite →
accept → join tenant) needs to be built. The `profiles` table supports it; the frontend and auth
routes do not. Post-freeze work.
