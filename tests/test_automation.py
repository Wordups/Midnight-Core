"""Jira automation layer (SCRUM-12/13/24): auto-push dedupe + severity fence,
sync-back done-stamping, readiness cadence, tick fault isolation, and the
one-click /sync endpoint."""
import os
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")
os.environ.setdefault("ENVIRONMENT", "dev")
os.environ.setdefault("AUTOMATION_SCHEDULER", "0")

from fastapi import Request
from fastapi.testclient import TestClient

from backend.integrations import jira_sync
from backend.integrations.jira_client import JiraConfig

TENANT = "11111111-1111-1111-1111-111111111111"
CONFIG = JiraConfig("https://acme.atlassian.net", "e@x.co", "tok", "GRC")


def _gap(control_id, severity="critical", framework="SOC 2"):
    return {"control_id": control_id, "severity": severity, "framework": framework,
            "name": f"Control {control_id}", "description": "d",
            "suggested_action": "fix it"}


class AutoPushTests(unittest.TestCase):
    def test_pushes_material_gaps_skips_linked_and_low(self):
        gaps = [_gap("SOC2-CC6.1"), _gap("SOC2-CC7.4", "medium"),
                _gap("ISO-A.5.15", "low"), _gap("SOC2-CC9.2")]
        fake_client = MagicMock()
        fake_client.create_issue.side_effect = [
            {"key": "GRC-1", "url": "u1"}, {"key": "GRC-2", "url": "u2"}]
        with patch.object(jira_sync, "load_config", return_value=CONFIG), \
             patch.object(jira_sync, "JiraClient", return_value=fake_client), \
             patch.object(jira_sync, "_linked_control_ids", return_value={"SOC2-CC9.2"}), \
             patch.object(jira_sync, "_record_link") as record, \
             patch.object(jira_sync, "alert") as alerted:
            out = jira_sync.auto_push_gaps(TENANT, gaps)
        self.assertEqual([p["control_id"] for p in out["pushed"]],
                         ["SOC2-CC6.1", "SOC2-CC7.4"])
        self.assertEqual(out["skipped_linked"], 1)
        self.assertEqual(out["skipped_severity"], 1)
        self.assertEqual(record.call_count, 2)
        alerted.assert_called_once()
        # summary carries the control id; labels mark the push as automated
        args = fake_client.create_issue.call_args_list[0].kwargs
        self.assertTrue(args["summary"].startswith("[SOC2-CC6.1]"))
        self.assertIn("auto-pushed", args["labels"])

    def test_unconfigured_tenant_is_a_noop(self):
        with patch.object(jira_sync, "load_config", return_value=None):
            out = jira_sync.auto_push_gaps(TENANT, [_gap("SOC2-CC6.1")])
        self.assertEqual(out["pushed"], [])

    def test_one_jira_failure_does_not_stop_the_rest(self):
        from backend.integrations.jira_client import JiraError
        fake_client = MagicMock()
        fake_client.create_issue.side_effect = [JiraError("boom"),
                                                {"key": "GRC-2", "url": "u"}]
        with patch.object(jira_sync, "load_config", return_value=CONFIG), \
             patch.object(jira_sync, "JiraClient", return_value=fake_client), \
             patch.object(jira_sync, "_linked_control_ids", return_value=set()), \
             patch.object(jira_sync, "_record_link"), \
             patch.object(jira_sync, "alert"):
            out = jira_sync.auto_push_gaps(
                TENANT, [_gap("SOC2-CC6.1"), _gap("SOC2-CC7.4")])
        self.assertEqual([p["control_id"] for p in out["pushed"]], ["SOC2-CC7.4"])


class SyncBackTests(unittest.TestCase):
    def test_done_issue_gets_resolved_at_and_alert(self):
        rows = [{"issue_key": "GRC-1", "control_id": "SOC2-CC6.1"},
                {"issue_key": "GRC-2", "control_id": "SOC2-CC7.4"}]
        fake_client = MagicMock()
        fake_client.get_issue_status.side_effect = [
            {"status": "Done", "done": True},
            {"status": "In Progress", "done": False}]
        with patch.object(jira_sync, "load_config", return_value=CONFIG), \
             patch.object(jira_sync, "JiraClient", return_value=fake_client), \
             patch.object(jira_sync, "db_select", return_value=rows), \
             patch.object(jira_sync, "db_update") as updated, \
             patch.object(jira_sync, "alert") as alerted:
            out = jira_sync.sync_back(TENANT)
        self.assertEqual(out["synced"], 2)
        self.assertEqual([d["key"] for d in out["newly_done"]], ["GRC-1"])
        done_patch = updated.call_args_list[0].kwargs["patch"]
        self.assertIn("resolved_at", done_patch)
        open_patch = updated.call_args_list[1].kwargs["patch"]
        self.assertNotIn("resolved_at", open_patch)
        self.assertIn("GRC-1", alerted.call_args.kwargs["summary"])

    def test_no_open_links_is_a_noop(self):
        with patch.object(jira_sync, "load_config", return_value=CONFIG), \
             patch.object(jira_sync, "db_select", return_value=[]):
            out = jira_sync.sync_back(TENANT)
        self.assertEqual(out, {"synced": 0, "newly_done": []})


