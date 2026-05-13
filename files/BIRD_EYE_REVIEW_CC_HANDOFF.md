# Bird Eye Review — Claude Code Build Handoff

**For:** Claude Code (Max plan)
**Stack:** FastAPI on AWS, Python, existing Midnight backend
**Build target:** Working v1 in one weekend
**Rule #1:** Multi-tenant isolation is non-negotiable. Every query filtered by `tenant_id`. No exceptions.

---

## Section 1 — What you're building

Bird Eye Review is a document intelligence layer for Midnight. It scans a tenant's policy/procedure/standard/runbook stack and surfaces:

1. **Duplicate content** — semantic overlap between documents
2. **Conflicting controls** — contradicting requirements (e.g. password min = 12 in one doc, 16 in another)
3. **Stale governance** — missing owners, expired review dates, missing version numbers
4. **Framework gaps** — missing framework tags (HIPAA, PCI, NIST, etc.)
5. **Orphaned documents** — policies without linked procedures/runbooks

**It runs when:**
- A user uploads a legacy doc (.docx, .pdf, .md, .txt)
- A user generates a new artifact inside Midnight
- A user manually clicks "Run Bird Eye Review"

**v1 success metric:** A compliance manager uploads a policy, runs Bird Eye, and sees duplicates / stale controls / conflicts / metadata gaps in under 5 minutes.

---

## Section 2 — Build order (do not skip steps)

### Step 1: Schema first
Before any code, write the migration. Two new tables, both tenant-scoped.

```sql
-- documents_index: searchable index of every tenant artifact
CREATE TABLE documents_index (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    artifact_type TEXT NOT NULL,  -- policy, procedure, standard, runbook, risk_assessment, training, vendor
    title TEXT NOT NULL,
    owner TEXT,
    version TEXT,
    last_reviewed_at TIMESTAMPTZ,
    next_review_at TIMESTAMPTZ,
    framework_tags TEXT[],         -- ['HIPAA', 'PCI', 'NIST-CSF']
    source_path TEXT,              -- S3 key or storage ref
    raw_text TEXT NOT NULL,        -- full extracted text
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_docs_tenant ON documents_index(tenant_id);
CREATE INDEX idx_docs_tenant_type ON documents_index(tenant_id, artifact_type);

-- document_chunks: section-level chunks with embeddings
CREATE TABLE document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    document_id UUID NOT NULL REFERENCES documents_index(document_id) ON DELETE CASCADE,
    section_label TEXT,            -- 'Purpose', 'Scope', 'Policy Statements', etc.
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1024),        -- Voyage voyage-3 dimension; adjust if you pick a different provider
    metadata JSONB,                -- {"control_refs": ["AC-2"], "numeric_requirements": {"password_min": 12}}
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_chunks_tenant ON document_chunks(tenant_id);
CREATE INDEX idx_chunks_embed ON document_chunks USING ivfflat (embedding vector_cosine_ops);

-- bird_eye_findings: every detected issue, tenant-scoped
CREATE TABLE bird_eye_findings (
    finding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    run_id UUID NOT NULL,
    document_id UUID,
    related_document_id UUID,
    finding_type TEXT NOT NULL,    -- duplicate, conflict, stale, framework_gap, orphan
    severity TEXT NOT NULL,        -- critical, high, medium, low, info
    summary TEXT NOT NULL,
    recommendation TEXT NOT NULL,
    similarity_score NUMERIC,
    evidence JSONB,                -- supporting data: section refs, exact text, numeric values
    status TEXT DEFAULT 'open',    -- open, dismissed, resolved
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_findings_tenant ON bird_eye_findings(tenant_id);
CREATE INDEX idx_findings_run ON bird_eye_findings(tenant_id, run_id);

-- bird_eye_runs: each invocation
CREATE TABLE bird_eye_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    triggered_by TEXT NOT NULL,    -- upload, generation, manual
    trigger_document_id UUID,
    documents_reviewed INT DEFAULT 0,
    findings_count INT DEFAULT 0,
    status TEXT DEFAULT 'running', -- running, complete, failed
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
CREATE INDEX idx_runs_tenant ON bird_eye_runs(tenant_id);
```

