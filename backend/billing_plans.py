"""
Midnight — per-plan limits and feature fences.

Single source of truth for what each plan_type allows.

Repriced 2026-08-20 against live market rates. The anchors: Ostendio's entry
contract is $2,994/yr and is the cheapest real GRC platform; Sprinto starts
near $4k with a ~$15k median; Vanta's median lands around $20k and Drata's
average around $34k; Conveyor -- the closest comp to what answer_questions
actually does -- runs $9,600/yr on credits. Self-serve stays the wedge, but a
$490/yr ceiling read as a toy next to that field, and price is a trust signal
in compliance software.

Tiers: free (1 watermarked generation, preview only) / starter $99 (one
framework, 10 documents a month) / pro $349 (everything mapped, full gap
list) / team $999 (10 seats, SME workflow at scale) / enterprise
(contact-only, from ~$25k, no self-serve checkout).

THE VALUE METRIC IS QUESTIONNAIRE RUNS, NOT SEATS. One run answers up to 50
questions against the evidence corpus and costs real model tokens, so every
tier carries a finite monthly cap -- including enterprise, whose number comes
from the contract rather than from this file. An agent driving the MCP
connector is not a seat and will never be billed like one; unlimited runs on
an agent-facing surface is how a plan goes gross-margin negative.

None = unlimited. Numbers and flags are product knobs — adjust here; no other
code changes needed. Legacy rows may still say trial/growth until the
20260716_tier_restructure migration runs; aliases keep them resolving.
"""

from __future__ import annotations

PLAN_LIMITS: dict[str, dict[str, int | bool | None]] = {
    "free": {
        "corpus_runs_per_month": 2,
        "max_uploads": 3,
        "max_frameworks": 1,
        "max_users": 1,
        "max_docs_per_month": None,
        "max_generations_total": 1,
        "docx_export": False,
        "full_gap_list": False,
        "haiku_only": True,
        "watermark": True,
    },
    "starter": {
        "corpus_runs_per_month": 20,
        "max_uploads": 50,
        "max_frameworks": 1,
        "max_users": 1,
        "max_docs_per_month": 10,
        "max_generations_total": None,
        "docx_export": True,
        "full_gap_list": False,
        "haiku_only": False,
        "watermark": False,
    },
    "pro": {
        "corpus_runs_per_month": 100,
        "max_uploads": None,
        "max_frameworks": None,
        "max_users": 3,
        "max_docs_per_month": None,
        "max_generations_total": None,
        "docx_export": True,
        "full_gap_list": True,
        "haiku_only": False,
        "watermark": False,
    },
    "team": {
        "corpus_runs_per_month": 400,
        "max_uploads": None,
        "max_frameworks": None,
        "max_users": 10,
        "max_docs_per_month": None,
        "max_generations_total": None,
        "docx_export": True,
        "full_gap_list": True,
        "haiku_only": False,
        "watermark": False,
    },
    "enterprise": {
        "corpus_runs_per_month": 2000,
        "max_uploads": None,
        "max_frameworks": None,
        "max_users": None,
        "max_docs_per_month": None,
        "max_generations_total": None,
        "docx_export": True,
        "full_gap_list": True,
        "haiku_only": False,
        "watermark": False,
    },
}

# Pre-restructure plan_type values that may linger in tenants rows.
LEGACY_PLAN_ALIASES: dict[str, str] = {
    "trial": "free",
    "growth": "pro",
}

_DEFAULT_KEY = "free"

_FEATURE_FLAGS = ("docx_export", "full_gap_list", "haiku_only", "watermark")


def resolve_plan(plan_type: str | None) -> str:
    """Normalize a stored plan_type to a canonical tier key."""
    key = (plan_type or "").strip().lower()
    key = LEGACY_PLAN_ALIASES.get(key, key)
    return key if key in PLAN_LIMITS else _DEFAULT_KEY


def limits_for(plan_type: str | None) -> dict[str, int | bool | None]:
    """Return the limit dict for a plan_type, defaulting to free for unknown."""
    return PLAN_LIMITS[resolve_plan(plan_type)]


def plan_features(plan_type: str | None) -> dict[str, bool]:
    """Boolean feature flags for the session payload / frontend fences."""
    limits = limits_for(plan_type)
    return {flag: bool(limits[flag]) for flag in _FEATURE_FLAGS}
