"""Trigger Bird Eye for the test tenant without re-ingesting."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env", override=True)

from backend.bird_eye.db import TABLE_FINDINGS, TABLE_RUNS, delete as db_delete, select as db_select
from backend.bird_eye.orchestrator import run_bird_eye

TENANT_ID = os.environ["TEST_TENANT_ID"]


def purge_prior_runs() -> None:
    runs = db_select(TABLE_RUNS, tenant_id=TENANT_ID, columns="id", filters={"run_type": "eq.bird_eye_review"})
    for r in runs:
        db_delete(TABLE_FINDINGS, tenant_id=TENANT_ID, filters={"run_id": f"eq.{r['id']}"})
        db_delete(TABLE_RUNS, tenant_id=TENANT_ID, filters={"id": f"eq.{r['id']}"})


def main() -> None:
    purge_prior_runs()
    summary = run_bird_eye(TENANT_ID, triggered_by="manual_validation")
    print(f"Run {summary['run_id']}: {summary['findings_count']} findings across {summary['documents_reviewed']} docs")


if __name__ == "__main__":
    main()
