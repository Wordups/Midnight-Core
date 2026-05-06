import unittest

from backend.core.beta_access import (
    is_invite_delivery_failure,
    manual_join_blocker,
    normalize_email,
)


class BetaAccessTests(unittest.TestCase):
    def test_normalize_email_trims_and_lowercases(self):
        self.assertEqual(normalize_email("  Tester@Example.COM "), "tester@example.com")

    def test_invite_delivery_failure_detection(self):
        self.assertTrue(is_invite_delivery_failure("Failed to invite user. Error sending invite email."))
        self.assertFalse(is_invite_delivery_failure("User already registered."))

    def test_manual_join_blocker_allows_empty_bootstrap_tenant(self):
        blocker = manual_join_blocker(
            source_tenant_id="tenant-empty",
            destination_tenant_id="tenant-owner",
            profile_count=1,
            has_policies=False,
            has_documents=False,
        )
        self.assertIsNone(blocker)

    def test_manual_join_blocker_blocks_multi_user_tenant(self):
        blocker = manual_join_blocker(
            source_tenant_id="tenant-shared",
            destination_tenant_id="tenant-owner",
            profile_count=2,
            has_policies=False,
            has_documents=False,
        )
        self.assertIn("multi-user tenant", blocker)

    def test_manual_join_blocker_blocks_live_policy_data(self):
        blocker = manual_join_blocker(
            source_tenant_id="tenant-live",
            destination_tenant_id="tenant-owner",
            profile_count=1,
            has_policies=True,
            has_documents=False,
        )
        self.assertIn("policy data", blocker)


if __name__ == "__main__":
    unittest.main()
