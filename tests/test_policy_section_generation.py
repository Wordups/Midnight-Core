import unittest

from backend.api.routes import (
    POLICY_REQUIRED_SLOTS,
    _build_policy_payload_from_sections,
    _ensure_required_slots,
    _validate_generated_section,
)
from backend.core.json_parser import PolicySchemaError


class PolicySectionGenerationTests(unittest.TestCase):
    def test_validate_generated_section_accepts_expected_slot(self):
        section = _validate_generated_section(
            {
                "slot_id": "purpose",
                "heading": "Purpose",
                "content": "Define why secure asset disposal is required.",
            },
            slot_spec={
                "slot_id": "purpose",
                "heading": "Purpose",
                "instruction": "Explain the purpose.",
            },
        )
        self.assertEqual(section["slot_id"], "purpose")
        self.assertEqual(section["sort_order"], 1)

    def test_validate_generated_section_rejects_wrong_slot(self):
        with self.assertRaises(PolicySchemaError):
            _validate_generated_section(
                {
                    "slot_id": "scope",
                    "heading": "Scope",
                    "content": "Applies to all devices.",
                },
                slot_spec={
                    "slot_id": "purpose",
                    "heading": "Purpose",
                    "instruction": "Explain the purpose.",
                },
            )

    def test_build_policy_payload_marks_missing_required_slots(self):
        payload = _build_policy_payload_from_sections(
            metadata={
                "title": "IT Asset Disposal Policy",
                "organization": "Takeoff LLC / Midnight",
                "owner": "Brian Word",
                "document_type": "Policy",
                "status": "Draft",
                "schema_version": "midnight-policy-v2",
                "selected_frameworks": ["HIPAA"],
                "version": "1.0",
            },
            sections=[
                {
                    "slot_id": "purpose",
                    "heading": "Purpose",
                    "content": "Define why secure asset disposal is required.",
                }
            ],
            section_errors=[{"slot_id": "scope", "error": "truncated"}],
        )
        missing = _ensure_required_slots(payload)
        self.assertIn("scope", missing)
        self.assertEqual(payload["framework_mappings"], {"HIPAA": []})
        self.assertEqual(payload["section_errors"][0]["slot_id"], "scope")

    def test_complete_required_slots_returns_no_missing(self):
        payload = _build_policy_payload_from_sections(
            metadata={
                "title": "IT Asset Disposal Policy",
                "organization": "Takeoff LLC / Midnight",
                "owner": "Brian Word",
                "document_type": "Policy",
                "status": "Draft",
                "schema_version": "midnight-policy-v2",
                "selected_frameworks": [],
                "version": "1.0",
            },
            sections=[
                {
                    "slot_id": slot,
                    "heading": slot.replace("_", " ").title(),
                    "content": f"Content for {slot}.",
                }
                for slot in POLICY_REQUIRED_SLOTS
            ],
        )
        self.assertEqual(_ensure_required_slots(payload), [])


if __name__ == "__main__":
    unittest.main()
