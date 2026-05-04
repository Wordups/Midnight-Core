"""
Midnight Core - FastAPI entry point.
Takeoff LLC
"""
from __future__ import annotations

from typing import Any

from config import settings
from logging_config import configure_logging

configure_logging(level=settings.LOG_LEVEL)

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from gotrue.errors import AuthApiError
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field
import jwt
import os
import re

from backend.storage.supabase_client import supabase, supabase_admin
from errors import register_exception_handlers
from health import router as health_router
from middleware.request_id import RequestIdMiddleware

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

app.add_middleware(RequestIdMiddleware)
register_exception_handlers(app)
app.include_router(health_router)

session_cookie_name = "midnight_session"


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    company_name: str = Field(min_length=2)
    name: str | None = None
    industry: str | None = None
    region: str | None = None
    employee_count: str | None = None


def _is_secure_cookie() -> bool:
    return settings.ENVIRONMENT == "prod"


def _normalize_display_name(name: str | None, email: str | None) -> str:
    if name and name.strip():
        return name.strip()
    local_part = (email or "").split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
    return " ".join(part.capitalize() for part in local_part.split()) or "Workspace User"


def _slugify_company_name(company_name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", company_name.strip().lower()).strip("-")
    return base or "organization"


def _cookie_max_age(expires_in: int | None) -> int:
    return max(int(expires_in or 0), 60 * 60)


def _set_auth_cookie(response: Response, access_token: str, expires_in: int | None) -> None:
    response.set_cookie(
        key=session_cookie_name,
        value=access_token,
        httponly=True,
        secure=_is_secure_cookie(),
        samesite="lax",
        max_age=_cookie_max_age(expires_in),
        path="/",
    )


def _extract_user_id_from_token(access_token: str) -> str:
    try:
        payload = jwt.decode(
            access_token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
            },
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token.",
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is missing a user identifier.",
        )
    return str(user_id)


def _database_setup_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Supabase multi-tenant schema is not ready: {exc}",
    )


def _first_row(data: Any) -> dict[str, Any] | None:
    if isinstance(data, list):
        return data[0] if data else None
    return data if isinstance(data, dict) else None


def _generate_unique_org_slug(company_name: str) -> str:
    base_slug = _slugify_company_name(company_name)
    slug = base_slug
    counter = 1

    while True:
        try:
            response = (
                supabase_admin.table("tenants")
                .select("id")
                .eq("slug", slug)
                .limit(1)
                .execute()
            )
        except APIError as exc:
            raise _database_setup_error(exc) from exc

        if not response.data:
            return slug

        counter += 1
        slug = f"{base_slug}-{counter}"


def _load_user_membership(user_id: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    try:
        user_response = (
            supabase_admin.table("profiles")
            .select("id, tenant_id, email, name, organization_name, role, created_at")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
    except APIError as exc:
        raise _database_setup_error(exc) from exc

    user_record = _first_row(user_response.data)
    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not provisioned for a Midnight organization.",
        )

    tenant_id = user_record.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is missing a tenant assignment.",
        )

    try:
        org_response = (
            supabase_admin.table("tenants")
            .select("id, slug, name, industry, region, employee_count, plan_type, created_at")
            .eq("id", tenant_id)
            .limit(1)
            .execute()
        )
    except APIError as exc:
        raise _database_setup_error(exc) from exc

    organization = _first_row(org_response.data)
    return user_record, organization


def _build_session_payload(
    *,
    authenticated: bool,
    user_record: dict[str, Any] | None = None,
    organization: dict[str, Any] | None = None,
    auth_user: Any | None = None,
) -> dict[str, Any]:
    email = (user_record or {}).get("email") or getattr(auth_user, "email", None)
    user_name = (user_record or {}).get("name")
    metadata_name = None
    if auth_user is not None and getattr(auth_user, "user_metadata", None):
        metadata_name = auth_user.user_metadata.get("name")

    display_name = _normalize_display_name(user_name or metadata_name, email)
    role = str((user_record or {}).get("role") or "owner").replace("_", " ").title()
    tenant_id = (user_record or {}).get("tenant_id")
    organization_name = (
        (organization or {}).get("name")
        or (user_record or {}).get("organization_name")
        or "Midnight Workspace"
    )

    return {
        "authenticated": authenticated,
        "workspace_id": tenant_id,
        "user_id": (user_record or {}).get("id") or getattr(auth_user, "id", None),
        "tenant_id": tenant_id,
        "org_id": tenant_id,
        "org_slug": (organization or {}).get("slug"),
        "email": email,
        "display_name": display_name,
        "organization_name": organization_name,
        "role": role,
        "environment": settings.ENVIRONMENT,
    }


def _authenticate_token(access_token: str) -> tuple[dict[str, Any], dict[str, Any], Any]:
    try:
        auth_user_response = supabase.auth.get_user(access_token)
    except AuthApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Supabase session.",
        ) from exc

    auth_user = getattr(auth_user_response, "user", None)
    if auth_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to validate Supabase session.",
        )

    token_user_id = _extract_user_id_from_token(access_token)
    if str(auth_user.id) != token_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token user does not match validated user.",
        )

    user_record, organization = _load_user_membership(token_user_id)
    return user_record, organization, auth_user


