# Workforce Off-Boarding Procedure

**Document Type:** Procedure
**Variant:** Formal — Legalese voice, full structure, traditional enterprise. The template a Fortune 500 General Counsel would approve.

---

## Cover Page

[LOGO: organization_logo.png] *(centered, 2" × 2")*

**Workforce Off-Boarding Procedure** — {{DOCUMENT_TITLE}}

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

## 1. Purpose

This Procedure establishes the standardized steps to be performed upon the voluntary or involuntary separation of a workforce member from {{ORGANIZATION_NAME}} ("Organization"). This Procedure is promulgated pursuant to the Access Control Policy and shall be construed in accordance with applicable laws, including data protection laws of the jurisdictions in which the Organization and the separating workforce member operate.

## 2. Scope

2.1 This Procedure applies to the separation of any workforce member, including employees, contractors, consultants, interns, and temporary workforce. The Procedure shall be initiated upon written notification of separation, regardless of cause.

2.2 This Procedure addresses considerations under SOC 2 Trust Services Criterion CC6.2 (de-provisioning), HIPAA 45 CFR 164.308(a)(3)(ii)(C) (termination procedures), and ISO/IEC 27001:2022 Annex A.6.5 (responsibilities after termination or change of employment).

## 3. Prerequisites

1. Notification of separation shall have been received in writing by the Off-Boarding Coordinator from the Human Resources function or, in the case of contractors, the Contract Manager.
2. The separation date and the final access end-time shall be documented in the Off-Boarding Tracker. Where the final access end-time differs from the separation date, both shall be recorded.
3. The Hiring Manager shall have identified, in writing, the recipient(s) of any business knowledge, ongoing work product, and access responsibilities held by the separating workforce member.

## 4. Procedure Steps

### 4.1 T-minus 5 Business Days (Planning)

1. Off-Boarding Coordinator shall create an entry in the Off-Boarding Tracker including: workforce member name, role, manager, separation date, final access end-time, and reason category.
2. Hiring Manager shall complete the Knowledge Transfer Form identifying ongoing projects, customer relationships, system ownerships, and any unique credentials or knowledge held.
3. Off-Boarding Coordinator shall schedule access transfer conversations with the identified recipients.

### 4.2 Final Workday (Access Reduction)

1. IT / Identity Operator shall reduce the workforce member's privileged role assignments to the minimum required for their final workday's activities.
2. Off-Boarding Coordinator shall verify that all customer-facing communications channels (shared inboxes, on-call rotations, customer portal access) have been transitioned to designated successors.
3. Hiring Manager shall conduct the exit interview if applicable.

### 4.3 Final Access End-Time (Disablement)

1. IT / Identity Operator shall disable the workforce member's account in the identity provider within four (4) business hours of the final access end-time. Disablement shall be confirmed in the identity provider audit log.
2. IT / Identity Operator shall disable or rotate any service account credentials known to the separating workforce member within twenty-four (24) hours.
3. IT / Identity Operator shall remove the workforce member from all distribution lists, shared mailboxes, and group memberships outside of those required for the duration of access retention (if any).
4. Off-Boarding Coordinator shall record the disablement time, the operator, and the audit log reference in the Off-Boarding Tracker.

### 4.4 T-plus 5 Business Days (Asset Recovery)

1. Off-Boarding Coordinator shall confirm receipt of all Organization-issued hardware. Outstanding hardware shall be escalated to the Hiring Manager and the Human Resources function.
2. Recovered endpoints shall be wiped using the approved sanitization procedure and either reassigned or disposed of in accordance with the Asset Management Policy.
3. Personal devices enrolled in the mobile device management framework shall be unenrolled and work data wiped, leaving personal data intact.

### 4.5 T-plus 15 Business Days (Confirmation)

1. Off-Boarding Coordinator shall confirm that all account disablements and access removals have been verified by sampling the identity provider audit log and at least two downstream systems.
2. Off-Boarding Coordinator shall mark the Off-Boarding Tracker entry as Complete only upon satisfactory confirmation.
3. Any item that cannot be completed within this timeframe shall be escalated per Section 6.

## 5. Quality Checks

1. The Off-Boarding Coordinator shall conduct a quarterly review of completed Off-Boarding Tracker entries against the workforce roster maintained by Human Resources to identify any separations not processed.
2. The Information Security function shall conduct an annual review of a sample of off-boardings, verifying that account disablement timing met the four-business-hour SLA in Section 4.3 and that all credentials known to the workforce member were rotated.
3. Findings of non-conformance shall be documented in the Off-Boarding Findings Register and remediated within thirty (30) days.

## 6. Escalation Path

Where any step of this Procedure cannot be completed within its specified timeframe, the matter shall be escalated as follows: (i) initial escalation to {{POLICY_OWNER}}; (ii) escalation after twenty-four (24) hours of inaction to {{APPROVER_NAME}}; (iii) escalation of any matter involving suspected misconduct, unrecovered access, or unauthorized retention of Organization data to the Information Security function for treatment as a security incident under the Incident Response Plan.

## 7. Records and Documentation

1. The Off-Boarding Tracker shall be maintained as the authoritative record of off-boarding execution. Entries shall be retained for the period specified in the Document Retention Schedule.
2. Knowledge Transfer Forms shall be retained for a minimum of two (2) years following separation.
3. Hardware recovery and disposal records shall be retained in accordance with the Asset Management Policy.
4. Identity provider audit logs evidencing account disablement shall be retained for the period required by applicable law and customer agreements.


## Roles and Responsibilities

| Role | Responsibilities |
| --- | --- |
| Procedure Owner ({{POLICY_OWNER}}) | Maintains this Procedure, schedules reviews, and approves material changes to the steps. |
| Approver ({{APPROVER_NAME}}, {{APPROVER_TITLE}}) | Provides executive approval at issuance and annual review. |
| Off-Boarding Coordinator | Executes the steps in Section 4 for each separating workforce member; documents completion in the Off-Boarding Tracker. |
| Hiring Manager | Notifies HR of separation; identifies access transfer recipients; participates in knowledge transfer. |
| IT / Identity Operator | Disables access, recovers credentials and devices, completes the technical steps within the SLA. |

## Review and Maintenance

**Next review date:** {{NEXT_REVIEW_DATE}}

**Review frequency:** Annually, or upon a material change in process, identity provider, or HRIS.

**Review triggers:**

- A material change in applicable laws, regulations, or contractual obligations.
- Findings from an internal or external audit that affect this document.
- A security or privacy incident that exposes a gap in the document.
- An organizational change (acquisition, divestiture, new business line) that affects scope.

## Related Documents

- Access Control Policy
- Acceptable Use Policy
- Information Security Policy
- Asset Management Policy

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
