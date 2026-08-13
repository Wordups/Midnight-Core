# Suspected PHI Breach Runbook

**Document Type:** Runbook
**Variant:** Detailed — Comprehensive, long-form, every consideration covered. The template a regulated startup would use to over-prepare.

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

This Runbook applies to any incident in which Protected Health Information under the custody or control of {{ORGANIZATION_NAME}} has, or may have, been used, disclosed, accessed, acquired, modified, or destroyed in a manner not permitted under the HIPAA Privacy Rule, the Organization's Business Associate Agreements with its Covered Entity customers, the Organization's Business Associate Subcontractor Agreements with its subprocessors, or applicable state or federal law. The Runbook applies regardless of whether the incident affects a single record or a population of records, and regardless of whether the impermissible activity has been confirmed or remains suspected pending investigation.

This Runbook is operationalized within the Organization's broader Incident Response Plan. Where this Runbook and the Incident Response Plan conflict, this Runbook governs for incidents involving PHI; the Incident Response Plan governs for all other incidents.

## Detection Criteria

Any of the following signals shall trigger initiation of this Runbook. The on-call security responder is responsible for recognizing the signals and initiating Runbook execution.

1. Workforce reports submitted through any approved channel — security email, dedicated Slack channel, PagerDuty escalation, or formal HR complaint — describing facts that may constitute an impermissible use or disclosure of PHI. Workforce reports shall not be subject to triage delay; the Runbook is initiated upon receipt.
2. Monitoring alerts from the Organization's security tooling indicating possible unauthorized access to a system holding PHI. In-scope alert sources include: authentication-anomaly detections from the identity provider; data-exfiltration signatures from the endpoint detection-and-response solution; anomalous query patterns from database activity monitoring; misconfiguration findings from the cloud security posture management tool; and any other alert specifically tagged as PHI-relevant.
3. Customer notifications alleging that the Organization's actions or omissions resulted in an impermissible use or disclosure. Customer notifications shall be treated as Runbook-initiating regardless of the certainty of the customer's allegation; the four-factor risk assessment is the appropriate vehicle for evaluating the allegation.
4. Subprocessor notifications reporting a security incident or potential breach affecting PHI processed by the subprocessor on the Organization's behalf. Subprocessor notifications shall trigger this Runbook in addition to the Subprocessor Incident Procedure.
5. Discoveries in the course of routine operations — including audit findings, vulnerability scans, code review observations, and operational change reviews — of conditions that may constitute prior or ongoing impermissible use or disclosure.
6. External communications — including security researcher disclosures, media inquiries, and regulator-driven inquiries — that allege or imply a PHI exposure.

## Severity Classification

The Incident Commander shall classify the incident at one of four severities upon initiation and shall reclassify as facts develop. Severity classification drives response cadence, communication obligations, and escalation. The criteria below are guidelines; the Incident Commander applies judgment to specific facts.

| Severity | Criteria | Initial Response | Notification Posture |
| --- | --- | --- | --- |
| Sev-1 | Confirmed unauthorized access to or acquisition of PHI by a party outside the permitted scope; or public exposure of PHI; or any incident affecting 500 or more individuals. | Immediate paging across response team. Outside counsel engaged within 4 hours. | Customer notification within 24 hours. HHS Secretary notification per Breach Notification Rule timelines. |
| Sev-2 | Reasonable likelihood of impermissible disclosure, including PHI access by an internal party outside their permitted scope; or potential breach affecting fewer than 500 individuals. | Engaged within 1 business hour. Outside counsel consultation within 24 hours. | Customer notification per BAA timeline upon Breach determination. |
| Sev-3 | Possible impermissible disclosure with material uncertainty; near-miss events; single-record events with low likelihood of compromise. | Engaged within 4 business hours. | Customer notification only upon Breach determination after four-factor risk assessment. |
| Sev-4 | Confirmed non-event; access fully attributable to authorized scope; fully de-identified data; documented for record only. | Documented in the Incident Register; no active response required. | No external notification. |

## Response Steps

### Phase 1 — T+0 to T+1 Hour (Initiation)

