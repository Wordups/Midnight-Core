"""
Per-tenant API keys for machine access (the remote MCP gateway).

Format: mk_<urlsafe random>. The full key exists exactly once — in the mint
response. Storage is sha256(key); verification is a hash lookup, which is the
one deliberate cross-tenant read here (the key itself names the tenant).
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import UTC, datetime
from typing import Any

import requests

from backend.bird_eye.db import _rest_url, _service_headers
from backend.bird_eye.db import select as db_select
from backend.bird_eye.db import update as db_update

logger = logging.getLogger("midnight.api_keys")

_TABLE = "api_keys"
_PREFIX_LEN = 11  # "mk_" + 8 chars — enough to recognize, useless to guess


def _hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def mint_key(tenant_id: str, name: str = "AI connector") -> dict[str, Any]:
    """Create a key for a tenant. Returns the FULL key — the only time it
    ever leaves the server."""
    key = "mk_" + secrets.token_urlsafe(36)
    row = {
        "tenant_id": tenant_id,
        "name": (name or "AI connector").strip()[:80] or "AI connector",
        "key_hash": _hash(key),
        "key_prefix": key[:_PREFIX_LEN],
        "created_at": datetime.now(UTC).isoformat(),
    }
    resp = requests.post(_rest_url(_TABLE), headers=_service_headers(),
                         json=[row], timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"api key mint failed {resp.status_code}: {resp.text[:200]}")
    created = (resp.json() or [{}])[0]
    return {"id": created.get("id"), "key": key, "key_prefix": row["key_prefix"],
            "name": row["name"], "created_at": row["created_at"]}


def verify_key(key: str) -> str | None:
    """Full key → tenant_id, or None. Revoked keys never verify. Stamps
    last_used_at best-effort."""
    key = (key or "").strip()
    if not key.startswith("mk_") or len(key) < 20:
        return None
    try:
        resp = requests.get(
            _rest_url(_TABLE), headers=_service_headers(),
            params={"select": "id,tenant_id,revoked_at",
                    "key_hash": f"eq.{_hash(key)}"},
            timeout=30,
        )
        if resp.status_code >= 400:
            return None
        rows = resp.json() or []
    except Exception as exc:
        logger.warning("api key verify failed: %s", exc)
        return None
    if not rows or rows[0].get("revoked_at"):
        return None
    tenant_id = rows[0]["tenant_id"]
    try:
        db_update(_TABLE, tenant_id=tenant_id,
                  filters={"id": f"eq.{rows[0]['id']}"},
                  patch={"last_used_at": datetime.now(UTC).isoformat()})
    except Exception:
        pass
    return tenant_id


def list_keys(tenant_id: str) -> list[dict[str, Any]]:
    """Keys for the settings UI — prefix and metadata only, never hashes."""
    rows = db_select(_TABLE, tenant_id=tenant_id,
                     columns="id,name,key_prefix,created_at,last_used_at,revoked_at",
                     order="created_at.desc", limit=50)
    return rows


def revoke_key(tenant_id: str, key_id: str) -> bool:
    """Revoke one of the tenant's own keys. Tenant-scoped — a key id from
    another tenant matches nothing."""
    updated = db_update(_TABLE, tenant_id=tenant_id,
                        filters={"id": f"eq.{key_id}", "revoked_at": "is.null"},
                        patch={"revoked_at": datetime.now(UTC).isoformat()})
    return bool(updated)
