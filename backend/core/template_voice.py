"""
Midnight Core — template_voice.py

The template library ships four variants per document category (formal, modern,
detailed, executive). Each variant is a distinct WRITING REGISTER, not just a
different shell: the library defines a voice and a target length for each
(source: midnight-template-build/manifest.json, word_count + description fields).

The generation path was variant-blind — it produced the same prose regardless of
which variant the user picked, then rendered it into a style-identical shell, so
"formal" and "executive" came out identical. This module carries the variant's
voice and length budget into the per-section generation prompt so the four
variants actually diverge: formal reads like legalese, executive reads like a
one-page board brief.

Profiles are transcribed verbatim from the library manifest (the descriptions
are the user's own words; target_words is the mean word count across the nine
categories for that variant).
"""
from __future__ import annotations

VARIANTS = ("formal", "modern", "detailed", "executive")
DEFAULT_VARIANT = "modern"

# variant -> library description (verbatim) + mean word count + a concise
# generation directive derived from that description.
VARIANT_PROFILES: dict[str, dict] = {
    "formal": {
        "title": "Formal",
        "description": (
            "Legalese voice, full structure, traditional enterprise. "
            "The template a Fortune 500 General Counsel would approve."
        ),
        "target_words": 1200,
        "directive": (
            "Write in a formal legal register: complete sentences, defined terms, "
            "explicit 'shall' / 'must' obligations, and traditional enterprise "
            "structure. Precise and authoritative — the wording a Fortune 500 "
            "General Counsel would approve. No bullet fragments where a full "
            "clause belongs."
        ),
    },
    "modern": {
        "title": "Modern",
        "description": (
            "Scannable, plain-language, modern enterprise. Short paragraphs, "
            "clear headings, designed for readability."
        ),
        "target_words": 725,
        "directive": (
            "Write in plain, modern language: short paragraphs, active voice, and "
            "scannable structure. Prefer clear bullet lists over dense prose. A "
            "non-lawyer should understand it on first read."
        ),
    },
    "detailed": {
        "title": "Detailed",
        "description": (
            "Comprehensive, long-form, every consideration covered. "
            "The template a regulated startup would use to over-prepare."
        ),
        "target_words": 2000,
        "directive": (
            "Write comprehensively and long-form: cover every consideration, "
            "edge case, and exception, with sub-clauses and explicit rationale. "
            "Err toward over-preparation — the depth a regulated startup would "
            "bring to an audit."
        ),
    },
    "executive": {
        "title": "Executive",
        "description": (
            "One-page brief style, decision-maker focused, high-density. "
            "Shows up in board packs."
        ),
        "target_words": 500,
        "directive": (
            "Write as a tight executive brief: high-density, decision-maker "
            "focused, lead with the point. One-page discipline — cut anything a "
            "board member would skip. Prefer one crisp sentence over three."
        ),
    },
}


def normalize_variant(variant: str | None) -> str:
    v = str(variant or "").strip().lower()
    return v if v in VARIANT_PROFILES else DEFAULT_VARIANT


def profile_for(variant: str | None) -> dict:
    return VARIANT_PROFILES[normalize_variant(variant)]


def section_word_budget(variant: str | None, *, num_slots: int) -> int:
    """Per-section word target = the variant's whole-document budget spread over
    its sections, floored so a section never collapses to nothing."""
    profile = profile_for(variant)
    slots = max(int(num_slots or 1), 1)
    return max(profile["target_words"] // slots, 40)


def section_voice_block(variant: str | None, *, num_slots: int) -> str:
    """The directive lines injected into each per-section generation prompt so
    the section is written in the selected variant's register and length."""
    profile = profile_for(variant)
    budget = section_word_budget(variant, num_slots=num_slots)
    return (
        f"Template Variant: {profile['title']} — {profile['description']}\n"
        f"Voice & Style: {profile['directive']}\n"
        f"Target Length: about {budget} words for this section "
        f"(the {profile['title']} variant targets ~{profile['target_words']} "
        f"words for the whole document)."
    )
