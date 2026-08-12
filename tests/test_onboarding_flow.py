from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ["ANTHROPIC_API_KEY"] = "sk-test"
os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-role"
os.environ["ENVIRONMENT"] = "dev"

from fastapi.testclient import TestClient  # noqa: E402

from backend.api.main import app  # noqa: E402


_AUTH_USER = type(
    "AuthUser",
    (),
    {
        "id": "user-onboarding-001",
        "email": "bword8249@gmail.com",
        "user_metadata": {"name": "Brian"},
    },
)()

_USER_RECORD = {
    "id": "user-onboarding-001",
    "tenant_id": "tenant-onboarding-001",
    "email": "bword8249@gmail.com",
    "name": "Brian",
    "organization_name": "Takeoff Test",
    "role": "owner",
}

_ORGANIZATION = {
    "id": "tenant-onboarding-001",
    "slug": "takeoff-test",
    "name": "Takeoff Test",
    "industry": "Technology",
    "region": "North America",
    "employee_count": "1-50",
    "plan_type": "trial",
}


class TestOnboardingPlanEntry(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_authenticated_new_signup_can_land_on_onboarding_plan(self):
        with patch(
            "backend.api.main._authenticate_token",
            return_value=(_USER_RECORD, _ORGANIZATION, _AUTH_USER),
        ):
            response = self.client.get(
                "/onboarding/plan",
                cookies={"midnight_session": "valid-test-token"},
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Start onboarding", response.text)
        self.assertIn("TRIAL", response.text)

    def test_logged_out_start_now_serves_onboarding_not_signup(self):
        response = self.client.get("/onboarding/plan", follow_redirects=False)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Start onboarding", response.text)
        self.assertIn("Create your workspace", response.text)
        self.assertNotIn("Back to signup", response.text)

    def test_authenticated_user_can_save_onboarding_session(self):
        with (
            patch(
                "backend.api.main._authenticate_token",
                return_value=(_USER_RECORD, _ORGANIZATION, _AUTH_USER),
            ),
            patch("backend.api.main.update_onboarding_session") as update_session,
        ):
            update_session.return_value = {
                "tenant_id": "tenant-onboarding-001",
                "frameworks": ["soc2", "nist_csf"],
                "primary_objective": "audit_prep",
                "build_method": "upload_existing_docs",
                "current_step": "complete",
                "progress": 100,
                "completed": True,
            }
            response = self.client.post(
                "/onboarding/session",
                json={
                    "frameworks": ["soc2", "nist_csf"],
                    "primary_objective": "audit_prep",
                    "build_method": "upload_existing_docs",
                },
                cookies={"midnight_session": "valid-test-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["redirect_to"], "/midnight_dashboard.html")
        update_session.assert_called_once_with(
            "tenant-onboarding-001",
            {
                "frameworks": ["soc2", "nist_csf"],
                "primary_objective": "audit_prep",
                "build_method": "upload_existing_docs",
                "current_step": "complete",
                "progress": 100,
                "completed": True,
            },
        )

    def test_onboarding_save_rejects_logged_out_users(self):
        response = self.client.post(
            "/onboarding/session",
            json={
                "frameworks": ["soc2"],
                "primary_objective": "audit_prep",
                "build_method": "guided_review",
            },
        )

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
