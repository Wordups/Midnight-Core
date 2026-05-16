"""P0 engine-lockdown regression tests.

Covers the policy-generation hot path:
  - parse_model_json handles prose-wrapped, fenced, clean JSON
  - _validate_policy_metadata enforces required fields with 422
  - _validate_policy_metadata canonicalizes selected_frameworks against
    RECOGNIZED_FRAMEWORKS and 422s on unknown values
  - _compute_quality_flags emits the homogeneous-shape flag array with
    correct severity for each threshold class
  - section-spec / prompt resolvers return generic fallback when the
    registry is empty (P0 default state)

Tests are unit-level (no Supabase, no real Anthropic). They exercise
the same parser + validator + quality-flag functions the hot path
runs. End-to-end HTTP coverage lives in test_assessments.py and the
ship-gate script.
"""
from __future__ import annotations

import os
import unittest

# Env scaffolding so config imports succeed when this module is
# collected before any other env is loaded.
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role")
os.environ.setdefault("TOOL_PASSWORD", "test-password")
os.environ.setdefault("ENVIRONMENT", "dev")

from fastapi import HTTPException  # noqa: E402

from backend.api.routes import (  # noqa: E402
    CreatePolicyRequest,
    POLICY_SLOT_SPECS,
    RECOGNIZED_FRAMEWORKS,
    SLOT_SPEC_REGISTRY,
    METADATA_PROMPT_REGISTRY,
    SECTION_PROMPT_REGISTRY,
    _build_metadata_prompt,
    _build_section_prompt,
    _canonicalize_framework,
    _compute_quality_flags,
    _metadata_prompt_loader,
    _section_prompt_loader,
    _slot_specs_for_category,
    _validate_policy_metadata,
)
from backend.core.json_parser import parse_model_json  # noqa: E402


# ─── Fixtures ────────────────────────────────────────────────────────────────

def _make_request(
    policy_name: str = "Test Policy",
    doc_type: str = "POLICY",
    frameworks: list[str] | None = None,
) -> CreatePolicyRequest:
    return CreatePolicyRequest(
        policy_name=policy_name,
        doc_type=doc_type,
        industry="Technology",
        frameworks=frameworks or ["SOC_2"],
        owner="Security Lead",
    )


_DEFAULT = object()


def _well_formed_metadata(
    *,
    title: str = "Test Policy",
    selected_frameworks=_DEFAULT,
) -> dict:
    # Sentinel pattern so an explicit empty list isn't collapsed back to
    # the default by `selected_frameworks or [...]`.
    frameworks = ["SOC_2"] if selected_frameworks is _DEFAULT else selected_frameworks
    return {
        "title": title,
        "organization": "Test Org",
        "owner": "Security Lead",
        "document_type": "Policy",
        "status": "Draft",
        "schema_version": "1.0",
        "selected_frameworks": frameworks,
    }


def _section(slot_id: str, heading: str, content: str) -> dict:
    return {
        "slot_id": slot_id,
        "heading": heading,
        "content": content,
        "sort_order": 1,
        "source_origin": "ai_generated",
    }


# Body that comfortably exceeds the 200-char thin threshold.
_FAT_BODY = (
    "This policy establishes the operational, technical, and "
    "administrative requirements for the program. It applies to all "
    "personnel, contractors, and authorized third parties. Compliance "
    "is mandatory and tracked through quarterly review cycles documented "
    "by the security team and reviewed annually."
)
assert len(_FAT_BODY) >= 200  # sanity


# ─── Test 1: IT Asset Disposal — prose-wrapped JSON parses + validates ──────

