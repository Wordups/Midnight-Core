"""
Stripe billing — checkout session creation and webhook receiver.

Two routers are exported:
  billing_router         — include with verify_access dependency (checkout lives here)
  billing_webhook_router — include bare, no auth (Stripe calls this directly)

Session 4 will add: stripe.Webhook.construct_event in stripe_webhook,
STRIPE_WEBHOOK_SECRET env var, and plan activation on checkout.session.completed.
"""
from __future__ import annotations

import os

import stripe
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

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
async def create_checkout_session(payload: CheckoutRequest) -> dict:
    price_id = _resolve_price_id(payload.tier)
    base = _base_url()
    session = stripe.checkout.Session.create(
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{base}/midnight_dashboard.html?checkout=success",
        cancel_url=f"{base}/midnight_dashboard.html?checkout=cancelled",
    )
    return {"checkout_url": session.url}


# ── Unauthenticated webhook receiver ──────────────────────────────────────────
# Included in main.py with no dependencies — Stripe calls this server-to-server.
# Session 4: add construct_event + STRIPE_WEBHOOK_SECRET + event dispatch here.

billing_webhook_router = APIRouter(prefix="/billing", tags=["billing"])


@billing_webhook_router.post("/webhook")
async def stripe_webhook(request: Request) -> Response:
    return Response(status_code=200)
