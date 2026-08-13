"""Corpus + Answer Engine core.

Serves the structured compliance corpus for audits, security questionnaires,
vendor assessments, and internal security requests. Deterministic first; the
LLM step is constrained, cited, and fail-closed per
knowledge/vendor_risk_process_spec.md. No HTTP in this module — the router
wires auth, plan fencing, and the real Anthropic client.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Callable

from backend.bird_eye.db import insert as db_insert, select as db_select
from backend.bird_eye.embeddings import cosine, embed_chunks
from backend.core.gap_engine import is_control_covered, load_control_registry
from backend.core.json_parser import ParsedModelOutputError, parse_model_json

logger = logging.getLogger("midnight.corpus")

TOP_K = 6
SIMILARITY_FLOOR = 0.35
MAX_QUESTIONS = 50
STALE_AFTER_DAYS = 365
MAX_SECTION_CHARS = 1600
MAX_CITATIONS = 4
MAX_CANDIDATE_CONTROLS = 30

STATUSES = (
    "satisfied",
    "partially_satisfied",
    "not_satisfied",
    "insufficient_evidence",
    "not_applicable",
)
CONFIDENCES = ("high", "medium", "low")
USE_CASES = ("audit", "questionnaire", "vendor_assessment", "internal")

# The assessment stance from knowledge/vendor_risk_process_spec.md, applied to
# answering inbound questions from the tenant's own corpus.
ANSWER_PROMPT = """You are a compliance analyst answering an assessment question strictly from an organization's policy corpus.

Rules:
- Answer ONLY from the policy sections provided below. They are the complete evidence available.
- A claim is established only if the sections actually support it. Do not infer controls that are not written down.
- If the sections do not establish an answer, status is "insufficient_evidence". Never guess.
- If the question does not apply to this organization based on the sections, status is "not_applicable".
- Quotes in citations must be exact substrings of the provided section text.
- Map your conclusion to the applicable control IDs from the candidate list when justified.
- When status is partially_satisfied, not_satisfied, or insufficient_evidence, propose ONE targeted follow-up question that would resolve the requirement (challenge vague claims; ask for the specific standard, scope, or evidence).
- You recommend a classification; consequential risk decisions belong to humans.

Return JSON only — no markdown fences, no prose. Exact schema:
{{
  "status": "satisfied" | "partially_satisfied" | "not_satisfied" | "insufficient_evidence" | "not_applicable",
  "answer_text": "1-3 sentence answer written for an assessor",
  "citations": [{{"section_id": "...", "quote": "exact substring of that section"}}],
  "control_ids": ["..."],
  "confidence": "high" | "medium" | "low",
  "followup_question": "..." or null
}}

Candidate control IDs:
{controls}

Policy sections (id | document | heading):
{sections}

Question:
{question}"""


# ── corpus index ─────────────────────────────────────────────────────────


def _parse_iso(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def build_corpus_index(tenant_id: str) -> dict[str, Any]:
    """Deterministic structured view of the tenant's compliance corpus."""
    docs = db_select(
        "policies",
        tenant_id=tenant_id,
        columns="*",
        order="created_at.desc",
    )
    registry = load_control_registry()
    by_id = {c.id: c for c in registry}
    now = datetime.now(timezone.utc)

    documents: list[dict[str, Any]] = []
    covered_union: set[str] = set()
    stale_count = 0
    unmapped: list[str] = []

    for doc in docs:
        covered = [cid for cid in (doc.get("covered_control_ids") or []) if cid in by_id]
        covered_union.update(covered)
        reviewed = (
            _parse_iso(doc.get("last_reviewed_at"))
            or _parse_iso(doc.get("updated_at"))
            or _parse_iso(doc.get("created_at"))
        )
        age_days = (now - reviewed).days if reviewed else None
        stale = age_days is not None and age_days > STALE_AFTER_DAYS
        if stale:
            stale_count += 1
        if not covered:
            unmapped.append(doc.get("policy_name") or doc.get("id"))
        frameworks = sorted({by_id[cid].framework for cid in covered})
        documents.append(
            {
                "id": doc.get("id"),
                "name": doc.get("policy_name"),
                "document_type": doc.get("document_type"),
                "frameworks": frameworks or (doc.get("selected_frameworks") or []),
                "controls_covered": len(covered),
                "control_ids": covered,
                "last_reviewed_at": doc.get("last_reviewed_at") or doc.get("updated_at") or doc.get("created_at"),
                "age_days": age_days,
                "stale": stale,
            }
        )

    frameworks_out: list[dict[str, Any]] = []
    totals: dict[str, int] = {}
    covered_counts: dict[str, int] = {}
    for control in registry:
        totals[control.framework] = totals.get(control.framework, 0) + 1
        if is_control_covered(control.id, covered_union):
            covered_counts[control.framework] = covered_counts.get(control.framework, 0) + 1
    for framework in sorted(totals):
        total = totals[framework]
        covered_n = covered_counts.get(framework, 0)
        frameworks_out.append(
            {
                "framework": framework,
                "total_controls": total,
                "covered_controls": covered_n,
                "coverage_pct": round(100.0 * covered_n / total, 1) if total else 0.0,
            }
        )

    return {
        "document_count": len(documents),
        "documents": documents,
        "frameworks": frameworks_out,
        "controls_covered_total": len(covered_union),
        "controls_total": len(registry),
        "stale_count": stale_count,
        "unmapped_documents": unmapped,
        "generated_at": now.isoformat(),
    }


