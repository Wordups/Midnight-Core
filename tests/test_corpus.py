"""Corpus + Answer Engine — splitter, index math, fail-closed verdicts,
citation validation, auth, and tenant isolation.

See docs/superpowers/specs/2026-08-12-corpus-answer-engine-design.md.
"""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role")
os.environ.setdefault("ENVIRONMENT", "dev")

from backend.core import corpus  # noqa: E402
from backend.core.gap_engine import load_control_registry  # noqa: E402

TENANT = "00000000-0000-0000-0000-000000000001"


def _fake_llm(text: str):
    def llm(prompt: str):
        return {"text": text, "input_tokens": 100, "output_tokens": 50, "model": "actual-answering-model"}
    return llm


def _sections(content="All privileged access requires MFA via the SSO provider."):
    return [
        {
            "id": "sec-1",
            "policy_id": "pol-1",
            "policy_name": "Access Control Policy",
            "covered_control_ids": ["SOC2-CC6.1"],
            "heading": "Authentication",
            "content": content,
            "vector": [1.0, 0.0],
        }
    ]


class SplitterTests(unittest.TestCase):
    def test_numbered(self):
        text = "1. Do you require MFA for all users?\n2) Is data encrypted at rest?\n3: Do you have an incident response plan?"
        qs = corpus.split_questionnaire(text)
        self.assertEqual(len(qs), 3)
        self.assertTrue(qs[0].startswith("Do you require MFA"))

    def test_bullets_with_wrapped_lines(self):
        text = "- Do you perform annual penetration\n  testing of production systems?\n- Is access reviewed quarterly?"
        qs = corpus.split_questionnaire(text)
        self.assertEqual(len(qs), 2)
        self.assertIn("penetration testing", qs[0])

    def test_plain_lines(self):
        text = "Do you require MFA?\nIs data encrypted at rest?"
        self.assertEqual(len(corpus.split_questionnaire(text)), 2)

    def test_q_prefix(self):
        text = "Q1. Do you encrypt backups?\nQ2. Do you rotate keys?"
        self.assertEqual(len(corpus.split_questionnaire(text)), 2)

    def test_short_fragments_dropped(self):
        self.assertEqual(corpus.split_questionnaire("1. Yes\n2. Do you have a formal BCP?"), ["Do you have a formal BCP?"])

    def test_empty(self):
        self.assertEqual(corpus.split_questionnaire(""), [])


class IndexTests(unittest.TestCase):
    def _docs(self):
        return [
            {
                "id": "pol-1",
                "policy_name": "Access Control Policy",
                "document_type": "POLICY",
                "selected_frameworks": ["SOC2"],
                "covered_control_ids": ["SOC2-CC6.1", "FAKE-NOT-IN-REGISTRY"],
                "created_at": "2026-08-01T00:00:00+00:00",
                "updated_at": "2026-08-01T00:00:00+00:00",
                "last_reviewed_at": None,
            },
            {
                "id": "pol-2",
                "policy_name": "Ancient SOP",
                "document_type": "SOP",
                "selected_frameworks": [],
                "covered_control_ids": [],
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": None,
                "last_reviewed_at": "2024-01-01T00:00:00+00:00",
            },
        ]

    @patch("backend.core.corpus.db_select")
    def test_index_math(self, mock_select):
        mock_select.return_value = self._docs()
        registry_ids = {c.id for c in load_control_registry()}
        self.assertIn("SOC2-CC6.1", registry_ids)

        index = corpus.build_corpus_index(TENANT)
        self.assertEqual(index["document_count"], 2)
        # unknown control id filtered out
        self.assertEqual(index["documents"][0]["control_ids"], ["SOC2-CC6.1"])
        self.assertEqual(index["controls_covered_total"], 1)
        # ancient doc is stale + unmapped
        self.assertEqual(index["stale_count"], 1)
        self.assertEqual(index["unmapped_documents"], ["Ancient SOP"])
        soc2 = next(f for f in index["frameworks"] if f["framework"] == "SOC 2")
        # CC6.1 direct + CC6.3 via its cross-framework equivalence group
        self.assertEqual(soc2["covered_controls"], 2)
        self.assertGreater(soc2["total_controls"], 1)

    @patch("backend.core.corpus.db_select")
    def test_empty_corpus(self, mock_select):
        mock_select.return_value = []
        index = corpus.build_corpus_index(TENANT)
        self.assertEqual(index["document_count"], 0)
        self.assertEqual(index["stale_count"], 0)