1. The on-call security responder shall acknowledge the alert, report, or notification within fifteen (15) minutes during business hours and within one (1) hour after business hours. Acknowledgement is recorded in the incident-management system.
2. The Incident Commander shall be designated. By default the role is held by the Head of Engineering acting as HIPAA Security Officer; an alternate may be designated in writing in advance, and a delegate may be named for the duration of a specific incident if the default holder is unavailable.
3. A dedicated incident channel shall be opened in the Organization's collaboration platform. The channel name shall follow the convention #inc-YYYY-MMDD-shortname. All material communications during the incident shall occur in this channel.
4. The Incident Commander shall convene the response team, comprising at minimum: the HIPAA Privacy Officer, a Legal representative, the Communications Lead, and the on-call technical responder. Additional roles (Customer Success liaison, third-party forensics, Subprocessor Liaison) shall be added as facts develop.
5. The initial severity classification shall be recorded in the incident ticket with a brief written rationale. The Incident Commander revisits classification at each phase boundary.

### Phase 2 — T+1 to T+4 Hours (Triage and Containment)

1. The technical responder, under direction of the Incident Commander, shall identify the affected systems, the in-scope dataset, the time window of suspected impermissible activity, and the actor or actors potentially involved. Evidence preservation shall begin immediately: relevant logs shall be exported to a tamper-resistant store; system snapshots shall be captured where technically supported; memory captures may be taken on affected endpoints under the direction of forensics counsel.
2. Containment actions shall be authorized by the Incident Commander and executed by the technical responder. Typical actions include: access revocation for any account suspected of impermissible activity; system isolation (network segmentation or shutdown) for systems suspected of containing actor presence; credential rotation for any credentials known to or suspected to have been observed by the actor; emergency change deployment to close any exploited vulnerability.
3. For Sev-1 and Sev-2 incidents, Legal shall engage outside counsel under the privileged-counsel arrangement maintained by the Organization. The engagement shall be documented. All material incident communications produced thereafter shall be marked as Privileged and Confidential and shall be conducted under counsel's direction.
4. The HIPAA Privacy Officer shall begin the four-factor risk assessment under 45 CFR 164.402(2). The assessment shall be documented as it progresses, not solely at conclusion.

### Phase 3 — T+4 to T+24 Hours (Investigation)

1. Evidence collection shall continue under documented chain-of-custody discipline. All evidence shall be hashed (SHA-256) and time-stamped upon collection. A chain-of-custody log shall be maintained, recording for each evidence item: source, collector, collection time, hash, and storage location.
2. The four-factor risk assessment shall progress, with documented evaluation of: (i) the nature and extent of the PHI involved, including the categories of data and the number of records; (ii) the unauthorized person or organization who used the PHI or to whom the disclosure was made; (iii) whether the PHI was actually acquired or viewed; and (iv) the extent to which the risk to the PHI has been mitigated. Each factor shall be supported by specific evidence from the investigation.
3. The Communications Lead shall prepare a draft customer notification, reviewed by Legal. The notification shall include: the date and nature of the incident; the categories of PHI involved; the affected individuals (by count and category, with names provided in accordance with the BAA); the steps the Organization has taken to investigate and mitigate; the steps the customer may wish to take; and the contact for further inquiry.
4. The Incident Commander shall provide a written update to the Approver and to the affected customer's designated primary contact within twenty-four (24) hours of incident declaration. Updates shall be candid about uncertainty: where facts are not yet known, the update shall say so.
5. For Sev-1 incidents and for any incident with potential to affect 500 or more individuals, the Incident Commander shall begin preparation for the HHS Office for Civil Rights notification, even if the four-factor assessment is not yet complete.

### Phase 4 — T+24 Hours and Beyond (Notification and Recovery)

