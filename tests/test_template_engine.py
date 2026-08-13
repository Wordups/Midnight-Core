"""Template engine: styled shells resolve per doc_type x variant, bodies are
cleared, branding lands, and everything fails open to a blank Document."""
import os
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role")
os.environ.setdefault("ENVIRONMENT", "dev")

from docx.shared import RGBColor

from backend.core.template_engine import (
    DOC_TYPE_TO_CATEGORY,
    VARIANTS,
    load_template_shell,
    normalize_variant,
    shell_path,
)


class ShellResolutionTests(unittest.TestCase):
    def test_all_live_doc_types_have_all_variants(self):
        for doc_type in ("POLICY", "SOP", "STANDARD", "INCIDENT_RUNBOOK"):
            for variant in VARIANTS:
                path = shell_path(doc_type, variant)
                self.assertIsNotNone(path, f"{doc_type}/{variant} shell missing")

    def test_every_registered_category_resolves(self):
        for doc_type in DOC_TYPE_TO_CATEGORY:
            self.assertIsNotNone(shell_path(doc_type, "modern"), doc_type)

    def test_unknown_doc_type_returns_none(self):
        self.assertIsNone(shell_path("KARAOKE_NIGHT"))

    def test_variant_normalization(self):
        self.assertEqual(normalize_variant("FORMAL "), "formal")
        self.assertEqual(normalize_variant("nonsense"), "modern")
        self.assertEqual(normalize_variant(None), "modern")


class ShellLoadTests(unittest.TestCase):
    def test_shell_body_is_cleared_but_styles_survive(self):
        doc = load_template_shell("POLICY", "formal")
        self.assertTrue(doc.is_template_shell)
        self.assertEqual(len(doc.paragraphs), 0)
        style_names = {s.name for s in doc.styles}
        self.assertIn("Heading 1", style_names)
        self.assertIn("Title", style_names)

    def test_unknown_type_falls_back_to_blank(self):
        doc = load_template_shell("KARAOKE_NIGHT")
        self.assertFalse(doc.is_template_shell)

    def test_branding_color_applied_to_headings(self):
        doc = load_template_shell("POLICY", "modern", branding={
            "organization": "Pixel Forge Interactive",
            "title": "Access Control Policy",
            "primary_color": "#2563EB",
        })
        self.assertEqual(doc.styles["Heading 1"].font.color.rgb, RGBColor(0x25, 0x63, 0xEB))

    def test_bad_color_ignored(self):
        doc = load_template_shell("POLICY", "modern", branding={"primary_color": "not-a-color"})
        self.assertTrue(doc.is_template_shell)

    def test_render_into_shell_produces_valid_docx(self):
        from io import BytesIO
        from backend.renderers.docx_renderer import render_markdown_into

        doc = load_template_shell("SOP", "detailed")
        doc.add_heading("Purpose", level=1)
        render_markdown_into(doc, "This SOP defines **the steps** for onboarding.")
        buffer = BytesIO()
        doc.save(buffer)
        self.assertGreater(len(buffer.getvalue()), 1000)


if __name__ == "__main__":
    unittest.main()
