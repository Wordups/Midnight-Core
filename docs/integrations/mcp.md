# AI Connector (remote MCP gateway)

Midnight serves its tools to any MCP-speaking client — Claude custom
connectors, ChatGPT connectors, Cursor, agent frameworks — over MCP
Streamable HTTP at `POST /mcp`.

## Connect

1. Midnight dashboard → **Integrations → AI Connector** → create a key
   (shown once; sha256-hashed at rest, revocable, max 5 active).
2. In the assistant, add a custom connector:
   - URL: `https://<your-midnight-host>/mcp`
   - Auth: `Authorization: Bearer mk_…`

## Tools

| Tool | What it does |
|---|---|
| `get_posture` | Documents, coverage %, open gaps by severity |
| `answer_questions` | Cited answers from the corpus; fails closed; counts against the plan's monthly runs |
| `list_runs` / `get_run` | Questionnaire run history and full answers |
| `assign_to_reviewer` | Files a request into the Requests inbox |
| `list_requests` | Open/recent review requests |

## Design notes

- **Protocol, not SDK**: the gateway (`backend/api/mcp_gateway.py`) speaks
  JSON-RPC/MCP directly — the MCP SDK's dependency tree conflicts with the
  app's pinned FastAPI (that's why `mcp_server/` has its own venv). Stateless
  server responses; protocol versions 2024-11-05 / 2025-03-26 / 2025-06-18
  negotiated on `initialize`; GET returns 405 (no server-initiated SSE).
- **Auth**: per-tenant API keys (`backend/integrations/api_keys.py`,
  migration `006_api_keys.sql`), mounted bare like the Stripe webhook —
  the key is the auth. Rate-limited 60 calls / 5 min per tenant.
- **Fences hold**: tools run tenant-scoped and enforce the same plan limits
  as the app (corpus run caps, haiku_only model downgrade).
- **Auditable**: every `tools/call` lands in the tenant's activity feed as an
  `mcp_tool_call` signal — an AI acting on a GRC platform is itself evidence.
- The local stdio server (`mcp_server/midnight_mcp.py`) remains for
  Claude Desktop/Code users who prefer email/password env auth; it also has
  `draft_document`, which stays stdio-only until the remote gateway grows
  scoped write permissions.