class ReadinessTests(unittest.TestCase):
    def test_due_when_never_run(self):
        with patch.object(jira_sync, "db_select", return_value=[{"last_readiness_at": None}]):
            self.assertTrue(jira_sync.readiness_due(TENANT))

    def test_not_due_within_interval(self):
        recent = (datetime.now(UTC) - timedelta(days=5)).isoformat()
        with patch.object(jira_sync, "db_select", return_value=[{"last_readiness_at": recent}]):
            self.assertFalse(jira_sync.readiness_due(TENANT))

    def test_due_after_interval(self):
        stale = (datetime.now(UTC) - timedelta(days=31)).isoformat()
        with patch.object(jira_sync, "db_select", return_value=[{"last_readiness_at": stale}]):
            self.assertTrue(jira_sync.readiness_due(TENANT))

    def test_run_stamps_and_alerts(self):
        result = {"total_gaps": 4, "gaps_critical": 1, "gaps_medium": 3,
                  "gaps_low": 0, "overall_coverage_pct": 71,
                  "coverage_by_framework": {"SOC 2": 71}}
        with patch.object(jira_sync, "detect_gaps", return_value=result), \
             patch.object(jira_sync, "alert") as alerted, \
             patch.object(jira_sync, "db_update") as updated:
            out = jira_sync.run_readiness_check(TENANT)
        self.assertEqual(out["total_gaps"], 4)
        self.assertIn("71%", alerted.call_args.kwargs["summary"])
        self.assertIn("last_readiness_at", updated.call_args.kwargs["patch"])


class TickTests(unittest.TestCase):
    def test_stage_failure_never_blocks_the_next(self):
        with patch.object(jira_sync, "sync_back", side_effect=RuntimeError("db down")), \
             patch.object(jira_sync, "load_settings", return_value={"auto_push": True}), \
             patch.object(jira_sync, "auto_push_gaps", return_value={"pushed": []}) as pushed, \
             patch.object(jira_sync, "readiness_due", return_value=False):
            out = jira_sync.run_tick(TENANT)
        self.assertIn("error", out["sync"])
        pushed.assert_called_once()
        self.assertEqual(out["readiness"], {"ran": False})

    def test_auto_push_respects_setting(self):
        with patch.object(jira_sync, "sync_back", return_value={"synced": 0, "newly_done": []}), \
             patch.object(jira_sync, "load_settings", return_value={"auto_push": False}), \
             patch.object(jira_sync, "auto_push_gaps") as pushed, \
             patch.object(jira_sync, "readiness_due", return_value=False):
            jira_sync.run_tick(TENANT)
        pushed.assert_not_called()


class SyncEndpointTests(unittest.TestCase):
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
        self.assertEqual(
            self.client.post("/api/v1/integrations/jira/sync").status_code, 401)

    def test_fails_closed_without_config(self):
        self._login()
        with patch("backend.api.integrations.load_config", return_value=None):
            resp = self.client.post("/api/v1/integrations/jira/sync")
        self.assertEqual(resp.status_code, 409)

    def test_sync_runs_both_stages(self):
        self._login()
        with patch("backend.api.integrations.load_config", return_value=CONFIG), \
             patch("backend.integrations.jira_sync.sync_back",
                   return_value={"synced": 1, "newly_done": []}), \
             patch("backend.integrations.jira_sync.auto_push_gaps",
                   return_value={"pushed": [{"control_id": "SOC2-CC6.1", "key": "GRC-9"}],
                                 "skipped_linked": 0, "skipped_severity": 0}):
            resp = self.client.post("/api/v1/integrations/jira/sync")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["sync"]["synced"], 1)
        self.assertEqual(body["push"]["pushed"][0]["key"], "GRC-9")


class ConfigKeepTokenTests(unittest.TestCase):
    """Toggling automation settings must not require re-entering the token."""

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

    def test_empty_token_reuses_stored_config(self):
        self._login()
        with patch("backend.api.integrations.load_config", return_value=CONFIG), \
             patch("backend.api.integrations.save_config") as saved, \
             patch("backend.api.integrations.JiraClient") as client_cls:
            client_cls.return_value.test_connection.return_value = {"email": "e@x.co"}
            resp = self.client.put("/api/v1/integrations/jira/config", json={
                "site_url": "https://acme.atlassian.net", "auth_email": "e@x.co",
                "api_token": "", "auto_push": True,
            })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(saved.call_args.kwargs["api_token"], "tok")
        self.assertTrue(saved.call_args.kwargs["auto_push"])

    def test_empty_token_without_stored_config_is_rejected(self):
        self._login()
        with patch("backend.api.integrations.load_config", return_value=None):
            resp = self.client.put("/api/v1/integrations/jira/config", json={
                "site_url": "https://acme.atlassian.net", "auth_email": "e@x.co",
                "api_token": "",
            })
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
