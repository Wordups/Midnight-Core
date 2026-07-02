"""
Midnight — Anthropic model catalog.

Single source of truth for model IDs. Stale IDs (e.g. the old "claude-opus-4-5")
are rejected by the API with a hard 404, which breaks 100% of generations — so
every model string in the codebase resolves through here and is validated.

Update VALID_MODELS when the catalog changes.
"""

from __future__ import annotations

import os

# Current Anthropic catalog (Opus 4.6–4.8, Sonnet 4.6, Haiku 4.5, Fable 5).
VALID_MODELS: set[str] = {
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    "claude-fable-5",
}

# Default / creative-narrative tier and the structural tier (used by routing).
DEFAULT_MODEL = "claude-opus-4-8"
STRUCTURAL_MODEL = "claude-haiku-4-5"


def resolve_model(env_var: str = "ANTHROPIC_MODEL", default: str = DEFAULT_MODEL) -> str:
    """Return a valid model id, honoring an env override only if it's valid.
    An unknown/stale override falls back to the default rather than 404-ing."""
    candidate = os.getenv(env_var, default)
    return candidate if candidate in VALID_MODELS else default
