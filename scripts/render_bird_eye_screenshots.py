"""Render three standalone HTML pages showing the Bird Eye UI populated with the latest run.

Outputs are written under files/screenshots/. Run a headless browser against them to capture PNGs.
"""
from __future__ import annotations

import html
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env", override=True)

from collections import Counter

from backend.bird_eye.db import (
    TABLE_DOCUMENTS,
    TABLE_FINDINGS,
    TABLE_RUNS,
    select as db_select,
)

TENANT_ID = os.environ["TEST_TENANT_ID"]
OUT_DIR = REPO_ROOT / "files" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEV_COLOR = {
    "critical": "#ff5d5d",
    "high": "#ff9a4d",
    "medium": "#ffd24d",
    "low": "#9bd1ff",
    "info": "#9aa5b1",
}
TYPE_LABEL = {
    "duplicate": "Duplicate content",
    "conflict": "Conflicting control",
    "stale": "Stale governance",
    "framework_gap": "Framework gap",
    "orphan": "Orphaned document",
}

BASE_STYLE = """
:root {
  --bg: #0a0c10;
  --bg2: #11141a;
  --bg3: #161a22;
  --bg4: #1c2230;
  --text: #e6edf3;
  --text2: #8e98a7;
  --text3: #586168;
  --accent: #00d4f5;
  --border2: rgba(255,255,255,0.07);
  --font-display: 'Inter', -apple-system, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, Menlo, monospace;
}
* { box-sizing: border-box; }
body { margin: 0; padding: 40px; background: var(--bg); color: var(--text); font-family: var(--font-display); }
.panel { background: var(--bg2); border: 1px solid var(--border2); border-radius: 12px; padding: 24px; max-width: 1080px; margin: 0 auto; }
.panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.panel-title { font-family: var(--font-display); font-size: 22px; font-weight: 700; }
.btn { padding: 8px 14px; font-size: 11px; border-radius: 6px; border: 1px solid var(--accent); background: var(--accent); color: var(--bg); cursor: pointer; font-family: var(--font-mono); text-transform: uppercase; letter-spacing: 0.08em; }
"""


def fetch_latest_run() -> dict:
    runs = db_select(
        TABLE_RUNS,
        tenant_id=TENANT_ID,
        columns="id,status,documents_reviewed,findings_count,created_at,completed_at,triggered_by",
        filters={"run_type": "eq.bird_eye_review"},
        order="created_at.desc",
        limit=1,
    )
    return runs[0] if runs else {}


def fetch_findings(run_id: str) -> list[dict]:
    findings = db_select(
        TABLE_FINDINGS,
        tenant_id=TENANT_ID,
        columns="id,finding_type,severity,description,recommendation,evidence,similarity_score,policy_id,related_policy_id",
        filters={"run_id": f"eq.{run_id}"},
        limit=200,
    )
    doc_ids = {f["policy_id"] for f in findings if f.get("policy_id")} | {
        f["related_policy_id"] for f in findings if f.get("related_policy_id")
    }
    docs: list[dict] = []
    if doc_ids:
        docs = db_select(
            TABLE_DOCUMENTS,
            tenant_id=TENANT_ID,
            columns="id,policy_name,policy_number",
            filters={"id": "in.(" + ",".join(doc_ids) + ")"},
        )
    lookup = {d["id"]: d for d in docs}
    for f in findings:
        f["primary_document"] = lookup.get(f.get("policy_id"))
        f["related_document"] = lookup.get(f.get("related_policy_id"))
    return findings


def fetch_docs_count() -> int:
    return len(
        db_select(
            TABLE_DOCUMENTS,
            tenant_id=TENANT_ID,
            columns="id",
            filters={"policy_number": "like.TKO-*"},
        )
    )