# ── questionnaire splitting ──────────────────────────────────────────────

_QUESTION_LEAD_RE = re.compile(
    r"^\s*(?:q(?:uestion)?\s*)?(?:\d{1,3})(?:[.):\-])\s+|^\s*[-*•]\s+",
    re.IGNORECASE,
)
MIN_QUESTION_CHARS = 8


def split_questionnaire(raw_text: str) -> list[str]:
    """Deterministic splitter: numbered items, bullets, or one per line.

    Continuation lines (no list marker) are folded into the current question
    when the text uses list markers; in plain mode every non-empty line is a
    question.
    """
    text = (raw_text or "").strip()
    if not text:
        return []
    lines = text.splitlines()
    has_markers = any(_QUESTION_LEAD_RE.match(ln) for ln in lines)

    questions: list[str] = []
    if has_markers:
        current: list[str] = []
        for ln in lines:
            if _QUESTION_LEAD_RE.match(ln):
                if current:
                    questions.append(" ".join(current))
                current = [_QUESTION_LEAD_RE.sub("", ln).strip()]
            elif ln.strip():
                if current:
                    current.append(ln.strip())
                else:
                    current = [ln.strip()]
            else:
                if current:
                    questions.append(" ".join(current))
                    current = []
        if current:
            questions.append(" ".join(current))
    else:
        questions = [ln.strip() for ln in lines if ln.strip()]

    return [q for q in questions if len(q) >= MIN_QUESTION_CHARS]


# ── retrieval ────────────────────────────────────────────────────────────


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
            data = json.loads(s)
            if isinstance(data, list):
                return [float(x) for x in data]
        except Exception:
            return None
    return None


def load_corpus_sections(tenant_id: str) -> list[dict[str, Any]]:
    """Load embedded sections joined with their document names, once per run."""
    sections = db_select(
        "policy_sections",
        tenant_id=tenant_id,
        columns="id,policy_id,heading,content,embedding",
        filters={"embedding": "not.is.null"},
    )
    docs = db_select("policies", tenant_id=tenant_id, columns="id,policy_name,covered_control_ids")
    doc_meta = {d["id"]: d for d in docs}
    out = []
    for row in sections:
        vec = _coerce_embedding(row.get("embedding"))
        if not vec or not (row.get("content") or "").strip():
            continue
        meta = doc_meta.get(row.get("policy_id")) or {}
        out.append(
            {
                "id": row.get("id"),
                "policy_id": row.get("policy_id"),
                "policy_name": meta.get("policy_name") or "Unknown document",
                "covered_control_ids": meta.get("covered_control_ids") or [],
                "heading": row.get("heading") or "",
                "content": row.get("content") or "",
                "vector": vec,
            }
        )
    return out


def retrieve_sections(
    question: str,
    sections: list[dict[str, Any]],
    *,
    top_k: int = TOP_K,
    floor: float = SIMILARITY_FLOOR,
    qvec: list[float] | None = None,
) -> list[dict[str, Any]]:
    if not sections:
        return []
    if qvec is None:
        qvec = embed_chunks([question], input_type="query")[0]
    scored = []
    for sec in sections:
        sim = cosine(qvec, sec["vector"])
        if sim >= floor:
            scored.append((sim, sec))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [dict(sec, similarity=round(sim, 4)) for sim, sec in scored[:top_k]]


