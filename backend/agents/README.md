# Agents

Each module under `backend/agents/` exposes a single agent class plus its
schemas. All inherit `BaseAgent` (in `base.py`); concrete agents either follow
the `_run(data)` contract (input → output) or, for orchestrators, override
`run()` with a domain-specific signature (see Trace Agent below).

## Trace Agent

`backend/agents/trace_agent.py`. Batch-intake orchestrator that turns a
populated `generation_intake` row into an audit-ready `.docx` plus a
`process_trace.md` rationale file.

### When to use it

- You have a fully-populated intake row (deliverable type, audience, framework
  spine, scope, business context, declared assumptions, approval timestamp).
- No live user interaction during the run — Trace Agent doesn't ask
  clarifying questions.
- You need an auditor-readable record of every decision the agent made.

### How to invoke it

```python
from backend.agents.trace_agent import TraceAgent

result = TraceAgent().run(intake_id="3c7…")    # UUID of a generation_intake row
# result.status      -> 'complete' | 'draft' | 'failed'
# result.docx_path   -> filesystem path to the rendered .docx
# result.trace_path  -> filesystem path to process_trace.md
# result.activity_log_ids -> the 16 activity_log row IDs written for this run
```

Pass an explicit `output_dir` if you want artifacts written somewhere
specific (the e2e test does this with a tempdir):

```python
TraceAgent(output_dir="/var/lib/midnight/runs/2026-05-18/").run(intake_id)
```

### The 16-step loop

The loop is fixed. Reordering changes the trace contract auditors rely on.
Each step writes exactly one row to `activity_log` with a populated
`rationale` column.

| # | Step | What it does |
|---:|------|--------------|
| 1 | `load_intake` | `SELECT * FROM generation_intake WHERE id = …` (service-role read). |
| 2 | `plan` | Build the internal task list for the rest of the run. |
| 3 | `derive_questions` | **Batched mode: skipped.** Logged as "batched" so the row count stays 16. |
| 4 | `load_answers` | **Batched mode: skipped.** Answers live inside the intake row itself. |
| 5 | `freeze_assumptions` | Snapshot `scope_boundary` + `business_context` + `declared_assumptions` into an immutable `assumption_set`. Downstream LLM calls only see this. |
| 6 | `load_skill` | Load docx generation conventions — the rules the LLM must follow when building the spec. |
| 7 | `outline` | Look up `templates/outlines/{deliverable_type}_{framework}.yaml`. If present, use it (`outline_source: "template"`). Otherwise call Claude to generate the outline (`outline_source: "llm_fallback"`). |
| 8 | `build_script` | Call Claude with the outline + assumption set + skill conventions. Output is a structured JSON spec — **not** docx-js code — that the Node subprocess will render. |
| 9 | `generate` | Pipe the spec into `node build_docx.js <output_path>`. The Node side uses docx-js (`docx` npm v9.x) to produce a native Word file. No markdown intermediate, no python-docx. |
| 10 | `validate_schema` | Open the .docx as a zip, confirm OOXML parts and that `word/document.xml` parses with non-empty body. |
| 11 | `spot_check` | Extract text via `docx2txt` and confirm every outline-section heading is present. |
| 12 | `repair` | If 10 or 11 failed, compose a feedback string (schema error + spot-checker missing-section list) for the next attempt. |
| 13 | `rerun` | Loop 9→10→11→12 with the repair feedback baked into the next `build_script` call. Bounded to 3 total attempts. |
| 14 | `write_trace` | Write `<docx_stem>_process_trace.md` next to the .docx with the 16-step trace, validation history, and final status. |
| 15 | `verify_artifacts` | Both files exist, both non-zero. |
| 16 | `return` | Return `GenerationResult` to the caller. |

### Outputs

```python
class GenerationResult(BaseModel):
    intake_id: str
    policy_id: Optional[str]
    status: str               # 'complete' | 'draft' | 'failed'
    docx_path: Optional[str]
    trace_path: Optional[str]
    outline_source: Optional[str]   # 'template' | 'llm_fallback'
    activity_log_ids: list[str]     # 16 row IDs
    repair_attempts: int            # 0 if first attempt passed
    error: Optional[str]            # populated when status != 'complete'
```