def render_summary(run: dict, findings: list[dict], docs_count: int) -> str:
    open_findings = [f for f in findings if (f.get("status") or "open") == "open"]
    sev = Counter(f.get("severity") for f in open_findings)
    typ = Counter(f.get("finding_type") for f in open_findings)
    merge = typ.get("duplicate", 0)
    sev_html = " ".join(
        f'<span style="display:inline-block;margin-right:14px;"><span style="display:inline-block;width:8px;height:8px;background:{SEV_COLOR[k]};border-radius:50%;margin-right:6px;"></span>{html.escape(k)} <strong>{sev[k]}</strong></span>'
        for k in ("critical", "high", "medium", "low") if sev[k]
    )
    last_dt = run.get("completed_at") or run.get("created_at") or ""
    return f"""
<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Bird Eye - Exec Summary</title><style>{BASE_STYLE}</style></head><body>
<div class=\"panel\">
  <div class=\"panel-header\">
    <div>
      <div style=\"font-family:var(--font-mono);font-size:10px;color:var(--accent);letter-spacing:.12em;text-transform:uppercase;\">Bird Eye Review · Document Intelligence Engine</div>
      <div class=\"panel-title\" style=\"margin-top:6px;\">Executive Summary</div>
    </div>
    <button class=\"btn\">Run Bird Eye Review</button>
  </div>
  <div style=\"display:grid;grid-template-columns:repeat(4,1fr);gap:18px;padding:22px;background:rgba(0,212,245,0.04);border:1px solid rgba(0,212,245,0.18);border-radius:10px;\">
    <div>
      <div style=\"font-family:var(--font-mono);font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.08em;\">Documents Reviewed</div>
      <div style=\"font-family:var(--font-display);font-size:42px;font-weight:700;margin-top:6px;\">{docs_count}</div>
    </div>
    <div>
      <div style=\"font-family:var(--font-mono);font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.08em;\">Open Findings</div>
      <div style=\"font-family:var(--font-display);font-size:42px;font-weight:700;color:var(--accent);margin-top:6px;\">{len(open_findings)}</div>
    </div>
    <div>
      <div style=\"font-family:var(--font-mono);font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.08em;\">Merge Opportunities</div>
      <div style=\"font-family:var(--font-display);font-size:42px;font-weight:700;margin-top:6px;\">{merge}</div>
    </div>
    <div>
      <div style=\"font-family:var(--font-mono);font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.08em;\">Severity Mix</div>
      <div style=\"margin-top:10px;font-size:13px;color:var(--text2);\">{sev_html or '<span style=\"color:var(--text3);\">no open findings</span>'}</div>
    </div>
  </div>
  <div style=\"margin-top:18px;font-family:var(--font-mono);font-size:11px;color:var(--text3);\">
    Last run {html.escape(str(last_dt))[:19].replace('T', ' ')} UTC · trigger {html.escape(run.get('triggered_by') or 'manual')} · run id {html.escape((run.get('id') or '')[:8])}
  </div>
  <div style=\"margin-top:14px;font-size:13px;color:var(--text2);line-height:1.7;\">
    {', '.join(f'{TYPE_LABEL.get(k,k)}: <strong>{typ[k]}</strong>' for k in typ)}
  </div>
</div>
</body></html>
"""


def render_finding_card(f: dict, *, expanded_evidence: bool = False) -> str:
    color = SEV_COLOR.get(f.get("severity"), "#9aa5b1")
    summary = html.escape(f.get("description") or "")
    rec = html.escape(f.get("recommendation") or "")
    sim_pct = (
        f' · {round(float(f.get("similarity_score") or 0) * 100, 1)}%'
        if f.get("similarity_score")
        else ""
    )
    chips = []
    for doc in (f.get("primary_document"), f.get("related_document")):
        if not doc:
            continue
        chips.append(
            f'<span style="display:inline-block;margin-right:8px;padding:3px 10px;background:rgba(255,255,255,0.04);border:1px solid var(--border2);border-radius:6px;color:var(--text2);font-size:11px;">{html.escape(doc.get("policy_number") or "")} · {html.escape(doc.get("policy_name") or "")}</span>'
        )
    chips_html = "".join(chips)
    evidence_html = ""
    if expanded_evidence and f.get("evidence"):
        import json
        evidence_html = f'<details open style="margin-top:14px;font-size:11px;color:var(--text3);"><summary style="cursor:pointer;color:var(--text2);">Evidence</summary><pre style="margin-top:8px;padding:12px;background:var(--bg3);border:1px solid var(--border2);border-radius:6px;color:var(--text2);overflow:auto;font-family:var(--font-mono);">{html.escape(json.dumps(f["evidence"], indent=2))}</pre></details>'
    return f"""
<div style=\"padding:16px;background:var(--bg2);border:1px solid var(--border2);border-radius:10px;margin-bottom:10px;\">
  <div style=\"display:flex;align-items:flex-start;gap:12px;\">
    <div style=\"margin-top:6px;width:10px;height:10px;background:{color};border-radius:50%;box-shadow:0 0 10px {color}a0;flex-shrink:0;\"></div>
    <div style=\"flex:1;\">
      <div style=\"display:flex;align-items:center;gap:12px;flex-wrap:wrap;\">
        <span style=\"font-family:var(--font-mono);font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:{color};\">{html.escape(f.get('severity') or 'info')}{sim_pct}</span>
        <span style=\"font-family:var(--font-mono);font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.08em;\">{html.escape(TYPE_LABEL.get(f.get('finding_type'), f.get('finding_type') or ''))}</span>
      </div>
      <div style=\"margin-top:8px;font-size:14px;color:var(--text);line-height:1.55;\">{summary}</div>
      {f'<div style=\"margin-top:10px;\">{chips_html}</div>' if chips_html else ''}
      {f'<div style=\"margin-top:12px;font-size:12.5px;color:var(--text2);line-height:1.6;\"><strong style=\"color:var(--accent);\">Recommendation:</strong> {rec}</div>' if rec else ''}
      {evidence_html}
      <div style=\"margin-top:12px;display:flex;gap:8px;\">
        <button class=\"btn\" style=\"background:var(--bg4);color:var(--text2);border:1px solid var(--border2);\">Resolve</button>
        <button class=\"btn\" style=\"background:transparent;color:var(--text3);border:1px solid var(--border2);\">Dismiss</button>
      </div>
    </div>
  </div>
</div>
"""


