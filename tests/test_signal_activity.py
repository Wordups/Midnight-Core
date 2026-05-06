import unittest
from unittest.mock import patch

from backend.storage.file_store import create_signal_activity_event


class SignalActivityPersistenceTests(unittest.TestCase):
    def test_missing_tenant_skips_persistence(self):
        with patch("backend.storage.file_store._insert_activity_log") as insert_mock:
            result = create_signal_activity_event(
                tenant_id="",
                event_type="policy_generation_failed",
                source="pipeline.create.preview",
                summary="Policy preview failed.",
            )
        self.assertIsNone(result)
        insert_mock.assert_not_called()

    def test_valid_signal_persists_signal_type_action(self):
        with patch("backend.storage.file_store._insert_activity_log") as insert_mock:
            signal = create_signal_activity_event(
                tenant_id="tenant-123",
                user_id="user-123",
                event_type="policy_generation_failed",
                source="pipeline.create.preview",
                summary="Policy preview failed.",
                policy_id="policy-123",
                metadata={"doc_type": "POLICY"},
            )
        self.assertIsNotNone(signal)
        self.assertEqual(signal["signal_type"], "policy_generation_failed")
        insert_mock.assert_called_once_with(
            tenant_id="tenant-123",
            action="policy_generation_failed",
            policy_id="policy-123",
        )


if __name__ == "__main__":
    unittest.main()
