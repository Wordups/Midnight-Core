"""Supabase REST helper for Bird Eye.

Table mapping (Supabase Edition):
- documents_index   -> policies
- document_chunks   -> policy_sections
- bird_eye_runs     -> policy_runs
- bird_eye_findings -> policy_gaps
"""
from __future__ import annotations

from typing import Any, Iterable
import json

import requests

from config import settings


TABLE_DOCUMENTS = "policies"
TABLE_CHUNKS = "policy_sections"
TABLE_RUNS = "policy_runs"
TABLE_FINDINGS = "policy_gaps"
STORAGE_BUCKET = "midnight-documents"


def _service_headers(*, json_body: bool = True, prefer: str = "return=representation") -> dict[str, str]:
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Prefer": prefer,
    }
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def _rest_url(path: str) -> str:
    return f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/{path.lstrip('/')}"


def select(
    table: str,
    *,
    tenant_id: str,
    columns: str = "*",
    filters: dict[str, str] | None = None,
    limit: int | None = None,
    order: str | None = None,
) -> list[dict[str, Any]]:
    """SELECT with mandatory tenant_id filter."""
    if not tenant_id:
        raise ValueError("tenant_id required for select()")
    params: dict[str, str] = {"select": columns, "tenant_id": f"eq.{tenant_id}"}
    if filters:
        for k, v in filters.items():
            params[k] = v
    if limit:
        params["limit"] = str(limit)
    if order:
        params["order"] = order
    resp = requests.get(_rest_url(table), headers=_service_headers(), params=params, timeout=60)
    if resp.status_code >= 400:
        raise RuntimeError(f"select({table}) failed {resp.status_code}: {resp.text}")
    return resp.json() or []


def insert(table: str, payload: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """INSERT and return inserted rows."""
    rows = payload if isinstance(payload, list) else [payload]
    for r in rows:
        if "tenant_id" not in r or not r["tenant_id"]:
            raise ValueError(f"tenant_id missing from insert into {table}")
    resp = requests.post(
        _rest_url(table),
        headers=_service_headers(),
        data=json.dumps(rows),
        timeout=60,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"insert({table}) failed {resp.status_code}: {resp.text}")
    if not resp.content:
        return []
    return resp.json() or []


def update(table: str, *, tenant_id: str, filters: dict[str, str], patch: dict[str, Any]) -> list[dict[str, Any]]:
    if not tenant_id:
        raise ValueError("tenant_id required for update()")
    params: dict[str, str] = {"tenant_id": f"eq.{tenant_id}"}
    for k, v in filters.items():
        params[k] = v
    resp = requests.patch(
        _rest_url(table),
        headers=_service_headers(),
        params=params,
        data=json.dumps(patch),
        timeout=60,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"update({table}) failed {resp.status_code}: {resp.text}")
    if not resp.content:
        return []
    return resp.json() or []


def delete(table: str, *, tenant_id: str, filters: dict[str, str]) -> None:
    if not tenant_id:
        raise ValueError("tenant_id required for delete()")
    params: dict[str, str] = {"tenant_id": f"eq.{tenant_id}"}
    for k, v in filters.items():
        params[k] = v
    resp = requests.delete(
        _rest_url(table),
        headers=_service_headers(prefer="return=minimal"),
        params=params,
        timeout=60,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"delete({table}) failed {resp.status_code}: {resp.text}")


def rpc(name: str, body: dict[str, Any]) -> Any:
    resp = requests.post(
        _rest_url(f"rpc/{name}"),
        headers=_service_headers(),
        data=json.dumps(body),
        timeout=120,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"rpc({name}) failed {resp.status_code}: {resp.text}")
    if not resp.content:
        return None
    return resp.json()


def storage_upload(tenant_id: str, document_id: str, filename: str, content: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload to Supabase Storage at tenants/{tenant_id}/uploads/{document_id}/{filename}."""
    if not tenant_id:
        raise ValueError("tenant_id required for storage_upload()")
    path = f"tenants/{tenant_id}/uploads/{document_id}/{filename}"
    url = f"{settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{STORAGE_BUCKET}/{path}"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }
    resp = requests.post(url, headers=headers, data=content, timeout=120)
    if resp.status_code >= 400:
        # 409 means it exists - try PUT update
        if resp.status_code == 409 or resp.status_code == 400:
            resp = requests.put(url, headers=headers, data=content, timeout=120)
        if resp.status_code >= 400:
            raise RuntimeError(f"storage upload failed {resp.status_code}: {resp.text}")
    return path
