# Workforce Off-Boarding Procedure

**Document Type:** Procedure
**Variant:** Detailed — Comprehensive, long-form, every consideration covered. The template a regulated startup would use to over-prepare.

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

This Procedure provides the comprehensive, step-by-step instructions for the off-boarding of any workforce member separating from {{ORGANIZATION_NAME}}. The procedure exists to ensure that: (i) the workforce member's access to Organization information resources is removed within the timeframes required by the Access Control Policy and by applicable regulatory and contractual obligations; (ii) Organization-owned assets in the workforce member's possession are recovered and processed in accordance with the Asset Management Policy; (iii) institutional knowledge and ongoing work product are transferred to designated successors with minimal disruption; and (iv) the documentation produced by the off-boarding event is sufficient to satisfy internal control review and external audit inquiry.

This Procedure addresses considerations under the SOC 2 Type II Trust Services Criteria (CC6.2 — De-provisioning of access; CC1.1 — Integrity and ethics), the HIPAA Security Rule 45 CFR 164.308(a)(3)(ii)(C) (termination procedures), the HIPAA Privacy Rule provisions concerning workforce sanctions, ISO/IEC 27001:2022 Annex A.6.5 (responsibilities after termination or change of employment), Annex A.6.6 (confidentiality or non-disclosure agreements), and Annex A.5.11 (return of assets), and NIST CSF 2.0 PR.AA-05 (access permissions, entitlements, and authorizations).

## Scope

### In-Scope Separation Events

1. Voluntary separation, including resignation, retirement, and the conclusion of a fixed-term engagement.
2. Involuntary separation, including termination for cause, layoff, and the early termination of a contract.
3. Conversion events, including the conversion of a contractor to employee status or vice versa, where conversion entails a change in identity provider account or access rights.
4. Extended leave of absence exceeding ninety (90) days, where retention of access during the absence has not been expressly approved by {{POLICY_OWNER}}.
5. Internal transfers to roles that materially reduce the required access; for transfers, this Procedure shall be executed for the access being relinquished while the new access is provisioned under the Onboarding Procedure.

### In-Scope Workforce Categories

- Full-time and part-time employees of {{ORGANIZATION_NAME}}.
- Contractors, consultants, and independent professionals engaged on a fixed or open-ended basis.
- Interns, fellows, and other temporary workforce members.
- Authorized third-party vendors with named individual access to Organization systems.

## Prerequisites

1. Written notification of separation shall have been received by the Off-Boarding Coordinator. For employees, notification shall come from the Human Resources function. For contractors, notification shall come from the Contract Manager.
2. The notification shall specify: separation date, final access end-time (which may differ from the separation date in cases of garden leave or pending investigation), reason category (voluntary, involuntary, conversion, leave, transfer), and any special instructions (such as immediate access termination or extended access retention with compensating controls).
3. The Off-Boarding Tracker entry shall be created and populated with the information from the notification, the workforce member's role and manager, and a list of systems known to be accessed by the workforce member based on the identity provider role assignments and the most recent quarterly access review.
4. The Hiring Manager shall have completed the Knowledge Transfer Form, identifying: ongoing projects, customer relationships, system ownerships, shared credentials known to the workforce member, unique procedural knowledge, and recommended successors for each.

## Procedure Steps

### Phase 1 — Planning (T-minus 5 business days)

1. Off-Boarding Coordinator reviews the Knowledge Transfer Form and identifies any gaps. Gaps shall be resolved with the Hiring Manager before proceeding.
2. Off-Boarding Coordinator schedules access transfer conversations with each named successor. Each conversation shall be documented with a brief summary attached to the Off-Boarding Tracker entry.
3. Off-Boarding Coordinator notifies relevant downstream functions (Customer Success, Legal, Finance) of the upcoming separation so that any function-specific off-boarding steps may be initiated.
4. For involuntary separations classified as high-risk by Human Resources or Legal, the Off-Boarding Coordinator coordinates with the Information Security function on accelerated access termination and any necessary monitoring.

### Phase 2 — Final Workday Activities

1. IT / Identity Operator reduces privileged role assignments to the minimum necessary for the final workday. Production write access, customer data access, and key management operations should be removed unless specifically required.
2. Off-Boarding Coordinator verifies that shared inboxes, on-call rotations, customer portal accounts, document approval delegations, and signature authority have been transitioned to designated successors.
3. Hiring Manager conducts the exit interview, if applicable, and confirms with the workforce member: receipt of return-of-property instructions; reminder of post-employment obligations (non-disclosure, non-solicitation, intellectual property assignment); and channel for any post-separation questions.
4. Off-Boarding Coordinator confirms with the workforce member the address to which any final paperwork should be delivered.

