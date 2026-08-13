# Encryption Standard

**Document Type:** Standard
**Variant:** Modern — Scannable, plain-language, modern enterprise. Short paragraphs, clear headings, designed for readability.

---

## Cover Page

[LOGO: organization_logo.png] *(centered, 2" × 2")*

**Encryption Standard** — {{DOCUMENT_TITLE}}

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

This standard says which encryption algorithms we use, where we use them, and how we handle the keys. If you're building or operating a system that handles customer data, source code, financial records, or anything classified Restricted or Confidential, this applies to you.

The goal is to make encryption decisions boring. You shouldn't have to guess what cipher to use; the right answer is in this document.

## Scope

- All Restricted and Confidential data (PHI, payment data, source code, customer records).
- Endpoints, servers, databases, backups, and any system that holds in-scope data.
- Data in transit over the internet or any network we don't fully control.
- Includes our own systems and any vendor system handling our data.

## Technical Requirements

### What to use

| Where | Use | Notes |
| --- | --- | --- |
| Data at rest | AES-256 (GCM preferred) | Use TDE for databases, full-disk encryption for laptops. |
| Data in transit | TLS 1.2 or TLS 1.3 | Strong cipher suites only — no RC4, no CBC without HMAC. |
| Service-to-service | mTLS | For anything carrying Restricted data inside our VPC. |
| Passwords | Argon2id or scrypt; bcrypt cost >= 12 if needed | Never SHA-256 or MD5 for passwords. |
| Public-key | RSA 2048+ or ECC P-256+ | Ed25519 is fine where supported. |

### What not to use

- No MD5 or SHA-1 for anything security-relevant.
- No DES, 3DES, or RC4. They're dead.
- No TLS 1.0 or 1.1. Disable them at the load balancer.
- No hard-coded keys in source. Ever. We grep for this.

### Keys

- Production keys live in our key management service. Not in env files. Not in code. Not in 1Password (those are for humans).
- Rotate keys protecting Restricted data at least once a year. Faster if you suspect compromise.
- Use cryptographic agility — design so we can swap algorithms without rewriting the schema.
- Key destruction is documented and logged. Talk to {{POLICY_OWNER}} if you're destroying a production key.

## Implementation Guidance

Use libraries from the Cryptographic Library Approved List. Don't implement primitives yourself. If you're reaching for a custom crypto solution, talk to {{POLICY_OWNER}} first — usually there's a vetted library that does what you need.

For new systems with a long expected lifetime, design for post-quantum. You don't have to use PQ algorithms today, but your data model should make it easy to add them later.

## Compliance Verification

- Information Security reviews our cryptographic posture annually.
- Findings go in the Cryptographic Findings Register with assigned owners and dates.
- Every new system gets a crypto review as part of change management.
- We keep evidence so auditors can verify — usually for at least 7 years.

## Exceptions Process

If you need to deviate, submit a request to {{POLICY_OWNER}} with: what you're doing differently, why, what compensating control you're using, and for how long (default 90 days, renewable). Exceptions to ban-list algorithms (MD5, SHA-1, DES, etc.) require approval from {{APPROVER_NAME}}.


## Roles and Responsibilities

| Role | Responsibilities |
| --- | --- |
| Standard Owner ({{POLICY_OWNER}}) | Maintains this Standard, schedules reviews, processes exception requests, and reviews cryptographic library advisories. |
| Approver ({{APPROVER_NAME}}, {{APPROVER_TITLE}}) | Provides executive approval at issuance and at each annual review. |
| Implementation Lead | Validates that the technical requirements of this Standard are implemented in production systems within the timeframes specified. |
| End User / System Operator | Operates within the Standard. Reports cryptographic incidents and approved-algorithm exceptions through documented channels. |

## Review and Maintenance

**Next review date:** {{NEXT_REVIEW_DATE}}

**Review frequency:** Annually, or upon a qualifying trigger (cryptographic library deprecation, algorithm advisory, audit finding).

**Review triggers:**

- A material change in applicable laws, regulations, or contractual obligations.
- Findings from an internal or external audit that affect this document.
- A security or privacy incident that exposes a gap in the document.
- An organizational change (acquisition, divestiture, new business line) that affects scope.

## Related Documents

- Information Security Policy
- Access Control Policy
- Data Classification Policy
- Key Management Procedure

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