class AnswerTests(unittest.TestCase):
    def test_no_retrieval_skips_llm(self):
        called = {"n": 0}

        def llm(prompt):
            called["n"] += 1
            return {"text": "{}"}

        with patch("backend.core.corpus.embed_chunks", return_value=[[0.0, 1.0]]):
            answer = corpus.answer_question(TENANT, "Do you have SIEM?", llm=llm, sections=_sections())
        self.assertEqual(answer["status"], "insufficient_evidence")
        self.assertEqual(answer["provenance"], "deterministic")
        self.assertEqual(called["n"], 0)

    def test_garbage_llm_fails_closed(self):
        with patch("backend.core.corpus.embed_chunks", return_value=[[1.0, 0.0]]):
            answer = corpus.answer_question(
                TENANT, "Do you require MFA for privileged access?",
                llm=_fake_llm("I think probably yes? Not JSON at all."),
                sections=_sections(),
            )
        self.assertEqual(answer["status"], "insufficient_evidence")

    def test_invalid_status_fails_closed(self):
        verdict = '{"status": "definitely", "answer_text": "MFA is required.", "citations": [], "control_ids": [], "confidence": "high", "followup_question": null}'
        with patch("backend.core.corpus.embed_chunks", return_value=[[1.0, 0.0]]):
            answer = corpus.answer_question(
                TENANT, "Do you require MFA for privileged access?",
                llm=_fake_llm(verdict), sections=_sections(),
            )
        self.assertEqual(answer["status"], "insufficient_evidence")

    def test_valid_verdict_with_real_quote(self):
        verdict = (
            '{"status": "satisfied", "answer_text": "MFA is required for privileged access.",'
            ' "citations": [{"section_id": "sec-1", "quote": "All privileged access requires MFA"}],'
            ' "control_ids": ["SOC2-CC6.1"], "confidence": "high", "followup_question": null}'
        )
        with patch("backend.core.corpus.embed_chunks", return_value=[[1.0, 0.0]]):
            answer = corpus.answer_question(
                TENANT, "Do you require MFA for privileged access?",
                llm=_fake_llm(verdict), sections=_sections(),
            )
        self.assertEqual(answer["status"], "satisfied")
        self.assertEqual(answer["confidence"], "high")
        self.assertEqual(answer["citations"][0]["policy_name"], "Access Control Policy")
        self.assertEqual(answer["control_ids"], ["SOC2-CC6.1"])
        self.assertEqual(answer["usage"]["input_tokens"], 100)

    def test_fabricated_quote_stripped_and_downgraded(self):
        verdict = (
            '{"status": "not_satisfied", "answer_text": "No coverage found for key rotation.",'
            ' "citations": [{"section_id": "sec-1", "quote": "keys are rotated every 90 days"}],'
            ' "control_ids": [], "confidence": "high", "followup_question": "What is the key rotation interval?"}'
        )
        with patch("backend.core.corpus.embed_chunks", return_value=[[1.0, 0.0]]):
            answer = corpus.answer_question(
                TENANT, "Do you rotate encryption keys?",
                llm=_fake_llm(verdict), sections=_sections(),
            )
        self.assertEqual(answer["status"], "not_satisfied")
        self.assertEqual(answer["citations"], [])
        self.assertEqual(answer["confidence"], "medium")
        self.assertEqual(answer["followup_question"], "What is the key rotation interval?")

    def test_satisfied_without_citations_fails_closed(self):
        verdict = (
            '{"status": "satisfied", "answer_text": "Yes MFA everywhere.",'
            ' "citations": [{"section_id": "sec-1", "quote": "this quote is fabricated"}],'
            ' "control_ids": [], "confidence": "high", "followup_question": null}'
        )
        with patch("backend.core.corpus.embed_chunks", return_value=[[1.0, 0.0]]):
            answer = corpus.answer_question(
                TENANT, "Do you require MFA?", llm=_fake_llm(verdict), sections=_sections(),
            )
        self.assertEqual(answer["status"], "insufficient_evidence")

    def test_foreign_control_ids_filtered(self):
        verdict = (
            '{"status": "satisfied", "answer_text": "MFA required.",'
            ' "citations": [{"section_id": "sec-1", "quote": "All privileged access requires MFA"}],'
            ' "control_ids": ["SOC2-CC6.1", "ISO27001-A.5.1"], "confidence": "medium", "followup_question": null}'
        )
        with patch("backend.core.corpus.embed_chunks", return_value=[[1.0, 0.0]]):
            answer = corpus.answer_question(
                TENANT, "Do you require MFA?", llm=_fake_llm(verdict), sections=_sections(),
            )
        self.assertEqual(answer["control_ids"], ["SOC2-CC6.1"])


