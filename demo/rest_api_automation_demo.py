#!/usr/bin/env python3
"""
Midnight — REST-API automation demo
===================================

Shows the end-to-end automation the platform runs against Jira Cloud's REST
API v3: a detected compliance gap is turned into a tracked remediation issue,
then its status is read back — the same code path that runs in production.

It drives the REAL production client (backend/integrations/jira_client.py). By
default it points that client at an in-process mock of Jira (httpx
MockTransport), so it runs with NO credentials and NO network — clone and go:

    python demo/rest_api_automation_demo.py

To fire it at a real Jira instead (creates an actual ticket):

    JIRA_SITE_URL=https://you.atlassian.net JIRA_EMAIL=you@co.com \
    JIRA_API_TOKEN=xxxx JIRA_PROJECT_KEY=GRC \
    python demo/rest_api_automation_demo.py --live
"""
from __future__ import annotations

import json
import os
import sys

import httpx

# Import the production client — this demo does not reimplement anything.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.integrations.jira_client import JiraClient, JiraConfig  # noqa: E402


# ── a detected compliance gap (what the corpus/assessment engine emits) ──────
GAP = {
    "control_id": "SOC2-CC6.1",
    "framework": "SOC 2",
    "severity": "High",
    "document_id": "PFI-SEC-014",
    "title": "Enforce MFA on all administrative access paths",
    "finding": (
        "The evidence corpus contains no proof that multi-factor authentication "
        "is enforced on administrative/privileged remote access. CC6.1 requires "
        "MFA on every path that reaches production systems."
    ),
    "remediation": (
        "- Enforce MFA (passkey or TOTP) on the IdP for all admin roles.\n"
        "- Disable password-only fallback for privileged accounts.\n"
        "- Attach the enforcement config export as evidence to the corpus."
    ),
}


def build_summary(gap: dict) -> str:
    return f"[{gap['control_id']}] {gap['title']}"


def build_description(gap: dict) -> str:
    return (
        f"Source: Midnight Core — compliance gap\n"
        f"Document ID: {gap['document_id']}\n"
        f"Framework / Control: {gap['framework']} {gap['control_id']}\n"
        f"Severity: {gap['severity']}\n\n"
        f"Finding\n{gap['finding']}\n\n"
        f"Suggested remediation\n{gap['remediation']}"
    )


def build_labels(gap: dict) -> list[str]:
    return ["midnight", "gap-remediation", gap["framework"],
            f"severity-{gap['severity'].lower()}"]


# ── in-process mock of Jira Cloud (only used when not --live) ────────────────
def mock_jira() -> httpx.MockTransport:
    created: dict[str, dict] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/myself"):
            return httpx.Response(200, json={
                "accountId": "mock-123", "emailAddress": "demo@midnightgrc.com",
                "displayName": "Midnight Demo"})
        if path.endswith("/issue") and request.method == "POST":
            body = json.loads(request.content)
            key = "MS-DEMO-1"
            created[key] = body["fields"]
            return httpx.Response(201, json={"key": key, "id": "10001"})
        if "/issue/" in path and request.method == "GET":
            key = path.rsplit("/", 1)[-1]
            fields = created.get(key, {})
            return httpx.Response(200, json={"fields": {
                "summary": fields.get("summary"),
                "status": {"name": "To Do", "statusCategory": {"key": "new"}}}})
        return httpx.Response(404, json={"errorMessages": ["not found"]})

    return httpx.MockTransport(handler)


# ── pretty output ────────────────────────────────────────────────────────────
def h(text): print(f"\n\033[1;35m{text}\033[0m")          # magenta bold
def ok(text): print(f"  \033[32m✓\033[0m {text}")          # green check
def dim(text): print(f"  \033[2m{text}\033[0m")            # dim
def arrow(text): print(f"\033[36m→\033[0m {text}")          # cyan arrow


def main() -> int:
    live = "--live" in sys.argv
    h("Midnight — REST-API automation demo")
    dim("Detected compliance gap  →  Jira REST API v3  →  tracked remediation issue")

    if live:
        config = JiraConfig(
            site_url=os.environ["JIRA_SITE_URL"], email=os.environ["JIRA_EMAIL"],
            api_token=os.environ["JIRA_API_TOKEN"],
            project_key=os.environ.get("JIRA_PROJECT_KEY", "GRC"))
        client = JiraClient(config)   # real network
        dim(f"MODE: LIVE — creating a real ticket in {config.project_key} on {config.normalized_site()}")
    else:
        config = JiraConfig(site_url="https://demo.atlassian.net", email="demo@x.co",
                            api_token="demo-token", project_key="GRC")
        client = JiraClient(config, transport=mock_jira())  # in-process mock
        dim("MODE: MOCK — no credentials, no network (in-process Jira)")

    # 1. connection check (GET /rest/api/3/myself)
    h("1. Authenticate against the REST API")
    who = client.test_connection()
    ok(f"Connected as {who['display_name']} <{who['email']}>")

    # 2. show the gap the assessment engine surfaced
    h("2. A gap the evidence engine surfaced (fails closed on missing proof)")
    arrow(f"{GAP['control_id']} · {GAP['framework']} · severity {GAP['severity']}")
    dim(GAP["finding"])

    # 3. build + POST the issue (POST /rest/api/3/issue, ADF body)
    h("3. Automate it into a Jira issue (POST /rest/api/3/issue)")
    payload_preview = {
        "summary": build_summary(GAP),
        "labels": [x.replace(" ", "-") for x in build_labels(GAP)],
        "description": "<ADF document built from the finding + remediation>",
    }
    dim("payload (fields):")
    for line in json.dumps(payload_preview, indent=2).splitlines():
        dim("  " + line)
    issue = client.create_issue(
        summary=build_summary(GAP), description=build_description(GAP),
        labels=build_labels(GAP))
    ok(f"Created {issue['key']}  →  {issue['url']}")

    # 4. read status back (GET /rest/api/3/issue/{key})
    h("4. Read remediation status back (GET /rest/api/3/issue/{key})")
    status = client.get_issue_status(issue["key"])
    ok(f"{status['key']} is '{status['status']}'  (done={status['done']})")

    h("Done.")
    dim("Same client code runs in production: backend/integrations/jira_client.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
