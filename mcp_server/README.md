# midnight-mcp

An MCP server exposing the Midnight GRC platform to any MCP client
(Claude Desktop, Claude Code, other agents). Six tools: `get_posture`,
`answer_questions`, `list_runs`, `assign_to_reviewer`, `list_requests`,
`draft_document`.

It is a client of Midnight's REST API — cookie auth, tenant-scoped,
plan-fenced, and rate-limited by the server it talks to. Runs in its own
venv (the MCP SDK's dependency tree conflicts with the app's pinned
FastAPI — keep them isolated).

## Setup

```
python -m venv mcp_server/venv
mcp_server/venv/Scripts/pip install -r mcp_server/requirements.txt
set MIDNIGHT_URL=https://midnight-core-cod3.onrender.com
set MIDNIGHT_EMAIL=you@company.com
set MIDNIGHT_PASSWORD=...
```

## Register with Claude Code

```
claude mcp add midnight -- mcp_server/venv/Scripts/python.exe mcp_server/midnight_mcp.py
```

Then, in any session: "check my compliance posture", "answer this vendor
questionnaire from my corpus", "assign the pen-test gap to a reviewer".
