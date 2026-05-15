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

    @patch("backend.api.assessments._get_anthropic_client")
    def test_create_assessment_prose_wrapped_json_succeeds(self, mock_get_client):
        """The IT Asset Disposal regression: model emits valid JSON
        wrapped in prose. Pre-fix this crashed json.loads. With the
        two-pass parser the route should extract and validate."""
        mock_get_client.return_value = _FakeClient(
            """Here is my assessment of the policy:

            {
              "risk_score": 35,
              "risk_band": "high",
              "framework": "hipaa",
              "top_findings": [
                "No documented data disposal procedure",
                "Missing media sanitization controls",
                "No chain-of-custody tracking"
              ],
              "recommendations": [
                "Adopt NIST 800-88 disposal procedure",
                "Implement cryptographic erasure",
                "Add asset disposal log"
              ]
            }

            Let me know if you need more detail on any of these findings."""
        )

        response = self.client.post(
            "/api/v1/assessments",
            json={"text": "We do not have a documented IT asset disposal policy.", "framework": "hipaa"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["risk_band"], "high")
        self.assertEqual(response.json()["framework"], "hipaa")

    @patch("backend.api.assessments._get_anthropic_client")
    def test_create_assessment_unparseable_output_returns_502(self, mock_get_client):
        """Model returns content with no JSON at all -> 502 with the
        canonical {error, detail, request_id} envelope from errors.py.
        Pre-fix this would have raised json.JSONDecodeError and been
        mapped to a misleading 503 'AI provider unavailable.'"""
        mock_get_client.return_value = _FakeClient(
            "I cannot complete that request because the input is ambiguous."
        )

        response = self.client.post(
            "/api/v1/assessments",
            json={"text": "Assess this.", "framework": "soc2"},
        )

        self.assertEqual(response.status_code, 502)
        body = response.json()
        self.assertEqual(body.get("error"), "http_error")
        self.assertIn("unparseable", body.get("detail", "").lower())
        self.assertIn("request_id", body)


if __name__ == "__main__":
    unittest.main()