class TestITAssetDisposalProseWrapped(unittest.TestCase):
    """The known failure shape: model returns prose before+after a fenced
    JSON object. Pre-Phase-1 this crashed json.loads. Today the safe
    parser strips fences/prose and the validator accepts the result."""

    PROSE_WRAPPED_METADATA = (
        "Here is the policy metadata you requested:\n\n"
        "```json\n"
        '{\n'
        '  "title": "IT Asset Disposal Policy",\n'
        '  "organization": "Helix Health Systems",\n'
        '  "owner": "Security Lead",\n'
        '  "document_type": "Policy",\n'
        '  "status": "Draft",\n'
        '  "schema_version": "1.0",\n'
        '  "policy_number": "SEC-018",\n'
        '  "version": "1.0",\n'
        '  "selected_frameworks": ["HIPAA", "HITRUST"]\n'
        '}\n'
        "```\n\n"
        "Let me know if you want to adjust any of this."
    )

    def test_parser_extracts_clean_dict(self):
        parsed = parse_model_json(self.PROSE_WRAPPED_METADATA)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["title"], "IT Asset Disposal Policy")
        self.assertEqual(parsed["selected_frameworks"], ["HIPAA", "HITRUST"])

    def test_validator_accepts_after_parse(self):
        parsed = parse_model_json(self.PROSE_WRAPPED_METADATA)
        metadata = _validate_policy_metadata(
            parsed,
            request=_make_request(
                policy_name="IT Asset Disposal Policy",
                frameworks=["HIPAA", "HITRUST"],
            ),
            organization_hint="Helix Health Systems",
            normalized_frameworks=["HIPAA", "HITRUST"],
        )
        self.assertEqual(metadata["title"], "IT Asset Disposal Policy")
        self.assertEqual(metadata["selected_frameworks"], ["HIPAA", "HITRUST"])
        self.assertEqual(metadata["organization"], "Helix Health Systems")


# ─── Test 2: Acceptable Use Policy — clean happy path ────────────────────────

class TestAUPHappyPath(unittest.TestCase):
    """Pure JSON, no fences, no prose. Should parse on first try and
    validate without any 422."""

    CLEAN_METADATA = (
        '{"title":"Acceptable Use Policy","organization":"Test Org",'
        '"owner":"IT Director","document_type":"Policy",'
        '"status":"Approved","schema_version":"1.0",'
        '"selected_frameworks":["SOC_2"]}'
    )

    def test_parses_and_validates(self):
        parsed = parse_model_json(self.CLEAN_METADATA)
        metadata = _validate_policy_metadata(
            parsed,
            request=_make_request(policy_name="Acceptable Use Policy"),
            organization_hint="Test Org",
            normalized_frameworks=["SOC_2"],
        )
        self.assertEqual(metadata["title"], "Acceptable Use Policy")
        self.assertEqual(metadata["status"], "Approved")
        self.assertEqual(metadata["selected_frameworks"], ["SOC_2"])


# ─── Test 3a: Multi-framework valid ──────────────────────────────────────────

class TestMultiFrameworkValid(unittest.TestCase):
    """A policy spanning HIPAA + PCI_DSS + SOC_2 — all three canonicalize
    cleanly and pass the recognized-set check."""

    def test_three_frameworks_accepted(self):
        metadata = _validate_policy_metadata(
            _well_formed_metadata(
                selected_frameworks=["HIPAA", "PCI_DSS", "SOC_2"]
            ),
            request=_make_request(frameworks=["HIPAA", "PCI_DSS", "SOC_2"]),
            organization_hint="Test Org",
            normalized_frameworks=["HIPAA", "PCI_DSS", "SOC_2"],
        )
        self.assertEqual(
            sorted(metadata["selected_frameworks"]),
            ["HIPAA", "PCI_DSS", "SOC_2"],
        )

    def test_loose_input_forms_canonicalize(self):
        """Model returns frameworks in human-friendly form; canonicalizer
        normalizes them before checking the recognized set."""
        metadata = _validate_policy_metadata(
            _well_formed_metadata(
                selected_frameworks=["soc 2", "pci-dss", "ISO 27001"]
            ),
            request=_make_request(frameworks=["SOC_2", "PCI_DSS", "ISO_27001"]),
            organization_hint="Test Org",
            normalized_frameworks=["SOC_2", "PCI_DSS", "ISO_27001"],
        )
        self.assertEqual(
            sorted(metadata["selected_frameworks"]),
            ["ISO_27001", "PCI_DSS", "SOC_2"],
        )


# ─── Test 3b: Unrecognized framework rejected with 422 ───────────────────────

