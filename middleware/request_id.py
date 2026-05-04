import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from logging_config import request_id_var


logger = logging.getLogger("midnight.request")

UUID_LEN = 36


def _is_valid_uuid(value: str) -> bool:
    if len(value) != UUID_LEN:
        return False
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        rid = incoming if _is_valid_uuid(incoming) else str(uuid.uuid4())

        token = request_id_var.set(rid)
        request.state.request_id = rid

        start = time.perf_counter()
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-Id"] = rid
            return response
        finally:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "request_completed",
                extra={
                    "route": request.url.path,
                    "method": request.method,
                    "status": status_code,
                    "latency_ms": latency_ms,
                },
            )
            request_id_var.reset(token)
