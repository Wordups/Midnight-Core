# Suspected PHI Breach Runbook

**Document Type:** Runbook
**Variant:** Modern — Scannable, plain-language, modern enterprise. Short paragraphs, clear headings, designed for readability.

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

## Incident Type and Scope

You think PHI got accessed, disclosed, or copied in a way it shouldn't have. This is the runbook for that, one or one million records. Same procedure either way.

## Detection Criteria

Start the runbook if:

- Someone on the workforce reports something that smells off.
- Security tooling alerts on weird access patterns near PHI systems.
- A customer tells you there's a problem.
- A subprocessor reports an incident affecting our customer data.
- You stumble across something during normal work (misconfigured bucket, log of leaked access, etc.).

## Severity Classification

| Severity | Looks Like | Speed |
| --- | --- | --- |
| Sev-1 | Confirmed unauthorized PHI access, public exposure, or 500+ affected. | Page immediately. Outside counsel < 4 hrs. Customer notify < 24 hrs. |
| Sev-2 | Likely impermissible disclosure or PHI access outside permitted scope; fewer than 500. | Engage within 1 business hour. Counsel consult < 24 hrs. |
| Sev-3 | Possible impermissible disclosure with real uncertainty; single record or near-miss. | Engage within 4 business hours. |
| Sev-4 | Confirmed non-event. De-identified. Documented only. | No active response. |

## Response Steps

### Hour 0 — Get the team

1. On-call acknowledges within 15 minutes (business hours) / 1 hour (after).
2. Designate Incident Commander. Default: Head of Engineering as HIPAA Security Officer.
3. Open a Slack incident channel. All comms there.
4. Pull in: Privacy Officer, Legal, Communications, on-call tech responder.
5. Set initial severity. Record it.

### Hours 1-4 — Contain and triage

1. Identify affected systems and dataset. Preserve evidence (logs, snapshots).
2. Take containment actions: revoke access, isolate systems, rotate credentials.
3. Sev-1/Sev-2: Legal engages outside counsel.
4. Privacy Officer starts the four-factor risk assessment (45 CFR 164.402(2)).

### Hours 4-24 — Investigate

1. Continue evidence collection. Hash and timestamp everything.
2. Work through the four factors: nature of PHI, recipient, was it actually viewed, mitigation.
3. Communications drafts the customer notification; Legal reviews.
4. Incident Commander updates Approver and the affected customer within 24 hours.

### 24+ hours — Notify and recover

1. If the four-factor says it's a Breach: notify the customer per the BAA timeline (often 5 business days; some BAAs say 24-72 hours).
2. Coordinate any state-level notification with Legal.
3. Recovery in parallel: restore systems, reissue credentials, support customer remediation.
4. Close only when containment + notification + recovery are all documented complete.

## Communication Plan

Internal: every update in the incident channel. Approver gets a written summary at hour 1, hour 24, on any severity change, and at closure. External: CEO authorizes; Legal reviews; Communications Lead logs every notification (date, recipient, channel).

## Escalation Path

- Sev-1/Sev-2 → Approver within 1 hour.
- 500+ affected → Board rep within 24 hours.
- Regulatory inquiry or legal hold → Legal immediately, outside counsel within 4 hours.
- Subprocessor involved → Subprocessor Incident Procedure kicks in.

## Post-Incident Review Checklist

Within 15 business days of close. Incident Commander runs the meeting. Produces a Post-Incident Report covering:

- Timeline (detection → declaration → containment → notification → close).
- Root cause and contributing factors.
- What controls worked, what didn't, what was missing.
- Customer impact (individuals affected, PHI categories, notifications delivered).
- Regulator and contractual notifications.
- Remediation owners and dates.
- Updates to this runbook, the IR Plan, or related policies.


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
