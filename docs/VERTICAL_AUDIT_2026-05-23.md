# Vertical Alignment Audit — 2026-05-23

Read-only reconciliation of `docs/STRATEGY.md`, `docs/MULTI_TENANT_SPEC.md`,
`docs/LAUNCH_READY.md`, and `docs/POST_LAUNCH_ROADMAP.md` against the codebase and
`ARCHITECTURE.md` (the authoritative root-level scope audit dated 2026-05-21).

All claims below are backed by file:line citations or explicit "not found."

---

## Audit 1 — ILWAO Stage Mapping

### What the docs claim

STRATEGY §IV describes five stages: Input → Logic → Wedge → Automate → Output. §V names
specific files for each stage and calls this the architecture of the PM-for-compliance shape.
The Wedge is described as the key differentiator: "most tools tell you what's wrong. Midnight
tells you what to do next." STRATEGY §IX describes a 15-minute demo that walks all five stages
live.

### What the code shows

**Input.** Three surfaces are implied: (1) the onboarding wizard, (2) Bird Eye document upload,
(3) the SME request system. The onboarding wizard does not exist — `main.py:837` returns a 307
redirect back to the signup form. Bird Eye document upload exists in the backend
(`POST /bird-eye/ingest` in `bird_eye/routes.py`) with a frontend in `bird_talk.html` wired to
`/bird-eye/*` (ARCHITECTURE.md:15), though the exact upload form implementation in that file
was not verified here. The SME request/task system has zero code anywhere in the repo.

**Logic.** The five Bird Eye detectors in `bird_eye/detectors.py` are fully implemented.
`bird_eye/orchestrator.py` runs all five and persists findings. `core/framework_mapper.py` is
used by `FrameworkMappingAgent` (called from `agent_ops.py`). `core/gap_engine.py` has a
conditional call in `dashboard.py` — but `ARCHITECTURE.md:50` states the gaps route "returns
`GapsResponse()` with empty lists; gap_engine never called." The practical effect: gap_engine
runs only when pre-existing policies are present, and returns empty for any fresh or sparse
tenant. `ARCHITECTURE.md:177` identifies a structural mismatch: gap_engine has its own
hardcoded `CONTROL_REGISTRY` of 24 controls and never reads `frameworks/*.json`.

**Wedge.** The prioritization logic exists in code: `gap_engine.py` sorts gaps by severity
(explore agent: `gap_engine.py:456`). `signal_manager.py` attaches `recommended_next_action`
per event type. But neither is surfaced in any UI as a "prioritized next-action list."
`ARCHITECTURE.md:50` confirms the gap route returns empty. No dashboard view shows ranked
next actions.

**Automate.** `agents/trace_agent.py` is a fully implemented 16-step orchestrator.
`ARCHITECTURE.md:81` states it is "Dangling — no route calls it." The `generation_intake`
table it reads has no writer anywhere in the repo (ARCHITECTURE.md:140). Policy generation at
`POST /pipeline/create/generate` uses direct LLM calls in `routes.py`, not the Trace Agent.

**Output.** The GRC Summary tab in `midnight_dashboard.html:2067-2108` renders a form (org
name, industry, framework checkboxes) and a generate button that calls
`POST /pipeline/grc-summary`. `ARCHITECTURE.md:49` notes this returns mock data. No email
distribution, no PDF attachment, no Midnight watermark in the frontend. The "GRC Card" as
described in STRATEGY §XII does not exist as a code artifact.

**Code drift (not in STRATEGY §V).** ARCHITECTURE.md documents agents present in the codebase
but absent from §V: `MigrationAgent` (wired to `routes.py`), `BirdSongAgent` (wired to
`routes.py`), `SmartScanAgent` (wired to `smart_scan.py`), `PolicyAgent` (dangling — zero
callers, ARCHITECTURE.md:79).

### The gap

