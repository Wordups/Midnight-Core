from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from backend.agents.base import AgentValidationError, BaseAgent
from backend.agents.schemas import FrameworkMappingOutput


SUPPORTED_FRAMEWORKS = {
    "HIPAA",
    "NIST CSF",
    "PCI DSS",
    "SOC 2",
    "ISO 27001",
    "HITRUST",
    "HITRUST Domains",
}


class FrameworkMappingAgent(BaseAgent):
    name = "framework_mapping_agent"
    role = "Maps policy content to compliance frameworks"
    allowed_actions = ("validate_framework_scope", "prepare_gap_inputs", "explain_missing_coverage")
    forbidden_actions = ("invent_controls", "hallucinate_citations", "claim_certification")

    def validate_input(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise AgentValidationError("Framework Mapping Agent expects dict input.")
        tenant_id = str(data.get("tenant_id") or "").strip()
        title = str(data.get("document_title") or "").strip()
        if not tenant_id or not title:
            raise AgentValidationError("Framework Mapping Agent requires tenant_id and document_title.")
        return data

    def validate_output(self, data: Any) -> FrameworkMappingOutput:
        try:
            return FrameworkMappingOutput.model_validate(data)
        except ValidationError as exc:
            raise AgentValidationError(f"Framework Mapping Agent produced invalid output: {exc}") from exc

    def _run(self, data: dict[str, Any]) -> dict[str, Any]:
        frameworks = [str(item).strip() for item in data.get("frameworks", []) if str(item).strip()]
        unsupported = [fw for fw in frameworks if fw not in SUPPORTED_FRAMEWORKS]
        if unsupported:
            raise AgentValidationError(f"Unsupported frameworks requested: {', '.join(unsupported)}")
        return {
            "tenant_id": data["tenant_id"],
            "document_title": data["document_title"],
            "frameworks": frameworks,
            "mapped_controls": data.get("mapped_controls", {}),
            "gaps": data.get("gaps", []),
        }
