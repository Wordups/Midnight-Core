# Encryption Standard

**Document Type:** Standard
**Variant:** Formal — Legalese voice, full structure, traditional enterprise. The template a Fortune 500 General Counsel would approve.

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

## 1. Purpose

This Encryption Standard ("Standard") establishes the minimum cryptographic protections required for {{ORGANIZATION_NAME}}'s ("Organization") information assets, both at rest and in transit. This Standard is promulgated pursuant to the authority of the Information Security Policy and shall be construed in accordance with applicable laws, regulations, and contractual obligations to which the Organization is subject.

This Standard is intended to address considerations under applicable frameworks, including without limitation the HIPAA Security Rule (45 CFR Part 164, Subpart C), the Payment Card Industry Data Security Standard ("PCI DSS") v4.0 Requirements 3 and 4, the SOC 2 Trust Services Criterion CC6.1, and ISO/IEC 27001:2022 Annex A.8.24. Nothing herein shall be construed as creating an admission of compliance; such determinations are reserved to the Organization's auditors and regulators.

## 2. Scope

2.1 This Standard applies to all information assets classified Restricted or Confidential under the Data Classification Policy, and to all systems that create, receive, maintain, store, or transmit such information.

2.2 This Standard applies to: (i) endpoint devices owned or managed by the Organization; (ii) on-premises and cloud-hosted infrastructure operated by or on behalf of the Organization; (iii) data in transit over any external or untrusted network; and (iv) backup, archival, and disaster recovery copies of in-scope information assets.

2.3 In the event of a conflict between this Standard and a more restrictive customer requirement embodied in a written agreement, the more restrictive requirement shall govern.

## 3. Technical and Operational Requirements

### 3.1 Approved Cryptographic Algorithms

The following algorithms are approved for use under this Standard. Algorithms not enumerated below shall not be used to protect in-scope information assets absent written exception granted in accordance with Section 6.

| Use Case | Approved Algorithm(s) | Minimum Key Size |
| --- | --- | --- |
| Symmetric encryption at rest | AES (GCM, CCM, or CBC with HMAC) | 256 bits |
| Asymmetric encryption / key exchange | RSA-OAEP, ECDH (NIST curves P-256/P-384/P-521) | RSA 2048; ECC 256 |
| Digital signatures | RSA-PSS, ECDSA (NIST P-256/P-384/P-521), Ed25519 | RSA 2048; ECC 256 |
| Hash functions (general) | SHA-256, SHA-384, SHA-512, SHA-3 family | 256 bits |
| Password hashing | Argon2id (preferred), scrypt, bcrypt (cost >= 12) | N/A |
| Transport encryption | TLS 1.2 or TLS 1.3 with approved cipher suites | TLS 1.2 minimum |

### 3.2 Prohibited Algorithms

1. The use of MD5, SHA-1, RC4, DES, 3DES, and any algorithm with a published cryptanalytic break is prohibited for any security-relevant function.
2. The use of SSL (any version), TLS 1.0, and TLS 1.1 for the protection of Restricted or Confidential data in transit is prohibited.
3. The use of static or hard-coded cryptographic keys in source code, configuration files, or container images is prohibited.

### 3.3 Encryption at Rest

1. Restricted data stored in any persistent medium shall be encrypted using an approved symmetric algorithm with a minimum 256-bit key length.
2. Confidential data stored in any persistent medium shall be encrypted under the same requirements where technically feasible. Where not feasible, a documented compensating control shall be in place.
3. Endpoint devices used to access Restricted or Confidential data shall enable full-disk encryption with the recovery key escrowed in the Organization's key management service.
4. Database systems containing Restricted data shall employ transparent data encryption (TDE) or equivalent at the storage layer in addition to any field-level encryption applicable to specific data elements.
5. Backup and archival copies of in-scope data shall be encrypted under requirements equivalent to those applied to the source data.

### 3.4 Encryption in Transit

1. Restricted and Confidential data transmitted over any external or untrusted network shall be protected by TLS 1.2 or higher with approved cipher suites.
2. Internal service-to-service traffic carrying Restricted data shall use mutual TLS (mTLS) or equivalent where technically supported.
3. Email transmissions containing Restricted data shall use the Organization's approved secure email gateway or an equivalent end-to-end encrypted channel.
4. Web application endpoints serving Restricted data shall present a valid certificate issued by an approved certificate authority and shall enable HTTP Strict Transport Security with a minimum max-age of one year.

### 3.5 Key Management

1. Cryptographic keys shall be generated using a cryptographically secure pseudorandom number generator with an entropy source approved by the Information Security function.
2. Production keys shall be stored exclusively in an approved key management service, hardware security module, or equivalent. Storage of production keys in source code, configuration files, environment variables of unmanaged systems, or general-purpose secret stores is prohibited.
3. Symmetric keys protecting Restricted data shall be rotated at least annually or upon any reasonable suspicion of compromise.
4. Access to key management operations shall be controlled per the principle of least privilege and shall require multi-factor authentication for any administrative function.
5. Key destruction shall be performed in accordance with the Key Management Procedure and shall be documented in the Cryptographic Key Register.

## 4. Implementation Guidance

Implementation teams shall consult the Cryptographic Library Approved List, maintained by the Information Security function, when selecting libraries to implement the algorithms required by this Standard. Implementation of cryptographic primitives directly in application code is discouraged; teams shall use vetted libraries with active maintenance and a documented security response process.

New systems shall be designed for cryptographic agility, permitting the substitution of algorithms and key lengths without requiring a redesign of the data model or persistence layer. Where post-quantum considerations are material to the system's expected lifetime, the design shall accommodate the future addition of post-quantum algorithms.

## 5. Compliance Verification

1. The Information Security function shall conduct an annual review of the Organization's use of cryptographic algorithms, libraries, and key management services against this Standard.
2. Findings of non-conformance shall be documented in the Cryptographic Findings Register and remediated within the timeframes assigned by the Standard Owner.
3. New systems introduced to production shall be reviewed against this Standard as part of the change management process. Systems that materially fail this review shall not be released to production absent an approved exception.
4. Cryptographic verification evidence shall be retained in accordance with the Document Retention Schedule and shall be made available to internal and external auditors upon request.

## 6. Exceptions Process

Exceptions to this Standard may be granted only in writing. Requests shall be submitted to {{POLICY_OWNER}} setting forth: (i) the specific provision for which an exception is sought; (ii) the business justification; (iii) the proposed compensating control; and (iv) the proposed duration, not to exceed twelve (12) months without renewal. Approved exceptions shall be recorded in the Exception Register and reviewed at least every six (6) months. Exceptions implicating algorithms with known cryptanalytic weaknesses shall be granted only upon written approval of {{APPROVER_NAME}}.


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
