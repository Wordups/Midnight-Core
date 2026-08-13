import unittest

from backend.core.json_parser import (
    ParsedModelOutputError,
    PolicySchemaError,
    normalize_policy_payload,
    parse_model_json,
)


class JsonParserTests(unittest.TestCase):
    def test_parse_fenced_json(self):
        parsed = parse_model_json(
            """```json
            {"title":"IT Asset Disposal Policy","organization":"Takeoff LLC / Midnight","status":"Draft","sections":[{"heading":"Purpose","content":"Retire assets safely."}]}
            ```"""
        )
        self.assertEqual(parsed["title"], "IT Asset Disposal Policy")

    def test_parse_json_with_prose_before_and_after(self):
        parsed = parse_model_json(
            """Here is the policy draft:
            {"title":"IT Asset Disposal Policy","organization":"Takeoff LLC / Midnight","status":"Draft","sections":[{"heading":"Purpose","content":"Retire assets safely."}]}
            End of response."""
        )
        self.assertEqual(parsed["status"], "Draft")

    def test_parse_unquoted_keys_and_trailing_commas(self):
        parsed = parse_model_json(
            """{
              title: "IT Asset Disposal Policy",
              organization: "Takeoff LLC / Midnight",
              status: "Draft",
              sections: [
                {"heading":"Purpose","content":"Retire assets safely."},
              ],
            }"""
        )
        self.assertEqual(parsed["organization"], "Takeoff LLC / Midnight")

    def test_parse_smart_quotes(self):
        parsed = parse_model_json(
            """{
              “title”: “IT Asset Disposal Policy”,
              “organization”: “Takeoff LLC / Midnight”,
              “status”: “Draft”,
              “sections”: [{“heading”: “Purpose”, “content”: “Retire assets safely.”}]
            }"""
        )
        self.assertEqual(parsed["title"], "IT Asset Disposal Policy")

    def test_empty_response_raises(self):
        with self.assertRaises(ParsedModelOutputError):
            parse_model_json("")

    def test_unterminated_string_raises(self):
        with self.assertRaises(ParsedModelOutputError):
            parse_model_json(
                '{"title":"IT Asset Disposal Policy","organization":"Takeoff LLC / Midnight","status":"Draft","sections":[{"heading":"Purpose","content":"Asset disposal requires'
            )

    def test_python_style_dict_raises(self):
        with self.assertRaises(ParsedModelOutputError):
            parse_model_json(
                "{'title': 'IT Asset Disposal Policy', 'organization': 'Takeoff LLC / Midnight', 'status': 'Draft', 'sections': [{'heading': 'Purpose', 'content': 'Retire assets safely.'}]}"
            )

    def test_normalize_policy_payload_rejects_missing_title(self):
        with self.assertRaises(PolicySchemaError):
            normalize_policy_payload(
                {
                    "organization": "Takeoff LLC / Midnight",
                    "status": "Draft",
                    "sections": [{"heading": "Purpose", "content": "Retire assets safely."}],
                }
            )

    def test_normalize_policy_payload_rejects_array_root(self):
        with self.assertRaises(PolicySchemaError):
            normalize_policy_payload([])  # type: ignore[arg-type]

    def test_normalize_policy_payload_rejects_invalid_framework_mappings(self):
        with self.assertRaises(PolicySchemaError):
            normalize_policy_payload(
                {
                    "title": "IT Asset Disposal Policy",
                    "organization": "Takeoff LLC / Midnight",
                    "status": "Draft",
                    "sections": [{"heading": "Purpose", "content": "Retire assets safely."}],
                    "framework_mappings": ["HIPAA"],
                },
                required_frameworks=["HIPAA"],
            )

    def test_normalize_policy_payload_builds_sections_from_legacy_shape(self):
        normalized = normalize_policy_payload(
            {
                "policy_name": "IT Asset Disposal Policy",
                "organization": "Takeoff LLC / Midnight",
                "status": "Draft",
                "purpose": "Retire assets safely.",
                "scope": "Applies to all corporate endpoints.",
                "policy_statement": "All media must be disposed of securely.",
                "framework_mappings": {"HIPAA": ["164.310(d)(2)(i)"]},
            },
            required_frameworks=["HIPAA"],
        )
        self.assertEqual(normalized["title"], "IT Asset Disposal Policy")
        self.assertGreaterEqual(len(normalized["sections"]), 3)
        self.assertEqual(normalized["sections"][0]["slot_id"], "purpose")


if __name__ == "__main__":
    unittest.main()


def test_parse_survives_literal_control_chars_in_strings():
    """Groq/Llama emit literal newlines inside JSON strings; strict=False path."""
    raw = '{"heading": "Definitions", "content": "Line one\nLine two\ttabbed"}'
    parsed = parse_model_json(raw)
    assert "Line one" in parsed["content"]


def test_parse_survives_invalid_escapes():
    raw = '{"content": "Vendors must be tiered \& reviewed annually"}'
    parsed = parse_model_json(raw)
    assert "tiered" in parsed["content"]


def test_valid_escapes_untouched():
    raw = '{"content": "line\nbreak and \\"quote\\""}'
    parsed = parse_model_json(raw)
    assert parsed["content"] == 'line\nbreak and "quote"'
