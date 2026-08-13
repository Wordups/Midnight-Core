"""midnight-mcp — an MCP server for the Midnight GRC platform.

Exposes Midnight's REST API as MCP tools, so any MCP client (Claude Desktop,
Claude Code, or another agent) can operate a compliance workspace: read
posture, answer questionnaires from the evidence corpus, inspect gaps, and
route unresolved items to human reviewers.

Runs isolated from the app (its own venv — the MCP SDK's dependency tree
conflicts with the app's pinned FastAPI). It is a *client* of Midnight's
REST API, exactly like a browser session: cookie auth, tenant-scoped,
plan-fenced, and rate-limited by the server it talks to.

Config (env):
  MIDNIGHT_URL       default https://midnight-core-cod3.onrender.com
  MIDNIGHT_EMAIL     workspace login
  MIDNIGHT_PASSWORD  workspace password

Register in Claude Code:
  claude mcp add midnight -- mcp_server/venv/Scripts/python.exe mcp_server/midnight_mcp.py
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer

BASE_URL = os.getenv("MIDNIGHT_URL", "https://midnight-core-cod3.onrender.com").rstrip("/")

server = MCPServer(
    name="midnight",
    title="Midnight GRC",
    instructions=(
        "Tools for operating a Midnight compliance workspace. Answers come only "
        "from the tenant's own policy corpus with citations; unresolved questions "
        "fail closed to insufficient_evidence and can be routed to human reviewers."
    ),
    version="1.0.0",
)

_client: httpx.Client | None = None


def _http() -> httpx.Client:
    """Authenticated client; logs in lazily and re-logs-in on 401."""
    global _client
    if _client is None:
        _client = httpx.Client(base_url=BASE_URL, timeout=300.0, follow_redirects=True)
        _login(_client)
    return _client


def _login(client: httpx.Client) -> None:
    email = os.getenv("MIDNIGHT_EMAIL", "")
    password = os.getenv("MIDNIGHT_PASSWORD", "")
    if not email or not password:
        raise RuntimeError("Set MIDNIGHT_EMAIL and MIDNIGHT_PASSWORD in the environment.")
    resp = client.post("/auth/login", json={"email": email, "password": password})
    resp.raise_for_status()


def _request(method: str, path: str, **kwargs: Any) -> Any:
    client = _http()
    resp = client.request(method, path, **kwargs)
    if resp.status_code == 401:  # session expired — one re-login retry
        _login(client)
        resp = client.request(method, path, **kwargs)
    resp.raise_for_status()
    return resp.json()


@server.tool(description=(
    "The workspace's compliance posture: documents in the corpus, controls "
    "covered per framework (SOC 2, HIPAA, ISO 27001, NIST CSF, PCI DSS), "
    "coverage percentages, stale documents, and unmapped documents."
))
def get_posture() -> dict:
    return _request("GET", "/api/v1/corpus")


@server.tool(description=(
    "Answer assessment questions from the workspace's own policy corpus. "
    "Each answer carries a verdict (satisfied / partially_satisfied / "
    "not_satisfied / insufficient_evidence / not_applicable), exact-quote "
    "citations, mapped control ids, confidence, and a suggested follow-up "
    "when evidence is thin. Nothing is guessed — unresolved questions fail "
    "closed. use_case: audit | questionnaire | vendor_assessment | internal."
))
def answer_questions(questions: list[str], use_case: str = "questionnaire") -> dict:
    return _request("POST", "/api/v1/corpus/answer",
                    json={"questions": questions, "use_case": use_case})


@server.tool(description="List past questionnaire runs with their verdict counts and token usage.")
def list_runs() -> dict:
    return _request("GET", "/api/v1/corpus/runs")


@server.tool(description=(
    "Route an unresolved assessment question to a human reviewer: creates a "
    "request in the workspace's Requests inbox (open -> in_review -> complete). "
    "Use after answer_questions returns insufficient_evidence."
))
def assign_to_reviewer(title: str, description: str = "", control_id: str | None = None) -> dict:
    return _request("POST", "/pm/requests",
                    json={"title": title[:200], "description": description or None,
                          "control_id": control_id})


@server.tool(description="List open human-review requests and their states.")
def list_requests() -> dict:
    return _request("GET", "/pm/requests")


@server.tool(description=(
    "Draft a new compliance document from a description. Returns the structured "
    "preview (sections) — a human reviews it in Midnight's Studio before export. "
    "doc_type: POLICY | SOP | STANDARD | INCIDENT_RUNBOOK | PROCESS_FLOW | "
    "TRAINING_MODULE | RISK_ASSESSMENT | AUDIT_PACKAGE | AI_GOVERNANCE."
))
def draft_document(policy_name: str, description: str, doc_type: str = "POLICY",
                   frameworks: list[str] | None = None) -> dict:
    return _request("POST", "/pipeline/create/preview", json={
        "policy_name": policy_name,
        "doc_type": doc_type,
        "industry": "Technology / SaaS",
        "frameworks": frameworks or ["SOC 2"],
        "owner": "MCP Client",
        "description": description,
    })


if __name__ == "__main__":
    server.run(transport="stdio")
