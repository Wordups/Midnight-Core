"""
Midnight — LLM provider layer.

Claude (Anthropic) is the DEFAULT and the recommended production engine for
audit-facing output. Ollama is an optional, env-switchable backend for local
development and cost-free testing — it runs entirely on the developer's machine
(no data leaves the box), but a small local model is not audit-grade, so it is
opt-in only and never the default.

    LLM_PROVIDER = "anthropic" (default) | "ollama"
    OLLAMA_URL   = "http://localhost:11434"
    OLLAMA_MODEL = "qwen2.5-coder:7b"

The Ollama adapter mimics the subset of the Anthropic client used across the
codebase — ``client.messages.create(model=, max_tokens=, system=, messages=[...])``
returning an object with ``.content[0].text`` and ``.stop_reason`` — so every
existing call site works unchanged.
"""
from __future__ import annotations

import logging
import os
from types import SimpleNamespace

import httpx

logger = logging.getLogger("midnight.llm")


def provider() -> str:
    return os.getenv("LLM_PROVIDER", "anthropic").strip().lower()


def _ollama_url() -> str:
    return os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")


def _ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")


class _OllamaMessages:
    """Anthropic-shaped ``.messages.create`` backed by Ollama /api/chat."""

    def create(self, *, model=None, max_tokens: int = 1024, system=None, messages=None, **kwargs):
        chat: list[dict] = []
        if system:
            chat.append({"role": "system", "content": system})
        for m in (messages or []):
            content = m.get("content")
            if isinstance(content, list):  # Anthropic block form -> flatten to text
                content = "".join(b.get("text", "") for b in content if isinstance(b, dict))
            chat.append({"role": m.get("role", "user"), "content": content or ""})

        options = {"num_predict": max_tokens}
        if kwargs.get("temperature") is not None:
            options["temperature"] = kwargs["temperature"]

        payload = {"model": _ollama_model(), "messages": chat, "stream": False, "options": options}
        resp = httpx.post(f"{_ollama_url()}/api/chat", json=payload,
                          timeout=httpx.Timeout(600.0, connect=5.0))
        resp.raise_for_status()
        data = resp.json()

        text = (data.get("message") or {}).get("content", "")
        stop_reason = "max_tokens" if data.get("done_reason") == "length" else "end_turn"
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=text)],
            stop_reason=stop_reason,
            model=_ollama_model(),
            role="assistant",
            usage=SimpleNamespace(
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
            ),
        )


class OllamaClient:
    def __init__(self):
        self.messages = _OllamaMessages()


def get_client(*, anthropic_api_key: str | None = None):
    """Return an LLM client exposing the Anthropic ``.messages.create`` shape.

    Anthropic by default; Ollama when ``LLM_PROVIDER=ollama``. Raises
    RuntimeError if the selected provider isn't usable.
    """
    if provider() == "ollama":
        logger.info("llm_provider_ollama model=%s url=%s", _ollama_model(), _ollama_url())
        return OllamaClient()

    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Anthropic dependency is not installed on the server.") from exc
    if not anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured.")
    return anthropic.Anthropic(api_key=anthropic_api_key)
