"""C3 regression: a stale model id (e.g. 'claude-opus-4-5') 404s and breaks
100% of generations. These tests fail if any generation-path model constant
drifts off the valid catalog."""

import importlib

from backend.llm.models import VALID_MODELS, DEFAULT_MODEL, resolve_model


STALE = "claude-opus-4-5"  # the id this fix removed


def test_default_model_is_valid():
    assert DEFAULT_MODEL in VALID_MODELS
    assert STALE not in VALID_MODELS


def test_routes_model_is_current():
    routes = importlib.import_module("backend.api.routes")
    assert routes.ANTHROPIC_MODEL in VALID_MODELS
    assert routes.ANTHROPIC_MODEL != STALE


def test_trace_agent_model_is_current():
    ta = importlib.import_module("backend.agents.trace_agent")
    assert ta.ANTHROPIC_MODEL in VALID_MODELS
    assert ta.ANTHROPIC_MODEL != STALE


def test_resolve_model_rejects_stale_override(monkeypatch):
    # An operator setting a stale/unknown ANTHROPIC_MODEL must not 404 the app.
    monkeypatch.setenv("ANTHROPIC_MODEL", STALE)
    assert resolve_model() == DEFAULT_MODEL
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4-8")
    assert resolve_model() == "claude-opus-4-8"
