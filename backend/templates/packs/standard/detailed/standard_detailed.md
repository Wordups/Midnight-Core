# Encryption Standard

**Document Type:** Standard
**Variant:** Detailed — Comprehensive, long-form, every consideration covered. The template a regulated startup would use to over-prepare.

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

The purpose of this Encryption Standard is to specify the minimum cryptographic protections that {{ORGANIZATION_NAME}} requires for information assets at rest, in transit, in use where technically feasible, and during cryptographic key management operations. This Standard establishes a normative baseline against which the Organization's systems, vendors, and operational practices may be evaluated for audit-readiness against the HIPAA Security Rule (45 CFR Part 164, Subpart C), PCI DSS v4.0 (Requirements 3.5, 3.6, 3.7, and 4.1), SOC 2 Type II Trust Services Criteria (CC6.1, CC6.6, CC6.7), ISO/IEC 27001:2022 (Annex A.8.24, A.8.25, A.8.26), NIST SP 800-57 (Key Management Recommendations), and any contractual cryptographic requirements to which the Organization has agreed.

This Standard is one component of the Organization's information security program. It is operationally subordinate to the Information Security Policy and operates in conjunction with the Data Classification Policy (which determines what is in scope), the Key Management Procedure (which specifies operational handling of cryptographic keys), and the Vulnerability Management Policy (which governs the Organization's response to disclosed cryptographic weaknesses).

## Scope

### In-Scope Data Classes

1. Data classified Restricted under the Data Classification Policy, including but not limited to Protected Health Information (PHI) as defined in 45 CFR Section 160.103, payment card data within the scope of PCI DSS, attorney-client privileged communications, government-classified information, and any other class designated Restricted by the Information Security function.
2. Data classified Confidential under the Data Classification Policy, including but not limited to source code, financial records, customer lists, pricing, contracts, strategic plans, and human resources records.
3. Authentication secrets, cryptographic keys, and other security parameters regardless of the classification of the underlying data they protect.
4. Backup, archival, and disaster recovery copies of in-scope data, and any derived dataset that retains the sensitivity of the original.

### In-Scope Systems

1. Endpoint devices owned, leased, or managed by the Organization, including laptops, desktops, tablets, and mobile devices.
2. Server infrastructure, whether on-premises or cloud-hosted, operated by or on behalf of the Organization.
3. Database systems, object storage, file shares, and any persistent medium holding in-scope data.
4. Application-level encryption layers including envelope encryption, field-level encryption, and tokenization services.
5. Network infrastructure providing transport security including load balancers, reverse proxies, VPN concentrators, and service meshes.
6. Key management services including cloud-provider KMS, dedicated HSMs, and any equivalent service.
7. Backup, archival, and disaster recovery systems and their associated key management infrastructure.
8. Third-party services contractually permitted to process in-scope data on behalf of the Organization.

## Technical and Operational Requirements

### Approved Cryptographic Algorithms

The following algorithms are approved for use. Any algorithm not enumerated below shall not be used to protect in-scope information assets without a written exception granted in accordance with the Exceptions Process. The Information Security function maintains a current Cryptographic Algorithm Approved List as an operational reference; in the event of a conflict between that list and this Standard, this Standard shall govern.

