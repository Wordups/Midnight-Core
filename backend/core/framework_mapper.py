"""
Midnight Core — framework_mapper.py
Takeoff LLC

Deterministic control-to-document mapping. Given a document's text and the
frameworks in scope, decide which controls that document plausibly addresses.

This is intentionally NOT an AI call — it is a transparent keyword/term match
against each control's name and description, so the result is explainable and
reproducible. The gap engine consumes the resulting covered_control_ids.

Flow:
    map_document(text, frameworks) -> covered_control_ids
    compute_gaps(...)  (gap_engine) consumes those ids
"""

from __future__ import annotations

import re

from backend.core.gap_engine import CONTROL_REGISTRY, Control


# Words too generic to be evidence that a control is addressed.
_STOPWORDS = {
    "and", "or", "the", "a", "an", "of", "to", "for", "in", "on", "with", "that",
    "this", "are", "is", "be", "as", "by", "from", "at", "it", "its", "so",
    "control", "controls", "policy", "policies", "procedure", "procedures",
    "process", "processes", "management", "security", "information", "system",
    "systems", "data", "support", "maintain", "establish", "implement", "ensure",
    "appropriate", "relevant", "required", "requirements", "service", "services",
}


def _terms(text: str) -> set[str]:
    """Significant lowercase words from a piece of text."""
    words = re.findall(r"[a-z0-9]{4,}", text.lower())
    return {w for w in words if w not in _STOPWORDS}


def _control_signature(ctrl: Control) -> set[str]:
    """The set of significant terms that identify a control."""
    return _terms(f"{ctrl.name} {ctrl.description}")


def map_document(
    text: str,
    frameworks: list[str],
    *,
    min_overlap: int = 2,
) -> list[str]:
    """Return the IDs of controls (within the given frameworks) that the
    document text plausibly addresses.

    A control is considered addressed when the document shares at least
    `min_overlap` significant terms with the control's name+description.
    Controls with fewer than `min_overlap` signature terms match on all of them.

    Args:
        text:       full document text
        frameworks: framework display names in scope (e.g. ["HIPAA", "SOC 2"])
        min_overlap: minimum shared significant terms to count as covered

    Returns:
        sorted list of covered control IDs
    """
    fw_set = {f.strip() for f in frameworks if f and f.strip()}
    doc_terms = _terms(text or "")
    if not doc_terms:
        return []

    covered: list[str] = []
    for ctrl in CONTROL_REGISTRY:
        if fw_set and ctrl.framework not in fw_set:
            continue
        sig = _control_signature(ctrl)
        if not sig:
            continue
        overlap = len(sig & doc_terms)
        threshold = min(min_overlap, len(sig))
        if overlap >= threshold:
            covered.append(ctrl.id)
    return sorted(covered)


def map_document_detail(
    text: str,
    frameworks: list[str],
    *,
    min_overlap: int = 2,
) -> list[dict]:
    """Like map_document, but returns per-control match detail (id, framework,
    name, matched_terms) — useful for explainability in the UI."""
    doc_terms = _terms(text or "")
    fw_set = {f.strip() for f in frameworks if f and f.strip()}
    out: list[dict] = []
    for ctrl in CONTROL_REGISTRY:
        if fw_set and ctrl.framework not in fw_set:
            continue
        sig = _control_signature(ctrl)
        matched = sorted(sig & doc_terms)
        if sig and len(matched) >= min(min_overlap, len(sig)):
            out.append({
                "control_id": ctrl.id,
                "framework": ctrl.framework,
                "name": ctrl.name,
                "matched_terms": matched,
            })
    return out