| Stage | Gap classification | Smallest action |
|---|---|---|
| Input (onboarding) | ASPIRATIONAL-AT-LAUNCH | Build the wizard at `/onboarding/plan` (LAUNCH_READY item 3) |
| Input (SME system) | NOT YET WIRED | PM layer is entirely new build (LAUNCH_READY items 7-13) |
| Logic (detectors) | ALIGNED | None |
| Logic (gap_engine) | ASPIRATIONAL-AT-LAUNCH | Wire gap route to call gap_engine unconditionally; surface result in dashboard (ARCH task #1) |
| Logic (registry) | CODE DRIFT | Sync gap_engine CONTROL_REGISTRY with `frameworks/*.json` (ARCH task #7) |
| Wedge | ASPIRATIONAL-AT-LAUNCH | Surface the gap_engine severity-sorted output in the dashboard as a "fix this first" list; the sorting logic already exists |
| Automate | NOT YET WIRED | Add `/pipeline/trace/intake` + `/pipeline/trace/run` routes; add `generation_intake` writer (ARCH task #4) |
| Output (GRC Card) | DOC DRIFT | The docs describe a live analytics artifact; the code has a generation form returning mock data. See Audit 5. |
| §V undocumented agents | CODE DRIFT | Update STRATEGY §V to name Migration, BirdSong, SmartScan agents; remove PolicyAgent from agent layer or wire it |

---

## Audit 2 — LAUNCH_READY vs ARCHITECTURE Wiring Tasks

### What the docs claim

LAUNCH_READY.md has 24 items. ARCHITECTURE.md has 8 ranked wiring tasks. The implication is
that the launch scope covers the wiring backlog.

### What the code shows

| ARCH task | LAUNCH_READY item | Status |
|---|---|---|
| #1 Wire gap_engine → /dashboard/gaps | Item 14 (GRC Card live metrics DoD requires gap data) — **implied, not explicit** | MISSING as standalone item. Gap engine wiring is a prerequisite of item 14 but not broken out. Risk: item 14 fails its DoD if gap_engine wiring isn't sequenced first. |
| #2 Wire 8 studio lanes | Items 22-24 (launch frameworks DoD) — **partially implied** | MISSING as a standalone item. The Policy lane works; Procedure, Standard, Runbook, etc. show `workflowToast()` (ARCHITECTURE.md:33). The PM layer (items 7-13) needs these lanes for non-policy doc generation. No LAUNCH_READY item explicitly addresses lane wiring. |
| #3 Implement template_engine + midnight-template-build | Items 22-24 (generated output must be accurate) — **implied** | MISSING as explicit item. `template_engine.py` is a 3-line stub (ARCHITECTURE.md:158). All generated output currently uses raw `python-docx`, not the 36 professionally designed templates in `midnight-template-build/`. This affects launch framework DoDs (items 22-24). |
| #4 HTTP route + intake writer for TraceAgent | No corresponding item | **MISSING ENTIRELY.** TraceAgent is dangling (ARCHITECTURE.md:81). No LAUNCH_READY item names it. Policy generation implied in items 22-24 doesn't resolve the TraceAgent wiring. |
| #5 Bird Eye upload UI | Item 3 (self-serve onboarding DoD includes "first-doc upload") — **implied** | PARTIALLY COVERED. Upload is part of the onboarding DoD but not named explicitly. ARCHITECTURE.md task #5 notes no frontend upload form exists; if that's wrong (bird_talk.html has one), this is ALIGNED. |
| #6 Load knowledge/ sector defs into prompts | No corresponding item | **MISSING ENTIRELY.** `knowledge/` is entirely unused at runtime (ARCHITECTURE.md:179). Not in LAUNCH_READY. |
| #7 Sync gap_engine CONTROL_REGISTRY with frameworks/*.json | No corresponding item | **MISSING ENTIRELY.** Two diverging registries exist (ARCHITECTURE.md:177). Affects items 22-24 (launch frameworks DoD). No item covers this. |
| #8 Expose /pipeline/analyze + Smart Scan | No corresponding item | **MISSING ENTIRELY.** `/pipeline/analyze` calls a Go service not in the repo or Dockerfile — any call to this route will 500 in production (ARCHITECTURE.md:238). Not in LAUNCH_READY. |

**Additional gaps — LAUNCH_READY items with no ARCH precedent (new build work):**
- Items 4, 5 (auth, secrets): infra items, new work
- Item 6 (Stripe): 0 code — entirely new build
- Items 7-13 (PM layer: tasks, SME workspace, email, invite flow): 0 code — entirely new product
- Items 14-17 (GRC Card, Excel import, distribution, PDF export): 0 code — entirely new product
- Items 18-21 (polish, status page, docs, landing page): new work

### The gap

ASPIRATIONAL-AT-LAUNCH for 6 of 8 ARCH wiring tasks. ARCH tasks #2 (studio lanes), #3
(template_engine), #4 (TraceAgent route), #6 (knowledge/), #7 (control registry), #8
(analyze/Go) are not covered by any LAUNCH_READY item. The launch scope as written assumes
the wiring backlog is handled by implication in the framework DoDs. It is not. These tasks
need their own explicit LAUNCH_READY items, or the launch framework DoDs (items 22-24) will
fail.

**Smallest action:** Add 5 missing LAUNCH_READY items for ARCH tasks #2, #3, #4, #7, #8
(task #6 is optional; knowledge/ improves output quality but isn't a DoD blocker). Each item
needs a definition of done that matches the ARCHITECTURE.md task description.

---

## Audit 3 — Product Principles vs Codebase State

### What the docs claim

MULTI_TENANT_SPEC §0 and STRATEGY §XIII list 7 principles. Principle 7 (visibility over
productivity) is the override.

### What the code shows

| Principle | Code state | Classification |
|---|---|---|
| 1. Self-serve | `main.py:837` → 307 redirect back to signup. Onboarding wizard = 0 code. Self-serve signup works; everything after signup is broken. | NOT HONORED |
| 2. Always online | `ARCHITECTURE.md:190`: Voyage AI key absent from `config.py` Settings and not in `.env.example`. Canary deploy in ops config (per deploys.log) exists. The claim holds for deploy discipline but the missing Voyage AI key would cause Bird Eye to fail silently. | PARTIALLY HONORED |
| 3. Framework-led expansion | `frameworks/*.json` exist with control definitions. BUT `gap_engine.py` never reads them — it has a hardcoded `CONTROL_REGISTRY` (ARCHITECTURE.md:177). Adding a framework requires a code change to gap_engine, not a data addition. | ASPIRATIONAL-AT-LAUNCH |
| 4. Demo-free / Stripe at every tier | 0 Stripe imports, 0 billing code anywhere in `backend/`. Not in any route, any config, any dependency. | ASPIRATIONAL-AT-LAUNCH |
| 5. Build upward | No code test; architectural posture. | N/A |
| 6. Everything done before launch | Meta-principle. | N/A |
| 7. Visibility over productivity (OVERRIDE) | Shipped Bird Eye scan = productivity (finds problems, returns a list). No Wedge UI surfaces ranked next-actions (visibility). GRC Card distribution = visibility, but 0 code. Audit log for chain-of-custody = visibility, but LAUNCH_READY item 13 is not yet built. All shipped features today are productivity-tier. The override isn't yet honored by any shipped artifact. | ASPIRATIONAL-AT-LAUNCH |

### The gap

Principles 1, 3, 4, and 7 (the override) are all aspirational at launch. The most significant:
Stripe (principle 4) has zero code — the Demo-free principle requires a complete payment
infrastructure build. Framework-led expansion (principle 3) requires refactoring gap_engine to
read from `frameworks/*.json` instead of its hardcoded registry. The override principle (7) is
unachievable until the Wedge UI and GRC Card distribution exist.

---

## Audit 4 — ILWAO Sales Demo vs Demo Surface

### What the docs claim

STRATEGY §IX describes a 15-minute demo: upload a doc (Input, 2 min), show Bird Eye findings
(Logic, 2 min), show prioritized next-action list (Wedge, 2 min), show Trace Agent generating
a fix (Automate, 2 min), show GRC Card (Output, 2 min).

### What the code shows

- **Stage 1 — Input (upload):** Bird Eye backend is wired. `bird_talk.html` is identified as
  the Bird Eye UI (ARCHITECTURE.md:15). Whether it has an upload form or not determines
  whether stage 1 is demoable. ARCHITECTURE.md task #5 flags this as missing; the spec assumes
  it exists. Uncertain.

- **Stage 2 — Logic (Bird Eye findings):** If stage 1 works, stage 2 works. The detectors
  are fully wired and produce real findings.

- **Stage 3 — Wedge (prioritized next-action list):** The gap route returns empty lists for
  fresh tenants (ARCHITECTURE.md:50). If a policy library exists, gap_engine sorts by
  severity, but no UI surfaces "here's what to fix first" — the sorted list goes into a
  `GapsResponse` that is never displayed as a prioritized action list in the dashboard.
  **Stage 3 breaks the demo** for any tenant without a pre-existing policy library.

- **Stage 4 — Automate (Trace Agent generation):** trace_agent.py has no HTTP route
  (ARCHITECTURE.md:81). `generation_intake` has no writer. **Stage 4 is not executable.**
  The only reachable generation path is `POST /pipeline/create/generate`, which is the direct
  LLM path, not the Trace Agent. A demo can show policy generation but cannot show the
  Trace Agent specifically.

- **Stage 5 — Output (GRC Card):** The GRC Summary tab renders a form + mock output.
  Not a live analytics surface. If the demo shows the GRC Summary generation form, it reads
  as a tool, not a product artifact. The GRC Card as described in §XII does not exist to show.

### The gap

ASPIRATIONAL-AT-LAUNCH. The §IX demo breaks at stage 3 (Wedge is not surfaced for any
realistic demo prospect) and is blocked at stage 4 (Trace Agent has no HTTP entry point).
A partial demo of stages 1-2 (upload + Bird Eye findings) is the only fully demoable
sequence today.

**Smallest action to get to a 3-stage demo:** Wire the gap route to surface the severity-sorted
output and add a "top priority" indicator to the top finding. That makes stage 3 real. Stage 4
requires ARCH task #4 (half day + 1 day UI).

---

## Audit 5 — GRC Card Reality Check

### What the docs claim

STRATEGY §XII: GRC Card is a live summary artifact — framework coverage %, policy library
health, Bird Eye findings, audit calendar, pending SME work, recent activity. Distribution:
configurable cadence, HTML email + PDF attachment + Midnight watermark. Drives retention,
creates monthly brand exposure.

LAUNCH_READY item 14: GRC Card replaces the current dashboard as the primary view. DoD
requires live metrics from gap_engine, findings count from Bird Eye, pending task count from
PM layer.

### What the code shows

- `midnight_dashboard.html:2067-2108` — GRC Summary tab: form inputs (org name, industry,
  framework checkboxes), a generate button, a progress bar, an output text area, a download
  PDF button. This is a document generation form, not a live analytics surface.

- `POST /pipeline/grc-summary` in `routes.py` — returns mock framework data, no real gap
  computation (ARCHITECTURE.md:49).

- `dashboard.py` — `/dashboard/overview`, `/dashboard/gaps`, `/dashboard/documents` return
  live Supabase data. These are overview cards, not a GRC Card artifact.

- Email distribution: 0 code — no email send, no cadence configuration, no distro list
  anywhere in the repo.

- PDF attachment for GRC Card: 0 code. A PDF renderer exists for policy .docx files
  (`pdf_renderer.py`) but is not connected to any GRC Card concept.

- Midnight watermark: exists for trial-plan policy exports (`routes.py:2295`) only.

### The gap

DOC DRIFT. The GRC Card described in STRATEGY §XII is entirely aspirational. No artifact in
the codebase today fulfills the description. What exists is a generation form (GRC Summary)
that returns mock output. The distribution mechanic (email, PDF, cadence, watermark) is
zero code.

LAUNCH_READY item 14's DoD depends on:
1. gap_engine wiring (ARCH task #1, currently conditional/empty)
2. PM layer task count (LAUNCH_READY items 7-13, currently 0 code)
3. Bird Eye findings surfaced in a summary view (Bird Eye data exists; new UI component needed)
4. Email/distribution infrastructure (0 code)

Item 14 as written requires 4 upstream items to complete first. This dependency chain is not
visible in LAUNCH_READY as currently structured.

**Smallest action:** Add a note to LAUNCH_READY item 14 that it depends on items 1 (multi-
tenant correctness), the gap_engine wiring task (currently missing from LAUNCH_READY), and
items 7-13 (PM layer). This makes the sequencing visible before building starts.

---

## Audit 6 — Pricing vs Enforcement

### What the docs claim

STRATEGY §XV: 5-tier pricing (Free → Starter $495/mo → Professional $1,245/mo → Team
$2,995/mo → Enterprise $75K+). SME seats free at all paid tiers. Self-serve Stripe at every
tier.

### What the code shows

- `plan_type` column exists on `tenants` table (ARCHITECTURE.md:130 confirms).
- `verify_access()` enforces for `plan_type == "trial"`:
  - 1-user cap (`main.py:267-273`, `main.py:369-375`)
  - 3-upload limit (`routes.py:203-204`)
  - 1-framework limit (`routes.py:212-221`)
  - Trial watermark on exports (`routes.py:2295`, `2384`, `2522`, `2579`)
- **No plan_type checks exist for any non-trial tier.** Starter, Professional, Team, and
  Enterprise are not differentiated in code. Upgrading from trial to any paid tier would
  remove trial limits but apply no paid-tier-specific behavior.
- **0 Stripe code** anywhere in `backend/`. No checkout, no subscription management, no
  billing endpoint, no webhook handler.
- SME seat management (free seats at paid tiers): 0 code. The 1-user trial cap is the only
  seat logic that exists.

### The gap

ASPIRATIONAL-AT-LAUNCH. The trial enforcement layer is real and solid. The paid pricing model
has no code. A user who upgrades from trial to Starter (hypothetically, since there's no
Stripe checkout to enable this) would experience the same product as a trial user, minus
the trial limits.

LAUNCH_READY item 6 (Stripe checkout end-to-end) is the correct fix. It's listed but has
zero code to build on — it's a full implementation task, not a wiring task.

---

## Audit 7 — Open Bugs from Memory vs LAUNCH_READY Coverage

### What the docs claim

Memory from prior sessions listed three unfixed bugs:
1. Markdown symbol bleed in policy output
2. Hardcoded TOOL_PASSWORD auth
3. Dashboard still running on mock data

LAUNCH_READY items 4 (real auth) and 14 (GRC Card live metrics) were understood to cover
bugs 2 and 3 respectively.

### What the code shows

**Bug 1 — Markdown symbol bleed.** The explore agent found `backend/agents/docx_renderer.py`
with an `_split_inline()` function that parses inline markdown (`**bold**`, `*italic*`, `#heading`)
and converts it to Word formatting. Markdown markers are stripped and replaced with docx runs.
The bleed bug appears to be addressed in the docx output path. The memory note may refer to a
prior state or a different output surface (e.g., markdown in Bird Talk responses, or in policy
metadata displayed in the dashboard, rather than in .docx output). **Status: likely resolved
in docx path; no explicit LAUNCH_READY item covers it.** If it recurs, no DoD will catch it.

**Bug 2 — TOOL_PASSWORD.** The explore agent searched `backend/` and found no occurrences.
ARCHITECTURE.md does not mention it. The memory note may be stale, or the variable was named
differently in a prior version. LAUNCH_READY item 4's DoD (`grep -r "TOOL_PASSWORD" backend/`)
would pass today. **Status: not found in current codebase — memory appears stale.**

**Bug 3 — Dashboard on mock data.** The explore agent found that `dashboard.py` endpoints
(`/dashboard/overview`, `/dashboard/gaps`, `/dashboard/documents`) all issue live Supabase
queries. However, `/pipeline/grc-summary` returns mock framework data (ARCHITECTURE.md:49).
The memory note likely referred specifically to the GRC Summary output, which is still mock.
LAUNCH_READY item 14 (GRC Card live metrics) does cover this: its DoD requires live gap
data, live findings count, live task count. **Status: partially stale — main dashboard is
live DB; GRC Summary is still mock. Item 14 is the correct fix.**

### Coverage summary

| Bug | Covered by LAUNCH_READY? | Notes |
|---|---|---|
| Markdown symbol bleed | No explicit item | Appears resolved in docx path. If it recurs in another output surface, no DoD will catch it. Consider adding a note to items 22-24 DoDs to verify no markdown in generated artifacts. |
| TOOL_PASSWORD | Item 4 (Real auth) | Bug not found in codebase — memory stale. Item 4 DoD (`grep`) would pass today. |
| Dashboard mock data | Item 14 (GRC Card) | GRC Summary still mock. Item 14 resolves this but depends on multiple upstream builds. |

---

## Summary

| Audit area | Gap classification | Action required |
|---|---|---|
| 1. ILWAO — Input stage | ASPIRATIONAL-AT-LAUNCH | Onboarding wizard + SME system (new build) |
| 1. ILWAO — Logic stage | ALIGNED (with caveat) | Wire gap_engine unconditionally |
| 1. ILWAO — Wedge stage | ASPIRATIONAL-AT-LAUNCH | Surface sorted gap output as prioritized list in UI |
| 1. ILWAO — Automate stage | NOT YET WIRED | TraceAgent HTTP route + generation_intake writer (ARCH task #4) |
| 1. ILWAO — Output (GRC Card) | DOC DRIFT | GRC Card doesn't exist; GRC Summary is a generation form |
| 1. Undocumented agents | CODE DRIFT | Update STRATEGY §V to include Migration, BirdSong, SmartScan; remove or wire PolicyAgent |
| 2. LAUNCH_READY vs ARCH tasks | MISSING ITEMS | Add 5 missing LAUNCH_READY items for ARCH tasks #2, #3, #4, #7, #8 |
| 3. Principle 1 (self-serve) | NOT HONORED | Onboarding wizard |
| 3. Principle 2 (always online) | PARTIALLY HONORED | Voyage AI key absent from config.py + .env.example |
| 3. Principle 3 (framework-led) | ASPIRATIONAL-AT-LAUNCH | Refactor gap_engine to read frameworks/*.json |
| 3. Principle 4 (demo-free/Stripe) | ASPIRATIONAL-AT-LAUNCH | Complete Stripe integration (new build) |
| 3. Principle 7 (visibility override) | ASPIRATIONAL-AT-LAUNCH | Wedge UI + GRC Card distribution (both new build) |
| 4. ILWAO demo surface | ASPIRATIONAL-AT-LAUNCH | Demo breaks at stage 3 (Wedge) and is blocked at stage 4 (Trace Agent) |
| 5. GRC Card | DOC DRIFT | Described as live analytics artifact; code has a generation form with mock output |
| 6. Pricing enforcement | ASPIRATIONAL-AT-LAUNCH | Trial tier is enforced; paid tiers have no code; Stripe = 0 code |
| 7. Markdown bleed bug | LIKELY RESOLVED | No explicit LAUNCH_READY coverage; consider adding to framework DoDs |
| 7. TOOL_PASSWORD bug | NOT IN CODEBASE | Memory stale; LAUNCH_READY item 4 DoD passes today |
| 7. Dashboard mock data | PARTIALLY STALE | Main dashboard is live DB; GRC Summary still mock |

---

## Critical gaps not in any doc

These exist in ARCHITECTURE.md but appear in no strategic doc:

1. **`generation_intake` has no writer** (ARCHITECTURE.md:140). TraceAgent step 1 reads this
   table. Nothing in the repo writes to it. Even after wiring an HTTP route, TraceAgent will
   fail at step 1 until an intake writer is built. This is not surfaced in LAUNCH_READY.

2. **Go service not in repo** (ARCHITECTURE.md:238). `POST /pipeline/analyze` calls
   `GO_SERVICE_URL/analyze`. The Go service is not in the repo, not in the Dockerfile, and
   not deployed. Any call to this route will 500 in production. Not addressed in LAUNCH_READY.
   Smallest action: replace `_go_framework_coverage()` with a Python-only implementation,
   or remove the route until the Go service is in scope.

3. **Voyage AI key missing from config** (ARCHITECTURE.md:190). `bird_eye/embeddings.py`
   requires a Voyage AI API key. It is absent from `config.py` Settings and from
   `.env.example`. Bird Eye ingestion (and therefore the entire document analysis path) will
   fail silently at runtime if the key is not injected. Not covered by LAUNCH_READY item 5
   (which focuses on Anthropic/Supabase keys). Should be added to item 5's DoD.

4. **midnight-template-build is outside the repo** (ARCHITECTURE.md:146). 36 professional
   `.docx` templates live at `/c/Users/bword/Documents/midnight-template-build/`. The path
   is hardcoded. These templates can't be used in ECS without a repo inclusion strategy.
   Not addressed in LAUNCH_READY or STRATEGY.

---

*Audit produced: 2026-05-23. Read-only. No files modified.*
*Sources: ARCHITECTURE.md (2026-05-21), codebase state at HEAD (master, 3af1d7c + prior).*