| Use Case | Approved Algorithm | Min Key/Output | Notes |
| --- | --- | --- | --- |
| Symmetric (at rest) | AES-GCM, AES-CCM, AES-CBC with HMAC-SHA256 | 256-bit key | AES-GCM is preferred for new systems. |
| Symmetric (transit auth) | AES-GCM, ChaCha20-Poly1305 | 256-bit key | Both provide AEAD. |
| Asymmetric encryption | RSA-OAEP (SHA-256 or SHA-384), ECIES | RSA 2048; ECC 256 | For envelope encryption of symmetric keys. |
| Key exchange | ECDH (P-256, P-384, P-521), X25519 | ECC 256 | Use ephemeral keys for forward secrecy. |
| Digital signatures | RSA-PSS, ECDSA (P-256, P-384), Ed25519 | RSA 2048; ECC 256 | Ed25519 preferred where supported. |
| Cryptographic hash | SHA-256, SHA-384, SHA-512, SHA-3 family | 256-bit output | Truncated SHA-512 acceptable. |
| MAC | HMAC-SHA256, HMAC-SHA384, HMAC-SHA512 | 256-bit output | For non-AEAD use. |
| Password hashing | Argon2id (preferred), scrypt, bcrypt (cost >= 12) | Per algorithm spec | Never general hashes for passwords. |
| TLS | TLS 1.2 (constrained suites) or TLS 1.3 | Per RFC 8446 | TLS 1.3 preferred for new systems. |

### Prohibited Algorithms and Protocols

1. Hash functions: MD5, SHA-1, RIPEMD-160, and any hash with a public collision attack.
2. Symmetric ciphers: DES, 3DES, RC4, RC2, IDEA, Blowfish (legacy use only with exception).
3. Public-key parameters: RSA keys below 2048 bits; ECC curves not enumerated as approved; DH groups below 2048 bits.
4. Protocols: SSL all versions, TLS 1.0, TLS 1.1, SSHv1, IKEv1 with weak transforms.
5. Construction: ECB mode for any symmetric cipher; CBC mode without authenticated MAC; nonce reuse with stream ciphers or GCM.
6. Implementation: hard-coded keys in source code, configuration files, or container images; reliance on default initialization vectors; use of non-cryptographic random number generators for security-relevant operations.

### Encryption at Rest

1. Restricted data shall be encrypted under an approved symmetric algorithm with a minimum 256-bit key in every persistent medium where it is stored.
2. Confidential data shall be encrypted under the same requirements where technically feasible. Where infeasible, a written compensating control shall be documented and approved.
3. Endpoint devices accessing Restricted or Confidential data shall enable full-disk encryption with the recovery key escrowed in the Organization's key management service.
4. Database systems containing Restricted data shall employ transparent data encryption (TDE) at the storage layer. Additional field-level encryption shall be applied to specific sensitive elements where the data classification or customer agreement requires it.
5. Backup and archival copies shall be encrypted under requirements equivalent to those applied to the source data, with keys managed independently of the source data's keys to prevent simultaneous compromise.
6. Cryptographic erasure (the deletion of the protecting key) is an approved data-destruction technique for in-scope data when documented and witnessed in accordance with the Data Retention and Disposal Policy.

### Encryption in Transit

1. Restricted and Confidential data transmitted over any external network shall be protected by TLS 1.2 or higher with approved cipher suites enabling forward secrecy.
2. TLS configurations shall be reviewed at least annually against the current Mozilla SSL Configuration Generator "Intermediate" profile or its successor.
3. Internal service-to-service traffic carrying Restricted data shall use mutual TLS (mTLS) authentication where technically supported.
4. Web applications shall enable HTTP Strict Transport Security with a minimum max-age of 31,536,000 seconds (one year) and shall preload where appropriate.
5. Application APIs carrying Restricted data shall reject plaintext connections at the application layer in addition to network-layer enforcement.
6. Email transmissions carrying Restricted data shall use either the Organization's approved secure email gateway with opportunistic TLS or an end-to-end encrypted channel.

### Cryptographic Key Management

