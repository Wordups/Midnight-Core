"""
Midnight — per-plan limits.

Single source of truth for what each plan_type allows, so enforcement scales by
tier instead of the old binary trial / not-trial check (which handed a Starter
customer the same unlimited access as Enterprise). None = unlimited.

Tier names match the existing billing tiers (trial + the Stripe tiers). Numbers
are product knobs — adjust here; no other code changes needed.
"""

from __future__ import annotations

PLAN_LIMITS: dict[str, dict[str, int | None]] = {
    "trial":      {"max_uploads": 3,    "max_frameworks": 1,    "max_users": 3},
    "starter":    {"max_uploads": 50,   "max_frameworks": 3,    "max_users": 5},
    "growth":     {"max_uploads": 250,  "max_frameworks": 6,    "max_users": 20},
    "enterprise": {"max_uploads": None, "max_frameworks": None, "max_users": None},
}

_DEFAULT_KEY = "trial"


def limits_for(plan_type: str | None) -> dict[str, int | None]:
    """Return the limit dict for a plan_type, defaulting to trial for unknown."""
    return PLAN_LIMITS.get((plan_type or "").strip().lower(), PLAN_LIMITS[_DEFAULT_KEY])
