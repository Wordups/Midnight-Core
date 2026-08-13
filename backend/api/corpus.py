"""Corpus + Answer Engine API.

Serves the structured compliance corpus and answers questionnaires from it.
Auth (verify_access) is attached at registration in main.py; plan fencing and
LLM accounting live here so backend/core/corpus.py stays pure.
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from backend.billing_plans import limits_for, resolve_plan
from backend.bird_eye.db import select as db_select
from backend.core.corpus import (
    MAX_QUESTIONS,
    USE_CASES,
    answer_batch,
    build_corpus_index,
    load_corpus_sections,
    split_questionnaire,
)
from backend.storage.file_store import (
    SupabaseStoreError,
    count_activity_for_tenant,
    create_activity_event,
)

logger = logging.getLogger("midnight.corpus.api")

router = APIRouter(prefix="/api/v1/corpus", tags=["corpus"])

RUNS_PAGE_SIZE = 20


def _tenant_id(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return tenant_id


def _upgrade_403(plan: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": "upgrade_required", "plan": plan, "message": message},
    )


def _enforce_corpus_fence(request: Request, tenant_id: str) -> None:
    plan = resolve_plan(getattr(request.state, "plan_type", None))
    cap = limits_for(plan).get("corpus_runs_per_month")
    if cap is None:
        return
    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    try:
        used = count_activity_for_tenant(tenant_id, action="corpus_answered", since=month_start)
    except SupabaseStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if used >= cap:
        raise _upgrade_403(
            plan,
            f"The {plan} plan includes {cap} questionnaire runs per month. Upgrade for more.",
        )


def _llm_for_request(request: Request) -> tuple[Any, str]:
    """Constrained-verdict callable + model name for this tenant's plan."""
    from backend.api.routes import (  # late import: routes pulls heavy deps
        CREATIVE_MODEL,
        STRUCTURAL_MODEL,
        _get_anthropic_client,
    )

    plan_limits = limits_for(getattr(request.state, "plan_type", None))
    model = STRUCTURAL_MODEL if plan_limits.get("haiku_only") else CREATIVE_MODEL
    client = _get_anthropic_client()

    def llm(prompt: str) -> dict[str, Any]:
        response = client.messages.create(
            model=model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = getattr(response, "usage", None)
        return {
            "text": response.content[0].text if response.content else "",
            "input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(usage, "output_tokens", 0) or 0,
            # The provider switch may route to a different backend than the
            # configured Anthropic id — report what actually answered.
            "model": getattr(response, "model", None) or model,
        }

    return llm, model


class AnswerRequest(BaseModel):
    questions: list[str] | None = None
    raw_text: str | None = None
    use_case: str = Field(default="questionnaire")


@router.get("")
def corpus_index(request: Request) -> dict[str, Any]:
    tenant_id = _tenant_id(request)
    try:
        return build_corpus_index(tenant_id)
    except Exception as exc:
        logger.error("corpus index failed: %s", exc)
        raise HTTPException(status_code=503, detail="Corpus index is unavailable.") from exc


@router.post("/answer")
def corpus_answer(payload: AnswerRequest, request: Request) -> dict[str, Any]:
    tenant_id = _tenant_id(request)

    if payload.use_case not in USE_CASES:
        raise HTTPException(
            status_code=422,
            detail=f"use_case must be one of {', '.join(USE_CASES)}.",
        )
    questions = [q.strip() for q in (payload.questions or []) if q.strip()]
    if not questions:
        questions = split_questionnaire(payload.raw_text or "")
    if not questions:
        raise HTTPException(status_code=422, detail="No questions could be extracted from the input.")
    if len(questions) > MAX_QUESTIONS:
        raise HTTPException(
            status_code=413,
            detail=f"{len(questions)} questions submitted; the limit is {MAX_QUESTIONS} per run.",
        )

    from backend.core.ratelimit import allow as _rate_allow

    if not _rate_allow(f"corpus:{tenant_id}", max_hits=10, window_seconds=300):
        raise HTTPException(
            status_code=429,
            detail="Too many questionnaire runs — wait a few minutes and try again.",
        )

    _enforce_corpus_fence(request, tenant_id)

    try:
        sections = load_corpus_sections(tenant_id)
    except Exception as exc:
        logger.error("corpus sections load failed: %s", exc)
        raise HTTPException(status_code=503, detail="Corpus is unavailable.") from exc
    if not sections:
        raise HTTPException(
            status_code=409,
            detail="The corpus is empty. Ingest or generate at least one document first.",
        )

    llm, model = _llm_for_request(request)
    run = answer_batch(
        tenant_id,
        questions,
        use_case=payload.use_case,
        llm=llm,
        model_name=model,
        sections=sections,
    )
    try:
        create_activity_event(tenant_id=tenant_id, action="corpus_answered")
    except Exception as exc:  # accounting must not fail the run
        logger.warning("corpus activity event failed: %s", exc)
    return run


MAX_QUESTIONNAIRE_FILE_BYTES = 2 * 1024 * 1024


def _questions_from_rows(rows: list[list[str]]) -> list[str]:
    """SIG/CAIQ-style sheets: take the longest text cell per row as the question."""
    questions: list[str] = []
    for row in rows:
        cells = [str(c or "").strip() for c in row]
        # 12-char floor keeps IDs, refs, and header words ("Question") out
        # while real assessment questions comfortably clear it.
        cells = [c for c in cells if len(c) >= 12]
        if cells:
            questions.append(max(cells, key=len))
    return questions


@router.post("/parse")
async def corpus_parse_questionnaire(request: Request, file: UploadFile = File(...)) -> dict[str, Any]:
    """Parse an uploaded questionnaire file into questions for the runner.

    Returns questions for review in the paste box — parsing never triggers a
    run (and therefore never spends LLM tokens).
    """
    _tenant_id(request)
    raw = await file.read()
    if len(raw) > MAX_QUESTIONNAIRE_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Questionnaire file is larger than 2 MB.")
    name = (file.filename or "").lower()

    if name.endswith((".txt", ".md")):
        questions = split_questionnaire(raw.decode("utf-8", errors="ignore"))
    elif name.endswith((".csv", ".tsv")):
        import csv
        import io as _io

        delimiter = "\t" if name.endswith(".tsv") else ","
        reader = csv.reader(_io.StringIO(raw.decode("utf-8-sig", errors="ignore")), delimiter=delimiter)
        questions = _questions_from_rows(list(reader))
    elif name.endswith(".xlsx"):
        try:
            import openpyxl  # optional dependency
        except ImportError as exc:
            raise HTTPException(
                status_code=415,
                detail="XLSX parsing is not enabled on this server — export the sheet as CSV instead.",
            ) from exc
        import io as _io

        wb = openpyxl.load_workbook(_io.BytesIO(raw), read_only=True, data_only=True)
        rows = [[cell for cell in row] for row in wb.active.iter_rows(values_only=True)]
        questions = _questions_from_rows(rows)
    else:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type — use .csv, .tsv, .txt, .md, or .xlsx.",
        )

    truncated = len(questions) > MAX_QUESTIONS
    return {
        "questions": questions[:MAX_QUESTIONS],
        "count": min(len(questions), MAX_QUESTIONS),
        "truncated": truncated,
    }


