# Suspected PHI Breach Runbook

**Document Type:** Runbook
**Variant:** Executive — One-page brief style, decision-maker focused, high-density. Shows up in board packs.

---

## Cover Page

[LOGO: organization_logo.png] *(centered, 2" × 2")*

**Suspected PHI Breach Runbook** — {{DOCUMENT_TITLE}}

| Field | Value |
| --- | --- |
| Version | {{VERSION}} |
| Effective Date | {{EFFECTIVE_DATE}} |
| Owner | {{POLICY_OWNER}} |
| Approver | {{APPROVER_NAME}}, {{APPROVER_TITLE}} |
| Classification | {{CLASSIFICATION}} |

---

## Document Control

| Version | Date | Description of Changes | Author |
| --- | --- | --- | --- |
| 1.0 | {{EFFECTIVE_DATE}} | Initial issuance. | {{AUTHOR_NAME}} |

## Table of Contents

*(In the .docx version, this is auto-generated. Re-render by right-clicking the table and selecting "Update Field" in Word.)*

## Suspected PHI Breach Runbook — At a Glance

- **Applies to: **Any incident where PHI may have been used or disclosed outside our BAA scope.
- **What it does: **Phased response: initiate, contain, investigate, notify, recover, review.
- **Why it matters: **BAA breach windows are often 24-72 hours. Miss them and we owe the customer (and OCR) an explanation.
- **Owner: **{{POLICY_OWNER}} | Drilled annually | Next review: {{NEXT_REVIEW_DATE}}

## Severity

| Sev | When | Response |
| --- | --- | --- |
| 1 | Confirmed PHI access outside scope, or 500+ affected, or public exposure. | Page immediately. Outside counsel < 4 hrs. Customer notify < 24 hrs. |
| 2 | Likely impermissible disclosure, < 500 affected. | Engage < 1 business hour. Counsel consult < 24 hrs. |
| 3 | Possible impermissible disclosure with real uncertainty, or near-miss. | Engage < 4 business hours. |
| 4 | Confirmed non-event. Document only. | No active response. |

## Phases

1. **T+0 to T+1h: **Acknowledge, designate Incident Commander, open channel, convene team, set severity.
2. **T+1 to T+4h: **Identify, preserve evidence, contain. Sev-1/2: outside counsel engaged.
3. **T+4 to T+24h: **Investigate; four-factor risk assessment under 45 CFR 164.402(2); draft notifications.
4. **T+24h+: **Notify per BAA timeline (often 24-72 hrs). Recover in parallel. Close when all complete.

## Escalation

- Sev-1/2 → Approver within 1 hour.
- 500+ affected → Board rep within 24 hours.
- Regulator inquiry → Legal immediately; outside counsel within 4 hours.
- Subprocessor involved → Subprocessor Incident Procedure invoked.

## Post-Incident Review

Within 15 business days of close: timeline, root cause, control effectiveness, customer impact, notifications, remediation owners. Signed by Incident Commander, Privacy Officer, Legal.


## Roles and Responsibilities

| Role | Responsibilities |
| --- | --- |
| Runbook Owner ({{POLICY_OWNER}}) | Maintains this Runbook, schedules drills, and incorporates post-incident lessons learned. |
| Incident Commander | Single decision-maker during the incident. Coordinates the response and authorizes communications. |
| HIPAA Privacy Officer | Engaged for every suspected PHI incident; signs off on the four-factor risk assessment. |
| HIPAA Security Officer | Coordinates technical investigation, evidence collection, and containment. |
| Legal | Engaged at incident declaration. Manages outside-counsel engagement, regulator communications, and customer-notification language. |
| Communications Lead | Drafts internal and external communications. Coordinates with the customer affected by the incident. |

## Review and Maintenance

**Next review date:** {{NEXT_REVIEW_DATE}}

**Review frequency:** Annually, after each Sev-1 or Sev-2 incident, and upon material change to the Breach Notification Rule.

**Review triggers:**

- A material change in applicable laws, regulations, or contractual obligations.
- Findings from an internal or external audit that affect this document.
- A security or privacy incident that exposes a gap in the document.
- An organizational change (acquisition, divestiture, new business line) that affects scope.

## Related Documents

- Incident Response Plan
- Breach Notification Policy
- HIPAA Privacy Policy
- HIPAA Security Policy

## Approval Signatures

This document becomes effective upon execution by both signatories below.

### Policy Owner

Approved by:

________________________________

{{POLICY_OWNER}}

{{POLICY_OWNER_TITLE}}

Date: ____________________

### Approver

Approved by:

________________________________

{{APPROVER_NAME}}

{{APPROVER_TITLE}}

Date: ____________________
