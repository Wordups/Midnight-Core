"""
Stripe billing — checkout session creation and webhook receiver.

Two routers are exported:
  billing_router         — include with verify_access dependency (checkout lives here)
  billing_webhook_router — include bare, no auth (Stripe calls this directly)

The webhook verifies the Stripe signature, then activates the tenant's plan on
checkout.session.completed and downgrades on subscription cancellation. Plan
activation is idempotent (setting the same plan twice is harmless); a
processed-events ledger (migration 003) is used opportunistically for dedup.
"""
from __future__ import annotations

import logging
import os

import stripe
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from backend.storage.supabase_client import supabase_admin

logger = logging.getLogger("midnight.billing")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

_TIER_TO_ENV: dict[str, str] = {
    "starter":    "STRIPE_PRICE_STARTER",
    "growth":     "STRIPE_PRICE_GROWTH",
    "enterprise": "STRIPE_PRICE_ENTERPRISE",
}


def _resolve_price_id(tier: str) -> str:
    env_key = _TIER_TO_ENV.get(tier.lower())
    if not env_key:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier: '{tier}'. Must be starter, growth, or enterprise.",
        )
    price_id = os.getenv(env_key, "").strip()
    if not price_id:
        raise HTTPException(status_code=503, detail=f"{env_key} is not configured.")
    return price_id


def _base_url() -> str:
    return os.getenv("FRONTEND_BASE_URL", "http://localhost:8000").rstrip("/")


# ── Authenticated billing endpoints ───────────────────────────────────────────
# Included in main.py with dependencies=[Depends(verify_access)].

billing_router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    tier: str


@billing_router.post("/checkout")
async def create_checkout_session(payload: CheckoutRequest, request: Request) -> dict:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authenticated tenant context is missing.")
    tier = payload.tier.lower()
    price_id = _resolve_price_id(tier)
    base = _base_url()
    # tenant_id travels on the session AND the subscription so both
    # checkout.session.completed and later subscription.* events map back.
    session = stripe.checkout.Session.create(
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{base}/midnight_dashboard.html?checkout=success",
        cancel_url=f"{base}/midnight_dashboard.html?checkout=cancelled",
        client_reference_id=tenant_id,
        metadata={"tenant_id": tenant_id, "tier": tier},
        subscription_data={"metadata": {"tenant_id": tenant_id, "tier": tier}},
    )
    return {"checkout_url": session.url}


# ── Plan activation + event handling ──────────────────────────────────────────

def _activate_plan(tenant_id: str, plan: str) -> None:
    """Set tenants.plan_type. Idempotent — safe to apply the same plan twice."""
    supabase_admin.table("tenants").update({"plan_type": plan}).eq("id", tenant_id).execute()
    logger.info("plan_activated tenant=%s plan=%s", tenant_id, plan)


def _tenant_from_obj(obj: dict) -> str | None:
    return obj.get("client_reference_id") or (obj.get("metadata") or {}).get("tenant_id")


def _tier_from_obj(obj: dict) -> str | None:
    return (obj.get("metadata") or {}).get("tier")


def _already_processed(event_id: str) -> bool:
    """Best-effort dedup against the processed-events ledger (migration 003).
    If the table isn't present yet, returns False — activation is idempotent."""
    try:
        res = supabase_admin.table("processed_stripe_events").select("event_id").eq("event_id", event_id).limit(1).execute()
        return bool(res.data)
    except Exception:
        return False


def _mark_processed(event_id: str, event_type: str) -> None:
    try:
        supabase_admin.table("processed_stripe_events").insert(
            {"event_id": event_id, "event_type": event_type}
        ).execute()
    except Exception:
        logger.warning("processed_events_write_skipped", exc_info=True)


def _handle_stripe_event(event: dict) -> None:
    etype = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}
    tenant_id = _tenant_from_obj(obj)

    if etype == "checkout.session.completed":
        tier = _tier_from_obj(obj)
        if tenant_id and tier:
            _activate_plan(tenant_id, tier)
    elif etype == "customer.subscription.updated":
        tier = _tier_from_obj(obj)
        if tenant_id and tier:
            _activate_plan(tenant_id, tier)
    elif etype == "customer.subscription.deleted":
        if tenant_id:
            _activate_plan(tenant_id, "trial")
    else:
        logger.debug("stripe_event_ignored type=%s", etype)


# ── Unauthenticated webhook receiver ──────────────────────────────────────────
# Included in main.py with no dependencies — Stripe calls this server-to-server.

billing_webhook_router = APIRouter(prefix="/billing", tags=["billing"])


@billing_webhook_router.post("/webhook")
async def stripe_webhook(request: Request) -> Response:
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not secret:
        logger.error("stripe_webhook_secret_missing")
        raise HTTPException(status_code=500, detail="Webhook is not configured.")

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid payload.") from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=400, detail="Invalid signature.") from exc

    event_id = (event.get("id") if isinstance(event, dict) else getattr(event, "id", "")) or ""
    if event_id and _already_processed(event_id):
        return Response(status_code=200)

    try:
        _handle_stripe_event(event if isinstance(event, dict) else dict(event))
    except Exception:
        logger.exception("stripe_event_handler_failed")
        # 500 → Stripe retries; better than silently dropping a paid activation.
        raise HTTPException(status_code=500, detail="Event handling failed.")

    if event_id:
        _mark_processed(event_id, event.get("type", "") if isinstance(event, dict) else "")
    return Response(status_code=200)
