"""Layer-2 Jira integration: ADF building, the REST client (httpx mocked),
config masking, and the push-gap endpoint (auth + fail-closed)."""
import os
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")
os.environ.setdefault("ENVIRONMENT", "dev")

from fastapi import Request
from fastapi.testclient import TestClient

from backend.integrations.jira_client import JiraClient, JiraConfig, JiraError, _adf

TENANT = "11111111-1111-1111-1111-111111111111"


def _mock_httpx(status_code, json_body):
    """A context-manager httpx.Client whose get/post return a canned response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body

    client = MagicMock()
    client.get.return_value = resp
    client.post.return_value = resp

    @contextmanager
    def factory(*a, **k):
        yield client

    return factory, client, resp


class AdfTests(unittest.TestCase):
    def test_paragraphs_and_bullets(self):
        doc = _adf("Intro line\n\n- one\n- two\nOutro")
        self.assertEqual(doc["type"], "doc")
        types = [b["type"] for b in doc["content"]]
        self.assertIn("bulletList", types)
        self.assertIn("paragraph", types)

    def test_empty_text_is_valid_doc(self):
        doc = _adf("")
        self.assertEqual(doc["content"][0]["type"], "paragraph")


class JiraConfigTests(unittest.TestCase):
    def test_site_normalization(self):
        self.assertEqual(
            JiraConfig("midnightgrc.atlassian.net/", "e@x.co", "tok").normalized_site(),
            "https://midnightgrc.atlassian.net",
        )

    def test_client_requires_full_config(self):
        with self.assertRaises(JiraError):
            JiraClient(JiraConfig("", "", ""))


class JiraClientTests(unittest.TestCase):
    def _client(self):
        return JiraClient(JiraConfig("https://acme.atlassian.net", "e@x.co", "tok", "GRC"))

    def test_create_issue_builds_payload_and_url(self):
        factory, http, _ = _mock_httpx(201, {"key": "GRC-7", "id": "10007"})
        with patch("backend.integrations.jira_client.httpx.Client", factory):
            out = self._client().create_issue(
                summary="[SOC2-CC6.1] Enforce MFA", description="Finding\n\n- fix it",
                labels=["midnight", "severity high"],
            )
        self.assertEqual(out["key"], "GRC-7")
        self.assertEqual(out["url"], "https://acme.atlassian.net/browse/GRC-7")
        body = http.post.call_args.kwargs["json"]["fields"]
        self.assertEqual(body["project"]["key"], "GRC")
        self.assertEqual(body["issuetype"]["name"], "Task")
        self.assertEqual(body["description"]["type"], "doc")
        self.assertIn("severity-high", body["labels"])  # spaces -> hyphens

    def test_bad_credentials_raise_clean_error(self):
        factory, _, _ = _mock_httpx(401, {})
        with patch("backend.integrations.jira_client.httpx.Client", factory):
            with self.assertRaises(JiraError) as ctx:
                self._client().create_issue(summary="x", description="y")
        self.assertIn("credentials", str(ctx.exception).lower())

    def test_status_maps_done(self):
        factory, _, _ = _mock_httpx(200, {"fields": {"summary": "s", "status": {
            "name": "Done", "statusCategory": {"key": "done"}}}})
        with patch("backend.integrations.jira_client.httpx.Client", factory):
            out = self._client().get_issue_status("GRC-7")
        self.assertTrue(out["done"])
        self.assertEqual(out["status"], "Done")


class JiraEndpointTests(unittest.TestCase):
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
        self.assertEqual(self.client.get("/api/v1/integrations/jira/config").status_code, 401)

    def test_push_gap_fails_closed_without_config(self):
        self._login()
        with patch("backend.api.integrations.load_config", return_value=None):
            resp = self.client.post("/api/v1/integrations/jira/push-gap",
                                    json={"title": "Enforce MFA", "control_id": "SOC2-CC6.1"})
        self.assertEqual(resp.status_code, 409)

    def test_push_gap_creates_issue(self):
        self._login()
        fake_issue = {"key": "GRC-9", "id": "10009", "url": "https://acme.atlassian.net/browse/GRC-9"}
        fake_client = MagicMock()
        fake_client.create_issue.return_value = fake_issue
        with patch("backend.api.integrations.load_config",
                   return_value=JiraConfig("https://acme.atlassian.net", "e@x.co", "tok", "GRC")), \
             patch("backend.api.integrations.JiraClient", return_value=fake_client), \
             patch("backend.api.integrations.db_insert", return_value=None):
            resp = self.client.post("/api/v1/integrations/jira/push-gap", json={
                "title": "Enforce MFA on admin access", "control_id": "SOC2-CC6.1",
                "framework": "SOC 2", "severity": "High", "document_id": "PFI-SEC-014",
                "finding": "No MFA evidence.", "remediation": "Turn on MFA.",
            })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["key"], "GRC-9")
        # summary carries the control id; labels carry framework + severity
        args = fake_client.create_issue.call_args.kwargs
        self.assertTrue(args["summary"].startswith("[SOC2-CC6.1]"))
        self.assertIn("severity-high", args["labels"])


if __name__ == "__main__":
    unittest.main()