class BatchTests(unittest.TestCase):
    @patch("backend.core.corpus.db_insert")
    @patch("backend.core.corpus.load_corpus_sections")
    def test_batch_counts_and_persistence(self, mock_sections, mock_insert):
        mock_sections.return_value = _sections()
        mock_insert.side_effect = lambda table, payload: [{"id": "run-1"}]
        verdict = (
            '{"status": "satisfied", "answer_text": "MFA is required.",'
            ' "citations": [{"section_id": "sec-1", "quote": "All privileged access requires MFA"}],'
            ' "control_ids": [], "confidence": "high", "followup_question": null}'
        )
        with patch("backend.core.corpus.embed_chunks", return_value=[[1.0, 0.0]]):
            run = corpus.answer_batch(
                TENANT, ["Do you require MFA for privileged access?"],
                use_case="vendor_assessment", llm=_fake_llm(verdict), model_name="test-model",
            )
        self.assertEqual(run["run_id"], "run-1")
        self.assertEqual(run["counts"]["satisfied"], 1)
        self.assertEqual(run["input_tokens"], 100)
        self.assertEqual(run["use_case"], "vendor_assessment")
        # run reports the model that actually answered, not the configured one
        self.assertEqual(run["model"], "actual-answering-model")
        # runs row + answers rows
        self.assertEqual(mock_insert.call_count, 2)
        answers_payload = mock_insert.call_args_list[1].args[1]
        self.assertEqual(answers_payload[0]["tenant_id"], TENANT)
        self.assertEqual(answers_payload[0]["run_id"], "run-1")

    @patch("backend.core.corpus.db_insert")
    @patch("backend.core.corpus.load_corpus_sections")
    def test_llm_outage_degrades_not_500(self, mock_sections, mock_insert):
        mock_sections.return_value = _sections()
        mock_insert.side_effect = lambda table, payload: [{"id": "run-1"}]

        def broken_llm(prompt):
            raise RuntimeError("api down")

        with patch("backend.core.corpus.embed_chunks", return_value=[[1.0, 0.0]]):
            run = corpus.answer_batch(TENANT, ["Do you require MFA?"], use_case="audit", llm=broken_llm)
        self.assertEqual(run["counts"]["insufficient_evidence"], 1)

    @patch("backend.core.corpus.db_insert")
    @patch("backend.core.corpus.load_corpus_sections")
    def test_question_cap(self, mock_sections, mock_insert):
        mock_sections.return_value = []
        mock_insert.side_effect = lambda table, payload: [{"id": "run-1"}]
        run = corpus.answer_batch(
            TENANT, [f"Question number {i} about encryption?" for i in range(80)],
            use_case="questionnaire", llm=_fake_llm("{}"),
        )
        self.assertEqual(run["question_count"], corpus.MAX_QUESTIONS)


