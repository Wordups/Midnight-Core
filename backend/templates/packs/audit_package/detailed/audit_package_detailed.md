# SOC 2 Type II Audit Package

**Document Type:** Audit Package
**Variant:** Detailed — Comprehensive, long-form, every consideration covered. The template a regulated startup would use to over-prepare.

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

This Audit Package supports a SOC 2 Type II engagement covering the period {{AUDIT_PERIOD_START}} through {{AUDIT_PERIOD_END}}. The engagement evaluates the design and operating effectiveness of controls relevant to the Trust Services Criteria ("TSC") selected by the Organization. The Security category, comprising the Common Criteria CC1 through CC9, is the baseline. Additional categories are included as set forth in the System Description: Availability (A1), Confidentiality (C1), Processing Integrity (PI1), and Privacy (P1, P2, P3, P4, P5, P6, P7, P8). Categories not selected are excluded from the engagement.

This Package is prepared by the Information Security function based on the Organization's records and operates under the direction of the Package Owner. The Package is not, in itself, a SOC 2 report or attestation. The SOC 2 report is the auditor's deliverable, issued in the form prescribed by the AICPA following completion of the engagement.

The Package is provided to the auditor through the auditor portal in accordance with the engagement work plan. Materials provided in the portal are subject to the engagement letter's confidentiality and use restrictions.

## Control Inventory

The Control Inventory maps each in-scope Trust Services Criterion to the Organization's implementing control(s) and to the evidence supporting operating effectiveness during the audit period. The Inventory is maintained continuously in the Control Inventory Register; the table below is the audit-period snapshot.

| TSC Ref | Criterion (abbreviated) | Implementing Control | Evidence | Owner |
| --- | --- | --- | --- | --- |
| CC1.1 | Demonstrates commitment to integrity and ethics | Code of Conduct; annual acknowledgement | Policy + acks | HR Lead |
| CC1.4 | Demonstrates commitment to competence | Job descriptions; training program | JDs + LMS | HR Lead |
| CC2.1 | Communicates information internally | All-hands; policy library | Comms log + library | Info Sec |
| CC2.2 | Communicates information externally | Trust Center; security responses | TC content + responses | Info Sec |
| CC3.1 | Specifies suitable objectives | Annual Risk Assessment | RA + sign-off | Info Sec |
| CC3.2 | Identifies risks | Risk Register; threat library | Register entries | Info Sec |
| CC3.4 | Identifies, assesses changes | Change-management review of risk impact | Change-review records | Engineering |
| CC4.1 | Selects, develops, performs monitoring | Quarterly internal sampling (remediation) | Sampling records (in progress) | Info Sec |
| CC5.1 | Selects and develops control activities | Information Security Policy + standards | Policy library + approvals | Info Sec |
| CC5.2 | Selects and develops general technology controls | Engineering standards (encryption, logging) | Standard documents | Engineering |
| CC6.1 | Implements logical access controls | Okta SSO + MFA; role-based access | IDP export + role matrix | Info Sec |
| CC6.2 | Authorizes new access; removes departing | Onboarding/Off-boarding procedures | Provisioning tickets + tracker | Info Sec |
| CC6.3 | Periodic access review | Quarterly access review | Review records (4 per year) | Info Sec |
| CC6.6 | Logical access for external users | Customer auth; admin SSO; portal SSO | IDP records + auth logs | Info Sec |
| CC6.7 | Restricts transmission of information | TLS 1.2+; mTLS for service-to-service | TLS config + cipher audit | Engineering |
| CC6.8 | Prevents and detects unauthorized software | EDR + MDM; software approval | EDR logs + MDM compliance | Info Sec |
| CC7.1 | Detects vulnerabilities | VM Program (Dependabot, Inspector, pen test) | VM register + reports | Info Sec |
| CC7.2 | Monitors components | Datadog; cloud security posture mgmt | Monitoring config + alerts | Engineering |
| CC7.3 | Detects and responds to anomalies | Incident Response Plan; runbooks | Incident register + PIRs | Info Sec |
| CC7.4 | Responds to security incidents | IR Plan; runbooks; tabletop drills | Incidents + drill records | Info Sec |
| CC7.5 | Recovers from security incidents | Recovery procedures; DR plan | Recovery records; DR drill | Engineering |
| CC8.1 | Manages changes | Change Management Policy | PR records + deploy logs | Engineering |
| CC9.1 | Identifies, assesses, and manages risks from business disruption | Business Continuity Plan | BCP + drill records | Operations |
| CC9.2 | Assesses and manages risks from vendors | Vendor Management Policy; subprocessor register | Subprocessor reviews + BAAs | Vendor Owner |

## Evidence Index

The Evidence Index is the authoritative catalog of evidence supporting each control during the audit period. Each entry records: a unique Evidence Identifier (format EV-YYYY-NNNN); the linked control identifier(s); a description of the evidence; the collection date and collector; the storage location and access method; the applicable confidentiality classification; and any restrictions on auditor handling (such as encryption-in-transit requirements or data-residency considerations).

