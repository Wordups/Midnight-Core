from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from backend.agents.base import AgentValidationError, BaseAgent
from backend.agents.cleaner_agent import CleanerAgent
from backend.agents.schemas import AgentPolicyPayload


class PolicyAgent(BaseAgent):
    name = "policy_agent"
    role = "Handles policy creation and policy improvement workflows"
    allowed_actions = ("generate_draft_structure", "validate_sections", "prepare_render_payload")
    forbidden_actions = ("claim_approval", "claim_certification", "trust_raw_llm_output", "use_eval", "use_exec")

    def __init__(self) -> None:
        self.cleaner = CleanerAgent()

    def validate_input(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise AgentValidationError("Policy Agent expects dict input.")
        if "raw_output" not in data:
            raise AgentValidationError("Policy Agent requires raw_output.")
        return data

    def validate_output(self, data: Any) -> AgentPolicyPayload:
        try:
            return AgentPolicyPayload.model_validate(data)
        except ValidationError as exc:
            raise AgentValidationError(f"Policy Agent produced invalid policy payload: {exc}") from exc

    def _run(self, data: dict[str, Any]) -> dict[str, Any]:
        cleaned = self.cleaner.run(
            {
                "raw_output": data["raw_output"],
                "required_frameworks": data.get("required_frameworks"),
            }
        )
        return cleaned.model_dump()
