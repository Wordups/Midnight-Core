# Customer Data Deletion Request Process

**Document Type:** Process Flow
**Variant:** Modern — Scannable, plain-language, modern enterprise. Short paragraphs, clear headings, designed for readability.

---

## Cover Page

[LOGO: organization_logo.png] *(centered, 2" × 2")*

**Customer Data Deletion Request Process** — {{DOCUMENT_TITLE}}

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

A customer is asking us to delete their data. Here's how we do it, who does what, and how long it should take.

This process exists because data deletion under GDPR, CCPA, and most BAAs has a deadline (typically 30 days). Missing the deadline is a regulatory finding. The steps below get us there reliably.

## Process Owner and Stakeholders

- **Owner:** {{POLICY_OWNER}}
- **Customer Success:** Takes the request; confirms scope; talks to the customer.
- **Data Operations:** Actually deletes the data in our systems.
- **Legal:** Checks for legal holds before we delete.
- **Information Security:** Verifies and handles cryptographic erasure.

## Process Steps

1. **Acknowledge (1 day): **Customer Success acknowledges the request in writing and logs it in the Deletion Request Register.
2. **Verify scope and authority (3 days): **Confirm who's asking, what they're asking for, and whether they have authority.
3. **Legal hold check (3 days, parallel): **Legal checks for any retention obligation that would block deletion.
4. **Decision Point A — proceed, partial, defer: **Together we decide and communicate it back to the customer.
5. **Delete in production (21 days from request): **Data Ops removes from the primary DB, replicas, caches, search indexes, exports.
6. **Handle backups (30 days): **Either delete from backups or apply cryptographic erasure to the customer key.
7. **Notify subprocessors (30 days): **Tell our subprocessors; get written confirmations.
8. **Decision Point B — customer confirms: **Send the customer the deletion summary; get their acknowledgement.
9. **Close out (5 days after confirmation): **Close the register entry. Done.

## Inputs and Outputs

Every step has a clear input (what triggers it) and a clear output (what evidence it produces). The Deletion Request Register entry accumulates outputs as the process advances.

## Who does what (RACI)

| Step | CS | Data Ops | Legal | InfoSec |
| --- | --- | --- | --- | --- |
| Intake | R/A |  |  |  |
| Scope | R/A | C | C |  |
| Legal hold |  |  | R/A |  |
| Production deletion |  | R/A |  | C |
| Backup treatment |  | R/A |  | C |
| Subprocessor notify | R |  |  | A |
| Closure | A |  |  | C |

## Metrics

- Time-to-acknowledge: median ≤ 1 business day.
- Time-to-production-deletion: median ≤ 14 days; 95th-percentile ≤ 21 days.
- Time-to-closure: median ≤ 30 days; 95th-percentile ≤ 45 days.
- Subprocessor confirmation completeness: 100%.
- Reviewed quarterly. Misses go to {{POLICY_OWNER}} for root-cause.


## Roles and Responsibilities

| Role | Responsibilities |
| --- | --- |
| Process Owner ({{POLICY_OWNER}}) | Maintains this Process, schedules reviews, processes exception requests, and reports on metrics. |
| Approver ({{APPROVER_NAME}}, {{APPROVER_TITLE}}) | Provides executive approval at issuance and annual review. |
| Customer Success | Receives the request from the customer; confirms scope and authority; communicates timeline. |
| Data Operations | Executes deletion in production systems and authoritative data stores. |
| Legal | Reviews any legal hold or retention obligation that may suspend deletion. |
| Information Security | Confirms cryptographic erasure where applicable; verifies completion. |

## Review and Maintenance

**Next review date:** {{NEXT_REVIEW_DATE}}

**Review frequency:** Annually, or upon a material change in customer agreement template, retention obligations, or system architecture.

**Review triggers:**

- A material change in applicable laws, regulations, or contractual obligations.
- Findings from an internal or external audit that affect this document.
- A security or privacy incident that exposes a gap in the document.
- An organizational change (acquisition, divestiture, new business line) that affects scope.

## Related Documents

- Data Retention and Disposal Policy
- Data Classification Policy
- HIPAA Privacy Policy
- Customer Data Subject Access Request Procedure

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
