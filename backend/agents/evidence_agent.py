from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from backend.agents.base import AgentValidationError, BaseAgent
from backend.agents.schemas import AgentPolicyPayload, EvidenceRequirement, EvidenceSummaryOutput


class EvidenceAgent(BaseAgent):
    name = "evidence_agent"
    role = "Tracks audit readiness and evidence needs"
    allowed_actions = ("identify_evidence_requirements", "produce_readiness_summary")
    forbidden_actions = ("mark_evidence_complete_without_artifacts",)

    def validate_input(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise AgentValidationError("Evidence Agent expects dict input.")
        if not data.get("tenant_id"):
            raise AgentValidationError("Evidence Agent requires tenant_id.")
        if not data.get("policy"):
            raise AgentValidationError("Evidence Agent requires policy payload.")
        return data

    def validate_output(self, data: Any) -> EvidenceSummaryOutput:
        try:
            return EvidenceSummaryOutput.model_validate(data)
        except ValidationError as exc:
            raise AgentValidationError(f"Evidence Agent produced invalid output: {exc}") from exc

    def _run(self, data: dict[str, Any]) -> dict[str, Any]:
        policy = AgentPolicyPayload.model_validate(data["policy"])
        requirements: list[EvidenceRequirement] = []
        for section in policy.sections:
            if section.slot_id in {"procedures", "compliance_requirements", "approval"}:
                requirements.append(
                    EvidenceRequirement(
                        policy_title=policy.title,
                        slot_id=section.slot_id,
                        requirement=f"Provide evidence artifact supporting {section.heading}.",
                    )
                )
        summary = (
            "Evidence requirements identified from policy control-bearing sections."
            if requirements
            else "No explicit evidence requirements were identified from the current draft."
        )
        return {
            "tenant_id": data["tenant_id"],
            "policy_title": policy.title,
            "evidence_requirements": [item.model_dump() for item in requirements],
            "readiness_summary": summary,
        }
