from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from backend.agents.base import AgentValidationError, BaseAgent
from backend.agents.schemas import AgentPolicyPayload
from backend.core.json_parser import (
    ParsedModelOutputError,
    PolicySchemaError,
    normalize_policy_payload,
    parse_model_json,
)


class CleanerAgent(BaseAgent):
    name = "cleaner_agent"
    role = "Quality control and governance enforcement"
    allowed_actions = ("sanitize_json", "validate_schema", "reject_malformed_output")
    forbidden_actions = ("create_fake_records", "approve_broken_output", "silent_repairs")

    def validate_input(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise AgentValidationError("Cleaner Agent expects a dict input.")
        raw_output = data.get("raw_output")
        if not isinstance(raw_output, str) or not raw_output.strip():
            raise AgentValidationError("Cleaner Agent requires raw_output text.")
        return data

    def validate_output(self, data: Any) -> AgentPolicyPayload:
        try:
            return AgentPolicyPayload.model_validate(data)
        except ValidationError as exc:
            raise AgentValidationError(f"Cleaner Agent produced invalid policy payload: {exc}") from exc

    def _run(self, data: dict[str, Any]) -> dict[str, Any]:
        raw_output = data["raw_output"]
        required_frameworks = data.get("required_frameworks")
        try:
            parsed = parse_model_json(raw_output)
            normalized = normalize_policy_payload(parsed, required_frameworks=required_frameworks)
        except (ParsedModelOutputError, PolicySchemaError) as exc:
            raise AgentValidationError(str(exc)) from exc
        return normalized