class TestUnrecognizedFrameworkRejected(unittest.TestCase):

    def test_rejects_with_422_and_names_offender(self):
        with self.assertRaises(HTTPException) as ctx:
            _validate_policy_metadata(
                _well_formed_metadata(
                    selected_frameworks=["HIPAA", "MARS_2024"]
                ),
                request=_make_request(frameworks=["HIPAA"]),
                organization_hint="Test Org",
                normalized_frameworks=["HIPAA"],
            )
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("MARS_2024", ctx.exception.detail)
        self.assertIn("selected_frameworks", ctx.exception.detail)

    def test_empty_array_rejected_with_422(self):
        with self.assertRaises(HTTPException) as ctx:
            _validate_policy_metadata(
                _well_formed_metadata(selected_frameworks=[]),
                request=_make_request(),
                organization_hint="Test Org",
                normalized_frameworks=[],
            )
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("non-empty", ctx.exception.detail.lower())

    def test_missing_field_rejected_with_422(self):
        bad = _well_formed_metadata()
        bad.pop("selected_frameworks")
        with self.assertRaises(HTTPException) as ctx:
            _validate_policy_metadata(
                bad,
                request=_make_request(),
                organization_hint="Test Org",
                normalized_frameworks=["SOC_2"],
            )
        self.assertEqual(ctx.exception.status_code, 422)

    def test_missing_title_returns_422(self):
        bad = _well_formed_metadata()
        bad["title"] = ""
        # Without a title, the validator falls back to request.policy_name
        # — so to actually test the missing-required-field path we use a
        # request with empty policy_name. CreatePolicyRequest doesn't
        # accept empty policy_name (Pydantic-constrained), so we pass a
        # whitespace-only one and strip pushes it back to empty.
        with self.assertRaises(HTTPException) as ctx:
            _validate_policy_metadata(
                bad,
                request=_make_request(policy_name="   "),
                organization_hint="",
                normalized_frameworks=["SOC_2"],
            )
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("title", ctx.exception.detail)


# ─── Framework canonicalizer unit coverage ──────────────────────────────────

