"""
Midnight Core — FastAPI Entry Point
Takeoff LLC
"""
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import secrets
import os
import hashlib

load_dotenv()

app = FastAPI(title="Midnight Core", version="2.0.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic(auto_error=False)
session_cookie_name = "midnight_session"


class LoginRequest(BaseModel):
    password: str


def _get_password() -> str:
    password = os.getenv("TOOL_PASSWORD")
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if not password:
        if environment == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="TOOL_PASSWORD is not configured for production.",
            )
        password = "midnight-local-dev"
    return password


def _build_session_token(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_access(
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(security),
):
    password = _get_password()
    cookie_token = request.cookies.get(session_cookie_name)
    expected_token = _build_session_token(password)

    if cookie_token and secrets.compare_digest(cookie_token, expected_token):
        return "session"

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Basic"},
        )

    correct = secrets.compare_digest(credentials.password.encode(), password.encode())
    if not correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

from backend.api.routes     import router as pipeline_router
from backend.api.dashboard  import router as dashboard_router
from backend.api.smart_scan import router as smart_scan_router

app.include_router(pipeline_router,   dependencies=[Depends(verify_access)])
app.include_router(dashboard_router,  dependencies=[Depends(verify_access)])
app.include_router(smart_scan_router, dependencies=[Depends(verify_access)])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "midnight-core"}

@app.post("/auth/login")
async def login(payload: LoginRequest, response: Response):
    password = _get_password()
    if not secrets.compare_digest(payload.password.encode(), password.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password.")

    response.set_cookie(
        key=session_cookie_name,
        value=_build_session_token(password),
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "development").lower() == "production",
        samesite="lax",
        max_age=60 * 60 * 12,
    )
    return {"authenticated": True}

@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(session_cookie_name, samesite="lax")
    return {"authenticated": False}

@app.get("/auth/session")
async def session_status(request: Request):
    password = _get_password()
    authenticated = secrets.compare_digest(
        request.cookies.get(session_cookie_name, ""),
        _build_session_token(password),
    )
    return {"authenticated": authenticated}

@app.get("/")
async def root():
    return RedirectResponse(url="/index.html")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
