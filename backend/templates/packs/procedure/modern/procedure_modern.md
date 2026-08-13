# Workforce Off-Boarding Procedure

**Document Type:** Procedure
**Variant:** Modern — Scannable, plain-language, modern enterprise. Short paragraphs, clear headings, designed for readability.

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

## Purpose

Someone is leaving. Here's exactly what we do, in what order, to make sure their access goes away cleanly and our data goes with us.

This is the same procedure whether someone resigned, got promoted out, or was terminated. The steps don't care about the reason — they care about getting the access closed properly.

## Scope

Every separation: employees, contractors, interns, temps. Initiated when HR (or the contract manager for contractors) sends written notice. Aligned with what auditors look for under SOC 2 CC6.2, HIPAA 164.308(a)(3)(ii)(C), and ISO 27001 A.6.5.

## Prerequisites

- Written notification from HR with separation date and final access end-time.
- Hiring manager has named the people who pick up the work.
- Off-Boarding Tracker entry created.

## Procedure Steps

### 5 business days before

1. Create the tracker entry: name, role, manager, dates.
2. Manager fills out the Knowledge Transfer Form — projects, customers, system ownerships, anything they alone know.
3. Schedule the handoff conversations.

### Final workday

1. Drop their privileged role assignments down to what they need for the last day only.
2. Move shared inboxes, on-call rotations, customer portal accounts to the named successors.
3. Exit interview if applicable.

### Final access end-time

1. Disable the account in the identity provider within 4 business hours. This is the hard SLA.
2. Rotate any service-account credentials they knew within 24 hours.
3. Pull them off distribution lists and group memberships.
4. Record the disablement time and operator in the tracker.

### 5 business days after

1. Hardware back. If not, escalate to the manager and HR.
2. Wipe recovered devices and reassign or dispose per the Asset Management Policy.
3. Unenroll personal devices from MDM. Wipe work data only.

### 15 business days after

1. Spot-check the identity provider log and at least two downstream systems.
2. Mark the tracker entry Complete.
3. Anything stuck goes through Section "Escalation Path" below.

## Quality Checks

- Quarterly: reconcile completed tracker entries against the HR roster. Any separations we missed?
- Annually: Information Security samples off-boardings — was the 4-hour SLA met? Were credentials rotated?
- Findings go in the Off-Boarding Findings Register with assigned owners and SLAs.

## Escalation Path

If a step is blocked or late: tell {{POLICY_OWNER}}. After 24 hours of no progress: escalate to {{APPROVER_NAME}}. If there's suspected misconduct, unrecovered access, or data still in their hands — that's a security incident; the Incident Response Plan kicks in.

## Records and Documentation

- Off-Boarding Tracker is the source of truth. Retain per the Document Retention Schedule.
- Knowledge Transfer Forms kept at least 2 years post-separation.
- Hardware recovery records per Asset Management Policy.
- Identity provider audit logs per applicable law and customer agreements.


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
