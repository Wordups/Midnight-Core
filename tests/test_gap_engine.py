import unittest

from backend.core.gap_engine import compute_gaps


class GapEngineTests(unittest.TestCase):
    def test_cross_framework_control_counts_as_coverage(self):
        report = compute_gaps(
            document_name="Access Control Policy",
            doc_type="POLICY",
            covered_control_ids=["PCI-7.1"],
            frameworks=["HIPAA", "PCI DSS", "HITRUST", "ISO 27001"],
        )

        self.assertEqual(report.coverage_by_framework["PCI DSS"], 20)
        self.assertNotIn(
            "HIPAA-164.312(a)(1)",
            [gap.control.id for gap in report.gaps],
        )
        self.assertNotIn(
            "HITRUST-01.a",
            [gap.control.id for gap in report.gaps],
        )
        self.assertNotIn(
            "ISO-A.9.1",
            [gap.control.id for gap in report.gaps],
        )

    def test_gap_report_prioritizes_severity(self):
        report = compute_gaps(
            document_name="Minimal Policy",
            doc_type="POLICY",
            covered_control_ids=[],
            frameworks=["HIPAA", "SOC 2"],
        )

        severities = [gap.control.severity for gap in report.gaps]
        self.assertEqual(severities, sorted(severities, key=lambda level: {"critical": 0, "medium": 1, "low": 2}[level]))


if __name__ == "__main__":
    unittest.main()
