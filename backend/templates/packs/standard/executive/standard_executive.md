# Encryption Standard

**Document Type:** Standard
**Variant:** Executive — One-page brief style, decision-maker focused, high-density. Shows up in board packs.

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

## Encryption Standard — At a Glance

- **Applies to: **All Restricted and Confidential data, at rest and in transit, across all systems we own or vendor on our behalf.
- **What it does: **Defines approved cryptographic algorithms, key management requirements, and TLS standards.
- **Why it matters: **Encryption posture is one of the first ten things every auditor asks about.
- **Owner: **{{POLICY_OWNER}} | Reviewed annually | Next review: {{NEXT_REVIEW_DATE}}

## Use This

| Where | Use | Min Strength |
| --- | --- | --- |
| At rest | AES-GCM | 256-bit key |
| In transit (external) | TLS 1.2+ (TLS 1.3 preferred) | PFS suites only |
| In transit (internal, Restricted) | mTLS | 256-bit key |
| Passwords | Argon2id | Per spec |
| Public-key | RSA-PSS, ECDSA P-256+, or Ed25519 | RSA 2048 / ECC 256 |

## Not This

MD5, SHA-1, DES, 3DES, RC4. TLS 1.0, TLS 1.1, any SSL. Hard-coded keys. Any algorithm with a published cryptanalytic break.

## Keys

- Production keys in KMS or HSM. Never in source, configs, or env vars on unmanaged hosts.
- Rotate annually (Restricted) or every two years (Confidential). Faster on suspected compromise.
- Multi-factor authentication required for any key admin operation.
- Destruction is logged. Cryptographic erasure (delete the key) is an approved disposal method.

## Verification

Annual Information Security review. Per-change review at change management. Findings tracked in the Cryptographic Findings Register with assigned owners and SLAs.

## Exceptions

Submit to {{POLICY_OWNER}}. Decision in ten business days. Prohibited-algorithm exceptions require {{APPROVER_NAME}} approval. Max duration twelve months. Tracked in the Exception Register.


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
