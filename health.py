import asyncio
import logging

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import settings


logger = logging.getLogger("midnight.health")
router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


def _check_anthropic_key_present() -> bool:
    key = settings.ANTHROPIC_API_KEY
    return bool(key) and key.startswith("sk-")


async def _check_anthropic_ready() -> bool:
    return _check_anthropic_key_present()


async def _check_supabase_reachable() -> bool:
    try:
        url = settings.SUPABASE_URL.rstrip("/") + "/auth/v1/health"
        async with httpx.AsyncClient(timeout=httpx.Timeout(2.0, connect=1.5)) as client:
            response = await client.get(url)
            return response.status_code < 500
    except Exception:
        logger.warning("supabase_check_failed", exc_info=True)
        return False


@router.get("/ready")
async def ready():
    anthropic_ok, supabase_ok = await asyncio.gather(
        _check_anthropic_ready(),
        _check_supabase_reachable(),
    )

    checks = {"anthropic": anthropic_ok, "supabase": supabase_ok}
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "checks": checks},
    )
