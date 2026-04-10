import os
import unittest

from fastapi.testclient import TestClient


os.environ["TOOL_PASSWORD"] = "test-password"

from backend.api.main import app  # noqa: E402


class DashboardRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_dashboard_requires_authentication(self):
        response = self.client.get("/dashboard/summary")
        self.assertEqual(response.status_code, 401)

    def test_login_sets_session_cookie_and_allows_dashboard_access(self):
        login = self.client.post("/auth/login", json={"password": "test-password"})
        self.assertEqual(login.status_code, 200)
        self.assertTrue(login.json()["authenticated"])

        response = self.client.get("/dashboard/summary")
        self.assertEqual(response.status_code, 200)
        self.assertIn("policies_processed", response.json())


if __name__ == "__main__":
    unittest.main()
