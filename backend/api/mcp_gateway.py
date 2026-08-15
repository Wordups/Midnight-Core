"""
Midnight Core — remote MCP gateway (the AI handshake).

Serves Midnight's tools to ANY MCP-speaking client — Claude (custom
connectors), ChatGPT (connectors), Cursor, agents — over MCP's Streamable
HTTP transport at POST /mcp. Auth is a per-tenant API key minted in Settings
(Authorization: Bearer mk_…), so a customer pastes one URL + key and their
assistant becomes a GRC copilot over *their* corpus, inside their plan fences.

Implementation note: this speaks the MCP protocol directly (JSON-RPC 2.0,
stateless server responses, protocol negotiation on initialize) instead of
importing the MCP SDK — the SDK's dependency tree conflicts with the app's
pinned FastAPI (which is why mcp_server/ has its own venv). The protocol
surface a tools-only stateless server needs is small: initialize,
notifications/*, tools/list, tools/call, ping.

Mounted WITHOUT verify_access (like the Stripe webhook) — the API key is the
auth. Every tools/call is recorded in the tenant's activity feed: an AI
acting on a GRC platform should itself be auditable.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request, Response

from backend.billing_plans import limits_for, resolve_plan
from backend.bird_eye.db import select as db_select
from backend.core.corpus import (
    MAX_QUESTIONS,
    USE_CASES,
    answer_batch,
    build_corpus_index,
    load_corpus_sections,
)
from backend.core.ratelimit import allow as rate_allow
from backend.integrations.api_keys import verify_key
from backend.integrations.jira_sync import detect_gaps
from backend.storage.file_store import create_activity_event, create_signal_activity_event
from backend.storage.supabase_client import supabase_admin

logger = logging.getLogger("midnight.mcp")

router = APIRouter(tags=["mcp"])

PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}
DEFAULT_PROTOCOL = "2025-06-18"
SERVER_INFO = {"name": "midnight", "title": "Midnight GRC", "version": "2.0.0"}


# ── tool definitions ─────────────────────────────────────────────────────────

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_posture",
        "description": "The tenant's compliance posture: document count, framework "
                       "coverage percentages, and open gaps by severity with the top "
                       "gap details. Start here for any 'where do we stand' question.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "answer_questions",
        "description": "Answer security-questionnaire questions from the tenant's "
                       "evidence corpus with citations. Fails closed: no evidence, no "
                       "yes. Counts against the plan's monthly questionnaire runs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "questions": {"type": "array", "items": {"type": "string"},
                              "description": "The questions to answer (max %d)." % MAX_QUESTIONS},
                "use_case": {"type": "string", "enum": sorted(USE_CASES),
                             "description": "Answering register.", "default": "questionnaire"},
            },
            "required": ["questions"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_runs",
        "description": "Recent questionnaire runs (id, status, question count, created).",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_run",
        "description": "One run's full answers with citations, by run id.",
        "inputSchema": {
            "type": "object",
            "properties": {"run_id": {"type": "string"}},
            "required": ["run_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "assign_to_reviewer",
        "description": "File a review request into the tenant's Requests inbox — e.g. "
                       "'confirm MFA is enforced on the admin console'. Use for anything "
                       "needing a human decision or evidence collection.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short imperative title."},
                "description": {"type": "string"},
                "control_id": {"type": "string", "description": "Optional control, e.g. SOC2-CC6.1."},
            },
            "required": ["title"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_requests",
        "description": "Open and recent review requests in the tenant's inbox.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]


# ── tool implementations (tenant-scoped, plan-fenced) ────────────────────────

def _plan_type(tenant_id: str) -> str:
    try:
        res = supabase_admin.table("tenants").select("plan_type").eq("id", tenant_id).limit(1).execute()
        rows = res.data or []
        return resolve_plan(rows[0].get("plan_type") if rows else None)
    except Exception:
        return resolve_plan(None)


def _llm_for_plan(plan_type: str):
    from backend.api.routes import (  # late import: routes pulls heavy deps
        CREATIVE_MODEL,
        STRUCTURAL_MODEL,
        _get_anthropic_client,
    )

    model = STRUCTURAL_MODEL if limits_for(plan_type).get("haiku_only") else CREATIVE_MODEL
    client = _get_anthropic_client()

    def llm(prompt: str) -> dict[str, Any]:
        response = client.messages.create(
            model=model, max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = getattr(response, "usage", None)
        return {
            "text": response.content[0].text if response.content else "",
            "input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "output_tokens": getattr(usage, "output_tokens", 0) or 0,
            "model": getattr(response, "model", None) or model,
        }

    return llm, model


class ToolError(Exception):
    """User-visible tool failure — returned as an MCP tool error, not a
    protocol error."""


def _tool_get_posture(tenant_id: str, args: dict) -> dict:
    index = {}
    try:
        index = build_corpus_index(tenant_id) or {}
    except Exception:
        pass
    gaps = detect_gaps(tenant_id) or {}
    return {
        "documents": index.get("document_count", 0),
        "controls_covered": index.get("controls_covered_total"),
        "controls_total": index.get("controls_total"),
        "coverage_by_framework": gaps.get("coverage_by_framework", {}),
        "overall_coverage_pct": gaps.get("overall_coverage_pct"),
        "total_gaps": gaps.get("total_gaps", 0),
        "gaps_critical": gaps.get("gaps_critical", 0),
        "gaps_medium": gaps.get("gaps_medium", 0),
        "gaps_low": gaps.get("gaps_low", 0),
        "top_gaps": (gaps.get("gaps") or [])[:10],
    }


def _tool_answer_questions(tenant_id: str, args: dict) -> dict:
    questions = [str(q).strip() for q in (args.get("questions") or []) if str(q).strip()]
    if not questions:
        raise ToolError("Provide at least one question.")
    if len(questions) > MAX_QUESTIONS:
        raise ToolError(f"{len(questions)} questions submitted; the limit is {MAX_QUESTIONS} per run.")
    use_case = args.get("use_case") or "questionnaire"
    if use_case not in USE_CASES:
        raise ToolError(f"use_case must be one of {', '.join(sorted(USE_CASES))}.")

    plan = _plan_type(tenant_id)
    cap = limits_for(plan).get("corpus_runs_per_month")
    if cap is not None:
        from backend.storage.file_store import count_activity_for_tenant
        month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if count_activity_for_tenant(tenant_id, action="corpus_answered", since=month_start) >= cap:
            raise ToolError(f"The {plan} plan includes {cap} questionnaire runs per month. "
                            "Upgrade in the Midnight dashboard for more.")

    sections = load_corpus_sections(tenant_id)
    if not sections:
        raise ToolError("The corpus is empty — ingest or generate at least one document in Midnight first.")

    llm, model = _llm_for_plan(plan)
    run = answer_batch(tenant_id, questions, use_case=use_case,
                       llm=llm, model_name=model, sections=sections)
    try:
        create_activity_event(tenant_id=tenant_id, action="corpus_answered")
    except Exception:
        pass
    return run


def _tool_list_runs(tenant_id: str, args: dict) -> dict:
    rows = db_select("corpus_runs", tenant_id=tenant_id, columns="*",
                     order="created_at.desc", limit=20)
    return {"runs": rows}


def _tool_get_run(tenant_id: str, args: dict) -> dict:
    run_id = str(args.get("run_id") or "").strip()
    if not run_id:
        raise ToolError("run_id is required.")
    runs = db_select("corpus_runs", tenant_id=tenant_id, columns="*",
                     filters={"id": f"eq.{run_id}"})
    if not runs:
        raise ToolError("Run not found.")
    answers = db_select("corpus_answers", tenant_id=tenant_id, columns="*",
                        filters={"run_id": f"eq.{run_id}"}, order="position.asc")
    return {"run": runs[0], "answers": answers}


def _tool_assign_to_reviewer(tenant_id: str, args: dict) -> dict:
    title = str(args.get("title") or "").strip()
    if len(title) < 3:
        raise ToolError("A title of at least 3 characters is required.")
    row = {
        "tenant_id": tenant_id,
        "title": title[:200],
        "description": str(args.get("description") or "").strip()[:4000] or None,
        "control_id": str(args.get("control_id") or "").strip()[:60] or None,
        "status": "open",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    res = supabase_admin.table("requests").insert(row).execute()
    created = (res.data or [row])[0]
    return {"created": True, "id": created.get("id"), "title": row["title"],
            "status": "open"}


def _tool_list_requests(tenant_id: str, args: dict) -> dict:
    res = (supabase_admin.table("requests")
           .select("id,title,control_id,status,due_date,created_at")
           .eq("tenant_id", tenant_id).order("created_at", desc=True).limit(20).execute())
    return {"requests": res.data or []}


_TOOL_IMPL = {
    "get_posture": _tool_get_posture,
    "answer_questions": _tool_answer_questions,
    "list_runs": _tool_list_runs,
    "get_run": _tool_get_run,
    "assign_to_reviewer": _tool_assign_to_reviewer,
    "list_requests": _tool_list_requests,
}


# ── JSON-RPC plumbing ────────────────────────────────────────────────────────

def _rpc_result(msg_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _rpc_error(msg_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _handle_message(msg: dict, tenant_id: str) -> dict | None:
    """One JSON-RPC message → response dict, or None for notifications."""
    method = msg.get("method", "")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    if method.startswith("notifications/"):
        return None

    if method == "initialize":
        requested = str(params.get("protocolVersion") or "")
        version = requested if requested in PROTOCOL_VERSIONS else DEFAULT_PROTOCOL
        return _rpc_result(msg_id, {
            "protocolVersion": version,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
            "instructions": "Midnight is a GRC platform. Use get_posture first for "
                            "context; answer_questions answers from cited evidence and "
                            "fails closed on missing proof; assign_to_reviewer files "
                            "work for humans.",
        })

    if method == "ping":
        return _rpc_result(msg_id, {})

    if method == "tools/list":
        return _rpc_result(msg_id, {"tools": TOOLS})

    if method == "tools/call":
        name = str(params.get("name") or "")
        impl = _TOOL_IMPL.get(name)
        if impl is None:
            return _rpc_error(msg_id, -32602, f"Unknown tool: {name}")
        args = params.get("arguments") or {}
        try:
            result = impl(tenant_id, args)
            content = [{"type": "text", "text": json.dumps(result, default=str)}]
            _audit_call(tenant_id, name, error=False)
            return _rpc_result(msg_id, {"content": content, "isError": False})
        except ToolError as exc:
            _audit_call(tenant_id, name, error=True)
            return _rpc_result(msg_id, {
                "content": [{"type": "text", "text": str(exc)}], "isError": True,
            })
        except Exception as exc:
            logger.warning("mcp tool %s failed for %s: %s", name, tenant_id, exc)
            _audit_call(tenant_id, name, error=True)
            return _rpc_result(msg_id, {
                "content": [{"type": "text", "text": "The tool failed unexpectedly. Try again."}],
                "isError": True,
            })

    return _rpc_error(msg_id, -32601, f"Method not found: {method}")


def _audit_call(tenant_id: str, tool: str, *, error: bool) -> None:
    try:
        create_signal_activity_event(
            tenant_id=tenant_id, event_type="mcp_tool_call", source="mcp.gateway",
            summary=f"AI connector called {tool}" + (" (failed)" if error else ""),
            metadata={"tool": tool, "error": error},
        )
    except Exception:
        pass


# ── HTTP surface ─────────────────────────────────────────────────────────────

def _unauthorized() -> Response:
    return Response(
        content=json.dumps({"error": "Missing or invalid API key. Mint one in "
                            "Midnight → Integrations → AI Connector, and send it as "
                            "'Authorization: Bearer mk_…'."}),
        status_code=401, media_type="application/json",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/mcp")
async def mcp_endpoint(request: Request) -> Response:
    auth = request.headers.get("authorization", "")
    key = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    tenant_id = verify_key(key)
    if not tenant_id:
        return _unauthorized()

    if not rate_allow(f"mcp:{tenant_id}", max_hits=60, window_seconds=300):
        return Response(
            content=json.dumps({"error": "Rate limit exceeded — wait a few minutes."}),
            status_code=429, media_type="application/json",
        )

    try:
        body = await request.json()
    except Exception:
        return Response(
            content=json.dumps(_rpc_error(None, -32700, "Parse error")),
            status_code=400, media_type="application/json",
        )

    messages = body if isinstance(body, list) else [body]
    responses = [r for r in (_handle_message(m, tenant_id) for m in messages if isinstance(m, dict))
                 if r is not None]

    if not responses:  # notification(s) only
        return Response(status_code=202)
    payload = responses if isinstance(body, list) else responses[0]
    return Response(content=json.dumps(payload), media_type="application/json")


@router.get("/mcp")
async def mcp_get() -> Response:
    # Stateless server: no server-initiated SSE stream on offer.
    return Response(status_code=405, headers={"Allow": "POST"})