def verify_access(request: Request) -> dict[str, Any]:
    access_token = request.cookies.get(session_cookie_name, "").strip()
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    user_record, organization, auth_user = _authenticate_token(access_token)
    auth_context = _build_session_payload(
        authenticated=True,
        user_record=user_record,
        organization=organization,
        auth_user=auth_user,
    )
    request.state.access_token = access_token
    request.state.user_id = auth_context["user_id"]
    request.state.tenant_id = auth_context["tenant_id"]
    request.state.org_id = auth_context["tenant_id"]
    request.state.org_slug = auth_context["org_slug"]
    request.state.user_email = auth_context["email"]
    request.state.auth_context = auth_context
    return auth_context


@app.post("/auth/login")
async def login(payload: LoginRequest, response: Response):
    try:
        auth_response = supabase.auth.sign_in_with_password(
            {
                "email": payload.email.strip().lower(),
                "password": payload.password,
            }
        )
    except AuthApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        ) from exc

    session = auth_response.session
    auth_user = auth_response.user
    if session is None or auth_user is None or not session.access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase did not return a valid session.",
        )

    user_record, organization = _load_user_membership(str(auth_user.id))
    _set_auth_cookie(response, session.access_token, session.expires_in)

    return {
        **_build_session_payload(
            authenticated=True,
            user_record=user_record,
            organization=organization,
            auth_user=auth_user,
        ),
        "access_token": session.access_token,
        "redirect_to": "/",
    }


@app.post("/auth/signup")
async def signup(payload: SignupRequest, response: Response):
    try:
        auth_response = supabase.auth.sign_up(
            {
                "email": payload.email.strip().lower(),
                "password": payload.password,
                "options": {
                    "data": {
                        "name": (payload.name or "").strip(),
                        "company_name": payload.company_name.strip(),
                    }
                },
            }
        )
    except AuthApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    auth_user = auth_response.user
    if auth_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase signup did not return a user.",
        )

    org_slug = _generate_unique_org_slug(payload.company_name)

    try:
        org_response = (
            supabase_admin.table("tenants")
            .insert(
                {
                    "slug": org_slug,
                    "name": payload.company_name.strip(),
                    "industry": (payload.industry or "").strip() or None,
                    "region": (payload.region or "").strip() or None,
                    "employee_count": (payload.employee_count or "").strip() or None,
                    "plan_type": "trial",
                }
            )
            .execute()
        )
        organization = _first_row(org_response.data)
        if not organization or not organization.get("id"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Organization record was not created.",
            )

        user_response = (
            supabase_admin.table("profiles")
            .insert(
                {
                    "id": str(auth_user.id),
                    "tenant_id": organization["id"],
                    "email": payload.email.strip().lower(),
                    "name": (payload.name or "").strip() or None,
                    "organization_name": payload.company_name.strip(),
                    "role": "owner",
                }
            )
            .execute()
        )
        user_record = _first_row(user_response.data) or {
            "id": str(auth_user.id),
            "tenant_id": organization["id"],
            "email": payload.email.strip().lower(),
            "name": (payload.name or "").strip() or None,
            "organization_name": payload.company_name.strip(),
            "role": "owner",
        }

        (
            supabase_admin.table("onboarding_sessions")
            .insert(
                {
                    "tenant_id": organization["id"],
                    "current_step": "plan",
                    "progress": 0,
                    "completed": False,
                }
            )
            .execute()
        )
    except APIError as exc:
        raise _database_setup_error(exc) from exc

    session = auth_response.session
    if session and session.access_token:
        _set_auth_cookie(response, session.access_token, session.expires_in)

    return {
        **_build_session_payload(
            authenticated=bool(session and session.access_token),
            user_record=user_record,
            organization=organization,
            auth_user=auth_user,
        ),
        "access_token": session.access_token if session else None,
        "awaiting_confirmation": session is None,
        "redirect_to": "/onboarding/plan",
    }


@app.post("/auth/logout")
async def logout(request: Request, response: Response):
    access_token = request.cookies.get(session_cookie_name, "").strip()
    if access_token:
        try:
            supabase.auth.admin.sign_out(access_token, "global")
        except AuthApiError:
            pass

    response.delete_cookie(
        session_cookie_name,
        samesite="lax",
        path="/",
    )
    return {"authenticated": False}


@app.get("/auth/session")
async def session_status(request: Request):
    access_token = request.cookies.get(session_cookie_name, "").strip()
    if not access_token:
        return _build_session_payload(authenticated=False)

    try:
        user_record, organization, auth_user = _authenticate_token(access_token)
    except HTTPException:
        return _build_session_payload(authenticated=False)

    return _build_session_payload(
        authenticated=True,
        user_record=user_record,
        organization=organization,
        auth_user=auth_user,
    )


from backend.api.routes import router as pipeline_router
from backend.api.assessments import router as assessments_router
from backend.api.dashboard import router as dashboard_router
from backend.api.smart_scan import router as smart_scan_router

app.include_router(assessments_router)
app.include_router(pipeline_router, dependencies=[Depends(verify_access)])
app.include_router(dashboard_router, dependencies=[Depends(verify_access)])
app.include_router(smart_scan_router, dependencies=[Depends(verify_access)])


@app.get("/")
async def root():
    return RedirectResponse(url="/index.html")


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
