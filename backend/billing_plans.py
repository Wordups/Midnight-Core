"""
Midnight — per-plan limits and feature fences.

Single source of truth for what each plan_type allows. Tiers follow The Angle
tier split: free (1 watermarked generation, preview only) / starter $29
(one framework, 10 docs a month) / pro $99 (everything mapped, full gap list)
/ enterprise (contact-only, no self-serve checkout).

None = unlimited. Numbers and flags are product knobs — adjust here; no other
code changes needed. Legacy rows may still say trial/growth until the
20260716_tier_restructure migration runs; aliases keep them resolving.
"""

from __future__ import annotations

PLAN_LIMITS: dict[str, dict[str, int | bool | None]] = {
    "free": {
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
    "enterprise": {
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
