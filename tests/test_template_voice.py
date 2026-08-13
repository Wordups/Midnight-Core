"""The four template variants must carry distinct voices + length budgets into
section generation — the fix for 'the variants all came out identical'."""
import os
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")
os.environ.setdefault("ENVIRONMENT", "dev")

from backend.core.template_voice import (
    VARIANTS,
    VARIANT_PROFILES,
    normalize_variant,
    profile_for,
    section_voice_block,
    section_word_budget,
)


class TemplateVoiceTests(unittest.TestCase):
    def test_all_four_variants_defined(self):
        self.assertEqual(set(VARIANTS), {"formal", "modern", "detailed", "executive"})
        for v in VARIANTS:
            self.assertIn(v, VARIANT_PROFILES)
            self.assertTrue(VARIANT_PROFILES[v]["directive"])
            self.assertGreater(VARIANT_PROFILES[v]["target_words"], 0)

    def test_length_ordering_matches_library(self):
        # From the manifest: executive < modern < formal < detailed.
        wc = {v: VARIANT_PROFILES[v]["target_words"] for v in VARIANTS}
        self.assertLess(wc["executive"], wc["modern"])
        self.assertLess(wc["modern"], wc["formal"])
        self.assertLess(wc["formal"], wc["detailed"])

    def test_unknown_variant_falls_back_to_default(self):
        self.assertEqual(normalize_variant("nonsense"), "modern")
        self.assertEqual(normalize_variant(None), "modern")
        self.assertEqual(normalize_variant("FORMAL"), "formal")

    def test_word_budget_scales_down_with_more_slots(self):
        few = section_word_budget("detailed", num_slots=2)
        many = section_word_budget("detailed", num_slots=10)
        self.assertGreater(few, many)
        self.assertGreaterEqual(many, 40)  # floor

    def test_executive_budget_is_tighter_than_detailed(self):
        exe = section_word_budget("executive", num_slots=8)
        det = section_word_budget("detailed", num_slots=8)
        self.assertLess(exe, det)

    def test_voice_block_distinguishes_variants(self):
        formal = section_voice_block("formal", num_slots=8)
        executive = section_voice_block("executive", num_slots=8)
        self.assertNotEqual(formal, executive)
        self.assertIn("legal", formal.lower())
        self.assertIn("brief", executive.lower())
        # each block names its own variant title
        self.assertIn("Formal", formal)
        self.assertIn("Executive", executive)


class SectionPromptVariantTests(unittest.TestCase):
    def test_section_prompt_embeds_variant_voice(self):
        # The route builder must inject the voice block; formal and executive
        # prompts for the same slot must differ.
        from backend.api.routes import CreatePolicyRequest, _build_section_prompt

        common = dict(
            metadata={"title": "Access Policy", "organization": "Acme",
                      "owner": "Jane", "document_type": "POLICY"},
            slot_spec={"slot_id": "purpose", "heading": "Purpose",
                       "instruction": "State the purpose."},
            normalized_frameworks=["SOC 2"],
            fw_context=["SOC2-CC6.1"],
            mapping_rules="none",
            num_slots=8,
        )
        base = dict(policy_name="P", doc_type="POLICY", industry="Tech",
                    frameworks=["SOC 2"], owner="Jane")
        formal = _build_section_prompt(
            CreatePolicyRequest(**base, template_variant="formal"), **common)
        executive = _build_section_prompt(
            CreatePolicyRequest(**base, template_variant="executive"), **common)
        self.assertNotEqual(formal, executive)
        self.assertIn("legal", formal.lower())
        self.assertIn("brief", executive.lower())

    def test_missing_variant_defaults_not_crash(self):
        from backend.api.routes import CreatePolicyRequest, _build_section_prompt

        prompt = _build_section_prompt(
            CreatePolicyRequest(policy_name="P", doc_type="POLICY", industry="Tech",
                                frameworks=["SOC 2"], owner="Jane"),
            metadata={"title": "T", "organization": "O", "owner": "J",
                      "document_type": "POLICY"},
            slot_spec={"slot_id": "purpose", "heading": "Purpose", "instruction": "x"},
            normalized_frameworks=["SOC 2"], fw_context=["c"], mapping_rules="r",
            num_slots=8,
        )
        self.assertIn("Modern", prompt)  # default variant


if __name__ == "__main__":
    unittest.main()
