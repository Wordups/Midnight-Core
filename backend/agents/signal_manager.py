from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from backend.agents.base import AgentValidationError, BaseAgent
from backend.agents.schemas import Severity, SignalEventInput, SignalOutput, SignalType


class SignalManagerAgent(BaseAgent):
    name = "signal_manager_agent"
    role = "Collects and classifies user and system events"
    allowed_actions = ("classify_events", "emit_structured_signals")
    forbidden_actions = ("change_policy_content", "send_emails", "approve_documents", "bypass_tenant_isolation")

    def validate_input(self, data: Any) -> SignalEventInput:
        try:
            return SignalEventInput.model_validate(data)
        except ValidationError as exc:
            raise AgentValidationError(f"Signal Manager received invalid input: {exc}") from exc

    def validate_output(self, data: Any) -> SignalOutput:
        try:
            return SignalOutput.model_validate(data)
        except ValidationError as exc:
            raise AgentValidationError(f"Signal Manager produced invalid output: {exc}") from exc

    def _run(self, data: SignalEventInput) -> dict[str, Any]:
        event_type = data.event_type.lower().strip()
        signal_type = SignalType.UNKNOWN
        severity = Severity.LOW
        next_action = "Review activity details."

        if "policy" in event_type and "fail" in event_type:
            signal_type = SignalType.POLICY_GENERATION_FAILED
            severity = Severity.HIGH
            next_action = "Inspect model output and retry the failed policy section safely."
        elif "policy" in event_type and ("create" in event_type or "preview" in event_type or "generate" in event_type):
            signal_type = SignalType.POLICY_CREATED
            severity = Severity.MEDIUM
            next_action = "Review the generated draft and complete section validation."
        elif "migration" in event_type and "fail" in event_type:
            signal_type = SignalType.MIGRATION_FAILED
            severity = Severity.HIGH
            next_action = "Inspect extraction/classification issues before retrying migration."
        elif "migration" in event_type:
            signal_type = SignalType.MIGRATION_COMPLETED
            severity = Severity.MEDIUM
            next_action = "Review mapped sections and confirm no source content was lost."
        elif "framework" in event_type and "fail" in event_type:
            signal_type = SignalType.FRAMEWORK_MAPPING_FAILED
            severity = Severity.HIGH
            next_action = "Re-run framework mapping after validating control references."
        elif "framework" in event_type:
            signal_type = SignalType.FRAMEWORK_MAPPING_COMPLETED
            severity = Severity.MEDIUM
            next_action = "Review uncovered controls and update dashboard gap visibility."
        elif "invite" in event_type and "fail" in event_type:
            signal_type = SignalType.USER_INVITE_FAILED
            severity = Severity.HIGH
            next_action = "Check invite delivery configuration and offer safe manual onboarding."
        elif "onboarding" in event_type or "signup" in event_type:
            signal_type = SignalType.USER_ONBOARDING_EVENT
            severity = Severity.LOW
            next_action = "Continue onboarding and confirm tenant provisioning."

        if not data.tenant_id:
            raise AgentValidationError("Signal Manager requires tenant_id for persisted signals.")

        return {
            "signal_type": signal_type,
            "tenant_id": data.tenant_id,
            "user_id": data.user_id,
            "source": data.source,
            "severity": severity,
            "summary": data.summary,
            "recommended_next_action": next_action,
            "timestamp": data.timestamp,
        }