class TestFrameworkCanonicalization(unittest.TestCase):

    def test_canonical_values(self):
        cases = [
            ("HIPAA", "HIPAA"),
            ("hipaa", "HIPAA"),
            ("  hipaa  ", "HIPAA"),
            ("SOC 2", "SOC_2"),
            ("soc 2", "SOC_2"),
            ("Soc-2", "SOC_2"),
            ("SOC.2", "SOC_2"),
            ("PCI DSS", "PCI_DSS"),
            ("PCI-DSS", "PCI_DSS"),
            ("pci.dss", "PCI_DSS"),
            ("iso 27001", "ISO_27001"),
            ("ISO/27001", "ISO/27001"),  # `/` is not a recognized delimiter
            ("NIST CSF", "NIST_CSF"),
            ("nist_csf", "NIST_CSF"),
            ("HITRUST", "HITRUST"),
            ("COBIT 2019", "COBIT_2019"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(_canonicalize_framework(raw), expected)

    def test_recognized_set_membership(self):
        self.assertIn("HIPAA", RECOGNIZED_FRAMEWORKS)
        self.assertIn("SOC_2", RECOGNIZED_FRAMEWORKS)
        self.assertIn("PCI_DSS", RECOGNIZED_FRAMEWORKS)
        self.assertIn("ISO_27001", RECOGNIZED_FRAMEWORKS)
        self.assertIn("NIST_CSF", RECOGNIZED_FRAMEWORKS)
        self.assertIn("COBIT_2019", RECOGNIZED_FRAMEWORKS)
        self.assertIn("HITRUST", RECOGNIZED_FRAMEWORKS)
        self.assertEqual(len(RECOGNIZED_FRAMEWORKS), 7)


# ─── Quality flag thresholds ─────────────────────────────────────────────────

class TestQualityFlagsClean(unittest.TestCase):
    """Happy path: every section over the threshold and there are enough
    of them — no flags emitted."""

    def test_no_flags(self):
        sections = [
            _section(s["slot_id"], s["heading"], _FAT_BODY)
            for s in POLICY_SLOT_SPECS
        ]
        flags = _compute_quality_flags(
            sections=sections,
            tenant_id="tenant-x",
            policy_id="policy-x",
        )
        self.assertEqual(flags, [])


class TestQualityFlagsThinSection(unittest.TestCase):

    def test_one_thin_section_emits_one_warning(self):
        sections = [
            _section(s["slot_id"], s["heading"], _FAT_BODY)
            for s in POLICY_SLOT_SPECS
        ]
        # Replace one section's content with a short body
        sections[2]["content"] = "Very short body."  # 16 chars
        flags = _compute_quality_flags(
            sections=sections,
            tenant_id="tenant-x",
            policy_id="policy-x",
        )
        thin_flags = [f for f in flags if f["flag"] == "thin_section"]
        self.assertEqual(len(thin_flags), 1)
        flag = thin_flags[0]
        self.assertEqual(flag["severity"], "warning")
        self.assertIn("16 characters", flag["message"])
        self.assertEqual(flag["context"]["slot_id"], POLICY_SLOT_SPECS[2]["slot_id"])
        self.assertEqual(flag["context"]["char_count"], 16)
        # 1/9 thin = 11%, below the 30% threshold — no fail_thin
        self.assertFalse(any(f["flag"] == "fail_thin" for f in flags))


class TestQualityFlagsBrokenSection(unittest.TestCase):

    def test_placeholder_only_emits_broken_warning(self):
        sections = [
            _section(s["slot_id"], s["heading"], _FAT_BODY)
            for s in POLICY_SLOT_SPECS
        ]
        sections[0]["content"] = "{{org_name}}"
        flags = _compute_quality_flags(
            sections=sections,
            tenant_id="tenant-x",
            policy_id="policy-x",
        )
        broken = [f for f in flags if f["flag"] == "broken_section"]
        self.assertEqual(len(broken), 1)
        self.assertEqual(broken[0]["severity"], "warning")
        self.assertIn("placeholder", broken[0]["message"].lower())
        self.assertEqual(broken[0]["context"]["placeholder_text"], "{{org_name}}")

    def test_placeholder_with_surrounding_whitespace(self):
        sections = [_section("scope", "Scope", "   {{tenant_name}}   ")]
        flags = _compute_quality_flags(
            sections=sections, tenant_id="t", policy_id="p"
        )
        broken = [f for f in flags if f["flag"] == "broken_section"]
        self.assertEqual(len(broken), 1)

    def test_real_content_with_embedded_placeholder_not_flagged(self):
        # Placeholder embedded inside real prose isn't "only placeholder"
        sections = [
            _section("scope", "Scope", f"Applies to all systems at {{{{tenant_name}}}} including production. " + _FAT_BODY),
        ]
        flags = _compute_quality_flags(
            sections=sections, tenant_id="t", policy_id="p"
        )
        self.assertFalse(any(f["flag"] == "broken_section" for f in flags))


class TestQualityFlagsThinPolicy(unittest.TestCase):

    def test_two_sections_emits_thin_policy(self):
        sections = [
            _section("purpose", "Purpose", _FAT_BODY),
            _section("scope", "Scope", _FAT_BODY),
        ]
        flags = _compute_quality_flags(
            sections=sections, tenant_id="t", policy_id="p"
        )
        thin_policy = [f for f in flags if f["flag"] == "thin_policy"]
        self.assertEqual(len(thin_policy), 1)
        self.assertEqual(thin_policy[0]["severity"], "warning")
        self.assertEqual(thin_policy[0]["context"]["section_count"], 2)

    def test_three_sections_no_thin_policy(self):
        sections = [
            _section("purpose", "Purpose", _FAT_BODY),
            _section("scope", "Scope", _FAT_BODY),
            _section("definitions", "Definitions", _FAT_BODY),
        ]
        flags = _compute_quality_flags(
            sections=sections, tenant_id="t", policy_id="p"
        )
        self.assertFalse(any(f["flag"] == "thin_policy" for f in flags))


class TestQualityFlagsFailThin(unittest.TestCase):

    def test_fifty_percent_thin_triggers_fail_thin_error(self):
        sections = [
            _section("purpose", "Purpose", "short"),    # thin
            _section("scope", "Scope", "short"),        # thin
            _section("defs", "Definitions", "short"),   # thin
            _section("roles", "Roles", "short"),        # thin
            _section("policy_statement", "Policy", _FAT_BODY),
            _section("standards", "Standards", _FAT_BODY),
            _section("procedures", "Procedures", _FAT_BODY),
            _section("compliance", "Compliance", _FAT_BODY),
            _section("approval", "Approval", _FAT_BODY),
        ]
        flags = _compute_quality_flags(
            sections=sections, tenant_id="t", policy_id="p"
        )
        fail = [f for f in flags if f["flag"] == "fail_thin"]
        self.assertEqual(len(fail), 1)
        self.assertEqual(fail[0]["severity"], "error")
        self.assertEqual(fail[0]["context"]["thin_count"], 4)
        self.assertEqual(fail[0]["context"]["total_count"], 9)
        # 4/9 = 44%
        self.assertAlmostEqual(fail[0]["context"]["ratio"], 0.444, places=2)
        self.assertIn("44%", fail[0]["message"])

    def test_thirty_percent_thin_does_not_trigger_fail_thin(self):
        # 3 of 10 sections thin = 30% — strictly NOT > 0.30, so no fail_thin.
        # We use 10 to avoid the thin_policy threshold (<3 sections).
        sections = (
            [_section(f"s{i}", f"S{i}", "short") for i in range(3)]
            + [_section(f"s{i}", f"S{i}", _FAT_BODY) for i in range(3, 10)]
        )
        flags = _compute_quality_flags(
            sections=sections, tenant_id="t", policy_id="p"
        )
        self.assertFalse(any(f["flag"] == "fail_thin" for f in flags))


class TestQualityFlagShape(unittest.TestCase):
    """Every flag has the homogeneous {flag, severity, message, context}
    shape — frontend renders generically without per-flag switches."""

    REQUIRED_KEYS = {"flag", "severity", "message", "context"}

    def test_all_flag_types_share_shape(self):
        # One scenario that triggers every flag class at once.
        sections = [
            _section("a", "A", "short"),                  # thin_section
            _section("b", "B", "{{placeholder}}"),        # broken_section
        ]
        # only 2 sections => thin_policy. 1/2 thin_section => >30% =>
        # fail_thin. broken_section doesn't count as thin (different
        # category), so thin_count = 1, total = 2, ratio = 0.5 > 0.30.
        flags = _compute_quality_flags(
            sections=sections, tenant_id="t", policy_id="p"
        )
        flag_ids = {f["flag"] for f in flags}
        self.assertIn("thin_section", flag_ids)
        self.assertIn("broken_section", flag_ids)
        self.assertIn("thin_policy", flag_ids)
        self.assertIn("fail_thin", flag_ids)
        for flag in flags:
            self.assertEqual(set(flag.keys()), self.REQUIRED_KEYS, flag)
            self.assertIn(flag["severity"], {"warning", "error"})
            self.assertIsInstance(flag["context"], dict)
            self.assertIsInstance(flag["message"], str)
            self.assertGreater(len(flag["message"]), 0)


# ─── Resolver fallback (extensibility scaffolding) ──────────────────────────

class TestSlotSpecResolver(unittest.TestCase):

    def test_empty_registry_falls_back_to_generic(self):
        self.assertEqual(SLOT_SPEC_REGISTRY, {})  # P0 invariant
        self.assertIs(_slot_specs_for_category("anything"), POLICY_SLOT_SPECS)
        self.assertIs(_slot_specs_for_category(None), POLICY_SLOT_SPECS)
        self.assertIs(_slot_specs_for_category(""), POLICY_SLOT_SPECS)

    def test_registered_category_returns_its_specs(self):
        custom = [{"slot_id": "scope", "heading": "Scope", "instruction": "..."}]
        SLOT_SPEC_REGISTRY["procedure"] = custom
        try:
            self.assertIs(_slot_specs_for_category("procedure"), custom)
            # Unrelated category still falls back
            self.assertIs(_slot_specs_for_category("policy"), POLICY_SLOT_SPECS)
        finally:
            SLOT_SPEC_REGISTRY.pop("procedure", None)


class TestPromptResolvers(unittest.TestCase):

    def test_empty_registries_fall_back_to_generic_builders(self):
        self.assertEqual(METADATA_PROMPT_REGISTRY, {})
        self.assertEqual(SECTION_PROMPT_REGISTRY, {})
        self.assertIs(_metadata_prompt_loader("anything"), _build_metadata_prompt)
        self.assertIs(_section_prompt_loader("anything"), _build_section_prompt)

    def test_registered_builder_returned(self):
        sentinel_meta = object()
        sentinel_section = object()
        METADATA_PROMPT_REGISTRY["procedure"] = sentinel_meta
        SECTION_PROMPT_REGISTRY["procedure"] = sentinel_section
        try:
            self.assertIs(_metadata_prompt_loader("procedure"), sentinel_meta)
            self.assertIs(_section_prompt_loader("procedure"), sentinel_section)
            self.assertIs(_metadata_prompt_loader("policy"), _build_metadata_prompt)
        finally:
            METADATA_PROMPT_REGISTRY.pop("procedure", None)
            SECTION_PROMPT_REGISTRY.pop("procedure", None)


if __name__ == "__main__":
    unittest.main()
