# Customer Data Deletion Request Process

**Document Type:** Process Flow
**Variant:** Formal — Legalese voice, full structure, traditional enterprise. The template a Fortune 500 General Counsel would approve.

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

## 1. Purpose

This Process Flow describes the steps to be performed upon receipt of a Customer Data Deletion Request ("Request") submitted by or on behalf of a customer of {{ORGANIZATION_NAME}} ("Organization"). This Process is promulgated pursuant to the Data Retention and Disposal Policy and shall be construed in accordance with applicable data protection laws, including the GDPR, CCPA/CPRA, and HIPAA Privacy Rule as applicable, and the Organization's Business Associate Agreements and customer Master Service Agreements.

## 2. Process Owner and Stakeholders

The Process Owner is {{POLICY_OWNER}}. The Process Stakeholders comprise the Customer Success function (intake), the Data Operations function (execution), the Legal function (legal hold review), the Information Security function (verification and cryptographic erasure), and where applicable, the HIPAA Privacy Officer for Requests involving Protected Health Information.

## 3. Process Steps

The Process consists of seven (7) sequential steps with two (2) defined decision points. Each step is associated with a target service-level objective ("SLO") measured from receipt of the Request.

### 3.1 Step 1 — Intake and Acknowledgement (SLO: 1 business day)

Customer Success shall acknowledge the Request in writing, record the Request in the Deletion Request Register, and assign a Request Identifier. The acknowledgement shall reference the contractually committed timeline for deletion.

### 3.2 Step 2 — Scope and Authority Verification (SLO: 3 business days)

Customer Success shall verify: (i) that the Request originates from an individual with apparent authority to submit it (typically the customer's authorized administrator or, for individual data subjects, the customer designated as Data Controller); (ii) the precise scope (full tenant deletion, a defined data subset, or specific records); and (iii) any customer-specific requirements communicated in the Request.

### 3.3 Step 3 — Legal Hold and Retention Review (SLO: 3 business days, parallel with Step 2)

Legal shall review the Deletion Request Register entry against the Legal Hold Register and any applicable statutory retention obligation. Where a hold or retention obligation conflicts with the Request, Legal shall document the obligation, the data subset affected, and a recommended treatment (defer, partial deletion, or excluded scope).

### 3.4 Decision Point A — Proceed or Defer

Customer Success, in consultation with Legal and {{POLICY_OWNER}}, shall determine whether the Request proceeds in full, proceeds in part with documented exclusions, or is deferred pending resolution of a legal obligation. The decision and its rationale shall be recorded in the Deletion Request Register and communicated to the customer in writing.

### 3.5 Step 4 — Production Deletion (SLO: 21 calendar days from Request)

Data Operations shall execute deletion in the production systems of record, including: the primary database, any read replicas, any cached or search-indexed copies, and any customer-facing exports retained in object storage. Execution shall follow the Data Deletion Procedure and shall produce a deletion ticket linked to the Deletion Request Register entry.

### 3.6 Step 5 — Backup and Archival Treatment (SLO: 30 calendar days, or per Backup Retention Schedule)

Data Operations shall apply the customer's data to the backup-deletion workflow. Where backup deletion is technically infeasible within the SLO, cryptographic erasure shall be applied to the per-customer encryption key, and the customer shall be notified of the deletion method.

### 3.7 Step 6 — Vendor and Subprocessor Propagation (SLO: 30 calendar days)

Customer Success, with support from Information Security, shall notify each subprocessor processing the customer's data of the Request. Subprocessors shall confirm deletion in writing in accordance with their contractual obligations. The Subprocessor Deletion Confirmation log shall be maintained.

### 3.8 Decision Point B — Customer Confirmation

Customer Success shall present to the customer the deletion summary, including: confirmation of production deletion, the backup treatment applied, and subprocessor confirmations received. The customer shall be invited to acknowledge in writing.

### 3.9 Step 7 — Closure and Audit Record (SLO: 5 business days after customer confirmation)

Upon customer acknowledgement or, in the absence of customer response within fifteen (15) business days, the Process Owner shall close the Deletion Request Register entry. The closure record shall include: deletion ticket reference(s), subprocessor confirmations, cryptographic erasure record (if applicable), and any exclusions with rationale.

## 4. Inputs and Outputs per Step

| Step | Inputs | Outputs |
| --- | --- | --- |
| 1 | Customer Request | Acknowledgement; Deletion Request Register entry |
| 2 | Register entry; customer authority artifacts | Verified scope and authority record |
| 3 | Register entry; Legal Hold Register | Hold/retention applicability record |
| DP-A | Steps 2 and 3 outputs | Proceed/defer/partial decision |
| 4 | Decision; production systems | Deletion ticket; production confirmation |
| 5 | Backup Retention Schedule | Backup deletion ticket OR cryptographic erasure record |
| 6 | Subprocessor list | Subprocessor confirmation log |
| DP-B | Deletion summary | Customer acknowledgement (or non-response timeout) |
| 7 | All artifacts | Closed register entry; audit record |

## 5. Roles per Step (RACI)

R = Responsible (does the work); A = Accountable (owns the outcome); C = Consulted; I = Informed.

| Step | Customer Success | Data Ops | Legal | Info Sec |
| --- | --- | --- | --- | --- |
| 1 Intake | R/A | I | I | I |
| 2 Scope | R/A | C | C | I |
| 3 Legal hold | I | I | R/A | I |
| DP-A | A | C | C | C |
| 4 Production | I | R/A | C | C |
| 5 Backup | I | R/A | I | C |
| 6 Subprocessors | R | C | I | A |
| DP-B | R/A | C | I | I |
| 7 Closure | A | C | I | C |

## 6. Process Metrics

1. Time-to-Acknowledge: median and 95th-percentile elapsed time from Request receipt to written acknowledgement. Target: median ≤ 1 business day; 95th-percentile ≤ 2 business days.
2. Time-to-Production-Deletion: median and 95th-percentile elapsed time from Request receipt to production deletion confirmation. Target: median ≤ 14 calendar days; 95th-percentile ≤ 21 calendar days.
3. Time-to-Closure: median and 95th-percentile elapsed time from Request receipt to register-entry closure. Target: median ≤ 30 calendar days; 95th-percentile ≤ 45 calendar days.
4. Subprocessor Confirmation Completeness: percentage of in-scope subprocessors providing written confirmation within thirty (30) days. Target: 100%.
5. Cryptographic Erasure Rate: percentage of Requests where cryptographic erasure was applied to backup copies. Tracked for trend analysis.
6. Metrics shall be reviewed quarterly by the Process Owner with the Approver.


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
