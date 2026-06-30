import unittest

from backend.core.gap_engine import (
    compute_gaps,
    get_equivalent_controls,
    is_control_covered,
)


class GapEngineTests(unittest.TestCase):
    def test_cross_framework_control_counts_as_coverage(self):
        # Covering the HIPAA logical access-control standard should satisfy its
        # equivalents in ISO 27001:2022, SOC 2, and PCI via the cross-framework
        # map (IDs verified against the loaded frameworks/*.json libraries).
        covered = {"HIPAA-164.312(a)(1)"}
        equivalents = get_equivalent_controls("HIPAA-164.312(a)(1)")

        self.assertIn("ISO-A.5.15", equivalents)
        self.assertIn("SOC2-CC6.1", equivalents)
        self.assertIn("PCI-7.2", equivalents)

        # Every mapped equivalent is treated as covered when the HIPAA control is.
        for equivalent in equivalents:
            self.assertTrue(is_control_covered(equivalent, covered))

        # And those equivalents do not surface as gaps for a doc that covers HIPAA.
        report = compute_gaps(
            document_name="Access Control Policy",
            doc_type="POLICY",
            covered_control_ids=["HIPAA-164.312(a)(1)"],
            frameworks=["HIPAA", "ISO 27001", "SOC 2", "PCI DSS"],
        )
        gap_ids = [gap.control.id for gap in report.gaps]
        self.assertNotIn("ISO-A.5.15", gap_ids)
        self.assertNotIn("SOC2-CC6.1", gap_ids)

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
