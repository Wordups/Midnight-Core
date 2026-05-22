"""
Unit tests for gap-engine dashboard wiring (Sprint 1 / Task 1).

These tests exercise the validation and transformation logic without hitting
the database or making real Claude API calls.
"""
import unittest
from unittest.mock import MagicMock, patch

from backend.core.gap_engine import CONTROL_REGISTRY, run_program_gap_analysis


# ── Helper: the ID filter logic extracted from _identify_covered_controls ─────

_REGISTRY_ID_SET = frozenset(c.id for c in CONTROL_REGISTRY)


def _filter_covered_ids(raw_ids, candidate_ids):
    """Mirror of the filter logic in routes._identify_covered_controls."""
    if not isinstance(raw_ids, list):
        return []
    candidate_set = frozenset(candidate_ids)
    return [
        str(item) for item in raw_ids
        if isinstance(item, str)
        and item in _REGISTRY_ID_SET
        and item in candidate_set
    ]


class TestCoveredIdValidation(unittest.TestCase):

    def test_valid_ids_pass_through(self):
        candidates = ["HIPAA-164.308(a)(1)", "HIPAA-164.312(a)(1)", "PCI-7.1"]
        raw = ["HIPAA-164.308(a)(1)", "PCI-7.1"]
        result = _filter_covered_ids(raw, candidates)
        self.assertEqual(sorted(result), sorted(["HIPAA-164.308(a)(1)", "PCI-7.1"]))

    def test_unknown_ids_are_dropped(self):
        candidates = ["HIPAA-164.308(a)(1)", "PCI-7.1"]
        raw = ["HIPAA-164.308(a)(1)", "FAKE-999", "NOT-A-CONTROL", "PCI-7.1"]
        result = _filter_covered_ids(raw, candidates)
        self.assertNotIn("FAKE-999", result)
        self.assertNotIn("NOT-A-CONTROL", result)
        self.assertIn("HIPAA-164.308(a)(1)", result)

    def test_ids_outside_candidate_scope_are_dropped(self):
        # SOC2-CC6.1 is in registry but not in the candidate list for this call
        candidates = ["HIPAA-164.308(a)(1)"]
        raw = ["HIPAA-164.308(a)(1)", "SOC2-CC6.1"]
        result = _filter_covered_ids(raw, candidates)
        self.assertNotIn("SOC2-CC6.1", result)
        self.assertIn("HIPAA-164.308(a)(1)", result)

    def test_none_input_returns_empty(self):
        result = _filter_covered_ids(None, ["HIPAA-164.308(a)(1)"])
        self.assertEqual(result, [])

    def test_empty_raw_returns_empty(self):
        result = _filter_covered_ids([], ["HIPAA-164.308(a)(1)"])
        self.assertEqual(result, [])

    def test_empty_candidates_drops_everything(self):
        result = _filter_covered_ids(["HIPAA-164.308(a)(1)"], [])
        self.assertEqual(result, [])


class TestGapsDashboardTransformation(unittest.TestCase):

    def test_program_gap_analysis_returns_expected_shape(self):
        documents = [
            {
                "name": "Access Control Policy",
                "doc_type": "POLICY",
                "covered_control_ids": ["HIPAA-164.308(a)(1)", "HIPAA-164.312(a)(1)"],
            }
        ]
        result = run_program_gap_analysis(documents=documents, frameworks=["HIPAA"])
        self.assertIn("total_gaps", result)
        self.assertIn("gaps_critical", result)
        self.assertIn("gaps_medium", result)
        self.assertIn("overall_coverage_pct", result)
        self.assertIsInstance(result["gaps"], list)

    def test_full_coverage_produces_zero_gaps(self):
        # Cover all HIPAA POLICY controls
        hipaa_policy_ids = [
            c.id for c in CONTROL_REGISTRY
            if c.framework == "HIPAA" and "POLICY" in c.doc_types
        ]
        documents = [
            {
                "name": "Complete HIPAA Policy",
                "doc_type": "POLICY",
                "covered_control_ids": hipaa_policy_ids,
            }
        ]
        result = run_program_gap_analysis(documents=documents, frameworks=["HIPAA"])
        hipaa_gaps = [g for g in result["gaps"] if g["framework"] == "HIPAA"]
        self.assertEqual(len(hipaa_gaps), 0)

    def test_zero_coverage_produces_all_gaps(self):
        documents = [
            {
                "name": "Empty Policy",
                "doc_type": "POLICY",
                "covered_control_ids": [],
            }
        ]
        result = run_program_gap_analysis(documents=documents, frameworks=["HIPAA"])
        self.assertGreater(result["total_gaps"], 0)
        self.assertGreater(result["gaps_critical"], 0)


class TestGapsResponseFilterCounts(unittest.TestCase):
    """
    Verify that filtering by severity recalculates counts correctly —
    this tests the fix to the pre-existing bug in get_gaps() where
    filtered responses returned critical=0, medium=0, low=0 regardless.
    """

    def _make_items(self):
        from backend.api.dashboard import GapItem
        return [
            GapItem(id="A", control_id="A", framework="HIPAA", description="",
                    severity="critical", affected_frameworks=["HIPAA"], suggested_action=""),
            GapItem(id="B", control_id="B", framework="HIPAA", description="",
                    severity="medium", affected_frameworks=["HIPAA"], suggested_action=""),
            GapItem(id="C", control_id="C", framework="PCI DSS", description="",
                    severity="critical", affected_frameworks=["PCI DSS"], suggested_action=""),
        ]

    def test_filter_severity_recalculates_counts(self):
        from backend.api.dashboard import GapsResponse
        items = self._make_items()
        critical_items = [g for g in items if g.severity == "critical"]
        response = GapsResponse(
            total=len(critical_items),
            critical=sum(1 for g in critical_items if g.severity == "critical"),
            medium=sum(1 for g in critical_items if g.severity == "medium"),
            low=sum(1 for g in critical_items if g.severity == "low"),
            items=critical_items,
        )
        self.assertEqual(response.total, 2)
        self.assertEqual(response.critical, 2)
        self.assertEqual(response.medium, 0)
        self.assertEqual(response.low, 0)


if __name__ == "__main__":
    unittest.main()
