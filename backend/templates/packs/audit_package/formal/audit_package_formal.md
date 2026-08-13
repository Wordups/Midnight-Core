# SOC 2 Type II Audit Package

**Document Type:** Audit Package
**Variant:** Formal — Legalese voice, full structure, traditional enterprise. The template a Fortune 500 General Counsel would approve.

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

## 1. Audit Scope and Framework

This Audit Package supports a SOC 2 Type II engagement covering the period {{AUDIT_PERIOD_START}} through {{AUDIT_PERIOD_END}}. The engagement evaluates the design and operating effectiveness of controls relevant to the Trust Services Criteria ("TSC") selected for the audit. The Organization has selected the Security category as the baseline; additional categories (Availability, Confidentiality, Processing Integrity, Privacy) are included as set forth in the System Description.

This Package is prepared in good faith based on the Organization's records and is not, in itself, an attestation. The SOC 2 report is the attestation, issued by an independent CPA firm following completion of the engagement.

## 2. Control Inventory

The following table maps each in-scope Trust Services Criterion to the Organization's implementing control(s) and to the evidence supporting operating effectiveness during the audit period. Detailed control descriptions are maintained in the Control Inventory Register.

| TSC Ref | Criterion | Control | Evidence Type |
| --- | --- | --- | --- |
| CC1.1 | Demonstrates commitment to integrity and ethics | Code of Conduct policy with annual acknowledgement | Policy text + acknowledgement records |
| CC2.1 | Communicates information internally | All-hands updates; policy library publication | Communications log; library access metrics |
| CC3.1 | Specifies suitable objectives | Annual Risk Assessment with documented objectives | Risk Assessment artifact + sign-off |
| CC5.1 | Selects and develops control activities | Information Security Policy and supporting standards | Policy library + approval records |
| CC6.1 | Implements logical access controls | Identity provider with MFA; role-based access | IDP configuration export; access review records |
| CC6.2 | New access is authorized; departing access removed | Onboarding and Off-Boarding procedures | Access provisioning tickets; off-boarding tracker |
| CC6.3 | Periodic review of access | Quarterly access review | Access review records (4 per period) |
| CC6.6 | Logical access for external users | Customer authentication; admin SSO | IDP records; auth logs |
| CC7.1 | Vulnerability management | Vulnerability Management Program | VM register; remediation evidence |
| CC7.2 | Monitoring of system components | Datadog; cloud security posture management | Monitoring configuration; alert records |
| CC7.3 | Detection and response to anomalies | Incident Response Plan and runbooks | Incident register; post-incident reviews |
| CC8.1 | Change management | Change Management Policy | PR records; deployment logs; rollback evidence |
| CC9.2 | Vendor risk management | Vendor Management Policy; subprocessor register | Subprocessor reviews; BAA register |

## 3. Evidence Index

The evidence supporting each control is organized in the Evidence Index, with one entry per evidence artifact. Each entry records: control identifier; evidence description; collection date; collector; storage location; and applicable confidentiality classification. Sampling for testing shall be coordinated with the auditor per the engagement work plan.

## 4. Gap Analysis Summary

The Information Security function conducted a documented gap analysis against the in-scope Trust Services Criteria in advance of this engagement. The following gaps were identified and are tracked in the Remediation Plan in Section 5:

1. CC4.1 (Monitoring activities): The internal-audit function is informal; observations during the audit period were not consistently documented. Remediation: implement quarterly internal control sampling with documented findings.
2. CC9.2 (Vendor risk management): Three (3) Tier-2 subprocessor reviews are overdue. Remediation: complete reviews before audit fieldwork start.
3. Stale governance: two (2) policies have next-review dates in the past. Remediation: re-confirm or re-approve before audit fieldwork start.

## 5. Remediation Plan

The following remediation items are tracked. Each item carries a named owner, a target completion date, and a defined acceptance test. Remediation status as of {{REMEDIATION_STATUS_DATE}}:

| Item | Owner | Target | Status |
| --- | --- | --- | --- |
| Quarterly internal control sampling | {{INFO_SEC_LEAD}} | {{TARGET_DATE_1}} | In Progress |
| Subprocessor reviews (3) | {{VENDOR_OWNER}} | {{TARGET_DATE_2}} | In Progress |
| Stale policy re-confirmation (2) | {{POLICY_OWNER}} | {{TARGET_DATE_3}} | Complete |

## 6. Management Assertions

For the audit period {{AUDIT_PERIOD_START}} through {{AUDIT_PERIOD_END}}, management asserts that:

1. The system description is fairly presented in all material respects.
2. The controls described in the Control Inventory were suitably designed to provide reasonable assurance regarding the selected Trust Services Criteria.
3. The controls described operated effectively throughout the audit period, except as described in the gap analysis and remediation plan.

These assertions are made in good faith based on management's knowledge as of the date of signature. The assertions shall be signed by {{APPROVER_NAME}} and {{POLICY_OWNER}}.

## 7. Auditor Q&A Template

The following template is provided for routing auditor questions through the engagement. The Q&A log is maintained in the auditor portal and is the authoritative record of all material communications.

1. Question received (date/time, auditor, channel).
2. Question categorized (Clarification / Evidence Request / Observation).
3. Owner assigned (typically the named control owner).
4. Response drafted (with reference to underlying evidence or control text).
5. Response reviewed by {{POLICY_OWNER}} (and Legal where the question implicates legal interpretation).
6. Response delivered through the auditor portal; thread closed only upon auditor acknowledgement.


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