1. For incidents determined by the four-factor risk assessment to constitute a Breach as defined in 45 CFR 164.402, customer notification shall be made within the timeframe specified by the applicable Business Associate Agreement. The Organization's standard BAA specifies five (5) business days; many customer-specific BAAs require notification within twenty-four (24) to seventy-two (72) hours. The shorter timeline governs.
2. For Breaches affecting state-resident data subjects, the Communications Lead shall coordinate with Legal on state-specific notification obligations. State obligations vary substantially; Legal shall maintain a current state-notification matrix.
3. For Breaches affecting 500 or more individuals in a single state or jurisdiction, the Organization shall, where it is the notifying party, provide notification to prominent media outlets in the affected state and to the HHS Secretary within sixty (60) calendar days. Where the Covered Entity is the notifying party, the Organization shall support the Covered Entity's notification activities as required by the BAA.
4. Recovery activities shall proceed in parallel with notification activities. Recovery shall include: restoration of any disrupted service; reissuance of compromised credentials; coordinated remediation with the affected customer; and any product or process change identified during investigation.
5. The Incident Commander shall close the incident ticket only when: containment is verified; the four-factor risk assessment is documented and signed by the HIPAA Privacy Officer; notification obligations are documented as complete; and recovery actions are documented as complete or assigned to a tracked remediation plan with named owners and target dates.

## Communication Plan

### Internal Communications

All material updates shall be posted to the dedicated incident channel by the Incident Commander or a designated incident-channel scribe. The Approver shall receive a written summary at: (i) one hour after declaration; (ii) twenty-four hours after declaration; (iii) at any material change in scope, severity, or notification posture; and (iv) at closure. Summaries shall be marked Privileged and Confidential where outside counsel is engaged.

Where multiple workforce members are coordinating different aspects of the response (technical investigation, customer communication, internal coordination), they shall use distinct sub-channels off the main incident channel, with the Incident Commander syncing across them.

### External Communications

All external communications during the incident shall be authorized by the CEO and reviewed by Legal before release. The Communications Lead shall maintain the External Communications Log, recording for each communication: the date and time of release; the recipient (specific customer contact, regulator, media outlet); the channel (encrypted email, customer success portal, formal letter); a reference to the content (by document identifier); and the recipient's acknowledgement where applicable.

## Escalation Path

1. Sev-1 and Sev-2 incidents shall be escalated to the Approver within one (1) hour of declaration. The escalation shall include the initial severity, the response team composition, the initial containment posture, and the next-update schedule.
2. Any incident affecting five hundred (500) or more individuals shall be escalated to the Board of Directors representative within twenty-four (24) hours of identification, regardless of the four-factor risk assessment outcome.
3. Any incident involving potential regulatory inquiry, governmental investigation, or third-party legal hold shall be escalated to Legal immediately, with outside counsel engaged within four (4) hours of identification.
4. Any incident involving a subprocessor shall trigger the Subprocessor Incident Procedure, including invocation of the right-to-audit provisions of the applicable Business Associate Subcontractor Agreement.
5. Any incident involving suspected workforce-member misconduct shall be escalated to Human Resources within four (4) business hours of identification and shall be coordinated with Legal.

## Post-Incident Review Checklist

Within fifteen (15) business days of incident closure, the Incident Commander shall convene a Post-Incident Review meeting and shall produce a Post-Incident Report covering, at minimum:

1. Incident timeline, including the events of detection, declaration, containment, notification, recovery, and closure with specific timestamps for each event.
2. Root cause analysis, distinguishing immediate cause from contributing causes; explicit identification of any policy, procedure, or control whose absence or failure contributed to the incident.
3. Effectiveness review of controls: which controls operated as intended; which operated but were insufficient; which were absent; and what improvement is recommended for each.
4. Customer impact summary: number of affected individuals, categories of PHI involved, notifications delivered, customer-facing remediation provided.
5. Regulatory and contractual notifications made: each notification with recipient, date, and reference to the underlying communication.
6. Remediation actions with owners and target completion dates, tracked through the Organization's remediation register until closure.
7. Lessons learned and updates required to this Runbook, the Incident Response Plan, the Breach Notification Policy, and any related policy or procedure.
8. A communications summary including any media coverage, customer feedback, and regulatory inquiry triggered by the incident or the response.

The Post-Incident Report shall be signed by the Incident Commander, the HIPAA Privacy Officer, and Legal. The Report shall be retained in accordance with the Document Retention Schedule and shall be made available to internal and external auditors upon request, subject to applicable privilege.


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
