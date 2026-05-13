"""Inspect Bird Eye findings against the validation key."""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env", override=True)

from backend.bird_eye.db import TABLE_FINDINGS, TABLE_RUNS, select as db_select

TENANT_ID = os.environ.get("TEST_TENANT_ID", "").strip()


def main() -> None:
    runs = db_select(
        TABLE_RUNS,
        tenant_id=TENANT_ID,
        columns="id,status,documents_reviewed,findings_count,created_at,completed_at",
        filters={"run_type": "eq.bird_eye_review"},
        order="created_at.desc",
        limit=1,
    )
    if not runs:
        print("No Bird Eye runs found.")
        return
    run = runs[0]
    print(f"=== Run {run['id']} ===")
    print(
        f"status={run['status']}  docs={run['documents_reviewed']}  findings={run['findings_count']}  "
        f"started={run['created_at']}  finished={run.get('completed_at')}"
    )

    findings = db_select(
        TABLE_FINDINGS,
        tenant_id=TENANT_ID,
        columns="finding_type,severity,description,recommendation,evidence,similarity_score",
        filters={"run_id": f"eq.{run['id']}"},
        order="finding_type.asc",
        limit=200,
    )
    print(f"\n{len(findings)} findings\n")

    sev = Counter(f.get("severity") for f in findings)
    typ = Counter(f.get("finding_type") for f in findings)
    print("By type:", dict(typ))
    print("By severity:", dict(sev))
    print()
    out_path = REPO_ROOT / "files" / "bird_eye_actual_findings.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append(f"=== Run {run['id']} ===")
    lines.append(
        f"status={run['status']}  docs={run['documents_reviewed']}  findings={run['findings_count']}"
    )
    lines.append(f"By type: {dict(typ)}")
    lines.append(f"By severity: {dict(sev)}")
    lines.append("")
    for f in findings:
        lines.append(f"  [{f['finding_type']}/{f['severity']}] {f['description']}")
        if f.get("similarity_score"):
            lines.append(f"     similarity={f['similarity_score']}")
        if f.get("recommendation"):
            lines.append(f"     -> {f['recommendation'][:200]}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
