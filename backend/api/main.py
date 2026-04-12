"""
Midnight Core — FastAPI Entry Point
Takeoff LLC
"""
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_cookie_name = "midnight_session"

OWNER_EMAIL       = os.getenv("OWNER_EMAIL",       "admin@midnight.ai")
OWNER_NAME        = os.getenv("OWNER_NAME",        "Workspace Owner")
ORGANIZATION_NAME = os.getenv("ORGANIZATION_NAME", "Midnight Workspace")
TOOL_PASSWORD     = os.getenv("TOOL_PASSWORD",     "")
ENVIRONMENT       = os.getenv("ENVIRONMENT",       "development").lower()


class LoginRequest(BaseModel):
    email:    str
    password: str


def get_workspace_id() -> str:
    return os.getenv("WORKSPACE_ID", "personal")


def get_owner_profile() -> dict[str, str]:
    owner_email = OWNER_EMAIL.lower().strip()
    owner_name = OWNER_NAME.strip()
    if not owner_name:
        local_part = owner_email.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
        owner_name = " ".join(part.capitalize() for part in local_part.split()) or "Workspace Owner"
    organization_name = ORGANIZATION_NAME.strip() or "Midnight Workspace"
    return {
        "email": owner_email,
        "display_name": owner_name,
        "organization_name": organization_name,
        "role": "Owner",
        "environment": ENVIRONMENT,
    }


def _get_password() -> str:
    if TOOL_PASSWORD:
        return TOOL_PASSWORD
    if ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TOOL_PASSWORD is not configured for production.",
        )
    return "midnight-local-dev"


def _build_session_token(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_access(request: Request):
    password      = _get_password()
    cookie_token  = request.cookies.get(session_cookie_name, "")
    expected      = _build_session_token(password)
    if cookie_token and secrets.compare_digest(cookie_token, expected):
        return "session"
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
    )


# ── Health check (must be before routers and static mount) ──────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "midnight-core"}


# ── Public auth endpoints ────────────────────────────────────────────────
@app.post("/auth/login")
async def login(payload: LoginRequest, response: Response):
    password = _get_password()
    owner_profile = get_owner_profile()
    owner_email = owner_profile["email"]
    email_match    = secrets.compare_digest(
        payload.email.lower().strip().encode(),
        owner_email.encode(),
    )
    password_match = secrets.compare_digest(
        payload.password.encode(),
        password.encode(),
    )
    if not (email_match and password_match):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )
    response.set_cookie(
        key=session_cookie_name,
        value=_build_session_token(password),
        httponly=True,
        secure=ENVIRONMENT == "production",
        samesite="lax",
        max_age=60 * 60 * 12,
    )
    return {
        "authenticated": True,
        "workspace_id":  get_workspace_id(),
        **owner_profile,
    }


@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(session_cookie_name, samesite="lax")
    return {"authenticated": False}


@app.get("/auth/session")
async def session_status(request: Request):
    password      = _get_password()
    cookie_token  = request.cookies.get(session_cookie_name, "")
    authenticated = bool(cookie_token) and secrets.compare_digest(
        cookie_token,
        _build_session_token(password),
    )
    owner_profile = get_owner_profile()
    return {
        "authenticated": authenticated,
        "workspace_id":  get_workspace_id(),
        **owner_profile,
    }


# ── Protected routers ────────────────────────────────────────────────────
from backend.api.routes     import router as pipeline_router
from backend.api.dashboard  import router as dashboard_router
from backend.api.smart_scan import router as smart_scan_router

app.include_router(pipeline_router,   dependencies=[Depends(verify_access)])
app.include_router(dashboard_router,  dependencies=[Depends(verify_access)])
app.include_router(smart_scan_router, dependencies=[Depends(verify_access)])


# ── Root redirect ────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return RedirectResponse(url="/index.html")


# ── Static files (frontend) — mounted last ──────────────────────────────
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
