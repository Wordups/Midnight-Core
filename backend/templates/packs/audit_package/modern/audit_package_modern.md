# SOC 2 Type II Audit Package

**Document Type:** Audit Package
**Variant:** Modern — Scannable, plain-language, modern enterprise. Short paragraphs, clear headings, designed for readability.

---

## Cover Page

[LOGO: organization_logo.png] *(centered, 2" × 2")*

**SOC 2 Type II Audit Package** — {{DOCUMENT_TITLE}}

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

## Audit Scope and Framework

SOC 2 Type II engagement covering {{AUDIT_PERIOD_START}} through {{AUDIT_PERIOD_END}}. Trust Services Criteria selected: Security (baseline), plus what's named in the System Description.

This package is what we hand to the auditor. The SOC 2 report is what they hand back. Not the same thing.

## Control Inventory

TSC → control → evidence. Full list lives in the Control Inventory Register; here's the top of the page.

| TSC | Control | Evidence |
| --- | --- | --- |
| CC1.1 | Code of Conduct + annual acknowledgement | Policy text + acknowledgement records |
| CC3.1 | Annual Risk Assessment | Risk Assessment artifact + sign-off |
| CC6.1 | Okta + MFA; role-based access | IDP config; access reviews |
| CC6.2 | Onboarding/Off-boarding procedures | Provisioning tickets; off-boarding tracker |
| CC6.3 | Quarterly access review | Access review records (4) |
| CC7.1 | Vulnerability Management Program | VM register; remediation evidence |
| CC7.3 | Incident Response Plan | Incident register; post-incident reviews |
| CC8.1 | Change Management Policy | PR records; deployment logs |
| CC9.2 | Vendor Management | Subprocessor reviews; BAA register |

## Evidence Index

Every artifact has an index entry: control ID, description, collected date, collector, location. Sampling for testing happens with the auditor per the work plan.

## Gap Analysis Summary

- CC4.1: Informal internal audit. Fix: quarterly internal control sampling with documented findings.
- CC9.2: Three Tier-2 subprocessor reviews overdue. Fix: complete before fieldwork.
- Stale governance: two policies past next-review date. Fix: re-confirm or re-approve before fieldwork.

## Remediation Plan

| Item | Owner | Status |
| --- | --- | --- |
| Quarterly internal control sampling | {{INFO_SEC_LEAD}} | In Progress |
| Subprocessor reviews (3) | {{VENDOR_OWNER}} | In Progress |
| Stale policy re-confirmation | {{POLICY_OWNER}} | Complete |

## Management Assertions

For the audit period, management asserts:

1. System description fairly presented.
2. Controls suitably designed for the selected criteria.
3. Controls operated effectively over the period, except as noted in the gap analysis.

Signed by {{APPROVER_NAME}} and {{POLICY_OWNER}}.

## Auditor Q&A Template

Question → categorize → assign owner → draft response → review → deliver via portal → close on auditor ack. The portal is the system of record.


## Roles and Responsibilities

| Role | Responsibilities |
| --- | --- |
| Package Owner ({{POLICY_OWNER}}) | Assembles the package, owns the mapping baseline, signs management assertions. |
| Approver ({{APPROVER_NAME}}, {{APPROVER_TITLE}}) | Signs management assertions and the gap-analysis attestation. |
| Control Owners (per control) | Provide evidence on the requested cadence; sign off on operating effectiveness. |
| Information Security | Coordinates evidence collection; verifies completeness; runs gap analysis. |
| External Auditor | Reviews the package, samples evidence, conducts walkthroughs and tests. |

## Review and Maintenance

**Next review date:** {{NEXT_REVIEW_DATE}}

**Review frequency:** Compiled per engagement; the framework-mapping baseline reviewed annually.

**Review triggers:**

- A material change in applicable laws, regulations, or contractual obligations.
- Findings from an internal or external audit that affect this document.
- A security or privacy incident that exposes a gap in the document.
- An organizational change (acquisition, divestiture, new business line) that affects scope.

## Related Documents

- Information Security Policy
- Risk Management Policy
- Vendor Management Policy
- Annual Security Risk Assessment

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
