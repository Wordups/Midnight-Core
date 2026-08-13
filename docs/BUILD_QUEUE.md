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

- [ ] **Run rows report the model that actually answered.** `corpus_runs.model`
  stores the configured Anthropic model name even when the provider switch
  routes to Groq/Ollama. Thread the true model (from the provider response)
  into the run row and the API response. Small; add a test.

- [ ] **Overview view: posture first.** The Overview hero currently pushes
  Migrate/Create/Bird Talk. Make compliance posture the hero (documents,
  controls covered, framework coverage, open gaps — data already served for
  the corpus view) with the corpus/questionnaire flow as the primary CTA;
  demote the Migrate card. Frontend-only.

- [ ] **Session refresh for long operations.** Supabase JWTs expire (~1h);
  a long dashboard session dies mid-upload or mid-run with a 401 and the UI
  loses work. Frontend: on 401 from an API call, attempt one silent
  re-auth/redirect-to-login that preserves the corpus view state (stash the
  questionnaire text in sessionStorage before redirect, restore after).

- [ ] **Questionnaire file upload.** The runner accepts pasted text only.
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