### Step 2: Tenant guard (write this FIRST, before any business logic)

Every Bird Eye function must accept `tenant_id` as the first argument. Write a decorator that enforces it.

```python
from functools import wraps
from fastapi import HTTPException

def tenant_scoped(fn):
    @wraps(fn)
    async def wrapper(tenant_id: str, *args, **kwargs):
        if not tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id required")
        # Validate tenant_id is UUID format
        import uuid
        try:
            uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid tenant_id")
        return await fn(tenant_id, *args, **kwargs)
    return wrapper
```

Every SQL query that hits documents_index, document_chunks, bird_eye_findings, or bird_eye_runs MUST include `WHERE tenant_id = $1`. No raw queries without it. CC: add a test that scans the codebase for SELECT/UPDATE/DELETE statements against these tables and fails CI if any lack a tenant_id filter.

### Step 3: Document ingestion pipeline

Single endpoint, handles all four file types:

```python
POST /bird-eye/ingest
Body: {tenant_id, file: multipart, artifact_type, title}
```

Pipeline:
1. Save raw file to S3 under `tenants/{tenant_id}/uploads/{document_id}/`
2. Extract text:
   - .docx → python-docx (you already have this)
   - .pdf → pypdf or pdfplumber
   - .md/.txt → direct read
3. Detect sections by heading patterns (regex on `^#+\s`, `^[A-Z][A-Z\s]+$`, numbered headings)
4. Extract metadata via Claude Opus 4.5 single call: owner, version, review dates, framework tags, numeric requirements (password length, retention days, etc.)
5. Insert into `documents_index`
6. Chunk by section, embed each chunk, insert into `document_chunks`
7. Trigger Bird Eye run async

### Step 4: Embedding service

Use **Voyage AI `voyage-3`**. Reasons in Section 3 below. Single function:

```python
async def embed_chunks(texts: list[str]) -> list[list[float]]:
    # Voyage API, batch up to 128 chunks
    # Return list of 1024-dim vectors
    pass
```

### Step 5: Detection logic — five detectors

Each detector is a separate function. Each is tenant-scoped. Each writes findings to `bird_eye_findings`.

```python
@tenant_scoped
async def detect_duplicates(tenant_id, run_id, threshold=0.82):
    # pgvector cosine similarity within tenant
    # For each chunk, find top-3 nearest neighbors in same tenant
    # If similarity > threshold AND different document_id → finding
    pass

@tenant_scoped
async def detect_conflicts(tenant_id, run_id):
    # Pull numeric_requirements from metadata across all chunks
    # Group by requirement key (password_min, retention_days, mfa_required)
    # If same key has different values across documents → finding
    pass

@tenant_scoped
async def detect_stale_governance(tenant_id, run_id):
    # Query documents_index where:
    #   owner IS NULL OR
    #   version IS NULL OR
    #   next_review_at < NOW() OR
    #   last_reviewed_at < NOW() - INTERVAL '12 months'
    pass

@tenant_scoped
async def detect_framework_gaps(tenant_id, run_id):
    # For each document, check framework_tags against tenant's declared frameworks (from Bird Talk Q3)
    # If declared framework is HIPAA but doc has no HIPAA tag → flag
    pass

@tenant_scoped
async def detect_orphans(tenant_id, run_id):
    # For each policy, check if any procedure references it (by title match or explicit link)
    # If no linked procedure → orphan finding
    pass
```

### Step 6: Orchestrator

```python
@tenant_scoped
async def run_bird_eye(tenant_id, triggered_by, trigger_document_id=None):
    run = create_run(tenant_id, triggered_by, trigger_document_id)
    try:
        await detect_duplicates(tenant_id, run.run_id)
        await detect_conflicts(tenant_id, run.run_id)
        await detect_stale_governance(tenant_id, run.run_id)
        await detect_framework_gaps(tenant_id, run.run_id)
        await detect_orphans(tenant_id, run.run_id)
        finalize_run(run.run_id, status='complete')
    except Exception as e:
        finalize_run(run.run_id, status='failed')
        raise
    return run.run_id
```

### Step 7: API endpoints