# ── answering ────────────────────────────────────────────────────────────


def _normalize_ws(text: str) -> str:
    return " ".join((text or "").split())


def _insufficient(question: str, note: str, *, provenance: str = "deterministic") -> dict[str, Any]:
    return {
        "question": question,
        "status": "insufficient_evidence",
        "answer_text": note,
        "citations": [],
        "control_ids": [],
        "confidence": "low",
        "followup_question": None,
        "provenance": provenance,
    }


def _validate_answer(
    payload: Any,
    retrieved: list[dict[str, Any]],
    question: str,
) -> dict[str, Any]:
    """Validate the model verdict; fail closed on anything malformed."""
    if not isinstance(payload, dict):
        raise ParsedModelOutputError("verdict is not an object")
    status = payload.get("status")
    if status not in STATUSES:
        raise ParsedModelOutputError(f"invalid status: {status!r}")
    answer_text = str(payload.get("answer_text") or "").strip()
    if not answer_text:
        raise ParsedModelOutputError("empty answer_text")
    confidence = payload.get("confidence")
    if confidence not in CONFIDENCES:
        confidence = "low"

    by_section = {sec["id"]: _normalize_ws(sec["content"]) for sec in retrieved}
    section_names = {sec["id"]: sec["policy_name"] for sec in retrieved}
    section_headings = {sec["id"]: sec["heading"] for sec in retrieved}
    citations = []
    stripped_any = False
    raw_citations = payload.get("citations") or []
    if not isinstance(raw_citations, list):
        raw_citations = []
    for cit in raw_citations[:MAX_CITATIONS * 2]:
        if not isinstance(cit, dict):
            stripped_any = True
            continue
        sec_id = cit.get("section_id")
        quote = _normalize_ws(str(cit.get("quote") or ""))
        if sec_id in by_section and quote and quote in by_section[sec_id]:
            citations.append(
                {
                    "section_id": sec_id,
                    "policy_id": next((s["policy_id"] for s in retrieved if s["id"] == sec_id), None),
                    "policy_name": section_names[sec_id],
                    "section_heading": section_headings[sec_id],
                    "quote": quote,
                }
            )
        else:
            stripped_any = True
    citations = citations[:MAX_CITATIONS]
    if stripped_any and confidence != "low":
        confidence = "medium" if confidence == "high" else "low"

    # A satisfied/partial verdict with no surviving citation is not evidenced.
    if status in ("satisfied", "partially_satisfied") and not citations:
        return _insufficient(
            question,
            "The model asserted coverage but provided no verifiable citation from the corpus.",
            provenance="ai_assisted",
        )

    candidate_ids = {cid for sec in retrieved for cid in sec["covered_control_ids"]}
    control_ids = [
        cid for cid in (payload.get("control_ids") or [])
        if isinstance(cid, str) and cid in candidate_ids
    ][:MAX_CANDIDATE_CONTROLS]

    followup = payload.get("followup_question")
    followup = str(followup).strip() if isinstance(followup, str) and followup.strip() else None

    return {
        "question": question,
        "status": status,
        "answer_text": answer_text,
        "citations": citations,
        "control_ids": control_ids,
        "confidence": confidence,
        "followup_question": followup,
        "provenance": "ai_assisted",
    }


def _build_prompt(question: str, retrieved: list[dict[str, Any]]) -> str:
    controls = sorted({cid for sec in retrieved for cid in sec["covered_control_ids"]})[:MAX_CANDIDATE_CONTROLS]
    blocks = []
    for sec in retrieved:
        content = sec["content"][:MAX_SECTION_CHARS]
        blocks.append(f"[{sec['id']} | {sec['policy_name']} | {sec['heading']}]\n{content}")
    return ANSWER_PROMPT.format(
        controls=", ".join(controls) or "(none mapped yet)",
        sections="\n\n".join(blocks),
        question=question,
    )