class ApiTests(unittest.TestCase):
    """Router-level: auth and tenant scoping."""

    def setUp(self):
        from backend.api.main import app  # noqa: WPS433
        self.app = app
        self.client = TestClient(app)

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def _login(self, tenant=TENANT, plan="pro"):
        from fastapi import Request  # noqa: WPS433
        from backend.api.main import verify_access  # noqa: WPS433

        def fake_access(request: Request):
            request.state.tenant_id = tenant
            request.state.plan_type = plan
            return {"authenticated": True, "tenant_id": tenant, "plan_type": plan}

        self.app.dependency_overrides[verify_access] = fake_access

    def test_corpus_requires_auth(self):
        for path in ("/api/v1/corpus", "/api/v1/corpus/runs"):
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 401, path)
        resp = self.client.post("/api/v1/corpus/answer", json={"questions": ["Do you require MFA?"]})
        self.assertEqual(resp.status_code, 401)

    @patch("backend.api.corpus.build_corpus_index")
    def test_corpus_index_scoped_to_session_tenant(self, mock_index):
        mock_index.return_value = {"document_count": 0, "documents": [], "frameworks": [], "stale_count": 0, "unmapped_documents": [], "controls_covered_total": 0, "controls_total": 174, "generated_at": "now"}
        self._login()
        resp = self.client.get("/api/v1/corpus")
        self.assertEqual(resp.status_code, 200)
        mock_index.assert_called_once_with(TENANT)

    @patch("backend.api.corpus.db_select")
    def test_runs_list_scoped_to_session_tenant(self, mock_select):
        mock_select.return_value = []
        self._login(tenant="tenant-A")
        resp = self.client.get("/api/v1/corpus/runs")
        self.assertEqual(resp.status_code, 200)
        kwargs = mock_select.call_args.kwargs
        self.assertEqual(kwargs["tenant_id"], "tenant-A")

    @patch("backend.api.corpus.load_corpus_sections")
    def test_answer_empty_corpus_409(self, mock_sections):
        mock_sections.return_value = []
        self._login()
        resp = self.client.post("/api/v1/corpus/answer", json={"questions": ["Do you require MFA for admins?"]})
        self.assertEqual(resp.status_code, 409)

    def test_answer_rejects_oversized(self):
        self._login()
        resp = self.client.post(
            "/api/v1/corpus/answer",
            json={"questions": [f"Question number {i} about encryption controls?" for i in range(60)]},
        )
        self.assertEqual(resp.status_code, 413)

    def test_answer_requires_questions(self):
        self._login()
        resp = self.client.post("/api/v1/corpus/answer", json={"raw_text": ""})
        self.assertEqual(resp.status_code, 422)

    def test_answer_rejects_bad_use_case(self):
        self._login()
        resp = self.client.post(
            "/api/v1/corpus/answer",
            json={"questions": ["Do you require MFA for admins?"], "use_case": "spearphishing"},
        )
        self.assertEqual(resp.status_code, 422)

    @patch("backend.api.corpus.count_activity_for_tenant")
    def test_free_plan_monthly_fence(self, mock_count):
        mock_count.return_value = 2  # free cap is 2/month
        self._login(plan="free")
        resp = self.client.post(
            "/api/v1/corpus/answer",
            json={"questions": ["Do you require MFA for privileged access?"]},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()["detail"]["code"], "upgrade_required")

    @patch("backend.api.corpus.load_corpus_sections")
    @patch("backend.api.corpus.count_activity_for_tenant")
    def test_pro_plan_not_fenced(self, mock_count, mock_sections):
        mock_count.return_value = 999
        mock_sections.return_value = []
        self._login(plan="pro")
        resp = self.client.post(
            "/api/v1/corpus/answer",
            json={"questions": ["Do you require MFA for privileged access?"]},
        )
        # falls through the fence and hits the empty-corpus 409 instead
        self.assertEqual(resp.status_code, 409)
        mock_count.assert_not_called()


if __name__ == "__main__":
    unittest.main()


class ParseQuestionnaireTests(unittest.TestCase):
    def setUp(self):
        from backend.api.main import app
        self.app = app
        self.client = TestClient(app)

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def _login(self):
        from fastapi import Request
        from backend.api.main import verify_access

        def fake_access(request: Request):
            request.state.tenant_id = TENANT
            request.state.plan_type = "pro"
            return {"authenticated": True}

        self.app.dependency_overrides[verify_access] = fake_access

    def test_parse_requires_auth(self):
        resp = self.client.post("/api/v1/corpus/parse", files={"file": ("q.csv", b"a,b", "text/csv")})
        self.assertEqual(resp.status_code, 401)

    def test_parse_csv_takes_longest_cell(self):
        self._login()
        csv_body = b"ID,Question,Ref\nQ1,Do you require MFA for all privileged access?,IAM-1\nQ2,Is data encrypted at rest and in transit?,DP-2\n"
        resp = self.client.post("/api/v1/corpus/parse", files={"file": ("sig.csv", csv_body, "text/csv")})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["count"], 2)
        self.assertIn("MFA", data["questions"][0])

    def test_parse_markdown_uses_splitter(self):
        self._login()
        md = b"1. Do you have an incident response plan?\n2. Do you rotate encryption keys annually?\n"
        resp = self.client.post("/api/v1/corpus/parse", files={"file": ("q.md", md, "text/markdown")})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 2)

    def test_parse_rejects_unknown_type(self):
        self._login()
        resp = self.client.post("/api/v1/corpus/parse", files={"file": ("q.docx", b"x", "application/octet-stream")})
        self.assertEqual(resp.status_code, 415)