def render_findings_list(findings: list[dict]) -> str:
    type_order = ["conflict", "duplicate", "stale", "framework_gap", "orphan"]
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    grouped: dict[str, list[dict]] = {}
    for f in findings:
        grouped.setdefault(f.get("finding_type") or "other", []).append(f)
    blocks = []
    for t in type_order:
        items = grouped.get(t) or []
        if not items:
            continue
        items.sort(key=lambda x: sev_order.get(x.get("severity"), 9))
        blocks.append(
            f'<div style="margin-top:18px;font-family:var(--font-mono);font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.1em;">{TYPE_LABEL.get(t, t)} ({len(items)})</div>'
            + "".join(render_finding_card(it) for it in items[:4])
        )
    body = "".join(blocks)
    return f"""
<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Bird Eye - Findings</title><style>{BASE_STYLE}</style></head><body>
<div class=\"panel\">
  <div class=\"panel-header\">
    <div class=\"panel-title\">Bird Eye Findings <span style=\"font-family:var(--font-mono);font-size:11px;color:var(--text3);font-weight:400;margin-left:10px;\">{len(findings)} open · 5 finding types</span></div>
    <button class=\"btn\">Run Bird Eye Review</button>
  </div>
  {body}
</div>
</body></html>
"""


def render_single_finding(findings: list[dict]) -> str:
    # Pick the highest-severity duplicate finding (most informative single-card view)
    target = None
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    duplicates = sorted(
        (f for f in findings if f.get("finding_type") == "duplicate" and f.get("similarity_score")),
        key=lambda x: -float(x["similarity_score"] or 0),
    )
    if duplicates:
        target = duplicates[0]
    else:
        target = sorted(findings, key=lambda x: sev_order.get(x.get("severity"), 9))[0]
    card_html = render_finding_card(target, expanded_evidence=True)
    return f"""
<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Bird Eye - Finding Detail</title><style>{BASE_STYLE}</style></head><body>
<div class=\"panel\">
  <div class=\"panel-header\">
    <div>
      <div style=\"font-family:var(--font-mono);font-size:10px;color:var(--accent);letter-spacing:.12em;text-transform:uppercase;\">Bird Eye Finding</div>
      <div class=\"panel-title\" style=\"margin-top:6px;\">{html.escape(TYPE_LABEL.get(target.get('finding_type'), target.get('finding_type') or ''))}</div>
    </div>
    <span style=\"font-family:var(--font-mono);font-size:11px;color:var(--text3);\">finding {html.escape((target.get('id') or '')[:8])}</span>
  </div>
  {card_html}
</div>
</body></html>
"""


def main() -> None:
    run = fetch_latest_run()
    if not run:
        raise SystemExit("No Bird Eye runs found - cannot render screenshots.")
    findings = fetch_findings(run["id"])
    docs_count = fetch_docs_count()
    (OUT_DIR / "01_exec_summary.html").write_text(render_summary(run, findings, docs_count), encoding="utf-8")
    (OUT_DIR / "02_findings_list.html").write_text(render_findings_list(findings), encoding="utf-8")
    (OUT_DIR / "03_finding_detail.html").write_text(render_single_finding(findings), encoding="utf-8")
    print(f"Wrote three HTML previews to {OUT_DIR}")


if __name__ == "__main__":
    main()
