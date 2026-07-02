"""
Tests for Stripe billing endpoints — session 3, part 1.

All tests mock the Stripe SDK. Zero live API calls.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

# Set env vars before importing the app so config.py and stripe_router.py
# pick up test values. Pattern mirrors test_assessments.py.
os.environ["ANTHROPIC_API_KEY"] = "sk-test"
os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-role"
os.environ["ENVIRONMENT"] = "dev"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_fake"
os.environ["STRIPE_PRICE_STARTER"] = "price_test_starter"
os.environ["STRIPE_PRICE_GROWTH"] = "price_test_growth"
os.environ["STRIPE_PRICE_ENTERPRISE"] = "price_test_enterprise"
os.environ["FRONTEND_BASE_URL"] = "http://localhost:8000"

from fastapi import Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.api.main import app, verify_access  # noqa: E402
from backend.api.stripe_router import billing_router, billing_webhook_router  # noqa: E402

_MOCK_AUTH = {
    "authenticated": True,
    "tenant_id": "tenant-test-001",
    "user_id": "user-test-001",
    "plan_type": "trial",
    "email": "test@example.com",
    "role": "Owner",
    "organization_name": "Test Org",
}


def _mock_verify_access(request: Request):
    # Mirror the real verify_access: populate request.state so downstream
    # endpoints (checkout reads request.state.tenant_id) work under test.
    request.state.tenant_id = _MOCK_AUTH["tenant_id"]
    request.state.user_id = _MOCK_AUTH["user_id"]
    request.state.user_email = _MOCK_AUTH["email"]
    request.state.auth_context = _MOCK_AUTH
    return _MOCK_AUTH


class TestCheckoutSuccess(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[verify_access] = _mock_verify_access
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("backend.api.stripe_router.stripe.checkout.Session.create")
    def test_checkout_returns_checkout_url(self, mock_create):
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test_abc123"
        mock_create.return_value = mock_session

        response = self.client.post("/billing/checkout", json={"tier": "starter"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("checkout_url", body)
        self.assertEqual(body["checkout_url"], "https://checkout.stripe.com/test_abc123")

    @patch.dict(os.environ, {"STRIPE_PRICE_STARTER": "price_test_starter"})
    @patch("backend.api.stripe_router.stripe.checkout.Session.create")
    def test_checkout_passes_correct_price_id_to_stripe(self, mock_create):
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test_abc123"
        mock_create.return_value = mock_session

        self.client.post("/billing/checkout", json={"tier": "starter"})

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        line_items = call_kwargs.get("line_items", [])
        self.assertTrue(
            any(item.get("price") == "price_test_starter" for item in line_items),
            f"Expected price_test_starter in line_items, got: {line_items}",
        )

    @patch("backend.api.stripe_router.stripe.checkout.Session.create")
    def test_checkout_mode_is_subscription(self, mock_create):
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_create.return_value = mock_session

        self.client.post("/billing/checkout", json={"tier": "growth"})

        call_kwargs = mock_create.call_args.kwargs
        self.assertEqual(call_kwargs.get("mode"), "subscription")

    @patch("backend.api.stripe_router.stripe.checkout.Session.create")
    def test_checkout_does_not_redirect(self, mock_create):
        """Endpoint must return the URL, not issue a redirect."""
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_create.return_value = mock_session

        response = self.client.post(
            "/billing/checkout",
            json={"tier": "enterprise"},
            follow_redirects=False,
        )

        self.assertNotIn(response.status_code, (301, 302, 307, 308))
        self.assertIn("checkout_url", response.json())

    @patch.dict(os.environ, {
        "STRIPE_PRICE_STARTER": "price_test_starter",
        "STRIPE_PRICE_GROWTH": "price_test_growth",
        "STRIPE_PRICE_ENTERPRISE": "price_test_enterprise",
    })
    @patch("backend.api.stripe_router.stripe.checkout.Session.create")
    def test_all_tiers_resolve(self, mock_create):
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_create.return_value = mock_session

        for tier, expected_price in [
            ("starter", "price_test_starter"),
            ("growth", "price_test_growth"),
            ("enterprise", "price_test_enterprise"),
        ]:
            with self.subTest(tier=tier):
                mock_create.reset_mock()
                response = self.client.post("/billing/checkout", json={"tier": tier})
                self.assertEqual(response.status_code, 200)
                call_kwargs = mock_create.call_args.kwargs
                line_items = call_kwargs.get("line_items", [])
                self.assertTrue(
                    any(item.get("price") == expected_price for item in line_items),
                    f"Tier '{tier}': expected {expected_price} in line_items, got {line_items}",
                )


class TestCheckoutInvalidTier(unittest.TestCase):

    def setUp(self):
        app.dependency_overrides[verify_access] = _mock_verify_access
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_invalid_tier_returns_400(self):
        response = self.client.post("/billing/checkout", json={"tier": "platinum"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid tier", response.json()["detail"])

    def test_empty_tier_returns_400(self):
        response = self.client.post("/billing/checkout", json={"tier": ""})
        self.assertEqual(response.status_code, 400)

    def test_invalid_tier_makes_no_stripe_call(self):
        with patch("backend.api.stripe_router.stripe.checkout.Session.create") as mock_create:
            self.client.post("/billing/checkout", json={"tier": "free"})
            mock_create.assert_not_called()


class TestWebhook(unittest.TestCase):
    """Webhook must verify the Stripe signature and activate plans. Unsigned /
    forged payloads are rejected; a valid checkout.session.completed activates
    the tenant's plan. (Before C2 the webhook was a no-op stub that 200'd
    anything and never activated a plan — every paying customer stayed on trial.)"""

    def setUp(self):
        os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.pop("STRIPE_WEBHOOK_SECRET", None)

    def test_forged_payload_rejected_with_400(self):
        # No mock: construct_event runs for real and rejects the bad signature.
        response = self.client.post(
            "/billing/webhook",
            content=b'{"type":"checkout.session.completed","id":"evt_forged"}',
            headers={"stripe-signature": "t=1,v1=deadbeef"},
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_secret_returns_500(self):
        os.environ.pop("STRIPE_WEBHOOK_SECRET", None)
        response = self.client.post("/billing/webhook", content=b"{}",
                                    headers={"stripe-signature": "x"})
        self.assertEqual(response.status_code, 500)

    @patch("backend.api.stripe_router._mark_processed")
    @patch("backend.api.stripe_router._already_processed", return_value=False)
    @patch("backend.api.stripe_router._activate_plan")
    @patch("backend.api.stripe_router.stripe.Webhook.construct_event")
    def test_checkout_completed_activates_plan(self, mock_construct, mock_activate, *_):
        mock_construct.return_value = {
            "id": "evt_ok_1",
            "type": "checkout.session.completed",
            "data": {"object": {"client_reference_id": "tenant-test-001",
                                 "metadata": {"tenant_id": "tenant-test-001", "tier": "growth"}}},
        }
        response = self.client.post("/billing/webhook", content=b"{}",
                                    headers={"stripe-signature": "valid"})
        self.assertEqual(response.status_code, 200)
        mock_activate.assert_called_once_with("tenant-test-001", "growth")

    @patch("backend.api.stripe_router._mark_processed")
    @patch("backend.api.stripe_router._already_processed", return_value=False)
    @patch("backend.api.stripe_router._activate_plan")
    @patch("backend.api.stripe_router.stripe.Webhook.construct_event")
    def test_subscription_deleted_downgrades_to_trial(self, mock_construct, mock_activate, *_):
        mock_construct.return_value = {
            "id": "evt_del_1",
            "type": "customer.subscription.deleted",
            "data": {"object": {"metadata": {"tenant_id": "tenant-test-001"}}},
        }
        response = self.client.post("/billing/webhook", content=b"{}",
                                    headers={"stripe-signature": "valid"})
        self.assertEqual(response.status_code, 200)
        mock_activate.assert_called_once_with("tenant-test-001", "trial")

    @patch("backend.api.stripe_router._activate_plan")
    @patch("backend.api.stripe_router._already_processed", return_value=True)
    @patch("backend.api.stripe_router.stripe.Webhook.construct_event")
    def test_replayed_event_is_skipped(self, mock_construct, mock_seen, mock_activate):
        mock_construct.return_value = {
            "id": "evt_dupe",
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"tenant_id": "t", "tier": "starter"}}},
        }
        response = self.client.post("/billing/webhook", content=b"{}",
                                    headers={"stripe-signature": "valid"})
        self.assertEqual(response.status_code, 200)
        mock_activate.assert_not_called()


class TestWebhookSecurityBoundary(unittest.TestCase):
    """
    Structural tests: verify the two-router split enforces the auth boundary.

    The security guarantee is:
      billing_router         → gets verify_access at include time in main.py
      billing_webhook_router → included bare, no auth

    Testing that the webhook is on billing_webhook_router (not billing_router)
    proves it cannot receive the verify_access dependency.
    """

    def test_webhook_is_on_unauthenticated_router(self):
        webhook_paths = [r.path for r in billing_webhook_router.routes]
        self.assertIn(
            "/billing/webhook", webhook_paths,
            "Webhook must be on billing_webhook_router (no auth)",
        )

    def test_checkout_is_on_authenticated_router(self):
        checkout_paths = [r.path for r in billing_router.routes]
        self.assertIn(
            "/billing/checkout", checkout_paths,
            "Checkout must be on billing_router (gets verify_access at include time)",
        )

    def test_webhook_not_on_authenticated_router(self):
        authenticated_paths = [r.path for r in billing_router.routes]
        self.assertNotIn(
            "/billing/webhook", authenticated_paths,
            "Webhook must NOT be on billing_router — Stripe has no session cookie",
        )

    def test_checkout_not_on_unauthenticated_router(self):
        unauthenticated_paths = [r.path for r in billing_webhook_router.routes]
        self.assertNotIn(
            "/billing/checkout", unauthenticated_paths,
            "Checkout must NOT be on billing_webhook_router — requires auth",
        )


if __name__ == "__main__":
    unittest.main()
