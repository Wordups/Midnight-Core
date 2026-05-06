from __future__ import annotations


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_invite_delivery_failure(detail: str) -> bool:
    lowered = detail.lower()
    return "error sending invite email" in lowered or ("invite" in lowered and "email" in lowered and "send" in lowered)


def manual_join_blocker(
    *,
    source_tenant_id: str | None,
    destination_tenant_id: str,
    profile_count: int,
    has_policies: bool,
    has_documents: bool,
) -> str | None:
    normalized_source_tenant = str(source_tenant_id or "").strip()
    if not normalized_source_tenant or normalized_source_tenant == destination_tenant_id:
        return None
    if profile_count > 1:
        return "Tester already belongs to a multi-user tenant. Manual reassignment is blocked to avoid cross-tenant access."
    if has_policies or has_documents:
        return "Tester already has policy data in another tenant. Manual reassignment is blocked to avoid moving live records."
    return None
