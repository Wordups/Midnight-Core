"""Phase E security pass: headers, upload caps, rate limits."""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role")
os.environ.setdefault("ENVIRONMENT", "dev")

from backend.core import ratelimit  # noqa: E402

TENANT = "00000000-0000-0000-0000-000000000001"


class SecurityHeaderTests(unittest.TestCase):
    def test_baseline_headers_on_every_response(self):
        from backend.api.main import app
        client = TestClient(app)
        resp = client.get("/health")
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("Referrer-Policy", resp.headers)


class UploadCapTests(unittest.TestCase):
    def setUp(self):
        from backend.api.main import app, verify_access
        self.app = app
        self.client = TestClient(app)
        from fastapi import Request

        def fake_access(request: Request):
            request.state.tenant_id = TENANT
            request.state.plan_type = "pro"
            return {"authenticated": True}

        app.dependency_overrides[verify_access] = fake_access

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def test_ingest_rejects_unsupported_extension(self):
        resp = self.client.post("/bird-eye/ingest", files={"file": ("evil.exe", b"MZ", "application/octet-stream")})
        self.assertEqual(resp.status_code, 415)

    def test_ingest_rejects_oversized_upload(self):
        big = b"a" * (10 * 1024 * 1024 + 1)
        resp = self.client.post("/bird-eye/ingest", files={"file": ("big.txt", big, "text/plain")})
        self.assertEqual(resp.status_code, 413)


class RateLimitTests(unittest.TestCase):
    def setUp(self):
        ratelimit.reset()

    def tearDown(self):
        ratelimit.reset()

    def test_allows_within_window_blocks_beyond(self):
        for _ in range(10):
            self.assertTrue(ratelimit.allow("k", max_hits=10, window_seconds=60))
        self.assertFalse(ratelimit.allow("k", max_hits=10, window_seconds=60))

    def test_keys_are_independent(self):
        self.assertTrue(ratelimit.allow("a", max_hits=1, window_seconds=60))
        self.assertTrue(ratelimit.allow("b", max_hits=1, window_seconds=60))
        self.assertFalse(ratelimit.allow("a", max_hits=1, window_seconds=60))

    def test_corpus_answer_returns_429_when_limited(self):
        from backend.api.main import app, verify_access
        from fastapi import Request

        def fake_access(request: Request):
            request.state.tenant_id = TENANT
            request.state.plan_type = "pro"
            return {"authenticated": True}

        app.dependency_overrides[verify_access] = fake_access
        client = TestClient(app)
        try:
            with patch("backend.core.ratelimit.allow", return_value=False):
                resp = client.post("/api/v1/corpus/answer", json={"questions": ["Do you require MFA for admins?"]})
            self.assertEqual(resp.status_code, 429)
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
