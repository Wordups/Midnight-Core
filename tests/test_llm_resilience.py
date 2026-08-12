"""Wave B H1/H2: the Anthropic client must be built with an explicit timeout
and a retry count, so a single call can't hang ~600s and transient 429/529
overloads are retried across the multi-call generation pipeline."""

from backend.llm import provider


def test_defaults(monkeypatch):
    monkeypatch.delenv("LLM_MAX_RETRIES", raising=False)
    monkeypatch.delenv("LLM_TIMEOUT_SECONDS", raising=False)
    assert provider._llm_max_retries() == 4
    assert provider._llm_timeout() == 120.0


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("LLM_MAX_RETRIES", "7")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "45")
    assert provider._llm_max_retries() == 7
    assert provider._llm_timeout() == 45.0


def test_bad_env_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_MAX_RETRIES", "notanint")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "nope")
    assert provider._llm_max_retries() == 4
    assert provider._llm_timeout() == 120.0


def test_anthropic_client_configured(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("LLM_MAX_RETRIES", "4")
    client = provider.get_client(anthropic_api_key="sk-ant-test")
    assert getattr(client, "max_retries", None) == 4


def test_model_output_failure_logging_survives_reserved_keys():
    """context={'filename': ...} must not crash the logger (LogRecord reserves it).

    Regression: this KeyError inside logging converted a recoverable parse
    failure into a 500 'Extraction error' during live uploads.
    """
    from backend.api.routes import _log_model_output_failure

    _log_model_output_failure(
        flow="migrate_extraction",
        raw_text="not json",
        error=ValueError("bad"),
        context={"filename": "upload.md", "module": "x", "template_name": "generic"},
    )
