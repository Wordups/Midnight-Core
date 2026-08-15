"""Remote MCP gateway: API-key auth, protocol handshake (initialize/tools),
tool dispatch with tenant scoping, fail-closed tool errors, and the key
management endpoints."""
import json
import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")
os.environ.setdefault("ENVIRONMENT", "dev")
os.environ.setdefault("AUTOMATION_SCHEDULER", "0")

from fastapi import Request
from fastapi.testclient import TestClient

TENANT = "44444444-4444-4444-4444-444444444444"
AUTH = {"Authorization": "Bearer mk_test-key-value-long-enough"}


def _rpc(method, params=None, msg_id=1):
    msg = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


class GatewayAuthTests(unittest.TestCase):
    def setUp(self):
        from backend.api.main import app
        self.client = TestClient(app)

    def test_no_key_is_401(self):
        resp = self.client.post("/mcp", json=_rpc("tools/list"))
        self.assertEqual(resp.status_code, 401)
        self.assertIn("WWW-Authenticate", resp.headers)

    def test_bad_key_is_401(self):
        with patch("backend.api.mcp_gateway.verify_key", return_value=None):
            resp = self.client.post("/mcp", json=_rpc("tools/list"), headers=AUTH)
        self.assertEqual(resp.status_code, 401)

    def test_get_is_405(self):
        self.assertEqual(self.client.get("/mcp").status_code, 405)


