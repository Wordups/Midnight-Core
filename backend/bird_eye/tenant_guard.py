"""Tenant scope guard - every Bird Eye call must pass a valid tenant_id."""
from __future__ import annotations

import uuid
from functools import wraps

from fastapi import HTTPException


def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False


def require_tenant(tenant_id: str) -> str:
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id required")
    if not is_valid_uuid(tenant_id):
        raise HTTPException(status_code=400, detail="invalid tenant_id")
    return str(tenant_id)


def tenant_scoped(fn):
    @wraps(fn)
    async def awrapper(tenant_id: str, *args, **kwargs):
        require_tenant(tenant_id)
        return await fn(tenant_id, *args, **kwargs)

    @wraps(fn)
    def swrapper(tenant_id: str, *args, **kwargs):
        require_tenant(tenant_id)
        return fn(tenant_id, *args, **kwargs)

    import asyncio
    if asyncio.iscoroutinefunction(fn):
        return awrapper
    return swrapper
