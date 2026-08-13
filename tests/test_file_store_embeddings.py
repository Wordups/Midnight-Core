"""Studio-generated document sections must carry embeddings so the corpus
answer engine's retrieval can find them.

Queue item: "Embed generated documents' sections" — only Bird Eye uploads
got embeddings before this change; Studio-generated documents were invisible
to `backend.core.corpus.load_corpus_sections` (which filters on
`embedding IS NOT NULL`). `save_policy_draft(..., embed=True)` now embeds
saved sections with `backend.bird_eye.embeddings.embed_chunks`
(`input_type="document"`) the same way `backend/bird_eye/ingestion.py` does,
soft-failing on embedding errors so the document is still saved.
"""
import os
import types
import unittest
from unittest.mock import patch

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role")
os.environ.setdefault("ENVIRONMENT", "dev")

from fastapi.testclient import TestClient  # noqa: E402

from backend.api import routes  # noqa: E402
from backend.api.main import app, verify_access  # noqa: E402
from backend.core import corpus  # noqa: E402
from backend.storage import file_store  # noqa: E402


def _fake_postgrest(method, table_path, *, params=None, payload=None, prefer=None):
    """Stand in for Supabase PostgREST: echoes rows back like
    `return=representation` would, without any network I/O."""
    if table_path == "policies" and method == "POST":
        return [{**payload, "id": "pol-1"}]
    if table_path == "policies" and method == "PATCH":
        return [{"id": "pol-1", **payload}]
    if table_path == "policy_sections" and method == "POST":
        return payload
    if table_path == "policy_sections" and method == "DELETE":
        return None
    raise AssertionError(f"unexpected _postgrest call: {method} {table_path}")


def _draft_sections():
    return [
        {"slot_id": "purpose", "heading": "Purpose", "content": "Defines MFA requirements for privileged access."},
        {"slot_id": "scope", "heading": "Scope", "content": "Applies to all production systems."},
    ]


def _save(sections=None, embed=False):
    return file_store.save_policy_draft(
        tenant_id="t1",
        title="Access Control Policy",
        document_type="POLICY",
        organization="Acme",
        owner="Jane",
        status="Draft",
        schema_version="1.0",
        selected_frameworks=["HIPAA"],
        sections=sections if sections is not None else _draft_sections(),
        embed=embed,
    )


class SavePolicyDraftEmbeddingTests(unittest.TestCase):
    def test_embed_true_attaches_vectors_and_timestamps(self):
        with patch.object(file_store, "_postgrest", side_effect=_fake_postgrest), \
                patch.object(file_store, "embed_chunks", return_value=[[1.0, 0.0], [0.0, 1.0]]) as mock_embed:
            draft = _save(embed=True)

        mock_embed.assert_called_once()
        args, kwargs = mock_embed.call_args
        self.assertEqual(len(args[0]), 2)
        self.assertEqual(kwargs.get("input_type"), "document")

        stored = draft["sections"]
        self.assertEqual(len(stored), 2)
        for row in stored:
            self.assertIsNotNone(row["embedding"])
            self.assertIsNotNone(row["embedded_at"])
        self.assertEqual(stored[0]["embedding"], [1.0, 0.0])
        self.assertEqual(stored[1]["embedding"], [0.0, 1.0])

    def test_embed_false_by_default_does_not_call_embed_chunks(self):
        with patch.object(file_store, "_postgrest", side_effect=_fake_postgrest), \
                patch.object(file_store, "embed_chunks") as mock_embed:
            draft = _save()

        mock_embed.assert_not_called()
        for row in draft["sections"]:
            self.assertNotIn("embedding", row)
            self.assertNotIn("embedded_at", row)

    def test_embedding_failure_soft_fails_and_still_saves_sections(self):
        with patch.object(file_store, "_postgrest", side_effect=_fake_postgrest), \
                patch.object(file_store, "embed_chunks", side_effect=RuntimeError("voyage down")):
            draft = _save(embed=True)

        stored = draft["sections"]
        self.assertEqual(len(stored), 2)
        for row in stored:
            self.assertIsNone(row["embedding"])
            self.assertIsNone(row["embedded_at"])

    def test_empty_sections_skips_embedding_call(self):
        with patch.object(file_store, "_postgrest", side_effect=_fake_postgrest), \
                patch.object(file_store, "embed_chunks") as mock_embed:
            draft = _save(sections=[], embed=True)

        mock_embed.assert_not_called()
        self.assertEqual(draft["sections"], [])


