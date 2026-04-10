"""
Midnight Core - local workspace artifact store.

This is the minimal persistence layer for a single protected personal workspace.
It keeps generated document metadata in a small JSON index and stores binary
artifacts on disk so the dashboard can list and download them.
"""

from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
import json
import uuid
import re


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "workspaces"


def _workspace_dir(workspace_id: str) -> Path:
    root = DATA_DIR / workspace_id
    (root / "artifacts").mkdir(parents=True, exist_ok=True)
    return root


def _index_path(workspace_id: str) -> Path:
    return _workspace_dir(workspace_id) / "documents.json"


def _slugify(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", name.strip()).strip("-")
    return value or "document"


def _read_index(workspace_id: str) -> list[dict]:
    path = _index_path(workspace_id)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _write_index(workspace_id: str, documents: list[dict]) -> None:
    path = _index_path(workspace_id)
    path.write_text(json.dumps(documents, indent=2), encoding="utf-8")


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
) -> dict:
    document_id = uuid.uuid4().hex[:12]
    stored_name = f"{document_id}-{_slugify(filename)}"
    stored_path = _workspace_dir(workspace_id) / "artifacts" / stored_name
    stored_path.write_bytes(file_bytes)

    timestamp = datetime.now(UTC).isoformat()
    record = {
        "id": document_id,
        "name": document_name,
        "filename": filename,
        "doc_type": doc_type.upper(),
        "status": status,
        "preview": preview,
        "content_type": content_type,
        "timestamp": timestamp,
        "source_name": source_name or filename,
        "stored_path": str(stored_path),
    }

    documents = _read_index(workspace_id)
    documents.insert(0, record)
    _write_index(workspace_id, documents)
    return record


def list_generated_documents(workspace_id: str) -> list[dict]:
    return _read_index(workspace_id)


def get_generated_document(workspace_id: str, document_id: str) -> dict | None:
    for record in _read_index(workspace_id):
        if record["id"] == document_id:
            return record
    return None


def list_recent_activity(workspace_id: str, limit: int = 10) -> list[dict]:
    documents = list_generated_documents(workspace_id)[:limit]
    activity = []
    for record in documents:
        activity.append({
            "id": f"act-{record['id']}",
            "timestamp": record["timestamp"],
            "user_name": "You",
            "user_initials": "ME",
            "action": "Generated",
            "target": record["name"],
            "result": "audit-ready" if record["status"] == "ready" else record["status"],
        })
    return activity
