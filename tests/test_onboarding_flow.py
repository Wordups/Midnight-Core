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

    def test_logged_out_onboarding_plan_redirects_to_signup(self):
        response = self.client.get("/onboarding/plan", follow_redirects=False)

        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/login.html?mode=signup")


if __name__ == "__main__":
    unittest.main()