Evidence categories represented include: policy and procedure documents (one current version per control); operational records (access reviews, change records, incident tickets); system exports (identity provider configurations, monitoring rules, vulnerability registers); training records; subprocessor attestations; and human-witness evidence (interview notes signed by both parties).

Sampling for testing is coordinated with the auditor per the engagement work plan. Where the auditor selects a sample, the corresponding evidence items are made available through the auditor portal with the chain-of-custody and integrity verification maintained throughout the engagement.

## Gap Analysis Summary

The Information Security function conducted a documented gap analysis against the in-scope Trust Services Criteria in advance of this engagement. The gap analysis identified the following items, which are tracked through to remediation in the Remediation Plan below:

1. CC4.1 (Monitoring activities): The Organization's internal-audit function operates informally; observations during the audit period have not been consistently documented in a standardized form. Remediation: implement quarterly internal control sampling with documented findings and named-owner follow-through. Target completion before audit fieldwork start.
2. CC9.2 (Vendor risk management): Three (3) Tier-2 subprocessor reviews are overdue at audit-period close. Remediation: complete the three overdue reviews; update the Vendor Management Procedure to include automated review-cadence reminders. Target completion before audit fieldwork start.
3. Stale governance: two (2) policies have next-review dates in the past as of audit-period close. Remediation: re-confirm or re-approve each policy through the standard review process. Target completion before audit fieldwork start.
4. CC6.3 (Periodic access review): Q3 access review documentation incomplete (the privileged-role review section was not signed by the reviewer). Remediation: complete the Q3 documentation retroactively with a notation of the late completion. Target completion before audit fieldwork start.

## Remediation Plan

Each remediation item has a named owner, a target completion date, a defined acceptance test, and a tracking record in the Audit Remediation Register. The table below reflects status as of {{REMEDIATION_STATUS_DATE}}; the live record is in the Register.

| Item | TSC | Owner | Target | Status |
| --- | --- | --- | --- | --- |
| Quarterly internal control sampling with findings | CC4.1 | {{INFO_SEC_LEAD}} | {{TARGET_DATE_1}} | In Progress |
| Complete three Tier-2 subprocessor reviews | CC9.2 | {{VENDOR_OWNER}} | {{TARGET_DATE_2}} | In Progress |
| Re-confirm/re-approve two stale policies | Multiple | {{POLICY_OWNER}} | {{TARGET_DATE_3}} | Complete |
| Complete Q3 access review documentation | CC6.3 | {{INFO_SEC_LEAD}} | {{TARGET_DATE_4}} | Complete |
| Update Vendor Management Procedure (cadence reminders) | CC9.2 | {{VENDOR_OWNER}} | {{TARGET_DATE_5}} | In Progress |

## Management Assertions

For the audit period {{AUDIT_PERIOD_START}} through {{AUDIT_PERIOD_END}}, management asserts that:

1. The accompanying description of the Organization's system fairly presents the system that was designed and implemented during the audit period to provide the services to which the assertion pertains.
2. The controls included in the system description, and identified in the Control Inventory of this Package, were suitably designed to provide reasonable assurance that the Organization's service commitments and system requirements would be achieved based on the applicable Trust Services Criteria.
3. The controls included in the system description operated effectively throughout the audit period to provide reasonable assurance that the Organization's service commitments and system requirements were achieved based on the applicable Trust Services Criteria, except as described in the Gap Analysis and tracked in the Remediation Plan.
4. The criteria used to make these assertions are the Trust Services Criteria for the Security, [and additional selected categories], as set forth in TSP Section 100, "Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy."

These assertions are made in good faith based on management's knowledge as of the date of signature. The assertions shall be signed by {{APPROVER_NAME}} (Approver) and {{POLICY_OWNER}} (Package Owner). The signature block follows the standard format used for the Organization's management assertions and is included in the signature section of this document.

## Auditor Q&A Template

The following template governs the handling of questions, evidence requests, and observations raised by the auditor through the engagement. The Q&A log is maintained in the auditor portal and is the authoritative record of all material communications.

1. Question received: the portal records the date and time of receipt, the auditor name, the question text, and the categorization (Clarification / Evidence Request / Observation).
2. Owner assigned: typically the named control owner; for cross-cutting questions, the Package Owner assigns explicitly.
3. Response drafted: the assigned owner drafts the response, referencing underlying control documentation and evidence items by identifier. Direct citation is preferred over paraphrase.
4. Internal review: the response is reviewed by the Package Owner; Legal review is added where the question implicates legal interpretation, regulatory matters, or potential breach implications.
5. Response delivered: the response is posted through the auditor portal. Auditor acknowledgement is recorded in the thread.
6. Closure: threads are closed only upon auditor acknowledgement. Unresolved threads at engagement close are documented in the engagement close-out summary.

Response timing: target response within one (1) business day for Clarification questions and within three (3) business days for Evidence Requests. Observations are addressed on a case-by-case basis depending on materiality.


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
