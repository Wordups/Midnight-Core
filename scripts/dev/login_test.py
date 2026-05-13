"""Probe: hit Supabase's password-grant auth endpoint to verify SUPABASE_URL/KEY are wired.

Reads credentials from env (TEST_LOGIN_EMAIL / TEST_LOGIN_PASSWORD). Do not hardcode.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

email = os.getenv("TEST_LOGIN_EMAIL")
password = os.getenv("TEST_LOGIN_PASSWORD")
if not email or not password:
    raise SystemExit("Set TEST_LOGIN_EMAIL and TEST_LOGIN_PASSWORD in your env or .env to run this probe.")

url = f"{os.getenv('SUPABASE_URL')}/auth/v1/token?grant_type=password"

res = requests.post(
    url,
    headers={
        "apikey": os.getenv("SUPABASE_KEY"),
        "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}",
        "Content-Type": "application/json",
    },
    json={"email": email, "password": password},
)

print(res.status_code)
print(res.text)
