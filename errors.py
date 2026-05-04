import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger("midnight.errors")


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        rid = _request_id(request)
        logger.warning(
            "http_exception",
            extra={"status": exc.status_code, "detail": str(exc.detail)},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "http_error", "detail": exc.detail, "request_id": rid},
            headers={"X-Request-Id": rid} if rid else {},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        rid = _request_id(request)
        logger.warning("validation_error", extra={"errors": exc.errors()})
        return JSONResponse(
            status_code=422,
            content={"error": "validation_error", "detail": exc.errors(), "request_id": rid},
            headers={"X-Request-Id": rid} if rid else {},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        rid = _request_id(request)
        logger.exception("unhandled_exception")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "request_id": rid},
            headers={"X-Request-Id": rid} if rid else {},
        )
