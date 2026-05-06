from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from backend.agents.base import AgentValidationError, BaseAgent
from backend.agents.schemas import ExecutiveSummaryOutput


class ExecutiveSummaryAgent(BaseAgent):
    name = "executive_summary_agent"
    role = "Creates leadership-facing GRC summaries"
    allowed_actions = ("summarize_policy_status", "summarize_gaps", "summarize_activity")
    forbidden_actions = ("overstate_compliance", "claim_audit_readiness_without_evidence")

    def validate_input(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise AgentValidationError("Executive Summary Agent expects dict input.")
        tenant_id = str(data.get("tenant_id") or "").strip()
        if not tenant_id:
            raise AgentValidationError("Executive Summary Agent requires tenant_id.")
        return data

    def validate_output(self, data: Any) -> ExecutiveSummaryOutput:
        try:
            return ExecutiveSummaryOutput.model_validate(data)
        except ValidationError as exc:
            raise AgentValidationError(f"Executive Summary Agent produced invalid output: {exc}") from exc

    def _run(self, data: dict[str, Any]) -> dict[str, Any]:
        policy_status = data.get("policy_status", {})
        gaps_summary = data.get("gaps_summary", {})
        audit_readiness = data.get("audit_readiness", {})
        recent_activity = data.get("recent_activity", [])
        summary = (
            f"Midnight workspace has {policy_status.get('total', 0)} policies, "
            f"{gaps_summary.get('total_gaps', 0)} identified gaps, and "
            f"audit readiness status of {audit_readiness.get('status', 'in progress')}."
        )
        return {
            "tenant_id": data["tenant_id"],
            "summary": summary,
            "policy_status": policy_status,
            "gaps_summary": gaps_summary,
            "audit_readiness": audit_readiness,
            "recent_activity": recent_activity,
        }
