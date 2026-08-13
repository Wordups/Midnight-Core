# Suspected PHI Breach Runbook

**Document Type:** Runbook
**Variant:** Formal — Legalese voice, full structure, traditional enterprise. The template a Fortune 500 General Counsel would approve.

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

## 1. Incident Type and Scope

This Runbook applies to any incident in which Protected Health Information ("PHI") under the custody or control of {{ORGANIZATION_NAME}} ("Organization") has, or may have, been used, disclosed, accessed, acquired, modified, or destroyed in a manner not permitted under the HIPAA Privacy Rule, the Organization's Business Associate Agreements, or applicable law. The Runbook applies whether the suspected impermissible event involves a single record or a population of records.

## 2. Detection Criteria

The following signals shall trigger initiation of this Runbook:

1. A workforce report submitted through any approved channel describing facts that may constitute an impermissible use or disclosure of PHI.
2. A monitoring alert from the Organization's security tooling indicating possible unauthorized access to a system holding PHI, including authentication anomalies, data exfiltration signatures, and anomalous query patterns.
3. A customer notification alleging that the Organization's actions or omissions resulted in an impermissible use or disclosure.
4. A subprocessor notification reporting a security incident affecting PHI processed on the Organization's behalf.
5. Discovery, in the course of routine operations, of a previously unrecognized condition that may constitute an impermissible use or disclosure.

## 3. Severity Classification

Upon initiation, the Incident Commander shall classify the incident at one of the following severities, which classification may be adjusted as facts develop.

| Severity | Criteria | Response |
| --- | --- | --- |
| Sev-1 | Confirmed unauthorized access to or acquisition of PHI; or public exposure of PHI; or PHI loss affecting 500 or more individuals. | Immediate paging. Outside counsel engaged within 4 hours. Customer notification within 24 hours. |
| Sev-2 | Reasonable likelihood of impermissible disclosure; or PHI access by individual outside permitted scope; or affecting fewer than 500 individuals. | Engaged within 1 business hour. Outside counsel consultation within 24 hours. |
| Sev-3 | Possible impermissible disclosure with material uncertainty; or single-record or near-miss event. | Engaged within 4 business hours. |
| Sev-4 | Confirmed non-event or fully de-identified data; documented for record only. | Documented; no active response required. |

## 4. Response Steps

### 4.1 T+0 to T+1 Hour — Initiation

1. The on-call security responder shall acknowledge the alert or report within fifteen (15) minutes during business hours and within one (1) hour after business hours.
2. The Incident Commander shall be designated. By default this role is held by the Head of Engineering acting as HIPAA Security Officer; an alternate may be designated in writing.
3. A dedicated incident channel (Slack or equivalent) shall be opened. All material communications during the incident shall occur in this channel.
4. The Incident Commander shall convene the response team: HIPAA Privacy Officer, Legal, Communications Lead, and the on-call technical responder.
5. Initial severity classification shall be recorded in the incident ticket.

### 4.2 T+1 to T+4 Hours — Triage and Containment

1. The technical responder, under direction of the Incident Commander, shall identify the affected systems and the in-scope dataset, taking care to preserve evidence (logs, snapshots, memory captures where applicable).
2. Immediate containment actions shall be taken to halt any ongoing impermissible activity. Actions may include access revocation, system isolation, credential rotation, and emergency change deployment.
3. For Sev-1 and Sev-2 incidents, Legal shall engage outside counsel to advise on breach notification timing and content. The engagement shall be documented and the privilege noted on incident communications.
4. The HIPAA Privacy Officer shall begin the four-factor risk assessment under 45 CFR 164.402(2).

### 4.3 T+4 to T+24 Hours — Investigation

1. Evidence collection shall continue under chain-of-custody discipline. All evidence shall be hashed and time-stamped upon collection.
2. The four-factor risk assessment shall progress, with documented evaluation of: (i) the nature and extent of the PHI involved; (ii) the recipient of the impermissible disclosure; (iii) whether the PHI was actually acquired or viewed; and (iv) the extent to which the risk has been mitigated.
3. A draft customer notification shall be prepared by the Communications Lead with Legal review.
4. The Incident Commander shall provide an update to the Approver and to the affected customer's primary contact within twenty-four (24) hours of incident declaration.

### 4.4 T+24 Hours and Beyond — Notification and Recovery

1. For incidents determined by the four-factor risk assessment to constitute a Breach under 45 CFR 164.402, customer notification shall be made within the timeframe specified by the applicable Business Associate Agreement (typically within five business days; some agreements require notification within 24 to 72 hours).
2. For incidents affecting customer data subject to state-level breach notification statutes, the Communications Lead shall coordinate with Legal on state-specific notification obligations.
3. Recovery activities (system restoration, credential reissuance, customer support remediation) shall proceed in parallel with notification activities.
4. The Incident Commander shall close the incident ticket only when all containment, notification, and recovery activities are documented as complete.

## 5. Communication Plan

### 5.1 Internal Communications

All material updates shall be posted to the dedicated incident channel by the Incident Commander or a designated scribe. The Approver shall receive a written summary at: (i) one hour after declaration; (ii) twenty-four hours after declaration; (iii) at material changes in scope or severity; and (iv) at closure.

### 5.2 External Communications

All external communications shall be authorized by the CEO and reviewed by Legal before release. The Communications Lead shall maintain the customer-notification log, including the date and time of each notification, the recipient, the channel, and the content (by reference).

## 6. Escalation Path

1. Sev-1 and Sev-2 incidents shall be escalated to the Approver within one (1) hour of declaration.
2. Any incident involving five hundred (500) or more individuals shall be escalated to the Board of Directors representative within twenty-four (24) hours of identification.
3. Any incident involving potential regulatory inquiry, governmental investigation, or third-party legal hold shall be escalated to Legal immediately, with outside counsel engaged within four (4) hours of identification.
4. Any incident involving a subprocessor shall trigger the Subprocessor Incident Procedure, including the right-to-audit provisions of the applicable Business Associate Subcontractor Agreement.

## 7. Post-Incident Review Checklist

Within fifteen (15) business days of incident closure, the Incident Commander shall convene a post-incident review meeting and produce a Post-Incident Report covering at minimum:

1. Incident timeline, including detection, declaration, containment, notification, and closure events with timestamps.
2. Root cause analysis, distinguishing immediate cause from contributing causes.
3. Effectiveness review: which controls operated as intended, which did not, which were absent.
4. Customer impact: number of affected individuals, categories of PHI involved, notifications delivered.
5. Regulatory and contractual notifications made.
6. Remediation actions, owners, and target completion dates.
7. Lessons learned and updates required to this Runbook, the Incident Response Plan, or related policies.


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