@router.get("/runs")
def corpus_runs(request: Request) -> dict[str, Any]:
    tenant_id = _tenant_id(request)
    rows = db_select(
        "corpus_runs",
        tenant_id=tenant_id,
        columns="*",
        order="created_at.desc",
        limit=RUNS_PAGE_SIZE,
    )
    return {"runs": rows}


def _load_run(tenant_id: str, run_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    runs = db_select(
        "corpus_runs",
        tenant_id=tenant_id,
        columns="*",
        filters={"id": f"eq.{run_id}"},
    )
    if not runs:
        raise HTTPException(status_code=404, detail="Run not found.")
    answers = db_select(
        "corpus_answers",
        tenant_id=tenant_id,
        columns="*",
        filters={"run_id": f"eq.{run_id}"},
        order="position.asc",
    )
    return runs[0], answers


@router.get("/runs/{run_id}")
def corpus_run_detail(run_id: str, request: Request) -> dict[str, Any]:
    tenant_id = _tenant_id(request)
    run, answers = _load_run(tenant_id, run_id)
    return {"run": run, "answers": answers}


@router.get("/runs/{run_id}/export")
def corpus_run_export(run_id: str, request: Request) -> PlainTextResponse:
    tenant_id = _tenant_id(request)
    run, answers = _load_run(tenant_id, run_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["#", "question", "status", "answer", "confidence", "citations", "control_ids", "followup_question", "provenance"]
    )
    for answer in answers:
        citations = "; ".join(
            f"{c.get('policy_name')} — {c.get('section_heading')}: \"{c.get('quote')}\""
            for c in (answer.get("citations") or [])
        )
        writer.writerow(
            [
                answer.get("position", 0) + 1,
                answer.get("question", ""),
                answer.get("status", ""),
                answer.get("answer_text", ""),
                answer.get("confidence", ""),
                citations,
                ", ".join(answer.get("control_ids") or []),
                answer.get("followup_question") or "",
                answer.get("provenance", ""),
            ]
        )
    filename = f"corpus-run-{run.get('created_at', run_id)[:10]}.csv"
    return PlainTextResponse(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
