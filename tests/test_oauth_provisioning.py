"""OAuth sign-up: /auth/exchange auto-provisions a workspace for a first-time
OAuth user (Google/GitHub/Microsoft), and only for the exact not-provisioned
case; the provider redirect map covers github and rejects unknowns."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")
os.environ.setdefault("ENVIRONMENT", "dev")
os.environ.setdefault("AUTOMATION_SCHEDULER", "0")

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

USER_ID = "22222222-2222-2222-2222-222222222222"
TENANT_ID = "33333333-3333-3333-3333-333333333333"

AUTH_USER = SimpleNamespace(
    id=USER_ID,
    email="new.user@gmail.com",
    user_metadata={"full_name": "New User"},
)

USER_RECORD = {"id": USER_ID, "tenant_id": TENANT_ID, "email": "new.user@gmail.com",
               "name": "New User", "organization_name": "New User's Workspace",
               "role": "owner"}
ORGANIZATION = {"id": TENANT_ID, "slug": "new-users-workspace",
                "name": "New User's Workspace", "plan_type": "free"}

NOT_PROVISIONED = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User is not provisioned for a Midnight organization.",
)


class ExchangeProvisioningTests(unittest.TestCase):
    def setUp(self):
        from backend.api.main import app
        self.client = TestClient(app)

    def test_first_oauth_signin_provisions_workspace(self):
        with patch("backend.api.main._authenticate_token", side_effect=NOT_PROVISIONED), \
             patch("backend.api.main._validate_supabase_token", return_value=AUTH_USER), \
             patch("backend.api.main._provision_oauth_workspace",
                   return_value=(USER_RECORD, ORGANIZATION)) as provision:
            resp = self.client.post("/auth/exchange", json={"access_token": "tok"})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["provisioned"])
        self.assertEqual(body["redirect_to"], "/onboarding/plan")
        self.assertEqual(body["tenant_id"], TENANT_ID)
        provision.assert_called_once_with(AUTH_USER)

    def test_existing_user_is_not_reprovisioned(self):
        with patch("backend.api.main._authenticate_token",
                   return_value=(USER_RECORD, ORGANIZATION, AUTH_USER)), \
             patch("backend.api.main._provision_oauth_workspace") as provision:
            resp = self.client.post("/auth/exchange", json={"access_token": "tok"})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["provisioned"])
        provision.assert_not_called()

    def test_broken_tenant_assignment_still_fails(self):
        broken = HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                               detail="User is missing a tenant assignment.")
        with patch("backend.api.main._authenticate_token", side_effect=broken), \
             patch("backend.api.main._provision_oauth_workspace") as provision:
            resp = self.client.post("/auth/exchange", json={"access_token": "tok"})
        self.assertEqual(resp.status_code, 403)
        provision.assert_not_called()

    def test_invalid_token_still_401s(self):
        bad = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired Supabase session.")
        with patch("backend.api.main._authenticate_token", side_effect=bad):
            resp = self.client.post("/auth/exchange", json={"access_token": "tok"})
        self.assertEqual(resp.status_code, 401)


class ProvisionWorkspaceTests(unittest.TestCase):
    def test_missing_email_is_rejected(self):
        from backend.api.main import _provision_oauth_workspace
        no_email = SimpleNamespace(id=USER_ID, email=None, user_metadata={})
        with self.assertRaises(HTTPException) as ctx:
            _provision_oauth_workspace(no_email)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_creates_tenant_profile_and_onboarding(self):
        from backend.api.main import _provision_oauth_workspace

        inserted = {}

        def table(name):
            m = MagicMock()
            def capture(payload):
                inserted[name] = payload
                result = MagicMock()
                if name == "tenants":
                    result.execute.return_value = SimpleNamespace(data=[ORGANIZATION])
                else:
                    result.execute.return_value = SimpleNamespace(data=[USER_RECORD])
                return result
            m.insert.side_effect = capture
            return m

        with patch("backend.api.main.supabase_admin") as admin, \
             patch("backend.api.main._generate_unique_org_slug",
                   return_value="new-users-workspace"):
            admin.table.side_effect = table
            user_record, organization = _provision_oauth_workspace(AUTH_USER)

        self.assertEqual(organization["id"], TENANT_ID)
        self.assertEqual(inserted["tenants"]["plan_type"], "free")
        self.assertEqual(inserted["profiles"]["role"], "owner")
        self.assertEqual(inserted["profiles"]["tenant_id"], TENANT_ID)
        self.assertEqual(inserted["onboarding_sessions"]["tenant_id"], TENANT_ID)
        self.assertEqual(user_record["email"], "new.user@gmail.com")


class ProviderMapTests(unittest.TestCase):
    def test_github_maps(self):
        from backend.api.main import _oauth_provider_name
        self.assertEqual(_oauth_provider_name("github"), "github")
        self.assertEqual(_oauth_provider_name("microsoft"), "azure")

    def test_unknown_provider_404s(self):
        from backend.api.main import _oauth_provider_name
        with self.assertRaises(HTTPException) as ctx:
            _oauth_provider_name("aws")
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
