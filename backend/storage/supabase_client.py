"""
Midnight Core - Supabase client initialization.
Takeoff LLC
"""
from config import settings
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions


def _build_client(api_key: str) -> Client:
    return create_client(
        settings.SUPABASE_URL,
        api_key,
        options=ClientOptions(
            persist_session=False,
            auto_refresh_token=False,
        ),
    )


# Shared client for user-facing auth flows.
supabase: Client = _build_client(settings.SUPABASE_ANON_KEY)

# Shared admin client for privileged server-side operations.
supabase_admin: Client = _build_client(settings.SUPABASE_SERVICE_ROLE_KEY)
