# Customer Data Deletion Request Process

**Document Type:** Process Flow
**Variant:** Detailed — Comprehensive, long-form, every consideration covered. The template a regulated startup would use to over-prepare.

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

This Process Flow describes, in exhaustive detail, the steps to be performed by {{ORGANIZATION_NAME}} upon receipt of a Customer Data Deletion Request submitted by or on behalf of a customer. The Process is designed to satisfy: (i) the Organization's contractual obligations under customer Master Service Agreements and Business Associate Agreements; (ii) statutory obligations under the General Data Protection Regulation (Article 17 — Right to Erasure), the California Consumer Privacy Act as amended by the California Privacy Rights Act (Section 1798.105), the HIPAA Privacy Rule provisions concerning return or destruction of PHI upon termination of a Business Associate relationship (45 CFR 164.504(e)(2)(ii)(J)); and (iii) any applicable laws of jurisdictions where the customer's data subjects reside.

The Process integrates four organizational functions (Customer Success, Data Operations, Legal, and Information Security) and produces a complete, auditable record from intake through closure. Where this Process and a specific customer agreement conflict, the customer agreement shall govern; where this Process and applicable law conflict, applicable law shall govern.

## Process Owner and Stakeholders

The Process Owner is {{POLICY_OWNER}}, who is responsible for maintenance, review, and reporting of this Process. The Process Stakeholders, each of whom owns specific steps within the Process, are:

- **Customer Success: **Responsible for intake, scope and authority verification, customer communication, and closure.
- **Data Operations: **Responsible for production deletion, backup treatment, and any cross-system propagation under direct Organization control.
- **Legal: **Responsible for legal hold review, retention obligation analysis, and any customer escalation involving legal interpretation.
- **Information Security: **Responsible for cryptographic erasure operations, verification of deletion completeness, and subprocessor confirmation tracking.
- **HIPAA Privacy Officer (where applicable): **Consulted for Requests involving Protected Health Information; signs off on partial-deletion treatments where PHI is involved.

## Process Steps

The Process consists of seven (7) sequential primary steps with two (2) defined decision points. Each step is associated with target service-level objectives ("SLOs") measured from receipt of the Request. SLOs are operational targets and do not modify any contractually committed deletion deadline.

### Step 1 — Intake and Acknowledgement

SLO: One (1) business day from Request receipt.

Customer Success receives the Request through any of the accepted intake channels (customer-facing support portal, named contact email, customer success manager direct outreach). Within the SLO, Customer Success shall: (i) acknowledge the Request in writing to the originating customer contact; (ii) create an entry in the Deletion Request Register with a Request Identifier in the format DR-YYYY-NNNN; (iii) record the date and time of intake, the originating contact, the apparent scope, and any customer-stated deadline; and (iv) classify the Request by type (full tenant deletion, partial data deletion, end-of-relationship deletion).

### Step 2 — Scope and Authority Verification

SLO: Three (3) business days from Request receipt.

Customer Success shall verify the following before deletion proceeds:

1. The Requester has apparent authority. For deletions affecting an entire customer tenant, the Requester shall be a designated administrative contact of record. For Requests affecting a subset of records (e.g., a specific patient or end-user), the Requester shall be the customer's designated data protection contact who, in turn, shall represent the authority of the data subject or controller.
2. The scope of the Request is unambiguous. For partial deletions, the precise dataset shall be identified by customer-tenant identifier, data class, time range, and any other relevant qualifier. Ambiguity shall be resolved in writing with the customer before proceeding.
3. Any customer-specific contractual requirements (deletion deadlines shorter than statutory defaults, specific deletion-method preferences, post-deletion reporting requirements) are surfaced and recorded in the Deletion Request Register entry.

### Step 3 — Legal Hold and Retention Review

SLO: Three (3) business days from Request receipt; executed in parallel with Step 2.

Legal shall review the Deletion Request Register entry against:

1. The Legal Hold Register, identifying any active legal hold (litigation, regulatory inquiry, governmental investigation) that may suspend or modify deletion of the customer's data.
2. Applicable statutory retention obligations (tax records, employment records where the customer is an employer, healthcare records subject to HIPAA retention requirements).
3. Customer contractual requirements that may impose retention obligations (post-termination data retention windows, audit-period retention).

Where any hold or retention obligation is identified, Legal shall document the obligation, the affected data subset, and the recommended treatment in the Deletion Request Register entry. Recommended treatments include: deferred deletion until the obligation expires; partial deletion with documented retention exclusions; or, in exceptional cases, declination of the Request pending customer agreement.

### Decision Point A — Proceed, Partial, or Defer

Following completion of Steps 2 and 3, {{POLICY_OWNER}}, in consultation with Customer Success and Legal, shall make a documented decision among the following options: (i) Proceed in full — execute the Request as scoped; (ii) Proceed in part — execute the Request with documented exclusions, with the customer notified of the exclusions; (iii) Defer — pause the Request pending resolution of a legal hold or retention obligation, with the customer notified of the deferral and the expected resumption window. The decision and its rationale shall be recorded in the Deletion Request Register and communicated to the customer in writing within one (1) business day of the decision.

### Step 4 — Production Deletion

SLO: Twenty-one (21) calendar days from Request receipt.

Data Operations shall execute the Data Deletion Procedure against all production systems holding the in-scope data:

1. Primary database — including any sharded or partitioned storage and all read replicas.
2. Application caches — including all distributed cache layers and search indexes derived from the primary database.
3. Customer-facing object storage — including any reports, exports, or attachments retained on behalf of the customer.
4. Operational data warehouse — including any aggregate or analytical copy derived from the customer's data, where the copy retains personally identifying information.
5. Audit log retention — subject to the Audit Log Retention Standard, which may require continued retention of access logs (without underlying data) for the audit-readiness period.

Each deletion shall produce a deletion ticket containing: the system identifier, the dataset deleted, the operator, the timestamp, and a hash of the pre-deletion dataset count (or other reproducible verification). Tickets shall be linked to the Deletion Request Register entry.

### Step 5 — Backup and Archival Treatment

SLO: Thirty (30) calendar days from Request receipt, or per the Backup Retention Schedule, whichever is sooner.

Backup and archival copies require special handling because immediate deletion from immutable or append-only backup media is frequently infeasible. The following treatments apply, in priority order:

1. For backups using per-customer encryption keys, cryptographic erasure of the customer's data key constitutes destruction for purposes of this Process. The cryptographic erasure event shall be witnessed by a second authorized operator and recorded in the Cryptographic Key Register.
2. For backups using shared encryption keys, deletion shall occur upon the natural expiration of the backup retention window. Where the natural expiration falls within thirty (30) days, no special action is required beyond ensuring expiry is not extended. Where expiration falls outside thirty (30) days, the Information Security function shall evaluate the feasibility of accelerated deletion against the operational cost of restoring backup chains.
3. In all cases, the customer shall be notified in writing of the deletion method and the timeline.

### Step 6 — Vendor and Subprocessor Propagation

SLO: Thirty (30) calendar days from Request receipt.

Customer Success, with support from Information Security, shall notify each subprocessor processing the customer's data of the Request. The list of in-scope subprocessors shall be derived from the Subprocessor Register and shall include any subprocessor with a documented data processing relationship for the affected customer tenant. Subprocessors shall confirm deletion in writing in accordance with their contractual obligations. Confirmations shall be recorded in the Subprocessor Deletion Confirmation log linked to the Deletion Request Register entry.

### Decision Point B — Customer Confirmation

Customer Success shall present to the customer a Deletion Summary containing: confirmation of production deletion (with deletion ticket references); the backup treatment applied (deletion, cryptographic erasure, or natural-expiration); subprocessor confirmations received and outstanding; and any documented exclusions. The customer shall be invited to acknowledge the summary in writing. Acknowledgement may be express (signed confirmation) or implicit (non-response within fifteen (15) business days of receipt, with the original communication evidencing delivery).