class GatewayProtocolTests(unittest.TestCase):
    def setUp(self):
        from backend.api.main import app
        self.client = TestClient(app)
        self.verify = patch("backend.api.mcp_gateway.verify_key", return_value=TENANT)
        self.verify.start()

    def tearDown(self):
        self.verify.stop()

    def test_initialize_negotiates_protocol(self):
        resp = self.client.post("/mcp", headers=AUTH, json=_rpc(
            "initialize", {"protocolVersion": "2025-03-26",
                           "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}))
        self.assertEqual(resp.status_code, 200)
        result = resp.json()["result"]
        self.assertEqual(result["protocolVersion"], "2025-03-26")
        self.assertIn("tools", result["capabilities"])
        self.assertEqual(result["serverInfo"]["name"], "midnight")

    def test_unknown_protocol_falls_back(self):
        resp = self.client.post("/mcp", headers=AUTH, json=_rpc(
            "initialize", {"protocolVersion": "1999-01-01"}))
        self.assertEqual(resp.json()["result"]["protocolVersion"], "2025-06-18")

    def test_initialized_notification_is_202(self):
        resp = self.client.post("/mcp", headers=AUTH,
                                json={"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertEqual(resp.status_code, 202)

    def test_tools_list_has_six_tools(self):
        resp = self.client.post("/mcp", headers=AUTH, json=_rpc("tools/list"))
        tools = resp.json()["result"]["tools"]
        names = {t["name"] for t in tools}
        self.assertEqual(names, {"get_posture", "answer_questions", "list_runs",
                                 "get_run", "assign_to_reviewer", "list_requests"})
        for t in tools:
            self.assertIn("inputSchema", t)

    def test_unknown_method_is_rpc_error(self):
        resp = self.client.post("/mcp", headers=AUTH, json=_rpc("resources/list"))
        self.assertEqual(resp.json()["error"]["code"], -32601)

    def test_ping(self):
        resp = self.client.post("/mcp", headers=AUTH, json=_rpc("ping"))
        self.assertEqual(resp.json()["result"], {})


class GatewayToolTests(unittest.TestCase):
    def setUp(self):
        from backend.api.main import app
        self.client = TestClient(app)
        self.verify = patch("backend.api.mcp_gateway.verify_key", return_value=TENANT)
        self.verify.start()

    def tearDown(self):
        self.verify.stop()

    def _call(self, name, arguments=None):
        return self.client.post("/mcp", headers=AUTH, json=_rpc(
            "tools/call", {"name": name, "arguments": arguments or {}}))

    def test_get_posture_returns_tenant_scoped_summary(self):
        with patch("backend.api.mcp_gateway.build_corpus_index",
                   return_value={"document_count": 4, "controls_covered_total": 40,
                                 "controls_total": 174}) as idx, \
             patch("backend.api.mcp_gateway.detect_gaps",
                   return_value={"total_gaps": 3, "gaps_critical": 1, "gaps_medium": 2,
                                 "gaps_low": 0, "overall_coverage_pct": 62,
                                 "coverage_by_framework": {"SOC 2": 62}, "gaps": []}) as gaps:
            resp = self._call("get_posture")
        result = resp.json()["result"]
        self.assertFalse(result["isError"])
        data = json.loads(result["content"][0]["text"])
        self.assertEqual(data["documents"], 4)
        self.assertEqual(data["total_gaps"], 3)
        idx.assert_called_once_with(TENANT)
        gaps.assert_called_once_with(TENANT)

    def test_answer_questions_fails_closed_on_empty_corpus(self):
        with patch("backend.api.mcp_gateway._plan_type", return_value="pro"), \
             patch("backend.api.mcp_gateway.load_corpus_sections", return_value=[]):
            resp = self._call("answer_questions", {"questions": ["Do you encrypt at rest?"]})
        result = resp.json()["result"]
        self.assertTrue(result["isError"])
        self.assertIn("corpus is empty", result["content"][0]["text"])

    def test_answer_questions_enforces_plan_cap(self):
        with patch("backend.api.mcp_gateway._plan_type", return_value="free"), \
             patch("backend.storage.file_store.count_activity_for_tenant", return_value=2):
            resp = self._call("answer_questions", {"questions": ["Q1"]})
        result = resp.json()["result"]
        self.assertTrue(result["isError"])
        self.assertIn("free plan", result["content"][0]["text"])

    def test_assign_to_reviewer_inserts_request(self):
        fake = MagicMock()
        fake.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "req-1"}])
        with patch("backend.api.mcp_gateway.supabase_admin", fake):
            resp = self._call("assign_to_reviewer", {"title": "Confirm MFA on admin paths"})
        result = resp.json()["result"]
        self.assertFalse(result["isError"])
        data = json.loads(result["content"][0]["text"])
        self.assertTrue(data["created"])
        inserted = fake.table.return_value.insert.call_args.args[0]
        self.assertEqual(inserted["tenant_id"], TENANT)
        self.assertEqual(inserted["status"], "open")

    def test_unknown_tool_is_invalid_params(self):
        resp = self._call("delete_everything")
        self.assertEqual(resp.json()["error"]["code"], -32602)

    def test_unexpected_tool_crash_is_tool_error_not_500(self):
        with patch("backend.api.mcp_gateway.detect_gaps", side_effect=RuntimeError("db down")):
            resp = self._call("get_posture")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["result"]["isError"])


class ApiKeyModuleTests(unittest.TestCase):
    def test_verify_rejects_malformed_keys(self):
        from backend.integrations.api_keys import verify_key
        self.assertIsNone(verify_key(""))
        self.assertIsNone(verify_key("not-a-key"))
        self.assertIsNone(verify_key("mk_short"))

    def test_verify_rejects_revoked(self):
        from backend.integrations import api_keys
        resp = MagicMock(status_code=200)
        resp.json.return_value = [{"id": "k1", "tenant_id": TENANT,
                                   "revoked_at": "2026-08-14T00:00:00Z"}]
        with patch.object(api_keys.requests, "get", return_value=resp):
            self.assertIsNone(api_keys.verify_key("mk_" + "x" * 40))

    def test_verify_returns_tenant_and_stamps_use(self):
        from backend.integrations import api_keys
        resp = MagicMock(status_code=200)
        resp.json.return_value = [{"id": "k1", "tenant_id": TENANT, "revoked_at": None}]
        with patch.object(api_keys.requests, "get", return_value=resp), \
             patch.object(api_keys, "db_update") as stamped:
            self.assertEqual(api_keys.verify_key("mk_" + "x" * 40), TENANT)
        stamped.assert_called_once()


class KeyEndpointTests(unittest.TestCase):
    def setUp(self):
        from backend.api.main import app
        self.app = app
        self.client = TestClient(app)

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def _login(self):
        from backend.api.main import verify_access

        def fake_access(request: Request):
            request.state.tenant_id = TENANT
            request.state.plan_type = "pro"
            return {"authenticated": True, "tenant_id": TENANT, "plan_type": "pro"}

        self.app.dependency_overrides[verify_access] = fake_access

    def test_requires_auth(self):
        self.assertEqual(self.client.get("/api/v1/api-keys").status_code, 401)

    def test_mint_returns_key_once(self):
        self._login()
        minted = {"id": "k1", "key": "mk_full-secret", "key_prefix": "mk_full-sec",
                  "name": "Claude", "created_at": "2026-08-14T00:00:00Z"}
        with patch("backend.api.api_keys_router.list_keys", return_value=[]), \
             patch("backend.api.api_keys_router.mint_key", return_value=minted):
            resp = self.client.post("/api/v1/api-keys", json={"name": "Claude"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["key"], "mk_full-secret")

    def test_active_key_cap(self):
        self._login()
        active = [{"id": str(i), "revoked_at": None} for i in range(5)]
        with patch("backend.api.api_keys_router.list_keys", return_value=active):
            resp = self.client.post("/api/v1/api-keys", json={"name": "one too many"})
        self.assertEqual(resp.status_code, 409)

    def test_revoke_unknown_is_404(self):
        self._login()
        with patch("backend.api.api_keys_router.revoke_key", return_value=False):
            resp = self.client.delete("/api/v1/api-keys/nope")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
