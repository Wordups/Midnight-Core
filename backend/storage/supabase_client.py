"""
Midnight Core - lightweight Supabase REST client wrappers.

The installed supabase-py stack in this repo is currently brittle with the
available httpx/gotrue versions, so Phase 1 auth and membership lookups are
wrapped through direct HTTPS calls instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
import json

import requests
from gotrue.errors import AuthApiError, ErrorCode

from config import settings


def _base_headers(api_key: str, *, json_body: bool = True) -> dict[str, str]:
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
    }
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def _auth_headers(access_token: str | None = None) -> dict[str, str]:
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _raise_auth_error(response: requests.Response) -> None:
    try:
        payload = response.json()
    except ValueError:
        payload = {"message": response.text or "Unexpected Supabase auth error."}
    message = payload.get("msg") or payload.get("message") or "Supabase auth request failed."
    code = payload.get("code") or "unexpected_failure"
    raise AuthApiError(message, response.status_code, code)  # type: ignore[arg-type]


def _coerce_user(data: dict[str, Any] | None) -> SimpleNamespace | None:
    if not data:
        return None
    return SimpleNamespace(**data)


@dataclass
class SessionData:
    access_token: str
    refresh_token: str | None
    expires_in: int | None
    expires_at: int | None = None
    token_type: str | None = None
    user: Any | None = None


@dataclass
class AuthResponseData:
    user: Any | None
    session: SessionData | None


@dataclass
class QueryResult:
    data: Any


class TableQuery:
    def __init__(self, client: "SupabaseRestClient", table_name: str):
        self._client = client
        self._table_name = table_name
        self._params: dict[str, str] = {}
        self._payload: Any = None
        self._method = "GET"
        self._prefer = "return=representation"

    def select(self, columns: str) -> "TableQuery":
        self._method = "GET"
        self._params["select"] = columns
        return self

    def eq(self, column: str, value: Any) -> "TableQuery":
        self._params[column] = f"eq.{value}"
        return self

    def limit(self, value: int) -> "TableQuery":
        self._params["limit"] = str(value)
        return self

    def insert(self, payload: Any) -> "TableQuery":
        self._method = "POST"
        self._payload = payload
        return self

    def update(self, payload: Any) -> "TableQuery":
        self._method = "PATCH"
        self._payload = payload
        return self

    def delete(self) -> "TableQuery":
        self._method = "DELETE"
        self._payload = None
        self._prefer = "return=minimal"
        return self

    def execute(self) -> QueryResult:
        data = self._client.request_table(
            method=self._method,
            table_name=self._table_name,
            params=self._params,
            payload=self._payload,
            prefer=self._prefer,
        )
        return QueryResult(data=data)


class AuthAdminClient:
    def sign_out(self, access_token: str, scope: str = "global") -> None:
        response = requests.post(
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/logout?scope={scope}",
            headers=_auth_headers(access_token),
            timeout=30,
        )
        if response.status_code >= 400:
            _raise_auth_error(response)


class AuthClient:
    def __init__(self):
        self.admin = AuthAdminClient()

    def sign_in_with_password(self, credentials: dict[str, Any]) -> AuthResponseData:
        response = requests.post(
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password",
            headers=_auth_headers(),
            json=credentials,
            timeout=30,
        )
        if response.status_code >= 400:
            _raise_auth_error(response)
        payload = response.json()
        user = _coerce_user(payload.get("user"))
        session = SessionData(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_in=payload.get("expires_in"),
            expires_at=payload.get("expires_at"),
            token_type=payload.get("token_type"),
            user=user,
        )
        return AuthResponseData(user=user, session=session)

    def sign_up(self, credentials: dict[str, Any]) -> AuthResponseData:
        response = requests.post(
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/signup",
            headers=_auth_headers(),
            json=credentials,
            timeout=30,
        )
        if response.status_code >= 400:
            _raise_auth_error(response)
        payload = response.json()
        user = _coerce_user(payload.get("user"))
        session = None
        if payload.get("access_token"):
            session = SessionData(
                access_token=payload["access_token"],
                refresh_token=payload.get("refresh_token"),
                expires_in=payload.get("expires_in"),
                expires_at=payload.get("expires_at"),
                token_type=payload.get("token_type"),
                user=user,
            )
        return AuthResponseData(user=user, session=session)

    def get_user(self, access_token: str) -> SimpleNamespace:
        response = requests.get(
            f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
            headers=_auth_headers(access_token),
            timeout=30,
        )
        if response.status_code >= 400:
            _raise_auth_error(response)
        user = _coerce_user(response.json())
        return SimpleNamespace(user=user)


class SupabaseRestClient:
    def __init__(self, *, api_key: str):
        self._api_key = api_key
        self.auth = AuthClient()

    def table(self, table_name: str) -> TableQuery:
        return TableQuery(self, table_name)

    def request_table(
        self,
        *,
        method: str,
        table_name: str,
        params: dict[str, str] | None = None,
        payload: Any = None,
        prefer: str | None = None,
    ) -> Any:
        headers = _base_headers(self._api_key)
        if prefer:
            headers["Prefer"] = prefer
        response = requests.request(
            method,
            f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/{table_name}",
            headers=headers,
            params=params,
            json=payload,
            timeout=30,
        )
        if response.status_code >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = {"message": response.text or "Supabase data request failed."}
            raise Exception(payload)
        if not response.content:
            return None
        return response.json()


supabase = SupabaseRestClient(api_key=settings.SUPABASE_ANON_KEY)
supabase_admin = SupabaseRestClient(api_key=settings.SUPABASE_SERVICE_ROLE_KEY)
