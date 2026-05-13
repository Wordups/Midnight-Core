# Encryption Standard

**Document ID:** TKO-STD-002
**Version:** 1.0
**Owner:** Brian Word, Founder
**Effective Date:** 2026-02-15
**Last Reviewed:** 2026-04-01
**Next Review:** 2027-04-01
**Frameworks:** SOC 2, NIST 800-53, PCI DSS
**Status:** Active

---

## 1. Purpose

This standard defines cryptographic requirements for protecting Takeoff LLC data at rest, in transit, and in use across all production systems.

## 2. Scope

Applies to all Takeoff systems processing customer data, internal data, or authentication material, including AWS infrastructure, application databases, S3 storage, and network communications.

## 3. Definitions

- **Data at Rest:** Data persisted to non-volatile storage
- **Data in Transit:** Data traversing a network between systems
- **Approved Algorithm:** A cryptographic algorithm meeting FIPS 140-2 or NIST SP 800-131A requirements

## 4. Standard Requirements

### 4.1 Encryption at Rest

All customer data is encrypted at rest using AES-256. All data in transit uses TLS 1.2 or higher. Encryption keys are managed via AWS KMS.

### 4.2 Encryption in Transit

- All network communications between Takeoff systems use TLS 1.2 or higher
- External API endpoints must support only TLS 1.2 and above
- Internal service-to-service communication uses mutual TLS where supported
- Deprecated protocols (SSLv2, SSLv3, TLS 1.0, TLS 1.1) are prohibited

### 4.3 Key Management

- All encryption keys are managed via AWS Key Management Service (KMS)
- Customer master keys (CMKs) are rotated annually
- Access to KMS key material is restricted to Founder and approved service accounts
- Key access events are logged to CloudTrail and retained for 2 years

### 4.4 Algorithm Requirements

Approved algorithms:
- Symmetric encryption: AES-256-GCM
- Asymmetric encryption: RSA-3072 or ECC P-384
- Hashing: SHA-256 or SHA-384
- Key derivation: PBKDF2 with minimum 600,000 iterations, or Argon2id

Prohibited algorithms:
- MD5, SHA-1 for security purposes
- DES, 3DES
- RC4

### 4.5 Certificate Management

- TLS certificates use minimum RSA-2048 or ECC P-256 keys
- Certificate expiration monitored with 30-day advance alerting
- Self-signed certificates prohibited in production

## 5. Roles and Responsibilities

- **Founder:** Approves cryptographic exceptions
- **Engineering:** Implements and maintains cryptographic controls

## 6. Enforcement

Deployments using prohibited algorithms or below-baseline configurations must be remediated within 30 days.

## 7. Review Cadence

Reviewed annually or upon material change to industry cryptographic standards.
