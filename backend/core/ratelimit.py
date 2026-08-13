"""Minimal in-memory rate limiter for expensive (LLM) surfaces.

Single-process by design — matches the current deployment shape. When the
architecture grows a worker fleet, replace with a shared store; the call
sites won't change.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)


def allow(key: str, *, max_hits: int, window_seconds: int) -> bool:
    """True if `key` may proceed; False when it exceeded max_hits in window."""
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        q = _hits[key]
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= max_hits:
            return False
        q.append(now)
        return True


def reset() -> None:
    """Test helper."""
    with _lock:
        _hits.clear()