1. Keys shall be generated using a cryptographically secure pseudorandom number generator (CSPRNG) seeded from an entropy source approved by the Information Security function.
2. Production keys shall be stored exclusively in an approved key management service or hardware security module. Storage of production keys in source code, configuration files, environment variables on unmanaged systems, container images, or general-purpose secret stores is prohibited.
3. Symmetric keys protecting Restricted data shall be rotated at least annually. Symmetric keys protecting Confidential data shall be rotated at least every two (2) years. Asymmetric key pairs shall be rotated at least every three (3) years or at the expiration of the associated certificate, whichever is earlier.
4. Keys shall be rotated promptly upon reasonable suspicion of compromise, role change of any human operator with knowledge of the key, or the disclosure of a cryptographic weakness affecting the algorithm or library.
5. Access to key management operations shall be controlled per the principle of least privilege. Administrative operations including key creation, rotation, deletion, and policy modification shall require multi-factor authentication and shall be logged with the actor, timestamp, and operation details.
6. Key destruction shall be performed in accordance with the Key Management Procedure. Destruction of a production key affecting Restricted data shall be witnessed by a second authorized operator and recorded in the Cryptographic Key Register.
7. Cryptographic operations performed by third-party services on behalf of the Organization shall be subject to written contractual provisions consistent with this Standard, including provisions addressing key residency, key ownership upon termination, and breach notification.

### Cryptographic Agility

New systems shall be designed for cryptographic agility, permitting the substitution of algorithms, key sizes, and protocols without redesigning the data model or persistence layer. Specifically: (i) ciphertext shall be tagged with the algorithm and key identifier used to produce it; (ii) the data plane shall be agnostic to the specific algorithm in use; and (iii) the system shall support concurrent operation of multiple algorithms during a transition.

### Post-Quantum Considerations

Systems whose protected data has an expected sensitivity lifetime exceeding ten (10) years shall be designed to permit the future incorporation of post-quantum cryptographic algorithms upon their standardization and approval by the Information Security function. The Organization shall track the standardization status of post-quantum algorithms and shall update this Standard upon material developments.

## Implementation Guidance

Implementation teams shall consult the Cryptographic Library Approved List when selecting libraries to satisfy the requirements of this Standard. Direct implementation of cryptographic primitives in application code is discouraged absent compelling business justification; teams shall use vetted libraries with active maintenance, a documented security response process, and continued community or commercial support.

Common implementation patterns approved under this Standard include: (a) envelope encryption with KMS-managed data keys for application-level encryption; (b) database transparent data encryption for storage-layer protection; (c) reverse-proxy TLS termination with mTLS between proxy and origin for service-mesh deployments; and (d) hardware-backed key storage on endpoint devices for credential and certificate protection. Other patterns may be approved upon review by the Information Security function.

## Compliance Verification

1. The Information Security function shall conduct a documented annual review of the Organization's use of cryptographic algorithms, libraries, key management services, and TLS configurations against this Standard.
2. Findings of non-conformance shall be documented in the Cryptographic Findings Register with severity, affected systems, assigned remediation owner, and target remediation date.
3. New systems and material changes to existing systems shall be reviewed against this Standard as part of the change management process. The review shall include verification of algorithm selection, key management approach, and library version.
4. Findings classified High or Critical shall be remediated or compensated within thirty (30) days of identification; Medium findings within sixty (60) days; Low findings within one-hundred-twenty (120) days. Exceptions to these timeframes require written approval of {{POLICY_OWNER}}.
5. Cryptographic verification evidence shall be retained for a minimum of seven (7) years and shall be made available to internal and external auditors upon request.

## Exceptions Process

Exceptions to specific provisions of this Standard may be granted only in writing under the following process. The Authorized User or system owner shall submit an Exception Request Form to {{POLICY_OWNER}} setting forth: (a) the specific provision for which an exception is sought; (b) the business justification for the exception; (c) the alternative cryptographic control(s) that will mitigate the risk addressed by the provision; (d) the proposed duration of the exception, not to exceed twelve (12) months without renewal; and (e) the proposed acceptance signatory.

{{POLICY_OWNER}} shall evaluate each request in consultation with the Information Security function within ten (10) business days. Material exceptions, including any exception involving prohibited algorithms or key management deviations, shall be referred to {{APPROVER_NAME}}. Approved exceptions shall be documented in the Exception Register and reviewed at least every six (6) months. No exception shall be effective absent written documentation.


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