### Phase 3 — Final Access End-Time

1. IT / Identity Operator disables the workforce member's primary account in the identity provider within four (4) business hours of the final access end-time. The disablement event in the identity provider audit log shall be the authoritative record.
2. IT / Identity Operator disables or rotates any service account credentials known to the separating workforce member within twenty-four (24) hours. The list of affected service accounts shall be derived from the Knowledge Transfer Form, the system ownership records, and any credentials retrieved from the workforce member's password manager export (where applicable).
3. IT / Identity Operator removes the workforce member from all distribution lists, shared mailboxes, channel memberships, and group permissions, excluding only those required to support data retention obligations during a defined retention window.
4. For any system not federated through the central identity provider, the system owner of record shall confirm in writing that local access has been removed.
5. Where the workforce member held key custodian or split-knowledge roles in any cryptographic key management process, the Information Security function shall be engaged to rotate the affected keys per the Key Management Procedure.
6. Off-Boarding Coordinator records the disablement time, the operator, the audit log reference, and any exceptions in the Off-Boarding Tracker.

### Phase 4 — Asset Recovery (T-plus 5 business days)

1. Off-Boarding Coordinator confirms receipt of all Organization-issued hardware against the asset records. Outstanding hardware shall be escalated to the Hiring Manager and to Human Resources for written follow-up with the workforce member, and may, where permitted by law, be the subject of payroll deduction or civil recovery.
2. Recovered endpoints shall be wiped using the approved sanitization procedure documented in the Asset Management Policy. Endpoints shall be either reassigned to incoming workforce members after a full reimaging or disposed of through a certified e-waste vendor.
3. Personal devices enrolled in the mobile device management framework shall be unenrolled, with work data, applications, and certificates wiped, leaving personal data and applications intact.
4. Authentication tokens, hardware security keys, and badges shall be recovered and either reassigned or destroyed in accordance with the Asset Management Policy.

### Phase 5 — Confirmation (T-plus 15 business days)

1. Off-Boarding Coordinator verifies in the identity provider that the workforce member's account is disabled and that no derived service accounts remain active.
2. Off-Boarding Coordinator samples at least two downstream systems (one cloud infrastructure provider, one application) and confirms that the workforce member's access has been removed in those systems.
3. Off-Boarding Coordinator confirms with the Human Resources function that all final paperwork has been processed.
4. The Off-Boarding Tracker entry is marked Complete only upon satisfactory confirmation of all the above items.

## Quality Checks

1. Quarterly Reconciliation: The Off-Boarding Coordinator reconciles completed Off-Boarding Tracker entries against the workforce roster maintained by Human Resources. Any separations identified in the roster but not present as Tracker entries shall be retroactively processed and the gap analyzed.
2. Annual Sample Audit: The Information Security function conducts a documented audit of a representative sample of off-boardings completed during the year, verifying compliance with the four-business-hour disablement SLA, the credential rotation requirement, and the asset recovery requirement.
3. Continuous Drift Detection: The identity provider and the HR information system shall be reconciled on a continuous or daily basis. Accounts active in the identity provider for workforce members no longer in the HR roster shall trigger an automated alert to the Information Security function.
4. All findings from quality checks shall be documented in the Off-Boarding Findings Register with severity, root cause, assigned remediation owner, and remediation target date.

## Escalation Path

Where any step of this Procedure cannot be completed within the specified timeframe, the matter shall be escalated as follows: (i) initial escalation to {{POLICY_OWNER}} within one business day of identification of the delay; (ii) further escalation after twenty-four (24) hours of inaction to {{APPROVER_NAME}}; (iii) escalation of any matter involving suspected misconduct, unrecovered access, or unauthorized retention of Organization data to the Information Security function for treatment as a potential security incident under the Incident Response Plan; (iv) escalation to Legal of any matter involving potential litigation, regulatory inquiry, or third-party legal hold.

## Records and Documentation

1. The Off-Boarding Tracker is the authoritative record of off-boarding execution. Entries shall be retained for the period specified in the Document Retention Schedule, which shall in no case be less than six (6) years.
2. Knowledge Transfer Forms shall be retained for a minimum of two (2) years following separation.
3. Hardware recovery and disposal records shall be retained in accordance with the Asset Management Policy.
4. Identity provider audit logs evidencing account disablement shall be retained for the period required by applicable law and customer agreements, and at minimum for one (1) year.
5. Quality check findings shall be retained in the Off-Boarding Findings Register for the life of the program plus six (6) years.


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
