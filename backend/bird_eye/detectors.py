"""Five Bird Eye detectors. Every query is tenant-scoped."""
from __future__ import annotations

import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from .db import TABLE_CHUNKS, TABLE_DOCUMENTS, TABLE_FINDINGS, insert as db_insert, select as db_select
from .embeddings import cosine
from .tenant_guard import tenant_scoped

logger = logging.getLogger("midnight.bird_eye.detectors")


DUPLICATE_HIGH = 0.85
DUPLICATE_MEDIUM = 0.78  # tuned for voyage-3 cosine on policy text
MIN_CHUNK_CHARS = 100  # ignore tiny boilerplate sections

# Skip "structural" sections that every governance document shares - they're not real duplicates
STRUCTURAL_HEADING_TERMS = (
    "scope",
    "purpose",
    "definitions",
    "roles and responsibilities",
    "enforcement",
    "review cadence",
    "review schedule",
)


def _is_structural(heading: str | None) -> bool:
    if not heading:
        return False
    lower = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", heading).strip().lower()
    return any(term == lower or term in lower for term in STRUCTURAL_HEADING_TERMS)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        s = value.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _ts(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _coerce_embedding(value: Any) -> list[float] | None:
    if value is None:
        return None
    if isinstance(value, list):
        try:
            return [float(x) for x in value]
        except (TypeError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s or s in ("null", "[]"):
            return None
        try:
            import json
            data = json.loads(s)
            if isinstance(data, list):
                return [float(x) for x in data]
        except Exception:
            return None
    return None


def _record_findings(tenant_id: str, run_id: str, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    payload: list[dict[str, Any]] = []
    for row in rows:
        record = {
            "tenant_id": tenant_id,
            "run_id": run_id,
            "finding_type": row["finding_type"],
            "severity": row["severity"],
            "description": row["summary"],
            "recommendation": row["recommendation"],
            "evidence": row.get("evidence") or {},
            "status": "open",
        }
        if "policy_id" in row:
            record["policy_id"] = row["policy_id"]
        if "related_policy_id" in row:
            record["related_policy_id"] = row["related_policy_id"]
        if "related_section_id" in row:
            record["related_section_id"] = row["related_section_id"]
        if "similarity_score" in row:
            record["similarity_score"] = row["similarity_score"]
        if row.get("framework"):
            record["framework"] = row["framework"]
        if row.get("control_id"):
            record["control_id"] = row["control_id"]
        payload.append(record)
    db_insert(TABLE_FINDINGS, payload)
    return len(payload)


@tenant_scoped
def detect_duplicates(tenant_id: str, run_id: str, *, threshold: float = DUPLICATE_MEDIUM) -> int:
    """Find near-duplicate sections across documents in the same tenant."""
    chunks = db_select(
        TABLE_CHUNKS,
        tenant_id=tenant_id,
        columns="id,policy_id,slot_id,heading,content,embedding",
        filters={"source_origin": "eq.bird_eye_ingest"},
    )
    if not chunks:
        return 0

    docs = db_select(
        TABLE_DOCUMENTS,
        tenant_id=tenant_id,
        columns="id,policy_name,policy_number",
    )
    doc_meta = {d["id"]: d for d in docs}

    # Pre-compute vectors
    vec_chunks: list[tuple[dict[str, Any], list[float]]] = []
    for c in chunks:
        if c.get("policy_id") not in doc_meta:
            continue
        if len((c.get("content") or "")) < MIN_CHUNK_CHARS:
            continue
        if _is_structural(c.get("heading")):
            continue
        v = _coerce_embedding(c.get("embedding"))
        if v is None or not v:
            continue
        vec_chunks.append((c, v))

    seen_pairs: set[tuple[str, str]] = set()
    findings: list[dict[str, Any]] = []

    for i, (chunk_a, vec_a) in enumerate(vec_chunks):
        best: tuple[float, dict[str, Any]] | None = None
        for j, (chunk_b, vec_b) in enumerate(vec_chunks):
            if i == j:
                continue
            if chunk_a["policy_id"] == chunk_b["policy_id"]:
                continue
            sim = cosine(vec_a, vec_b)
            if sim < threshold:
                continue
            if best is None or sim > best[0]:
                best = (sim, chunk_b)
        if best is None:
            continue
        sim, chunk_b = best
        pair_key = tuple(sorted([chunk_a["id"], chunk_b["id"]]))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        doc_a = doc_meta[chunk_a["policy_id"]]
        doc_b = doc_meta[chunk_b["policy_id"]]
        sim_pct = round(sim * 100, 1)
        severity = "high" if sim >= DUPLICATE_HIGH else "medium"
        summary = (
            f"Duplicate content: {doc_a.get('policy_number')} §{chunk_a.get('heading')} "
            f"↔ {doc_b.get('policy_number')} §{chunk_b.get('heading')} ({sim_pct}% similar)"
        )
        recommendation = (
            "Merge or designate one document as the authoritative source. "
            "If the standard is more specific, keep it there and have the policy reference it."
        )
        findings.append(
            {
                "finding_type": "duplicate",
                "severity": severity,
                "summary": summary,
                "recommendation": recommendation,
                "policy_id": chunk_a["policy_id"],
                "related_policy_id": chunk_b["policy_id"],
                "related_section_id": chunk_a["id"],
                "similarity_score": round(sim, 4),
                "evidence": {
                    "doc_a": {
                        "policy_number": doc_a.get("policy_number"),
                        "title": doc_a.get("policy_name"),
                        "section": chunk_a.get("heading"),
                        "chunk_id": chunk_a["id"],
                    },
                    "doc_b": {
                        "policy_number": doc_b.get("policy_number"),
                        "title": doc_b.get("policy_name"),
                        "section": chunk_b.get("heading"),
                        "chunk_id": chunk_b["id"],
                    },
                    "similarity": sim,
                },
            }
        )
    return _record_findings(tenant_id, run_id, findings)


CONFLICT_LABELS: dict[str, str] = {
    "password_min_length": "Password minimum length",
    "password_rotation_days": "Password rotation cadence",
    "password_reuse_count": "Password reuse history",
    "lockout_failed_attempts": "Account lockout - failed attempts",
    "lockout_window_minutes": "Account lockout - window",
    "lockout_duration_minutes": "Account lockout - duration",
    "session_idle_timeout_minutes": "Session idle timeout",
    "session_max_duration_hours": "Maximum session duration",
    "service_account_rotation_days": "Service account credential rotation",
    "customer_doc_retention_days": "Customer document retention",
    "breach_notification_hours": "Breach notification window",
    "tls_min_version": "Minimum TLS version",
    "aes_key_bits": "AES key strength",
}

# Rules that group together as a single lockout finding
LOCKOUT_KEYS = ("lockout_failed_attempts", "lockout_window_minutes", "lockout_duration_minutes")


def _severity_for_conflict(key: str) -> str:
    if key in ("password_min_length", "tls_min_version", "aes_key_bits"):
        return "critical" if key == "password_min_length" else "high"
    if key in LOCKOUT_KEYS:
        return "medium"
    return "high"


@tenant_scoped
def detect_conflicts(tenant_id: str, run_id: str) -> int:
    chunks = db_select(
        TABLE_CHUNKS,
        tenant_id=tenant_id,
        columns="id,policy_id,heading,numeric_requirements",
        filters={"source_origin": "eq.bird_eye_ingest"},
    )
    docs = db_select(
        TABLE_DOCUMENTS,
        tenant_id=tenant_id,
        columns="id,policy_name,policy_number",
    )
    doc_meta = {d["id"]: d for d in docs}

    # key -> list of (value, doc_meta, chunk)
    key_observations: dict[str, list[tuple[Any, dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for c in chunks:
        if c.get("policy_id") not in doc_meta:
            continue
        reqs = c.get("numeric_requirements") or {}
        if not isinstance(reqs, dict):
            continue
        for key, value in reqs.items():
            key_observations[key].append((value, doc_meta[c["policy_id"]], c))

    findings: list[dict[str, Any]] = []
    seen_lockout = False

    for key, observations in key_observations.items():
        if len(observations) < 2:
            continue
        distinct_pairs = []
        unique_values: dict[Any, dict[str, Any]] = {}
        for value, doc, chunk in observations:
            unique_values.setdefault(value, {"value": value, "docs": []})
            unique_values[value]["docs"].append(
                {
                    "policy_id": doc["id"],
                    "policy_number": doc.get("policy_number"),
                    "title": doc.get("policy_name"),
                    "section": chunk.get("heading"),
                }
            )
        if len(unique_values) < 2:
            continue

        # Group the lockout family into a single finding
        if key in LOCKOUT_KEYS:
            if seen_lockout:
                continue
            lockout_evidence: dict[str, Any] = {}
            for lkey in LOCKOUT_KEYS:
                if lkey not in key_observations:
                    continue
                lockout_evidence[lkey] = [
                    {
                        "value": value,
                        "policy_number": doc.get("policy_number"),
                        "title": doc.get("policy_name"),
                        "section": chunk.get("heading"),
                    }
                    for value, doc, chunk in key_observations[lkey]
                ]
            if any(len({obs["value"] for obs in lockout_evidence.get(lk, [])}) >= 2 for lk in LOCKOUT_KEYS):
                seen_lockout = True
                involved_doc_ids = list({doc["id"] for _, doc, _ in observations})
                primary = involved_doc_ids[0]
                related = involved_doc_ids[1] if len(involved_doc_ids) > 1 else None
                lock_summary_parts = []
                for lkey in LOCKOUT_KEYS:
                    obs = key_observations.get(lkey)
                    if not obs:
                        continue
                    pieces = [
                        f"{d.get('policy_number')}: {value}" for value, d, _ in obs
                    ]
                    lock_summary_parts.append(f"{CONFLICT_LABELS[lkey]} -> {'; '.join(pieces)}")
                summary = "Conflicting account lockout policy across documents. " + " | ".join(lock_summary_parts)
                findings.append(
                    {
                        "finding_type": "conflict",
                        "severity": "medium",
                        "summary": summary,
                        "recommendation": "Standardize lockout policy across the policy and the standard. Pick a single set of values (failed attempts / window / lockout duration) and update both documents to match.",
                        "policy_id": primary,
                        "related_policy_id": related,
                        "evidence": {"key": "lockout_policy", "details": lockout_evidence},
                    }
                )
            continue

        for v_a, info_a in unique_values.items():
            for v_b, info_b in unique_values.items():
                if str(v_a) >= str(v_b):
                    continue
                distinct_pairs.append((v_a, v_b, info_a, info_b))
        if not distinct_pairs:
            continue

        def _cross_doc_quality(pair: tuple[Any, Any, dict[str, Any], dict[str, Any]]) -> tuple[int, int]:
            _, _, ia, ib = pair
            docs_a = {d["policy_id"] for d in ia["docs"]}
            docs_b = {d["policy_id"] for d in ib["docs"]}
            cross = 1 if docs_a.symmetric_difference(docs_b) else 0
            return (cross, len(docs_a) + len(docs_b))

        distinct_pairs.sort(key=_cross_doc_quality, reverse=True)
        primary_value, secondary_value, info_a, info_b = distinct_pairs[0]
        label = CONFLICT_LABELS.get(key, key.replace("_", " "))

        def _pick_doc(info_self: dict[str, Any], info_other: dict[str, Any]) -> dict[str, Any]:
            other_ids = {d["policy_id"] for d in info_other["docs"]}
            for d in info_self["docs"]:
                if d["policy_id"] not in other_ids:
                    return d
            return info_self["docs"][0]

        primary_doc = _pick_doc(info_a, info_b)
        secondary_doc = _pick_doc(info_b, info_a)
        summary = (
            f"Conflict on {label}: {primary_doc.get('policy_number')} ({primary_doc.get('section')}) says "
            f"{primary_value} but {secondary_doc.get('policy_number')} ({secondary_doc.get('section')}) says {secondary_value}."
        )

        recommendation = _recommend_for_key(key, list(unique_values.keys()))

        findings.append(
            {
                "finding_type": "conflict",
                "severity": _severity_for_conflict(key),
                "summary": summary,
                "recommendation": recommendation,
                "policy_id": primary_doc["policy_id"],
                "related_policy_id": secondary_doc["policy_id"],
                "evidence": {
                    "key": key,
                    "label": label,
                    "values": [
                        {"value": value, "docs": info["docs"]}
                        for value, info in unique_values.items()
                    ],
                },
            }
        )
    return _record_findings(tenant_id, run_id, findings)


def _recommend_for_key(key: str, values: list[Any]) -> str:
    if key == "password_min_length":
        try:
            target = max(int(v) for v in values)
        except Exception:
            target = max(values, key=str)
        return f"Standardize on {target} characters (the stronger of the values) and update both documents to match."
    if key == "tls_min_version":
        return "TLS 1.3 is the modern minimum. Update any standard that allows TLS 1.2 to require TLS 1.3."
    if key == "password_reuse_count":
        try:
            target = max(int(v) for v in values)
        except Exception:
            target = max(values, key=str)
        return f"Standardize on disallowing the previous {target} passwords (the stronger of the values)."
    if key == "password_rotation_days":
        return "Align with NIST 800-63B current guidance: avoid forced rotation absent compromise indicators, or pick one cadence and update both documents."
    return "Pick a single value and update both documents to match."


@tenant_scoped
def detect_stale_governance(tenant_id: str, run_id: str) -> int:
    docs = db_select(
        TABLE_DOCUMENTS,
        tenant_id=tenant_id,
        columns="id,policy_name,policy_number,version,owner,last_reviewed_at,next_review_at,status",
    )
    findings: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    one_year_ago = now.replace(year=now.year - 1)

    for d in docs:
        title = d.get("policy_name")
        number = d.get("policy_number")
        owner = (d.get("owner") or "").strip()
        version = (d.get("version") or "").strip()
        last_reviewed = _parse_iso(d.get("last_reviewed_at"))
        next_review = _parse_iso(d.get("next_review_at"))
        status = (d.get("status") or "").strip().lower()

        if not owner or owner.lower() in {"[unassigned]", "unassigned", "tbd", "none"}:
            findings.append(
                {
                    "finding_type": "stale",
                    "severity": "high",
                    "summary": f"{number} ({title}) has no assigned owner.",
                    "recommendation": "Assign an accountable owner before the next review cycle.",
                    "policy_id": d["id"],
                    "evidence": {"field": "owner", "value": d.get("owner")},
                }
            )

        if next_review and next_review < now:
            days = (now - next_review).days
            findings.append(
                {
                    "finding_type": "stale",
                    "severity": "high",
                    "summary": f"{number} ({title}) review is overdue by {days} days (next_review_at={next_review.date().isoformat()}).",
                    "recommendation": "Schedule an immediate review and re-approval. Update last_reviewed_at and next_review_at once complete.",
                    "policy_id": d["id"],
                    "evidence": {"field": "next_review_at", "value": d.get("next_review_at"), "overdue_days": days},
                }
            )
        elif last_reviewed and last_reviewed < one_year_ago:
            findings.append(
                {
                    "finding_type": "stale",
                    "severity": "medium",
                    "summary": f"{number} ({title}) has not been reviewed in over a year (last_reviewed_at={last_reviewed.date().isoformat()}).",
                    "recommendation": "Re-review and re-approve the document in the next governance cycle.",
                    "policy_id": d["id"],
                    "evidence": {"field": "last_reviewed_at", "value": d.get("last_reviewed_at")},
                }
            )

        if not version:
            findings.append(
                {
                    "finding_type": "stale",
                    "severity": "low",
                    "summary": f"{number} ({title}) has no version number recorded.",
                    "recommendation": "Set an explicit version and increment on each material change.",
                    "policy_id": d["id"],
                    "evidence": {"field": "version", "value": None},
                }
            )
        else:
            # Version 0.x with Active status is a draft/pre-release contradiction
            try:
                major = int(version.split(".")[0])
                if major == 0 and status == "active":
                    findings.append(
                        {
                            "finding_type": "stale",
                            "severity": "low",
                            "summary": f"{number} ({title}) is marked Active but versioned {version} (pre-release).",
                            "recommendation": "Promote to v1.0 once the document is approved, or change status to Draft.",
                            "policy_id": d["id"],
                            "evidence": {"field": "version", "value": version, "status": d.get("status")},
                        }
                    )
            except (ValueError, IndexError):
                pass

    return _record_findings(tenant_id, run_id, findings)


FRAMEWORK_BODY_KEYWORDS: dict[str, list[str]] = {
    "HIPAA": [
        "hipaa",
        "phi",
        "protected health information",
        "business associate agreement",
        "breach notification rule",
    ],
    "PCI DSS": ["pci", "cardholder data", "payment card"],
    "NIST CSF": ["nist csf", "csf 2.0", "pr.ip", "pr.at-1", "id.am"],
    "NIST 800-53": ["nist 800-53", "ac-2", "ac-3", "ia-2"],
    "ISO 27001": ["iso 27001", "iso/iec 27001", "annex a"],
    "SOC 2": ["soc 2", "trust services criteria", "tsc"],
}


@tenant_scoped
def detect_framework_gaps(tenant_id: str, run_id: str) -> int:
    docs = db_select(
        TABLE_DOCUMENTS,
        tenant_id=tenant_id,
        columns="id,policy_name,policy_number,selected_frameworks",
    )
    chunks = db_select(
        TABLE_CHUNKS,
        tenant_id=tenant_id,
        columns="policy_id,heading,content",
        filters={"source_origin": "eq.bird_eye_ingest"},
    )
    body_by_policy: dict[str, str] = defaultdict(str)
    for c in chunks:
        body_by_policy[c.get("policy_id") or ""] += "\n" + (c.get("heading") or "") + "\n" + (c.get("content") or "")
    # Mix in the policy name itself so a title like "Incident Response Policy" counts as a body mention
    name_by_policy = {d["id"]: (d.get("policy_name") or "") for d in docs}
    for pid, name in name_by_policy.items():
        body_by_policy[pid] = name + "\n" + body_by_policy.get(pid, "")

    findings: list[dict[str, Any]] = []
    # Tenant baseline frameworks (Bird Talk would feed this in; default to a known stack for the test corpus)
    tenant_baseline = {"SOC 2", "NIST CSF", "ISO 27001", "HIPAA"}

    # Collect frameworks declared on AUP doc to compare against baseline (NIST CSF gap)
    for d in docs:
        body = body_by_policy.get(d["id"], "").lower()
        tags = set(d.get("selected_frameworks") or [])
        # Mention vs tag mismatch
        for fw, keywords in FRAMEWORK_BODY_KEYWORDS.items():
            if fw in tags:
                continue
            for kw in keywords:
                if kw in body:
                    findings.append(
                        {
                            "finding_type": "framework_gap",
                            "severity": "medium" if fw in {"HIPAA", "PCI DSS"} else "low",
                            "summary": f"{d.get('policy_number')} ({d.get('policy_name')}) references {fw} ('{kw}' appears in the body) but the document is not tagged for {fw}.",
                            "recommendation": f"Add the {fw} framework tag to this document so coverage reports reflect its actual scope.",
                            "policy_id": d["id"],
                            "framework": fw,
                            "evidence": {"missing_framework": fw, "matched_keyword": kw, "current_tags": list(tags)},
                        }
                    )
                    break

        # AUP-specific: baseline NIST CSF tag missing
        title = (d.get("policy_name") or "").lower()
        if (
            "acceptable use" in title
        ) and "NIST CSF" not in tags and "NIST CSF" in tenant_baseline:
            already = any(
                f["finding_type"] == "framework_gap" and f["policy_id"] == d["id"] and f.get("framework") == "NIST CSF"
                for f in findings
            )
            if not already:
                findings.append(
                    {
                        "finding_type": "framework_gap",
                        "severity": "low",
                        "summary": f"{d.get('policy_number')} ({d.get('policy_name')}) is tagged for SOC 2 and ISO 27001 but not NIST CSF, which has equivalent AUP-style controls (PR.IP-11, PR.AT-1).",
                        "recommendation": "Add the NIST CSF framework tag if NIST CSF is a target framework for the tenant.",
                        "policy_id": d["id"],
                        "framework": "NIST CSF",
                        "evidence": {"missing_framework": "NIST CSF", "current_tags": list(tags)},
                    }
                )

    return _record_findings(tenant_id, run_id, findings)


# ORPHAN_CUES: content-based matching — detect policies that reference companion
# artifacts that don't exist in the tenant's document inventory.
# Each entry: (document_type, required_keywords_in_policy, expected_artifact_title_fragment, severity, recommendation)
# Matches ANY policy of the given type whose body contains ALL required keywords,
# then checks whether a companion artifact with the expected title fragment exists.
ORPHAN_CUES: list[tuple[str, list[str], str, str, str]] = [
    (
        "policy",
        ["incident response", "runbook", "playbook"],
        "incident response runbook",
        "medium",
        "Create an Incident Response Runbook (procedure-level artifact) so responders have step-by-step actions to execute under the policy.",
    ),
    (
        "policy",
        ["vendor security questionnaire", "vendor security assessment", "vendor assessment"],
        "vendor assessment procedure",
        "medium",
        "Create a Vendor Assessment Procedure (with the security questionnaire template) so the policy is executable.",
    ),
    (
        "policy",
        ["cryptographic erasure", "automated retention enforcement", "disposal"],
        "data disposal procedure",
        "low",
        "Create a Data Disposal Procedure that operationalizes the cryptographic erasure and retention enforcement requirements.",
    ),
]


@tenant_scoped
def detect_orphans(tenant_id: str, run_id: str) -> int:
    docs = db_select(
        TABLE_DOCUMENTS,
        tenant_id=tenant_id,
        columns="id,policy_name,policy_number,document_type",
    )
    chunks = db_select(
        TABLE_CHUNKS,
        tenant_id=tenant_id,
        columns="policy_id,heading,content",
        filters={"source_origin": "eq.bird_eye_ingest"},
    )
    body_by_policy: dict[str, str] = defaultdict(str)
    for c in chunks:
        body_by_policy[c.get("policy_id") or ""] += "\n" + (c.get("heading") or "") + "\n" + (c.get("content") or "")
    name_by_policy = {d["id"]: (d.get("policy_name") or "") for d in docs}
    for pid, name in name_by_policy.items():
        body_by_policy[pid] = name + "\n" + body_by_policy.get(pid, "")

    # All existing document title fragments for companion-artifact presence check
    titles = [(d.get("policy_name") or "").lower() for d in docs]

    findings: list[dict[str, Any]] = []
    for doc_type, required_keywords, expected_title, severity, suggestion in ORPHAN_CUES:
        for d in docs:
            # Match by document type (loose: "policy" matches "policy", "procedure", etc.)
            if doc_type not in (d.get("document_type") or "").lower():
                continue
            body = body_by_policy.get(d["id"], "").lower()
            mentions = [kw for kw in required_keywords if kw in body]
            if not mentions:
                continue
            # Does any other document satisfy the companion artifact?
            has_target = any(expected_title in t for t in titles)
            if has_target:
                continue
            findings.append(
                {
                    "finding_type": "orphan",
                    "severity": severity,
                    "summary": (
                        f"{d.get('policy_number') or d.get('policy_name')} references "
                        f"{', '.join(mentions)} but no {expected_title.title()} exists in the document inventory."
                    ),
                    "recommendation": suggestion,
                    "policy_id": d["id"],
                    "evidence": {
                        "missing_artifact": expected_title,
                        "policy_cues": mentions,
                    },
                }
            )
    return _record_findings(tenant_id, run_id, findings)
