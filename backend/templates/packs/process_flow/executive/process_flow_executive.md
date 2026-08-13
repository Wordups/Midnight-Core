# Customer Data Deletion Request Process

**Document Type:** Process Flow
**Variant:** Executive — One-page brief style, decision-maker focused, high-density. Shows up in board packs.

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

## Customer Data Deletion Process — At a Glance

- **Trigger: **Customer submits a deletion request through any accepted channel.
- **Commitment: **Production deletion within 21 days; backups within 30 days; full closure within 30-45 days.
- **Why it matters: **GDPR/CCPA/BAA deletion deadlines are statutory. Misses are notifiable to regulators.
- **Owner: **{{POLICY_OWNER}} | Reviewed annually | Next review: {{NEXT_REVIEW_DATE}}

## The Flow

| Step | Owner | SLO |
| --- | --- | --- |
| 1. Acknowledge | Customer Success | 1 business day |
| 2. Scope + authority verify | Customer Success | 3 business days |
| 3. Legal hold check (parallel) | Legal | 3 business days |
| DP-A. Proceed / partial / defer | Policy Owner | 1 business day after Steps 2+3 |
| 4. Production deletion | Data Ops | 21 calendar days |
| 5. Backup treatment (delete or cryptographic erasure) | Data Ops | 30 calendar days |
| 6. Subprocessor propagation | Customer Success + InfoSec | 30 calendar days |
| DP-B. Customer confirmation | Customer Success | 5 business days |
| 7. Closure with signed audit record | Policy Owner | 5 business days post-confirmation |

## Key Metrics

- Time-to-production-deletion median ≤ 14 days; 95th-percentile ≤ 21 days.
- Time-to-closure median ≤ 30 days; 95th-percentile ≤ 45 days.
- Subprocessor confirmation completeness: 100%.
- Reported quarterly to the Approver; available to internal audit on request.


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
