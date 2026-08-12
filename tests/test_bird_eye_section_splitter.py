"""Regression tests for Bird Eye document section splitting."""

from backend.bird_eye.ingestion import split_sections


def test_split_sections_accepts_numbered_all_caps_policy_headings():
    raw = """1. PURPOSE
This playbook defines SOC operations.

2. SCOPE
This applies to all SOC analysts.

3. INCIDENT LIFECYCLE
Detection, triage, containment, recovery.
"""

    sections = split_sections(raw)

    assert [s["heading"] for s in sections] == [
        "Purpose",
        "Scope",
        "Incident Lifecycle",
    ]
    assert sections[0]["content"] == "This playbook defines SOC operations."


def test_split_sections_accepts_decimal_numbered_headings():
    raw = """4.1 Authentication Requirements
Passwords must be at least 14 characters.

4.2 Password Requirements
MFA is required for privileged access.
"""

    sections = split_sections(raw)

    assert [s["heading"] for s in sections] == [
        "Authentication Requirements",
        "Password Requirements",
    ]


def test_split_sections_preserves_table_headers_inside_numbered_section():
    raw = """3. ROLES AND RESPONSIBILITIES

ROLE
RESPONSIBILITIES
Tier 1 — Triage Analyst
Review alerts, validate automation, close false positives.

4. INCIDENT LIFECYCLE
All incidents follow five phases.
"""

    sections = split_sections(raw)

    assert [s["heading"] for s in sections] == [
        "Roles And Responsibilities",
        "Incident Lifecycle",
    ]
    assert "ROLE" in sections[0]["content"]
    assert "RESPONSIBILITIES" in sections[0]["content"]
    assert "Tier 1" in sections[0]["content"]


def test_split_sections_accepts_known_grc_headings_without_numbering():
    raw = """PURPOSE
This policy defines expected behavior.

SCOPE
This applies to employees and contractors.

REVIEW CADENCE
This policy is reviewed annually.
"""

    sections = split_sections(raw)

    assert [s["heading"] for s in sections] == [
        "Purpose",
        "Scope",
        "Review Cadence",
    ]


def test_split_sections_chunks_long_unheaded_documents_instead_of_single_blob():
    paragraph = "This is operational content with enough detail to matter for analysis. " * 12
    raw = "\n\n".join(paragraph + str(i) for i in range(12))

    sections = split_sections(raw)

    assert len(sections) > 1
    assert all(s["heading"].startswith("Document Part ") for s in sections)
    assert all(s["content"].strip() for s in sections)
