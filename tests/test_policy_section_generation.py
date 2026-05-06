import unittest

from backend.api.routes import (
    POLICY_REQUIRED_SLOTS,
    _build_policy_payload_from_sections,
    _ensure_required_slots,
    _normalize_policy_payload_or_400,
    _validate_generated_section,
)
from backend.core.json_parser import PolicySchemaError
from fastapi import HTTPException


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

    def test_cleaner_backed_normalizer_preserves_metadata_fields(self):
        normalized = _normalize_policy_payload_or_400(
            {
                "title": "IT Asset Disposal Policy",
                "policy_name": "IT Asset Disposal Policy",
                "organization": "Takeoff LLC / Midnight",
                "status": "Draft",
                "version": "1.0",
                "policy_number": "OPS-001",
                "sections": [
                    {
                        "slot_id": "purpose",
                        "heading": "Purpose",
                        "content": "Define why secure asset disposal is required.",
                        "source_origin": "ai_generated",
                    }
                ],
                "framework_mappings": {"HIPAA": []},
            },
            organization_hint="Takeoff LLC / Midnight",
            required_frameworks=["HIPAA"],
        )
        self.assertEqual(normalized["policy_number"], "OPS-001")
        self.assertEqual(normalized["version"], "1.0")
        self.assertEqual(normalized["sections"][0]["source_origin"], "ai_generated")

    def test_cleaner_backed_normalizer_returns_400_for_invalid_policy_payload(self):
        with self.assertRaises(HTTPException) as ctx:
            _normalize_policy_payload_or_400(
                {
                    "title": "Broken Policy",
                    "organization": "Takeoff LLC / Midnight",
                    "status": "Draft",
                    "sections": [],
                },
                organization_hint="Takeoff LLC / Midnight",
                required_frameworks=[],
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Policy data is invalid", str(ctx.exception.detail))


if __name__ == "__main__":
    unittest.main()
