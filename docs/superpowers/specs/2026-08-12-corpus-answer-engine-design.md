# Corpus + Answer Engine — Design

**Date:** 2026-08-12 · **Branch:** `launch-blitz` · **Status:** approved by owner

## Purpose

Make the resume claim true in code: a **structured compliance corpus** built from
Midnight's existing ingestion (Bird Eye), standardization (Create Studio), and
control mapping (174-control registry + gap engine), served for four use cases:
audits, security questionnaires, vendor assessments, and internal security
requests. One mechanism serves all four; `use_case` is a stored label.

Interview honesty rule: this is new, dated pivot work. Never present it as part
of v1.

## What exists (verified)

- `policies` table holds both generated and uploaded docs; `covered_control_ids`
  populated by generation and AI processing (`file_store.py:842`).
- `policy_sections` holds chunks with 1024-dim voyage-3 embeddings
  (`ingestion.py:519`); similarity is local cosine (`detectors.py:157`).
- Control registry: `gap_engine.load_control_registry()` — 174 controls
  (61 SOC 2, 20 HIPAA, 93 ISO 27001:2022), 4 equivalence groups, severity per
  control. Say "across", not "mapped across" (18 controls cross-walked).
- Strict-JSON LLM parsing: `backend/core/json_parser.parse_model_json` —
  fail-closed pattern used by `assessments.py` and `metadata_llm.py`.
- Auth: routers registered in `main.py` with `Depends(verify_access)`.
- Tenant scoping: `bird_eye.db` insert/update/delete require `tenant_id`.
- Plan fencing: `_enforce_plan_limits` + `billing_plans` feature flags.

## Components

### 1. `backend/core/corpus.py` (pure logic, no HTTP)

- `build_corpus_index(tenant_id) -> CorpusIndex`
  Deterministic. Every policy row × its `covered_control_ids` × registry lookup
  (framework, severity, equivalents) × freshness (`last_reviewed`/`updated_at`
  vs. review window; stale = > 365 days). Roll-ups: coverage % per framework,
  stale count, unmapped-document list. No LLM.
- `split_questionnaire(raw_text) -> list[str]`
  Deterministic splitter: numbered lists, bullets, one-question-per-line.
  Cap: 50 questions per run (413 above).
- `answer_question(tenant_id, question) -> Answer`
  1. Embed question with voyage `input_type="query"`.
  2. Cosine over the tenant's `policy_sections` in Python; top-k = 6,
     similarity floor 0.35.
  3. **Zero retrieved sections → status `insufficient_evidence`, no LLM call.**
  4. One constrained Claude call: question + retrieved sections + candidate
     control IDs in; strict JSON out:
     `{status: satisfied|partially_satisfied|not_satisfied|
       insufficient_evidence|not_applicable, answer_text,
       citations: [{policy_id, policy_name, section_heading, quote}],
       control_ids: [...], confidence: high|medium|low,
       followup_question: str|null}`
     Status vocabulary follows the assessment-outcome states in
     `knowledge/vendor_risk_process_spec.md`; `followup_question` is the
     targeted follow-up the model recommends when evidence is insufficient
     or partial ("challenge vague responses"). System prompt embeds the
     spec's core instruction: assess against requirements, cite evidence,
     never fabricate, defer consequential judgment to humans.
  5. Parse via `parse_model_json`; any parse/validation failure →
     `insufficient_evidence` (fail-closed).
  6. Citation validation: `quote` must be a substring of a retrieved section's
     text (whitespace-normalized). Invalid citations are stripped; if any were
     stripped, confidence is downgraded one level.

### 2. `backend/api/corpus.py` — router `/api/v1/corpus`

Registered in `main.py` with `Depends(verify_access)`.

- `GET  /api/v1/corpus` — structured index.
- `POST /api/v1/corpus/answer` — body `{questions: [...]}` **or**
  `{raw_text: "..."}` plus
  `use_case: audit|questionnaire|vendor_assessment|internal`.
  Runs questions sequentially, persists run + answers, returns the run.
- `GET  /api/v1/corpus/runs` — run history (tenant-scoped).
- `GET  /api/v1/corpus/runs/{id}` — run detail with answers.
- `GET  /api/v1/corpus/runs/{id}/export` — CSV.

### 3. Persistence — `supabase/migrations/20260812_corpus_runs.sql`

- `corpus_runs`: id, tenant_id, use_case, question_count, answered_count,
  partial_count, unanswerable_count, model, input_tokens, output_tokens,
  created_at.
- `corpus_answers`: id, run_id, tenant_id, question, status, answer_text,
  citations jsonb, control_ids text[], confidence,
  provenance (`ai_assisted|deterministic`), created_at.

Inserts via `bird_eye.db` helpers (tenant_id enforced).

### 4. Dashboard — `#view-corpus` in `frontend/midnight_dashboard.html`

Nav item "Corpus". Top: corpus table (document, type, frameworks, controls
covered, freshness badge) + per-framework coverage bar. Bottom: questionnaire
runner — use-case selector, paste box, Run button → answer table (status badge,
answer text, citation chips expandable to quote, confidence), unanswerable rows
flagged "needs human", run-history dropdown, Export CSV. Plain JS in the
existing view pattern; no new dependencies.

### 5. Plan fence + accounting

- Answer runs fenced like generation: free plan gets a small monthly cap via
  the `_enforce_plan_limits` pattern (activity action `corpus_answered`).
- Every run logs model + token usage into the run row and `activity_log` —
  the per-call LLM accounting the truth audit flagged as missing.

### 6. Error handling

- No corpus (zero documents) → `GET /corpus` returns empty index with
  `document_count: 0`; `POST /answer` → 409 "corpus is empty".
- Voyage/Anthropic outage mid-run → per-question `unanswerable` with
  `provenance: deterministic` note; run completes, never 500s halfway.
- Oversized paste (> 50 questions) → 413 with the count.

### 7. Tests — `tests/test_corpus.py`

- Splitter: numbered, bulleted, line-per-question, mixed, oversized.
- Index math on fixture rows (coverage %, stale detection, unmapped list).
- Fail-closed: mocked LLM returns garbage → `unanswerable`.
- Citation validation: fabricated quote stripped + confidence downgraded.
- Auth: 401 without session on every corpus route.
- Tenant isolation: tenant A cannot read tenant B's runs.

## Build sequence

1. Show pending security-fix diff → commit it on `launch-blitz` (its own commit).
2. Migration + `corpus.py` core with tests.
3. Router + registration with tests.
4. Dashboard view.
5. Plan fence + accounting.

## Out of scope (YAGNI)

Vendor intake/tiering workflow (VENDOR_RISK_EXTENSION stages 1–3+), pgvector
RPC, streaming answers, file-upload questionnaires (paste only), scheduler,
RBAC beyond `verify_access`.
