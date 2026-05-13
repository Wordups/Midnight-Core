# Information Security Policy

**Document ID:** TKO-POL-001
**Version:** 1.2
**Owner:** Brian Word, Founder
**Effective Date:** 2026-01-15
**Last Reviewed:** 2026-04-01
**Next Review:** 2027-04-01
**Frameworks:** SOC 2, NIST CSF 2.0, ISO 27001
**Status:** Active

---

## 1. Purpose

This policy establishes the foundational information security requirements for Takeoff LLC and all subsidiary products, including Midnight. It defines the principles by which Takeoff protects the confidentiality, integrity, and availability of customer data, intellectual property, and operational systems.

## 2. Scope

This policy applies to:
- All Takeoff LLC employees, contractors, and authorized agents
- All Takeoff-owned or operated information systems, including AWS production infrastructure (us-east-1), GitHub repositories, and SaaS tools
- All customer data processed by Midnight, including uploaded policies, generated artifacts, and tenant metadata
- All third-party vendors with access to Takeoff systems or data

## 3. Definitions

- **Confidential Data:** Customer-uploaded documents, generated policy packs, tenant identifiers, billing information, and any internal Takeoff financial or strategic records
- **Production System:** Any AWS resource, database, or service that processes live customer data
- **Authorized User:** An individual with a documented business need and approved access to a Takeoff system

## 4. Policy Statements

### 4.1 Data Classification
All data handled by Takeoff systems will be classified as Public, Internal, Confidential, or Restricted. Customer-uploaded artifacts default to Confidential. Generated outputs default to Confidential and inherit the customer's tenant scope.

### 4.2 Access Control
Access to production systems requires multi-factor authentication. All access is granted on a least-privilege basis. Access reviews are conducted quarterly.

### 4.3 Encryption
All customer data is encrypted at rest using AES-256. All data in transit uses TLS 1.3 or higher. Encryption keys are managed via AWS KMS.

### 4.4 Incident Response
Security incidents are managed in accordance with the Takeoff Incident Response Policy (TKO-POL-003). All incidents involving customer data trigger customer notification within 72 hours.

### 4.5 Vendor Management
Third-party vendors with access to Takeoff systems or data must undergo a security review prior to onboarding. Vendor reviews are repeated annually.

## 5. Roles and Responsibilities

- **Founder (CISO function):** Owns this policy, approves exceptions, signs off on annual review
- **Engineering:** Implements technical controls, maintains AWS configuration baselines
- **All Personnel:** Comply with this policy, complete security awareness training annually

## 6. Enforcement

Violations of this policy may result in disciplinary action, including termination of employment or contractor engagement, and may be reported to relevant authorities where required by law.

## 7. Review Cadence

This policy is reviewed annually or upon material change to Takeoff systems or regulatory obligations.