class CreateGeneratePassesEmbedTrueTests(unittest.TestCase):
    """Contract check: the /pipeline/create/generate call site opts into
    embedding (the incremental preview-save loop must not)."""

    BODY = {
        "policy_data": {
            "policy_name": "Access Control Policy",
            "version": "1.0",
            "doc_type": "POLICY",
            "_session": {"frameworks": ["HIPAA"], "policy_id": "p1", "source_name": "src"},
        }
    }

    def setUp(self):
        self.captured_kwargs = {}
        app.dependency_overrides[verify_access] = lambda: {"authenticated": True}
        self.patchers = [
            patch.object(routes, "_tenant_context_from_request",
                         lambda request: {"id": "t1", "name": "Acme", "plan_type": "pro"}),
            patch.object(routes, "_merge_sections_from_top_level", lambda pd: pd),
            patch.object(routes, "_normalize_policy_payload_or_400", lambda pd, **k: pd),
            patch.object(routes, "_ensure_required_slots_or_400", lambda pd: pd),
            patch.object(routes, "_identify_covered_controls", lambda **k: []),
            patch.object(routes, "update_policy_covered_controls", lambda *a, **k: None),
            patch.object(routes, "EVIDENCE_AGENT",
                         types.SimpleNamespace(run=lambda payload: types.SimpleNamespace(
                             evidence_requirements=[], readiness_summary=""))),
            patch.object(routes, "_emit_signal", lambda *a, **k: None),
            patch.object(routes, "_render_and_store_docx",
                         lambda **k: ({"id": "doc123"}, b"PKfakedocxbytes", "preview text")),
        ]
        for p in self.patchers:
            p.start()

        def _capture_save_policy_draft(**kwargs):
            self.captured_kwargs = kwargs
            return {"policy": {"id": "p1"}}

        capture_patcher = patch.object(routes, "save_policy_draft", _capture_save_policy_draft)
        capture_patcher.start()
        self.patchers.append(capture_patcher)

    def tearDown(self):
        for p in self.patchers:
            p.stop()
        app.dependency_overrides.clear()

    def test_create_generate_route_requests_embedding(self):
        client = TestClient(app)
        r = client.post("/pipeline/create/generate", json=self.BODY, headers={"Accept": "application/json"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(self.captured_kwargs.get("embed"))


class RetrievalFindsEmbeddedGeneratedSectionsTests(unittest.TestCase):
    """End-to-end: a section embedded via save_policy_draft(embed=True) is
    retrievable by the corpus answer engine's similarity search."""

    def test_generated_section_is_retrieved_by_corpus_engine(self):
        with patch.object(file_store, "_postgrest", side_effect=_fake_postgrest), \
                patch.object(file_store, "embed_chunks", return_value=[[1.0, 0.0]]):
            draft = _save(
                sections=[{"slot_id": "purpose", "heading": "Purpose", "content": "MFA required for all admins."}],
                embed=True,
            )

        stored_section = draft["sections"][0]
        # What load_corpus_sections would hand retrieve_sections after the
        # `embedding IS NOT NULL` DB filter passes for this row.
        section_for_retrieval = {
            "id": "sec-1",
            "policy_id": "pol-1",
            "policy_name": "Access Control Policy",
            "covered_control_ids": [],
            "heading": stored_section["heading"],
            "content": stored_section["content"],
            "vector": stored_section["embedding"],
        }

        results = corpus.retrieve_sections(
            "Do you require MFA?",
            [section_for_retrieval],
            qvec=[1.0, 0.0],
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["heading"], "Purpose")

    def test_unembedded_section_would_be_filtered_before_retrieval(self):
        with patch.object(file_store, "_postgrest", side_effect=_fake_postgrest), \
                patch.object(file_store, "embed_chunks", side_effect=RuntimeError("voyage down")):
            draft = _save(
                sections=[{"slot_id": "purpose", "heading": "Purpose", "content": "MFA required."}],
                embed=True,
            )

        stored_section = draft["sections"][0]
        self.assertIsNone(stored_section["embedding"])


if __name__ == "__main__":
    unittest.main()
