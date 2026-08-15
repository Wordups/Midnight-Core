# Midnight Core — Architecture

For the maintained, current-state architecture reference, see
[`../CLAUDE.md`](../CLAUDE.md)'s Architecture section — it's kept in sync with
the code and is what Claude Code sessions actually work from. This file is a
short pointer, not a duplicate, so the two can't drift apart again.

## Pipeline (current)

upload/generate → framework-map → gap-analyze → render → store

- **Bird Eye** (`backend/bird_eye/`) ingests uploaded documents, embeds them,
  and runs detectors (conflicts, duplicates, gaps, orphans, stale governance).
- **Create Studio** (`backend/api/routes.py::create_generate`) generates new
  documents via `backend/core/master_template.py` + `template_voice.py` +
  `template_engine.py` — python-docx based, no external subprocess.
- **Framework mapping** (`backend/core/framework_mapper.py`) and the **gap
  engine** (`backend/core/gap_engine.py`, deterministic, no AI) compute
  coverage against `frameworks/*.json`.
- **Corpus** (`backend/core/corpus.py`) answers questionnaires from the
  document corpus with citations, fail-closed on missing evidence.

## Layers

- **api/** — FastAPI routes (pipeline + dashboard + integrations)
- **core/** — pure engine logic, no template or API concerns
- **agents/** — AI agents (policy, cleaner, evidence, framework-mapping, etc.), see `backend/agents/README.md`
- **renderers/** — docx + pdf output
- **templates/** — modular template packs
- **storage/** — file handling + Supabase client

## Rules

1. No template logic inside core engine files
2. No company-specific content ever enters this repo
3. Every output is a draft — nothing is "compliant"
4. Validate in 2.0, productize in Core