def answer_question(
    tenant_id: str,
    question: str,
    *,
    llm: Callable[[str], dict[str, Any]],
    sections: list[dict[str, Any]] | None = None,
    qvec: list[float] | None = None,
) -> dict[str, Any]:
    """Answer one question from the corpus. Fail-closed at every step.

    `llm` takes a prompt and returns
    {"text": str, "input_tokens": int, "output_tokens": int}.
    """
    if sections is None:
        sections = load_corpus_sections(tenant_id)
    retrieved = retrieve_sections(question, sections, qvec=qvec)
    if not retrieved:
        answer = _insufficient(
            question,
            "No sufficiently relevant policy sections were found in the corpus for this question.",
        )
        answer["usage"] = {"input_tokens": 0, "output_tokens": 0}
        return answer

    result: dict[str, Any] = {}
    try:
        result = llm(_build_prompt(question, retrieved)) or {}
        payload = parse_model_json(result.get("text") or "")
        answer = _validate_answer(payload, retrieved, question)
    except (ParsedModelOutputError, KeyError, TypeError, ValueError) as exc:
        logger.warning("corpus verdict failed closed: %s", exc)
        answer = _insufficient(
            question,
            "The analysis could not be validated and was withheld. Route to a human reviewer.",
            provenance="ai_assisted",
        )
    answer["usage"] = {
        "input_tokens": int(result.get("input_tokens") or 0),
        "output_tokens": int(result.get("output_tokens") or 0),
        "model": str(result.get("model") or ""),
    }
    return answer


def answer_batch(
    tenant_id: str,
    questions: list[str],
    *,
    use_case: str,
    llm: Callable[[str], dict[str, Any]],
    model_name: str = "",
    sections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Answer a questionnaire and persist the run. Never fails mid-run."""
    if use_case not in USE_CASES:
        use_case = "questionnaire"
    questions = questions[:MAX_QUESTIONS]
    if sections is None:
        try:
            sections = load_corpus_sections(tenant_id)
        except Exception as exc:
            logger.error("corpus section load failed: %s", exc)
            sections = []

    # One batched embedding call per run: per-question calls trip free-tier
    # rate limits (Voyage 429) and fail questions that have perfectly good
    # corpus coverage.
    qvecs: list[list[float]] | None = None
    if sections and questions:
        try:
            qvecs = embed_chunks(questions, input_type="query")
        except Exception as exc:
            logger.warning("batch query embedding failed; falling back per-question: %s", exc)

    answers: list[dict[str, Any]] = []
    input_tokens = 0
    output_tokens = 0
    actual_model = model_name
    for idx, question in enumerate(questions):
        qvec = qvecs[idx] if qvecs and idx < len(qvecs) else None
        try:
            answer = answer_question(tenant_id, question, llm=llm, sections=sections, qvec=qvec)
        except Exception as exc:  # outage mid-run: degrade, don't 500
            logger.error("corpus answer failed hard for %r: %s", question[:80], exc)
            answer = _insufficient(
                question,
                "Analysis was unavailable for this question. Route to a human reviewer.",
            )
            answer["usage"] = {"input_tokens": 0, "output_tokens": 0}
        usage = answer.pop("usage", {})
        input_tokens += usage.get("input_tokens", 0)
        output_tokens += usage.get("output_tokens", 0)
        if usage.get("model"):
            actual_model = usage["model"]
        answers.append(answer)

    counts = {status: 0 for status in STATUSES}
    for answer in answers:
        counts[answer["status"]] += 1

    run_row = {
        "tenant_id": tenant_id,
        "use_case": use_case,
        "question_count": len(answers),
        "satisfied_count": counts["satisfied"],
        "partial_count": counts["partially_satisfied"],
        "not_satisfied_count": counts["not_satisfied"],
        "insufficient_count": counts["insufficient_evidence"],
        "not_applicable_count": counts["not_applicable"],
        "model": actual_model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    run_id = None
    try:
        inserted = db_insert("corpus_runs", run_row)
        run_id = inserted[0]["id"] if inserted else None
        if run_id:
            db_insert(
                "corpus_answers",
                [
                    {
                        "run_id": run_id,
                        "tenant_id": tenant_id,
                        "position": idx,
                        **{k: v for k, v in answer.items() if k != "provenance"},
                        "provenance": answer["provenance"],
                    }
                    for idx, answer in enumerate(answers)
                ],
            )
    except Exception as exc:
        logger.error("corpus run persistence failed: %s", exc)

    return {
        "run_id": run_id,
        "use_case": use_case,
        "question_count": len(answers),
        "counts": counts,
        "model": actual_model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "answers": answers,
    }
