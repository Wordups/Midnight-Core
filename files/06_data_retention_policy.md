# Data Retention Policy

**Document ID:** TKO-POL-005
**Version:** 0.9
**Owner:** _[unassigned]_
**Effective Date:** 2024-08-15
**Last Reviewed:** 2024-08-15
**Next Review:** 2025-08-15
**Frameworks:** SOC 2
**Status:** Active

---

## 1. Purpose

This policy defines how Takeoff LLC retains and disposes of data across customer artifacts, operational records, and corporate documents.

## 2. Scope

Applies to all data created, processed, or stored by Takeoff systems, including:
- Customer-uploaded source documents
- Midnight-generated policy and GRC artifacts
- Audit logs and access logs
- Billing and contractual records
- Internal corporate documents

## 3. Definitions

- **Active Data:** Data currently in use by ongoing business operations
- **Archived Data:** Data retained for compliance or business continuity but not actively used
- **Disposal:** Secure deletion or destruction of data such that recovery is infeasible

## 4. Policy Statements

### 4.1 Customer Data Retention

- Customer-uploaded source documents: retained for the duration of the active subscription plus **90 days** after termination
- Midnight-generated artifacts: retained for the duration of the active subscription plus **180 days** after termination
- Customer may request deletion at any time during active subscription

### 4.2 Audit Log Retention

- Application audit logs: **365 days**
- Security event logs: **2 years**
- Authentication logs: **1 year**

### 4.3 Financial Records

- Invoices and payment records: **7 years**
- Tax records: **7 years**

### 4.4 Corporate Records

- Contracts and agreements: **life of contract plus 7 years**
- Personnel records: **7 years after separation**

### 4.5 Disposal Requirements

Data scheduled for disposal must be deleted using cryptographic erasure (key destruction) or NIST 800-88 compliant overwrite methods.

## 5. Roles and Responsibilities

- **Founder:** Approves retention exceptions
- **Engineering:** Implements automated retention enforcement

## 6. Enforcement

Failure to comply with retention requirements may result in regulatory penalties and contractual breach.

## 7. Review Cadence

Reviewed annually.
