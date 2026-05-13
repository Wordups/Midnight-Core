"""Voyage AI embedding service - voyage-3, 1024-dim."""
from __future__ import annotations

import os
import time
from typing import Iterable

import requests


VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = "voyage-3"
VOYAGE_DIM = 1024
BATCH_SIZE = 128


def _voyage_key() -> str:
    key = os.getenv("VOYAGE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("VOYAGE_API_KEY is not configured")
    return key


def _normalize(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())[:8000]


def embed_chunks(texts: list[str], *, input_type: str = "document") -> list[list[float]]:
    """Return embeddings for each text. Length == len(texts). 1024-dim vectors."""
    if not texts:
        return []
    cleaned = [_normalize(t) or " " for t in texts]
    out: list[list[float]] = []
    key = _voyage_key()
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    for i in range(0, len(cleaned), BATCH_SIZE):
        batch = cleaned[i : i + BATCH_SIZE]
        payload = {"input": batch, "model": VOYAGE_MODEL, "input_type": input_type}
        last_err: Exception | None = None
        succeeded = False
        for attempt in range(5):
            try:
                resp = requests.post(VOYAGE_URL, headers=headers, json=payload, timeout=60)
                if resp.status_code == 429:
                    backoff = 2 ** attempt
                    time.sleep(backoff)
                    last_err = RuntimeError(f"Voyage rate-limited (429); attempt {attempt + 1}")
                    continue
                if resp.status_code >= 400:
                    raise RuntimeError(f"Voyage API {resp.status_code}: {resp.text[:300]}")
                data = resp.json().get("data") or []
                embeds = [item["embedding"] for item in data]
                if len(embeds) != len(batch):
                    raise RuntimeError(f"Voyage returned {len(embeds)} embeddings for {len(batch)} inputs")
                out.extend(embeds)
                succeeded = True
                last_err = None
                break
            except Exception as exc:
                last_err = exc
                time.sleep(2 * (attempt + 1))
        if not succeeded:
            raise last_err or RuntimeError("Voyage embedding failed after retries")
    return out


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0 or nb == 0:
        return 0.0
    import math
    return dot / (math.sqrt(na) * math.sqrt(nb))
