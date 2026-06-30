"""
Midnight — transactional email.

Thin wrapper over Resend's REST API. If RESEND_API_KEY is not set the functions
are honest no-ops that log and return False — nothing is faked, and callers
degrade gracefully (e.g. an invite is still created; the email just isn't sent).

Configure via environment (Render / ECS task def / .env):
    RESEND_API_KEY   the Resend API key
    EMAIL_FROM       e.g. "Midnight <noreply@yourdomain.com>"
    APP_BASE_URL     e.g. "https://app.midnight..." (used to build links)
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger("midnight.email")

_RESEND_ENDPOINT = "https://api.resend.com/emails"


def is_configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY", "").strip())


def app_base_url() -> str:
    return os.getenv("APP_BASE_URL", "").rstrip("/")


def send_email(*, to: str, subject: str, html: str) -> bool:
    """Send one transactional email. Returns True on success, False otherwise
    (including when email is not configured). Never raises."""
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    if not api_key:
        logger.warning("email_not_configured", extra={"to": to, "subject": subject})
        return False

    sender = os.getenv("EMAIL_FROM", "").strip() or "Midnight <onboarding@resend.dev>"
    try:
        resp = httpx.post(
            _RESEND_ENDPOINT,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": sender, "to": [to], "subject": subject, "html": html},
            timeout=15.0,
        )
        if resp.status_code >= 300:
            logger.warning("email_send_failed", extra={"to": to, "status": resp.status_code, "body": resp.text[:500]})
            return False
        return True
    except Exception:
        logger.exception("email_send_error", extra={"to": to})
        return False


def _wrap(title: str, body_html: str) -> str:
    return f"""\
<div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;color:#1b2433">
  <div style="background:#10131a;color:#fff;padding:16px 20px;font-weight:700;letter-spacing:.08em">MIDNIGHT</div>
  <div style="padding:24px 20px;line-height:1.6;font-size:14px">
    <h2 style="font-size:18px;margin:0 0 12px">{title}</h2>
    {body_html}
  </div>
  <div style="padding:14px 20px;color:#6b7280;font-size:11px;border-top:1px solid #e5e7eb">
    Midnight — compliance program management. You received this because someone invited you or assigned you work.
  </div>
</div>"""


def send_invite_email(*, to: str, org_name: str, accept_url: str) -> bool:
    body = (
        f"<p>You've been invited to join <strong>{org_name}</strong> on Midnight as a subject-matter expert.</p>"
        f"<p><a href=\"{accept_url}\" style=\"display:inline-block;background:#10131a;color:#fff;"
        f"text-decoration:none;padding:10px 18px;border-radius:8px\">Accept invitation</a></p>"
        f"<p style=\"color:#6b7280;font-size:12px\">This link expires in 7 days.</p>"
    )
    return send_email(to=to, subject=f"You're invited to {org_name} on Midnight", html=_wrap("You've been invited", body))


def send_task_assigned_email(*, to: str, title: str, description: str, due_date: str | None, link: str) -> bool:
    due = f"<p><strong>Due:</strong> {due_date}</p>" if due_date else ""
    body = (
        f"<p>A task has been assigned to you:</p><p><strong>{title}</strong></p>"
        f"<p>{description or ''}</p>{due}"
        f"<p><a href=\"{link}\" style=\"display:inline-block;background:#10131a;color:#fff;"
        f"text-decoration:none;padding:10px 18px;border-radius:8px\">View task</a></p>"
    )
    return send_email(to=to, subject=f"New task: {title}", html=_wrap("A task was assigned to you", body))


def send_task_complete_email(*, to: str, title: str, link: str) -> bool:
    body = (
        f"<p>The following task was marked complete:</p><p><strong>{title}</strong></p>"
        f"<p><a href=\"{link}\" style=\"display:inline-block;background:#10131a;color:#fff;"
        f"text-decoration:none;padding:10px 18px;border-radius:8px\">Review it</a></p>"
    )
    return send_email(to=to, subject=f"Task complete: {title}", html=_wrap("A task was completed", body))
