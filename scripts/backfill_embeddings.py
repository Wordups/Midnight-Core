"""Backfill missing embeddings for TKO-* corpus chunks."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env", override=True)

from datetime import datetime, timezone

from backend.bird_eye.db import TABLE_CHUNKS, TABLE_DOCUMENTS, select as db_select, update as db_update
from backend.bird_eye.embeddings import embed_chunks

TENANT_ID = os.environ["TEST_TENANT_ID"]


def main() -> None:
    docs = db_select(TABLE_DOCUMENTS, tenant_id=TENANT_ID, columns="id,policy_number", filters={"policy_number": "like.TKO-*"})
    for d in docs:
        chunks = db_select(
            TABLE_CHUNKS,
            tenant_id=TENANT_ID,
            columns="id,heading,content,embedding",
            filters={"policy_id": f"eq.{d['id']}"},
        )
        missing = [c for c in chunks if c.get("embedding") in (None, "", "[]")]
        if not missing:
            print(f"  {d['policy_number']}: complete")
            continue
        print(f"  {d['policy_number']}: backfilling {len(missing)} chunks")
        texts = [f"{c.get('heading') or ''}\n{c.get('content') or ''}" for c in missing]
        # Voyage free tier rate limit is low; throttle generously
        for attempt in range(8):
            try:
                vectors = embed_chunks(texts)
                break
            except RuntimeError as exc:
                if "rate-limited" in str(exc) or "429" in str(exc):
                    wait = 30 + 10 * attempt
                    print(f"    voyage 429; sleeping {wait}s")
                    time.sleep(wait)
                else:
                    raise
        else:
            raise RuntimeError(f"voyage exhausted retries for {d['policy_number']}")
        now = datetime.now(timezone.utc).isoformat()
        for c, v in zip(missing, vectors):
            db_update(
                TABLE_CHUNKS,
                tenant_id=TENANT_ID,
                filters={"id": f"eq.{c['id']}"},
                patch={"embedding": v, "embedded_at": now},
            )
        time.sleep(20)  # space out per-doc to stay under RPM


if __name__ == "__main__":
    main()
