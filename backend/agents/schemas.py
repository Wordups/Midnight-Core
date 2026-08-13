from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalType(str, Enum):
    POLICY_CREATED = "policy_created"
    POLICY_GENERATION_FAILED = "policy_generation_failed"
    MIGRATION_COMPLETED = "migration_completed"
    MIGRATION_FAILED = "migration_failed"
    FRAMEWORK_MAPPING_COMPLETED = "framework_mapping_completed"
    FRAMEWORK_MAPPING_FAILED = "framework_mapping_failed"
    USER_INVITE_FAILED = "user_invite_failed"
    USER_ONBOARDING_EVENT = "user_onboarding_event"
    UNKNOWN = "unknown"


class SignalEventInput(BaseModel):
    event_type: str = Field(..., min_length=1)
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    source: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class SignalOutput(BaseModel):
    signal_type: SignalType
    tenant_id: str
    user_id: Optional[str] = None
    source: str
    severity: Severity
    summary: str
    recommended_next_action: str
    timestamp: datetime = Field(default_factory=utc_now)


class AgentPolicySection(BaseModel):
    model_config = ConfigDict(extra="allow")
    slot_id: str = Field(..., min_length=1)
    heading: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    sort_order: Optional[int] = None
    source_origin: Optional[str] = None
    confidence_score: Optional[float] = None


class AgentPolicyPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: str = Field(..., min_length=1)
    organization: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    sections: list[AgentPolicySection] = Field(..., min_length=1)
    framework_mappings: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("framework_mappings")
    @classmethod
    def validate_framework_mappings(cls, value: dict[str, list[str]]) -> dict[str, list[str]]:
        for framework, controls in value.items():
            if not framework or not isinstance(framework, str):
                raise ValueError("Framework mapping keys must be non-empty strings.")
            if not isinstance(controls, list):
                raise ValueError("Framework mapping values must be lists.")
        return value


class TenantScopedInput(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class TenantScopedOutput(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    allowed: bool = True
    reason: Optional[str] = None


class FrameworkMappingOutput(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    document_title: str = Field(..., min_length=1)
    frameworks: list[str] = Field(default_factory=list)
    mapped_controls: dict[str, list[str]] = Field(default_factory=dict)
    gaps: list[dict[str, Any]] = Field(default_factory=list)


class EvidenceRequirement(BaseModel):
    policy_title: str = Field(..., min_length=1)
    slot_id: str = Field(..., min_length=1)
    requirement: str = Field(..., min_length=1)
    evidence_status: str = Field(default="missing")


class EvidenceSummaryOutput(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    policy_title: str = Field(..., min_length=1)
    evidence_requirements: list[EvidenceRequirement] = Field(default_factory=list)
    readiness_summary: str = Field(..., min_length=1)


class ExecutiveSummaryOutput(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    policy_status: dict[str, Any] = Field(default_factory=dict)
    gaps_summary: dict[str, Any] = Field(default_factory=dict)
    audit_readiness: dict[str, Any] = Field(default_factory=dict)
    recent_activity: list[dict[str, Any]] = Field(default_factory=list)