```
POST /bird-eye/runs                  → trigger manual run
GET  /bird-eye/runs/{run_id}         → run status + summary
GET  /bird-eye/findings?run_id=...   → list findings for a run
PATCH /bird-eye/findings/{id}        → dismiss/resolve a finding
GET  /bird-eye/library-summary       → exec summary card data
```

All endpoints extract `tenant_id` from authenticated user session. Never accept tenant_id from request body for read operations.

### Step 8: UI — Bird Eye panel inside Library

One page. Three sections:
- **Top:** Executive summary card (X documents reviewed, Y issues, Z merge opportunities, last run timestamp, "Run Bird Eye Review" button)
- **Middle:** Findings list, grouped by finding_type, sortable by severity. Each finding card shows: type badge, summary, related documents (linkable), recommendation, "Dismiss" / "Resolve" actions
- **Bottom:** Run history (last 10 runs)

No charts. No graphs. Findings are the product.

---

## Section 3 — The embeddings architecture decision

Four candidates. Recommendation: **Voyage AI voyage-3**.

| Provider | Model | Dim | Cost / 1M tokens | Why pick / skip |
|---|---|---|---|---|
| **Voyage AI** | voyage-3 | 1024 | $0.06 | **Pick this.** Best-in-class retrieval quality for legal/compliance text. Cheap. Anthropic-aligned partner. |
| OpenAI | text-embedding-3-large | 3072 | $0.13 | Good but pricier and you're already off OpenAI for generation |
| Anthropic | (no first-party embeddings as of build date) | — | — | N/A — Anthropic doesn't ship embeddings; their docs recommend Voyage |
| Self-hosted | nomic-embed-text via sentence-transformers | 768 | $0 + GPU | Skip for v1. GPU ops on AWS are infra you don't want to own yet. |

**Storage: pgvector on RDS Postgres.**
- You're already on AWS. RDS is one click.
- pgvector handles up to ~1M chunks comfortably with IVFFlat indexing
- No new vendor, no new bill, no new failure mode
- Pinecone/Weaviate are correct at 10M+ chunks. You will not be there in v1. Defer.

**Re-embedding strategy:**
- When a document is updated (regen), DELETE all chunks for that document_id, re-extract sections, re-embed
- Don't try to do diff-based re-embedding in v1. Full re-embed is $0.001 per doc. Not worth the complexity.

**Embedding hygiene:**
- Normalize text before embedding: strip whitespace, lowercase headings, remove page numbers/footers
- Embed at section level, not document level. Whole-document embeddings lose granularity.
- Store `section_label` alongside the embedding so findings can cite "Section 4.2 — Access Control" not "page 7"

---

## Section 4 — Multi-tenant guardrails (CC: write these tests FIRST)

These are the tests that must exist and pass BEFORE Bird Eye ships. CC: write them in `tests/test_tenant_isolation.py` and make them part of the build.

```python
import pytest

# Test 1: Cross-tenant query returns nothing
async def test_no_cross_tenant_findings(client, db):
    tenant_a = await create_tenant_with_policy(name="Tenant A", policy_text="password min 12")
    tenant_b = await create_tenant_with_policy(name="Tenant B", policy_text="password min 16")

    await run_bird_eye(tenant_a.id, triggered_by="manual")
    findings_a = await client.get(f"/bird-eye/findings", headers={"X-Tenant": tenant_a.id})
    findings_b = await client.get(f"/bird-eye/findings", headers={"X-Tenant": tenant_b.id})

    # No tenant_a finding may reference any tenant_b document
    for f in findings_a.json():
        assert f["tenant_id"] == tenant_a.id
        if f.get("related_document_id"):
            doc = await db.fetch_one("SELECT tenant_id FROM documents_index WHERE document_id = $1", f["related_document_id"])
            assert doc["tenant_id"] == tenant_a.id

# Test 2: Embedding similarity search is tenant-bounded
async def test_similarity_search_respects_tenant(db):
    # Insert identical chunks for two tenants
    # Query nearest neighbors from tenant_a's chunk
    # Result set must be empty across tenant_b's identical chunk
    pass

# Test 3: Direct API tenant injection rejected
async def test_cannot_inject_tenant_id_via_body(client, user_a_token):
    # User authenticated as tenant_a tries to POST with body tenant_id=tenant_b
    response = await client.post("/bird-eye/runs",
                                  headers={"Authorization": f"Bearer {user_a_token}"},
                                  json={"tenant_id": "tenant_b_uuid"})
    # Body tenant_id must be ignored — session tenant_id is the source of truth
    run = response.json()
    assert run["tenant_id"] != "tenant_b_uuid"

# Test 4: SQL query audit — no raw SELECT without tenant_id
def test_codebase_has_no_unscoped_queries():
    # Grep for SELECT/UPDATE/DELETE against bird_eye_*, documents_index, document_chunks
    # Fail if any match lacks "tenant_id" in the same statement
    pass

# Test 5: S3 path enforcement
async def test_s3_uploads_isolated_by_tenant(s3_client):
    # Upload as tenant_a
    # Attempt to read from tenants/{tenant_b}/uploads/* with tenant_a's credentials
    # Must 403
    pass
```

