# Midnight Build Queue

Worked by the nightly build agent: **top-most unchecked item only, one per
night**, implemented with tests, delivered as a PR against `master`. Never
push `master` directly. Check the box in the PR branch as part of the PR.
The owner reorders this file to reprioritize; the agent never reorders it.

## Queue

- [x] **Embed generated documents' sections.** Only Bird Eye uploads get
  embeddings today; Studio-generated documents are invisible to the corpus
  answer engine's retrieval. In the create/generate path, embed saved
  sections with the existing `bird_eye.embeddings.embed_chunks` (one batched
  call, `input_type="document"`) and persist to `policy_sections.embedding`,
  soft-failing like ingestion does. Tests: generated doc sections carry
  embeddings; retrieval finds them.

- [x] **"Draft the missing policy" button on unresolved answers.** In the
  Compliance Corpus answer table, rows with status `insufficient_evidence`
  or `partially_satisfied` get a button linking to Create Studio pre-filled:
  doc type inferred from the question, tenant frameworks, description seeded
  from the question + the engine's `followup_question`. Frontend:
  `midnight_dashboard.html` + `create_studio.js` (accept prefill query
  params). No backend change expected.

- [x] **CI: run the test suite on push.** Extend `.github/workflows/` with a
  workflow that installs `backend/requirements.txt` on Python 3.12 and runs
  `pytest tests/ --ignore=tests/test_tenant_isolation.py
  --ignore=tests/test_document_isolation.py` (those two need live Supabase).
  Stub required env vars the way tests/test_birdsong.py does.

- [x] **Run rows report the model that actually answered.** `corpus_runs.model`
  stores the configured Anthropic model name even when the provider switch
  routes to Groq/Ollama. Thread the true model (from the provider response)
  into the run row and the API response. Small; add a test.

- [x] **Overview view: posture first.** The Overview hero currently pushes
  Migrate/Create/Bird Talk. Make compliance posture the hero (documents,
  controls covered, framework coverage, open gaps — data already served for
  the corpus view) with the corpus/questionnaire flow as the primary CTA;
  demote the Migrate card. Frontend-only.

- [x] **Session refresh for long operations.** Supabase JWTs expire (~1h);
  a long dashboard session dies mid-upload or mid-run with a 401 and the UI
  loses work. Frontend: on 401 from an API call, attempt one silent
  re-auth/redirect-to-login that preserves the corpus view state (stash the
  questionnaire text in sessionStorage before redirect, restore after).

- [x] **Questionnaire file upload.** The runner accepts pasted text only.
  Accept .csv/.xlsx uploads of questionnaires (one question per row, common
  SIG/CAIQ-style layouts): parse client-side or via a small endpoint reusing
  `split_questionnaire` semantics; feed the same answer pipeline. Cap at the
  existing MAX_QUESTIONS.

## Rules for the agent

- One item per night. If the suite fails on your change set, fix or revert —
  never open a red PR.
- If the top item already has an open PR (branch `queue/<slug>` exists on
  origin), take the next unchecked item instead.
- Branch naming: `queue/<short-slug>`. PR body: what changed, how it was
  tested, and any scope you deliberately left out.
- Respect existing patterns: provider layer for all LLM calls, tenant_id on
  every query, fail-closed error handling, tests alongside code.

- [ ] **Template picker shows preview images.** The packs ship preview PNGs
  (backend/templates/packs/<cat>/<variant>/*_preview.png). Serve them and
  render thumbnails in the Studio "Template style" picker so choosing a
  variant is visual. Frontend + one static route if needed.

- [ ] **Un-gate lanes whose templates now exist.** Process Flow, Training,
  Audit Package, AI Governance have shells but no DOC_TYPE_SLOT_SPECS.
  Add slot specs for ONE lane (Audit Package first), add it to LIVE_LANES +
  LIVE_CREATE_LANES, verify preview/generate end-to-end with tests. One lane
  per night.

- [ ] **Brand logo renders in document headers.** tenants.brand_logo_url is
  stored but never rendered (brand color now is). In template_engine
  apply_branding: fetch the logo (timeout 5s, fail-open), insert into the
  shell's header at a sane width (~1.2in). Test with a stub image.

- [ ] **Wire Evidence + ExecutiveSummary agents to the UI.** Both are
  implemented and in the agent catalog with zero triggers. Add a "Generate
  executive summary" action on the GRC Summary view and an evidence panel
  entry point; route through the existing agent_ops endpoints. Tests for the
  routes if any are missing.

- [ ] **PM layer UI, phase 1 — Requests inbox.** backend/api/pm.py is a full
  request/task state machine (open -> in_review -> complete) with SME
  invites; no frontend. Add a "Requests" dashboard view: list, status
  chips, transition buttons, invite-SME form, calling the existing API only.
  No backend changes.

- [ ] **PM layer UI, phase 2 — assign a refusal to a human.** On
  insufficient_evidence corpus answers, next to "Draft the missing policy"
  add "Assign to reviewer": creates a request via the PM API pre-filled with
  the question + follow-up. Depends on the Requests inbox (previous item).

- [ ] **Decide TraceAgent: wire or delete.** 725 lines with no route and no
  generation_intake writer. If wiring: a minimal POST intake route + run
  trigger behind verify_access. If deleting: remove agent + test + table
  migration note. OWNER DECISION — skip this item and take the next one
  until the queue says otherwise.