### Step 7 — Closure and Audit Record

SLO: Five (5) business days after customer acknowledgement (or after the implicit-acknowledgement timeout).

The Process Owner shall close the Deletion Request Register entry. The closure record shall be cryptographically signed and shall contain: the Request Identifier; the dates of intake, decision, production deletion, backup treatment, subprocessor confirmation, and closure; the operator(s) for each step; the deletion ticket references; the subprocessor confirmation log; the cryptographic erasure record (where applicable); any documented exclusions with rationale; and the customer acknowledgement (express or implicit).

## Inputs and Outputs per Step

| Step | Inputs | Outputs |
| --- | --- | --- |
| 1 | Customer Request (intake channel record) | Acknowledgement; Deletion Request Register entry |
| 2 | Register entry; customer authority records; agreement repository | Verified scope, authority, and customer-specific requirements |
| 3 | Register entry; Legal Hold Register; retention obligation matrix | Hold/retention applicability record; recommended treatment |
| DP-A | Outputs of Steps 2 and 3 | Proceed/partial/defer decision and rationale |
| 4 | Decision; production systems; Data Deletion Procedure | Deletion tickets per system; production confirmation |
| 5 | Backup Retention Schedule; Cryptographic Key Register | Backup deletion ticket OR cryptographic erasure record |
| 6 | Subprocessor Register | Subprocessor Deletion Confirmation log entries |
| DP-B | Deletion Summary | Customer acknowledgement (express or implicit) |
| 7 | All artifacts | Closed register entry; cryptographically signed audit record |

## Roles per Step (RACI)

R = Responsible (performs the work); A = Accountable (owns the outcome); C = Consulted; I = Informed.

| Step | Customer Success | Data Ops | Legal | Info Sec | Privacy Officer |
| --- | --- | --- | --- | --- | --- |
| 1 Intake | R/A | I | I | I | I |
| 2 Scope/Authority | R/A | C | C | I | I |
| 3 Legal hold | I | I | R/A | I | C |
| DP-A | A | C | C | C | C |
| 4 Production | I | R/A | C | C | I |
| 5 Backup | I | R/A | I | C | I |
| 6 Subprocessors | R | C | I | A | I |
| DP-B | R/A | C | I | I | C |
| 7 Closure | A | C | I | C | I |

## Process Metrics

1. Time-to-Acknowledge: median and 95th-percentile elapsed time from Request receipt to written acknowledgement. Target: median ≤ 1 business day; 95th-percentile ≤ 2 business days.
2. Time-to-Production-Deletion: median and 95th-percentile elapsed time from Request receipt to production deletion confirmation across all in-scope systems. Target: median ≤ 14 calendar days; 95th-percentile ≤ 21 calendar days.
3. Time-to-Closure: median and 95th-percentile elapsed time from Request receipt to register-entry closure. Target: median ≤ 30 calendar days; 95th-percentile ≤ 45 calendar days.
4. Subprocessor Confirmation Completeness: percentage of in-scope subprocessors providing written confirmation within thirty (30) days of notification. Target: 100%.
5. Cryptographic Erasure Rate: percentage of Requests where cryptographic erasure was applied to backup copies (as distinct from natural expiration or selective deletion). Tracked for trend analysis and architecture decisions.
6. Decision Point A Defer Rate: percentage of Requests subject to deferred or partial decisions at Decision Point A. Trends toward an elevated defer rate warrant review of customer agreement templates and legal hold management.
7. Customer Acknowledgement Rate: percentage of Requests closed with express (rather than implicit) customer acknowledgement. Used to assess customer engagement and communication quality.
8. Metrics shall be reported quarterly by the Process Owner to the Approver and shall be made available to internal audit and to customer-driven attestation engagements upon request.


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
