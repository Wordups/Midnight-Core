"""Probe: list Supabase auth users via the admin API to verify the service-role key works."""
import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
)

res = supabase.auth.admin.list_users()
print(res)
