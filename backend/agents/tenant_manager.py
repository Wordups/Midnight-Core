from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from backend.agents.base import AgentValidationError, BaseAgent
from backend.agents.schemas import TenantScopedInput, TenantScopedOutput


class TenantManagerAgent(BaseAgent):
    name = "tenant_manager_agent"
    role = "Handles tenant and user relationship logic"
    allowed_actions = ("validate_tenant_scope", "enforce_membership", "reject_cross_tenant_payloads")
    forbidden_actions = ("hardcode_tenants", "expose_cross_tenant_records", "create_frontend_only_tenants")

    def validate_input(self, data: Any) -> TenantScopedInput:
        try:
            return TenantScopedInput.model_validate(data)
        except ValidationError as exc:
            raise AgentValidationError(f"Tenant Manager received invalid input: {exc}") from exc

    def validate_output(self, data: Any) -> TenantScopedOutput:
        try:
            return TenantScopedOutput.model_validate(data)
        except ValidationError as exc:
            raise AgentValidationError(f"Tenant Manager produced invalid output: {exc}") from exc

    def _run(self, data: TenantScopedInput) -> dict[str, Any]:
        payload_tenant = data.payload.get("tenant_id")
        if payload_tenant and str(payload_tenant) != str(data.tenant_id):
            raise AgentValidationError("Cross-tenant payload detected.")
        return {"tenant_id": data.tenant_id, "allowed": True}
