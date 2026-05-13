import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


os.environ["ANTHROPIC_API_KEY"] = "sk-test"
os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-role"
os.environ["TOOL_PASSWORD"] = "test-password"
os.environ["ENVIRONMENT"] = "dev"

from backend.api.main import app  # noqa: E402


class _FakeMessageContent:
    def __init__(self, text: str):
        self.text = text


class _FakeMessageResponse:
    def __init__(self, text: str):
        self.content = [_FakeMessageContent(text)]


class _FakeMessages:
    def __init__(self, text: str):
        self._text = text

    def create(self, **kwargs):
        return _FakeMessageResponse(self._text)


class _FakeClient:
    def __init__(self, text: str):
        self.messages = _FakeMessages(text)


class AssessmentsRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("backend.api.assessments._get_anthropic_client")
    def test_create_assessment_happy_path(self, mock_get_client):
        mock_get_client.return_value = _FakeClient(
            """
            {
              "risk_score": 72,
              "risk_band": "medium",
              "framework": "soc2",
              "top_findings": [
                "Missing access control enforcement",
                "No documented incident response",
                "Weak vendor validation"
              ],
              "recommendations": [
                "Implement RBAC controls",
                "Define incident response playbook",
                "Add vendor risk review process"
              ]
            }
            """
        )

        response = self.client.post(
            "/api/v1/assessments",
            json={
                "text": "Our vendor review process is informal and incident response is undocumented.",
                "framework": "soc2",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["risk_score"], 72)
        self.assertEqual(response.json()["risk_band"], "medium")
        self.assertEqual(response.json()["framework"], "soc2")
        self.assertEqual(len(response.json()["top_findings"]), 3)
        self.assertEqual(len(response.json()["recommendations"]), 3)


if __name__ == "__main__":
    unittest.main()
