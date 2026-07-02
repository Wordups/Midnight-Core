"""Wave C: generation routes structural sections to the cheaper tier (Haiku)
and creative/narrative sections to the stronger tier (Opus/Fable), both
env-overridable. Before this, every section used one model."""

from backend.llm import models


def test_structural_default_is_haiku(monkeypatch):
    monkeypatch.delenv("STRUCTURAL_MODEL", raising=False)
    assert models.resolve_structural_model() == "claude-haiku-4-5"


def test_creative_default_is_opus(monkeypatch):
    monkeypatch.delenv("CREATIVE_MODEL", raising=False)
    assert models.resolve_creative_model() == "claude-opus-4-8"


def test_creative_can_be_set_to_fable(monkeypatch):
    monkeypatch.setenv("CREATIVE_MODEL", "claude-fable-5")
    assert models.resolve_creative_model() == "claude-fable-5"


def test_creative_invalid_override_falls_back(monkeypatch):
    monkeypatch.setenv("CREATIVE_MODEL", "not-a-model")
    assert models.resolve_creative_model() == models.DEFAULT_MODEL


def test_slot_routing_differs_by_section():
    from backend.api import routes
    assert routes.STRUCTURAL_MODEL != routes.CREATIVE_MODEL
    # creative/narrative slots -> creative tier
    for slot in ("purpose", "scope", "policy_statement", "procedures", "exceptions"):
        assert routes._model_for_slot(slot) == routes.CREATIVE_MODEL
    # structural slots -> structural tier
    for slot in ("definitions", "roles_responsibilities", "review_cycle", "approval"):
        assert routes._model_for_slot(slot) == routes.STRUCTURAL_MODEL