**Guard rails beyond tests:**
- Postgres Row-Level Security (RLS) policies on all four Bird Eye tables. Enable RLS even though application code also filters — defense in depth.
- IAM policy on S3: tenant uploads go to `s3://midnight-tenants/{tenant_id}/...` with bucket policies that enforce path-based access
- Logging: every Bird Eye API call logs `tenant_id`, `user_id`, `endpoint`, `findings_returned_count`. Audit log retention 90 days minimum.

---

## Section 5 — What to NOT build in v1

CC has a tendency to over-scope. Hard non-goals for v1:

- ❌ No real-time/streaming Bird Eye. Async background job is fine.
- ❌ No webhook integrations (Slack/email notifications). Findings live in the UI.
- ❌ No diff visualization for duplicates. "82% similar" + section refs is enough.
- ❌ No auto-merge feature. Bird Eye recommends; humans merge.
- ❌ No fine-tuned classifier for finding severity. Use rule-based severity (critical = active conflict, high = duplicate >85%, medium = duplicate 70-85%, low = stale, info = framework gap).
- ❌ No customer-facing API for Bird Eye. Internal endpoints only, called from Midnight UI.
- ❌ No multi-language support. English-only for v1.

---

## Section 6 — Build order recap (for CC)

Ship in this exact order. Don't skip ahead.

1. Migration: four new tables with tenant_id on every row, indexes, pgvector extension enabled
2. Tenant guard decorator + 5 isolation tests (FAILING is fine — they pass when the rest is built)
3. Document ingestion endpoint (extract, chunk, embed, insert)
4. Voyage embedding service
5. Five detectors, one at a time, with unit tests for each
6. Orchestrator + manual trigger endpoint
7. UI panel inside Library
8. Wire automatic triggers (on upload, on generation)
9. Make all 5 isolation tests pass
10. Dogfood: run against Brian's HPS policy stack (SEC-P series) and verify findings make sense

---

## Section 7 — Definition of done for v1

- A compliance manager logs in, navigates to Library → Bird Eye Review
- Clicks "Run Bird Eye Review"
- Within 90 seconds, sees a results panel with:
  - Executive summary card
  - At least one duplicate, conflict, stale, framework_gap, or orphan finding (if data warrants)
  - Each finding linkable back to the source document(s)
  - Dismiss/Resolve actions work
- All five tenant isolation tests pass
- Bird Eye runs automatically when a new document is uploaded
- One real test customer (Brian's HPS data, used with permission) produces ≥3 meaningful findings

When all of the above is true: ship v1. Move on. Do not build v2 features until 5 customers have used v1.

---

## Section 8 — Notes for Brian (the human in the loop)

- Whole spec is one weekend with CC + Max if you don't deviate
- Dogfood on your own HPS SEC-P series — that's your test corpus, you already have access, no NDA concerns
- The 5 isolation tests are the gate. Don't ship without them passing.
- After v1 ships, the next 10 hours of work should be marketing assets (screenshots, demo Loom) — NOT v2 features. Bird Eye becomes the proof asset for the $2,500 Bird Eye Diagnostic services offer in the 90-day plan.
- The findings you see on your own HPS data become a real-life case study you can show prospects (with employer permission and any necessary redactions).
