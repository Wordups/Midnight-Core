# Workforce Off-Boarding Procedure

**Document Type:** Procedure
**Variant:** Executive — One-page brief style, decision-maker focused, high-density. Shows up in board packs.

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

## Off-Boarding Procedure — At a Glance

- **Applies to: **Every workforce separation — voluntary or involuntary, employees or contractors.
- **What it does: **Disables access, recovers assets, transfers knowledge in a defined, auditable sequence.
- **Why it matters: **Departed workforce with live access is the #1 access-control audit finding.
- **Owner: **{{POLICY_OWNER}} | Reviewed annually | Next review: {{NEXT_REVIEW_DATE}}

## The Sequence

| When | Who | What |
| --- | --- | --- |
| T-5 days | Manager + Coordinator | Knowledge Transfer Form completed; successors identified. |
| Final workday | IT + Coordinator | Privileged access reduced; shared resources transferred. |
| Final access end-time | IT | Account disabled in IdP within 4 business hours. Service-account credentials rotated within 24 hours. |
| T+5 days | Coordinator | Hardware recovered; endpoints wiped; MDM unenrolled. |
| T+15 days | Coordinator | Verified across IdP + 2 downstream systems. Tracker marked Complete. |

## Hard SLAs

- Account disablement: 4 business hours from final access end-time.
- Service-account credential rotation: 24 hours.
- Hardware recovery: 5 business days post-separation.
- End-to-end completion: 15 business days.

## Quality Checks

Quarterly reconciliation against HR roster. Annual sample audit by Information Security. Continuous IdP/HRIS drift detection.

## Escalation

Step blocked or late: {{POLICY_OWNER}}. No progress in 24 hours: {{APPROVER_NAME}}. Suspected misconduct or unrecovered access: treat as a security incident (Incident Response Plan).


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
