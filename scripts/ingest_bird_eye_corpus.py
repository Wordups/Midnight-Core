"""Ingest the Takeoff LLC test corpus into Supabase for Bird Eye validation."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

# .env lives at the project root and may contain real ANTHROPIC_API_KEY; override an empty shell env var.
load_dotenv(REPO_ROOT / ".env", override=True)

from backend.bird_eye.db import TABLE_DOCUMENTS, TABLE_CHUNKS, TABLE_FINDINGS, TABLE_RUNS, delete as db_delete, select as db_select
from backend.bird_eye.ingestion import ingest_document
from backend.bird_eye.orchestrator import run_bird_eye

TENANT_ID = os.environ.get("TEST_TENANT_ID", "").strip()
if not TENANT_ID:
    raise SystemExit("TEST_TENANT_ID env var is required.")

CORPUS_DIR = REPO_ROOT / "files"
TARGET_FILES = [
    "01_information_security_policy.md",
    "02_access_control_policy.md",
    "03_incident_response_policy.md",
    "04_acceptable_use_policy.md",
    "05_identity_authentication_standard.md",
    "06_data_retention_policy.md",
    "07_vendor_management_policy.md",
    "08_encryption_standard.md",
]


def purge_existing() -> None:
    docs = db_select(
        TABLE_DOCUMENTS,
        tenant_id=TENANT_ID,
        columns="id,policy_number",
        filters={"policy_number": "like.TKO-*"},
    )
    # Purge prior Bird Eye runs/findings first (findings reference chunks via FK)
    runs = db_select(TABLE_RUNS, tenant_id=TENANT_ID, columns="id", filters={"run_type": "eq.bird_eye_review"})
    for r in runs:
        db_delete(TABLE_FINDINGS, tenant_id=TENANT_ID, filters={"run_id": f"eq.{r['id']}"})
        db_delete(TABLE_RUNS, tenant_id=TENANT_ID, filters={"id": f"eq.{r['id']}"})
    for d in docs:
        pid = d["id"]
        # Some findings may not be tied to a run (orphaned cleanup just in case)
        db_delete(TABLE_FINDINGS, tenant_id=TENANT_ID, filters={"policy_id": f"eq.{pid}"})
        db_delete(TABLE_FINDINGS, tenant_id=TENANT_ID, filters={"related_policy_id": f"eq.{pid}"})
        db_delete(TABLE_CHUNKS, tenant_id=TENANT_ID, filters={"policy_id": f"eq.{pid}"})
        db_delete(TABLE_DOCUMENTS, tenant_id=TENANT_ID, filters={"id": f"eq.{pid}"})


def main(skip_run: bool = False) -> None:
    print(f"Purging existing TKO-* policies/runs for tenant {TENANT_ID}...")
    purge_existing()
    print("Done purge.\n")

    for filename in TARGET_FILES:
        path = CORPUS_DIR / filename
        if not path.exists():
            print(f"  -- missing {filename}")
            continue
        content = path.read_bytes()
        result = ingest_document(
            TENANT_ID,
            filename=filename,
            file_bytes=content,
            skip_storage=False,
        )
        print(
            f"  ok {result['policy_number']:<14} {result['artifact_type']:<10} sections={result['sections_count']:<2} :: {result['title']}"
        )

    print()
    if skip_run:
        print("--skip-run flag passed; not running Bird Eye.")
        return
    print("Running Bird Eye...")
    summary = run_bird_eye(TENANT_ID, triggered_by="corpus_ingest")
    print(f"Run {summary['run_id']} :: {summary['findings_count']} findings across {summary['documents_reviewed']} documents")


if __name__ == "__main__":
    skip = "--skip-run" in sys.argv
    main(skip_run=skip)
