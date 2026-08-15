"""
API key management for the AI connector (remote MCP gateway).

Tenant-scoped, mounted behind verify_access. The full key appears exactly once
— in the mint response — and is never retrievable again.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.core.ratelimit import allow as rate_allow
from backend.integrations.api_keys import list_keys, mint_key, revoke_key

logger = logging.getLogger("midnight.api_keys.api")

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])

MAX_ACTIVE_KEYS = 5


def _tenant_id(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return tenant_id


class MintRequest(BaseModel):
    name: str = Field(default="AI connector", max_length=80)


@router.get("")
def get_keys(request: Request) -> dict:
    return {"keys": list_keys(_tenant_id(request))}


@router.post("")
def create_key(payload: MintRequest, request: Request) -> dict:
    tenant_id = _tenant_id(request)
    if not rate_allow(f"api-key-mint:{tenant_id}", max_hits=10, window_seconds=3600):
        raise HTTPException(status_code=429, detail="Too many keys minted — wait an hour.")
    active = [k for k in list_keys(tenant_id) if not k.get("revoked_at")]
    if len(active) >= MAX_ACTIVE_KEYS:
        raise HTTPException(
            status_code=409,
            detail=f"You already have {MAX_ACTIVE_KEYS} active keys. Revoke one first.",
        )
    try:
        minted = mint_key(tenant_id, payload.name)
    except Exception as exc:
        logger.error("api key mint failed for %s: %s", tenant_id, exc)
        raise HTTPException(status_code=503, detail="Could not create the key — try again.") from exc
    return {**minted, "note": "Copy the key now — it is never shown again."}


@router.delete("/{key_id}")
def delete_key(key_id: str, request: Request) -> dict:
    if not revoke_key(_tenant_id(request), key_id):
        raise HTTPException(status_code=404, detail="Key not found or already revoked.")
    return {"revoked": True, "id": key_id}
