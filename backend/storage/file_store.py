"""
Midnight Core - Supabase-backed tenant artifact store.

This module preserves the old helper names so the rest of the application can
keep its current shape while persistence moves to Supabase Postgres + Storage.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable
import json
import mimetypes
import os
import re

import requests


SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
STORAGE_BUCKET = "midnight-documents"
SIGNED_URL_TTL_SECONDS = 60 * 60
_bucket_initialized = False


class SupabaseStoreError(RuntimeError):
    """Raised when Supabase persistence operations fail."""


def _require_supabase() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise SupabaseStoreError("Supabase storage is not configured.")


def _json_headers(*, prefer: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _binary_headers(content_type: str, *, upsert: bool = False) -> dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": content_type,
        "x-upsert": "true" if upsert else "false",
    }


def _request(method: str, path: str, *, headers: dict[str, str], **kwargs) -> requests.Response:
    _require_supabase()
    response = requests.request(method, f"{SUPABASE_URL}{path}", headers=headers, timeout=60, **kwargs)
    if response.status_code >= 400:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise SupabaseStoreError(f"Supabase request failed ({response.status_code}): {detail}")
    return response


def _postgrest(
    method: str,
    table_path: str,
    *,
    params: dict[str, Any] | None = None,
    payload: Any | None = None,
    prefer: str | None = None,
) -> Any:
    response = _request(
        method,
        f"/rest/v1/{table_path}",
        headers=_json_headers(prefer=prefer),
        params=params,
        json=payload,
    )
    if not response.content:
        return None
    return response.json()


def _ensure_storage_bucket() -> None:
    global _bucket_initialized
    if _bucket_initialized:
        return

    buckets = _request("GET", "/storage/v1/bucket", headers=_json_headers()).json()
    if not any(bucket.get("name") == STORAGE_BUCKET for bucket in buckets):
        _request(
            "POST",
            "/storage/v1/bucket",
            headers=_json_headers(),
            json={"id": STORAGE_BUCKET, "name": STORAGE_BUCKET, "public": False},
        )
    _bucket_initialized = True


def _slugify(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", name.strip()).strip("-")
    return value or "document"


def _guess_content_type(filename: str, fallback: str = "application/octet-stream") -> str:
    return mimetypes.guess_type(filename or "")[0] or fallback


def _build_signed_storage_url(storage_path: str, *, ttl_seconds: int = SIGNED_URL_TTL_SECONDS) -> str:
    payload = {"expiresIn": ttl_seconds}
    response = _request(
        "POST",
        f"/storage/v1/object/sign/{STORAGE_BUCKET}/{storage_path}",
        headers=_json_headers(),
        json=payload,
    ).json()
    signed_url = response.get("signedURL") or response.get("signedUrl")
    if not signed_url:
        raise SupabaseStoreError("Supabase did not return a signed storage URL.")
    if signed_url.startswith("http://") or signed_url.startswith("https://"):
        return signed_url
    return f"{SUPABASE_URL}/storage/v1{signed_url}"


def _upload_storage_object(*, storage_path: str, file_bytes: bytes, content_type: str) -> None:
    _ensure_storage_bucket()
    _request(
        "POST",
        f"/storage/v1/object/{STORAGE_BUCKET}/{storage_path}",
        headers=_binary_headers(content_type, upsert=True),
        data=file_bytes,
    )


def _download_storage_object(signed_url: str) -> bytes:
    response = requests.get(signed_url, timeout=60)
    if response.status_code >= 400:
        raise SupabaseStoreError(f"Supabase storage download failed ({response.status_code}).")
    return response.content


def _first_row(data: Any) -> dict[str, Any] | None:
    if isinstance(data, list):
        return data[0] if data else None
    return data if isinstance(data, dict) else None


def _select_by_ids(table: str, ids: Iterable[str], columns: str) -> dict[str, dict]:
    ids = [str(item) for item in ids if item]
    if not ids:
        return {}
    result = _postgrest(
        "GET",
        table,
        params={
            "select": columns,
            "id": f"in.({','.join(ids)})",
        },
    )
    return {row["id"]: row for row in result or [] if isinstance(row, dict) and row.get("id")}


def _insert_policy(
    *,
    tenant_id: str,
    name: str,
    status: str,
    policy_number: str | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    created = _postgrest(
        "POST",
        "policies",
        payload={
            "tenant_id": tenant_id,
            "policy_name": name,
            "policy_number": policy_number,
            "version": version,
            "status": status,
        },
        prefer="return=representation",
    )
    record = _first_row(created)
    if not record:
        raise SupabaseStoreError("Supabase did not return a policy record.")
    return record


def _insert_document_row(payload: dict[str, Any]) -> dict[str, Any]:
    created = _postgrest("POST", "documents", payload=payload, prefer="return=representation")
    record = _first_row(created)
    if not record:
        raise SupabaseStoreError("Supabase did not return a document record.")
    return record


def _insert_activity_log(*, tenant_id: str, action: str, policy_id: str | None = None) -> None:
    _postgrest(
        "POST",
        "activity_log",
        payload={
            "tenant_id": tenant_id,
            "policy_id": policy_id,
            "action": action,
        },
        prefer="return=minimal",
    )


def _normalize_document_record(document_row: dict[str, Any], policy_row: dict[str, Any] | None = None) -> dict:
    filename = document_row.get("file_name") or "document"
    name = (policy_row or {}).get("policy_name") or Path(filename).stem or "Untitled"
    doc_type = document_row.get("file_type") or Path(filename).suffix.lstrip(".").upper() or "DOC"
    status = (policy_row or {}).get("status") or "ready"
    timestamp = document_row.get("created_at") or datetime.now(UTC).isoformat()
    storage_path = document_row.get("file_path") or ""
    preview = f"{name} is stored in Midnight and ready for retrieval."

    return {
        "id": document_row["id"],
        "name": name,
        "filename": filename,
        "doc_type": doc_type,
        "status": status,
        "preview": preview,
        "content_type": _guess_content_type(filename),
        "timestamp": timestamp,
        "source_name": name,
        "stored_path": storage_path,
        "storage_url": _build_signed_storage_url(storage_path) if storage_path else document_row.get("storage_url"),
        "policy_id": document_row.get("policy_id"),
        "tenant_id": document_row.get("tenant_id"),
    }


def save_generated_document(
    *,
    workspace_id: str,
    filename: str,
    document_name: str,
    doc_type: str,
    preview: str,
    content_type: str,
    file_bytes: bytes,
    source_name: str | None = None,
    status: str = "ready",
    policy_number: str | None = None,
    version: str | None = None,
    policy_id: str | None = None,
) -> dict:
    tenant_id = workspace_id
    policy = None
    if policy_id:
        policies = _select_by_ids("policies", [policy_id], "id, tenant_id, policy_name, policy_number, version, status")
        policy = policies.get(policy_id)
    if policy is None:
        policy = _insert_policy(
            tenant_id=tenant_id,
            name=document_name,
            status=status,
            policy_number=policy_number,
            version=version,
        )
        policy_id = policy["id"]

    document_id = os.urandom(6).hex()
    stored_name = f"{document_id}-{_slugify(filename)}"
    storage_path = f"{tenant_id}/{policy_id}/{stored_name}"
    _upload_storage_object(storage_path=storage_path, file_bytes=file_bytes, content_type=content_type)
    signed_url = _build_signed_storage_url(storage_path)

    document_row = _insert_document_row(
        {
            "tenant_id": tenant_id,
            "policy_id": policy_id,
            "file_path": storage_path,
            "file_type": doc_type.upper(),
            "file_name": filename,
            "storage_url": signed_url,
        }
    )
    _insert_activity_log(tenant_id=tenant_id, action="generated", policy_id=policy_id)

    record = _normalize_document_record(document_row, policy)
    record["preview"] = preview
    record["source_name"] = source_name or filename
    record["content_type"] = content_type
    return record


def list_generated_documents(workspace_id: str) -> list[dict]:
    tenant_id = workspace_id
    rows = _postgrest(
        "GET",
        "documents",
        params={
            "select": "id,tenant_id,policy_id,file_path,file_type,file_name,storage_url,created_at",
            "tenant_id": f"eq.{tenant_id}",
            "order": "created_at.desc",
        },
    ) or []
    policy_map = _select_by_ids(
        "policies",
        [row.get("policy_id") for row in rows],
        "id, tenant_id, policy_name, policy_number, version, status",
    )
    return [_normalize_document_record(row, policy_map.get(row.get("policy_id"))) for row in rows]


def get_generated_document(workspace_id: str, document_id: str) -> dict | None:
    tenant_id = workspace_id
    rows = _postgrest(
        "GET",
        "documents",
        params={
            "select": "id,tenant_id,policy_id,file_path,file_type,file_name,storage_url,created_at",
            "tenant_id": f"eq.{tenant_id}",
            "id": f"eq.{document_id}",
            "limit": "1",
        },
    ) or []
    document_row = _first_row(rows)
    if not document_row:
        return None

    policy = None
    if document_row.get("policy_id"):
        policy = _select_by_ids(
            "policies",
            [document_row["policy_id"]],
            "id, tenant_id, policy_name, policy_number, version, status",
        ).get(document_row["policy_id"])
    return _normalize_document_record(document_row, policy)


def download_generated_document(workspace_id: str, document_id: str) -> tuple[dict, bytes]:
    record = get_generated_document(workspace_id, document_id)
    if record is None:
        raise SupabaseStoreError("Document not found.")
    if not record.get("storage_url"):
        raise SupabaseStoreError("Document is missing a signed storage URL.")
    return record, _download_storage_object(record["storage_url"])


def list_recent_activity(workspace_id: str, limit: int = 10) -> list[dict]:
    tenant_id = workspace_id
    rows = _postgrest(
        "GET",
        "activity_log",
        params={
            "select": "id,action,policy_id,created_at,tenant_id",
            "tenant_id": f"eq.{tenant_id}",
            "order": "created_at.desc",
            "limit": str(limit),
        },
    ) or []
    policy_map = _select_by_ids("policies", [row.get("policy_id") for row in rows], "id, policy_name, status")

    activity = []
    for row in rows:
        policy = policy_map.get(row.get("policy_id")) or {}
        action = row.get("action", "activity")
        activity.append(
            {
                "id": row.get("id", f"act-{os.urandom(4).hex()}"),
                "timestamp": row.get("created_at") or datetime.now(UTC).isoformat(),
                "user_name": "You",
                "user_initials": "ME",
                "action": str(action).replace("_", " ").title(),
                "target": policy.get("policy_name") or "Workspace item",
                "result": policy.get("status") or "ready",
            }
        )
    return activity


def count_documents_for_tenant(tenant_id: str) -> int:
    response = _request(
        "GET",
        "/rest/v1/documents",
        headers=_json_headers(),
        params={"tenant_id": f"eq.{tenant_id}", "select": "id"},
    )
    data = response.json()
    return len(data or [])


def count_activity_for_tenant(tenant_id: str, *, action: str | None = None) -> int:
    params = {"tenant_id": f"eq.{tenant_id}", "select": "id"}
    if action:
        params["action"] = f"eq.{action}"
    response = _request("GET", "/rest/v1/activity_log", headers=_json_headers(), params=params)
    data = response.json()
    return len(data or [])


def create_activity_event(*, tenant_id: str, action: str, policy_id: str | None = None) -> None:
    _insert_activity_log(tenant_id=tenant_id, action=action, policy_id=policy_id)


def get_tenant(tenant_id: str) -> dict[str, Any] | None:
    rows = _postgrest(
        "GET",
        "tenants",
        params={
            "select": "id,slug,name,industry,plan_type,region,employee_count,created_at",
            "id": f"eq.{tenant_id}",
            "limit": "1",
        },
    ) or []
    return _first_row(rows)


def get_tenant_by_slug(slug: str) -> dict[str, Any] | None:
    rows = _postgrest(
        "GET",
        "tenants",
        params={
            "select": "id,slug,name,industry,plan_type,region,employee_count,created_at",
            "slug": f"eq.{slug}",
            "limit": "1",
        },
    ) or []
    return _first_row(rows)


def create_tenant(*, name: str, slug: str, industry: str | None, region: str | None, employee_count: str | None, plan_type: str = "trial") -> dict[str, Any]:
    created = _postgrest(
        "POST",
        "tenants",
        payload={
            "name": name,
            "slug": slug,
            "industry": industry,
            "region": region,
            "employee_count": employee_count,
            "plan_type": plan_type,
        },
        prefer="return=representation",
    )
    record = _first_row(created)
    if not record:
        raise SupabaseStoreError("Tenant record was not created.")
    return record


def update_profile_membership(*, user_id: str, tenant_id: str, organization_name: str | None = None) -> dict[str, Any]:
    updated = _postgrest(
        "PATCH",
        "profiles",
        params={"id": f"eq.{user_id}"},
        payload={
            "tenant_id": tenant_id,
            **({"organization_name": organization_name} if organization_name else {}),
        },
        prefer="return=representation",
    )
    record = _first_row(updated)
    if not record:
        raise SupabaseStoreError("Profile update did not return a row.")
    return record


def create_onboarding_session(*, tenant_id: str) -> dict[str, Any]:
    created = _postgrest(
        "POST",
        "onboarding_sessions",
        payload={"tenant_id": tenant_id},
        prefer="return=representation",
    )
    record = _first_row(created)
    if not record:
        raise SupabaseStoreError("Onboarding session was not created.")
    return record


def get_onboarding_session(tenant_id: str) -> dict[str, Any] | None:
    rows = _postgrest(
        "GET",
        "onboarding_sessions",
        params={
            "select": "id,tenant_id,current_step,progress,build_method,primary_objective,frameworks,enabled_modules,completed,created_at",
            "tenant_id": f"eq.{tenant_id}",
            "order": "created_at.desc",
            "limit": "1",
        },
    ) or []
    return _first_row(rows)


def update_onboarding_session(tenant_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    session = get_onboarding_session(tenant_id)
    if session is None:
        session = create_onboarding_session(tenant_id=tenant_id)

    updated = _postgrest(
        "PATCH",
        "onboarding_sessions",
        params={"id": f"eq.{session['id']}"},
        payload=updates,
        prefer="return=representation",
    )
    record = _first_row(updated)
    if not record:
        raise SupabaseStoreError("Onboarding session update did not return a row.")
    return record


def replace_enabled_modules(tenant_id: str, module_keys: list[str]) -> list[dict[str, Any]]:
    existing = _postgrest(
        "GET",
        "enabled_modules",
        params={"tenant_id": f"eq.{tenant_id}", "select": "id,module_key"},
    ) or []
    if existing:
        _postgrest("DELETE", "enabled_modules", params={"tenant_id": f"eq.{tenant_id}"}, prefer="return=minimal")

    if not module_keys:
        return []

    created = _postgrest(
        "POST",
        "enabled_modules",
        payload=[{"tenant_id": tenant_id, "module_key": key, "enabled": True} for key in module_keys],
        prefer="return=representation",
    )
    return created or []
