"""License-safety tests for Midnight's public artifact knowledge layer."""

from pathlib import Path

from backend.core.public_artifacts import (
    ArtifactLibrary,
    build_generation_context,
    lint_artifact_library,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = REPO_ROOT / "knowledge" / "artifacts"


def test_artifact_lint_requires_license_metadata_and_blocks_restricted_raw_text():
    artifacts = [
        {
            "id": "iso_27001_a_5_1",
            "source_id": "iso_27001_2022",
            "title": "Policies for information security",
            "domain": "governance",
            "themes": ["policy governance"],
            "doc_types": ["policy"],
            "citation": "ISO/IEC 27001:2022 Annex A 5.1",
            "source_url": "https://www.iso.org/standard/27001",
            "license_policy": {
                "status": "restricted",
                "allowed_uses": ["index", "summarize", "cite", "generate_original_guidance"],
                "blocked_uses": ["quote_full_text", "redistribute", "template_clone"],
                "max_quote_chars": 0,
                "attribution_required": True,
                "source_license_url": "https://www.iso.org/copyright.html",
            },
            "midnight_summary": "Organizations should maintain approved security policies with ownership and review cadence.",
            "raw_text": "This should never be stored for a restricted source.",
        }
    ]

    issues = lint_artifact_library(artifacts)

    assert any("restricted artifact iso_27001_a_5_1 must not include raw_text" in issue for issue in issues)


def test_generation_context_excludes_restricted_raw_text_but_keeps_citation_and_summary():
    library = ArtifactLibrary.from_dir(ARTIFACT_DIR)

    context = build_generation_context(
        library,
        doc_type="policy",
        themes=["policy governance"],
        max_items=10,
    )

    iso_items = [item for item in context["artifacts"] if item["id"] == "iso_27001_a_5_1"]
    assert iso_items, "Expected ISO metadata-only artifact to match policy governance"
    iso = iso_items[0]

    assert iso["license_status"] == "restricted"
    assert "raw_text" not in iso
    assert iso["citation"] == "ISO/IEC 27001:2022 Annex A 5.1"
    assert "approved information security policies" in iso["midnight_summary"].lower()
    assert "Do not quote" in context["generation_guardrails"]


def test_generation_context_can_include_public_snippets_with_source_and_attribution():
    library = ArtifactLibrary.from_dir(ARTIFACT_DIR)

    context = build_generation_context(
        library,
        doc_type="playbook",
        themes=["incident response"],
        max_items=10,
    )

    nist_items = [item for item in context["artifacts"] if item["source_id"] == "nist_sp_800_61"]
    assert nist_items, "Expected NIST incident response artifact to match playbook context"
    nist = nist_items[0]

    assert nist["license_status"] in {"public_domain", "open_license"}
    assert "raw_text" in nist
    assert len(nist["raw_text"]) <= nist["max_quote_chars"]
    assert nist["source_url"].startswith("https://")


def test_context_matching_uses_doc_type_and_theme_without_limiting_to_nist():
    library = ArtifactLibrary.from_dir(ARTIFACT_DIR)

    context = build_generation_context(
        library,
        doc_type="standard",
        themes=["application security", "api security"],
        max_items=10,
    )

    source_ids = {item["source_id"] for item in context["artifacts"]}
    assert "owasp_asvs" in source_ids
    assert "nist_sp_800_61" not in source_ids


def test_repository_artifact_library_lints_clean():
    library = ArtifactLibrary.from_dir(ARTIFACT_DIR)

    issues = lint_artifact_library(library.artifacts)

    assert issues == []
