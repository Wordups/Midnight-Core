import unittest

from backend.agents import (
    CleanerAgent,
    EvidenceAgent,
    ExecutiveSummaryAgent,
    FrameworkMappingAgent,
    PolicyAgent,
    SignalManagerAgent,
    TenantManagerAgent,
)
from backend.agents.base import AgentValidationError


VALID_POLICY_JSON = """
```json
{
  "title": "IT Asset Disposal Policy",
  "organization": "Takeoff LLC / Midnight",
  "status": "Draft",
  "metadata": {
    "owner": "Brian Word",
    "document_type": "Policy"
  },
  "sections": [
    {
      "slot_id": "purpose",
      "heading": "Purpose",
      "content": "Define why secure asset disposal is required."
    }
  ],
  "framework_mappings": {
    "HIPAA": []
  }
}
```
"""


class AgentFoundationTests(unittest.TestCase):
    def test_agents_are_importable(self):
        self.assertEqual(CleanerAgent().name, "cleaner_agent")
        self.assertEqual(SignalManagerAgent().name, "signal_manager_agent")
        self.assertEqual(TenantManagerAgent().name, "tenant_manager_agent")

    def test_cleaner_agent_validates_good_policy_json(self):
        payload = CleanerAgent().run(
            {
                "raw_output": VALID_POLICY_JSON,
                "required_frameworks": ["HIPAA"],
            }
        )
        self.assertEqual(payload.title, "IT Asset Disposal Policy")
        self.assertEqual(payload.framework_mappings, {"HIPAA": []})

    def test_cleaner_agent_rejects_malformed_json(self):
        with self.assertRaises(AgentValidationError):
            CleanerAgent().run(
                {
                    "raw_output": '{"title":"Broken","organization":"Takeoff LLC / Midnight","status":"Draft","sections":[{"heading":"Purpose","content":"unterminated}',
                    "required_frameworks": [],
                }
            )

    def test_signal_manager_classifies_policy_generation_failure(self):
        signal = SignalManagerAgent().run(
            {
                "event_type": "policy_generation_failed",
                "tenant_id": "tenant-123",
                "user_id": "user-123",
                "source": "pipeline.create.preview",
                "summary": "Claude returned invalid JSON while drafting IT Asset Disposal Policy.",
            }
        )
        self.assertEqual(signal.signal_type.value, "policy_generation_failed")
        self.assertEqual(signal.tenant_id, "tenant-123")
        self.assertEqual(signal.severity.value, "high")

    def test_tenant_manager_requires_tenant_id(self):
        with self.assertRaises(AgentValidationError):
            TenantManagerAgent().run(
                {
                    "tenant_id": "",
                    "user_id": "user-123",
                    "payload": {"title": "No tenant"},
                }
            )

    def test_tenant_manager_rejects_cross_tenant_payload(self):
        with self.assertRaises(AgentValidationError):
            TenantManagerAgent().run(
                {
                    "tenant_id": "tenant-a",
                    "user_id": "user-123",
                    "payload": {"tenant_id": "tenant-b"},
                }
            )

    def test_policy_agent_uses_cleaner_boundary(self):
        payload = PolicyAgent().run(
            {
                "raw_output": VALID_POLICY_JSON,
                "required_frameworks": ["HIPAA"],
            }
        )
        self.assertEqual(payload.title, "IT Asset Disposal Policy")

    def test_framework_mapping_agent_rejects_unknown_framework(self):
        with self.assertRaises(AgentValidationError):
            FrameworkMappingAgent().run(
                {
                    "tenant_id": "tenant-123",
                    "document_title": "IT Asset Disposal Policy",
                    "frameworks": ["FedRAMP"],
                }
            )

    def test_evidence_agent_extracts_requirements(self):
        summary = EvidenceAgent().run(
            {
                "tenant_id": "tenant-123",
                "policy": CleanerAgent().run({"raw_output": VALID_POLICY_JSON, "required_frameworks": []}).model_dump(),
            }
        )
        self.assertEqual(summary.tenant_id, "tenant-123")

    def test_executive_summary_agent_builds_output(self):
        summary = ExecutiveSummaryAgent().run(
            {
                "tenant_id": "tenant-123",
                "policy_status": {"total": 5},
                "gaps_summary": {"total_gaps": 3},
                "audit_readiness": {"status": "in progress"},
                "recent_activity": [],
            }
        )
        self.assertIn("5 policies", summary.summary)


if __name__ == "__main__":
    unittest.main()