### Failure semantics

- `status = "complete"` — first attempt or a repair pass converged; both
  validators clean; both artifacts present.
- `status = "draft"` — 3 attempts exhausted without a clean pass, **or** one
  of the artifacts came back zero-bytes. The .docx and the trace still exist
  on disk; the trace's "Final failure reason" section explains what broke.
- `status = "failed"` — an unhandled exception bubbled up before the loop
  could complete the artifact-writing steps. `result.error` carries the
  exception class + message.

The agent never silently succeeds — every step writes its `rationale` to
`activity_log`, and a `draft` status surfaces the failure reason in both
the trace markdown and the API return value.

### Adding a new template outline

1. Drop a YAML file in `backend/agents/templates/outlines/` named
   `<deliverable_type>_<primary_framework>.yaml`.
2. The file must define `deliverable_type`, `framework`, `title`,
   `description`, and a non-empty `sections` list with `id`, `heading`,
   and `purpose` per section.
3. No code changes needed. `_load_outline` picks it up by filename.

If no template matches, Trace Agent calls Claude to produce one and logs
`outline_source: "llm_fallback"` in the trace.

### Operational notes

- The agent writes to `activity_log` using the `service_role` Supabase key
  (RLS bypass). Tenants can read their own rows because RLS still applies on
  the SELECT side.
- The classifier in `backend/api/agent_ops.py:_classify_action` does not
  currently route `trace_step_*` actions to a dashboard slot — those events
  fall through to `signal_manager` until a `trace_agent` slot is added. This
  is intentional in the first PR; a separate PR adds the dashboard surface.
- The docx-js subprocess is bounded by a 60-second timeout per generation.
  Token-heavy LLM responses can push `build_script` to ~30s on its own; total
  run time for a clean first-pass is typically 45–90s.

### Running tests locally

The e2e test requires:

- `TEST_TENANT_ID` and `ANTHROPIC_API_KEY` populated in `.env` (project root).
- The migration in `supabase/migrations/20260518_trace_agent_intake_and_activity_log.sql`
  applied to your Supabase instance via the SQL Editor — there's no REST DDL
  path. The test's `_prereq_check` fixture skips with a clear message if the
  migration hasn't been applied.
- Python deps installed: `docx2txt`, `PyYAML` (already in
  `backend/requirements.txt`; install via
  `pip install -r backend/requirements.txt` if you spin up a fresh venv).
- Node 20.x + the `docx` npm package installed in
  `backend/agents/generators/node_modules/` (the generator auto-runs
  `npm install` on first invocation if missing).

A single test run costs ~$0.10–0.20 in Anthropic API usage and takes 60–120s
of wallclock.

### Windows dev gotcha (subprocess encoding)

`backend/agents/generators/docx_generator.py` pins
`subprocess.run(..., encoding="utf-8")` when piping the JSON spec into the
Node docx-js subprocess. Without that explicit pin, `subprocess.run` uses
`locale.getpreferredencoding(False)` — which on Windows defaults to
**cp1252**. Node reads stdin as UTF-8, so any non-ASCII character in the
spec (em-dash, en-dash, smart quotes, ...) ends up as U+FFFD (REPLACEMENT
CHARACTER) in the generated .docx because cp1252's byte sequence isn't valid
UTF-8. The spot-checker then fails to match outline headings, and the agent
returns `status="draft"` instead of `"complete"`.

The fix is in place; do not remove the `encoding="utf-8"` argument. The
spot-checker also normalizes U+FFFD to em-dash as a second line of defense.

**Linux/Docker is the source of truth.** Local Windows e2e results have
historically diverged from prod on this exact I/O boundary (Linux's locale
defaults to UTF-8, so the bug was invisible there). When a Windows dev run
disagrees with a Linux/prod run, trust the Linux/prod result and look for
locale-sensitive I/O in the diff.
