# Access Control Policy

**Document ID:** TKO-POL-002
**Version:** 1.1
**Owner:** Brian Word, Founder
**Effective Date:** 2026-01-15
**Last Reviewed:** 2026-04-01
**Next Review:** 2027-04-01
**Frameworks:** SOC 2, NIST CSF 2.0, HIPAA, ISO 27001
**Status:** Active

---

## 1. Purpose

This policy defines requirements for granting, managing, and revoking access to Takeoff LLC systems and customer data processed by Midnight.

## 2. Scope

Applies to all Takeoff personnel, contractors, and any individual or system requiring access to production infrastructure, source code repositories, customer data, or administrative tools.

## 3. Definitions

- **Privileged Access:** Administrative, root, or elevated permissions on production systems
- **Standard Access:** Read or limited write access scoped to specific business functions
- **Service Account:** Non-human identity used for system-to-system authentication

## 4. Policy Statements

### 4.1 Authentication Requirements

All user accounts accessing Takeoff systems must use multi-factor authentication (MFA). MFA must be enforced via hardware token, authenticator app, or platform-managed passkey. SMS-based MFA is prohibited for privileged accounts.

### 4.2 Password Requirements

- Minimum password length: **14 characters**
- Must contain at least one uppercase letter, one lowercase letter, one number, and one symbol
- Password rotation: every 180 days for privileged accounts
- Password reuse: previous 12 passwords prohibited
- Account lockout: 5 failed attempts within 15 minutes triggers a 30-minute lockout

### 4.3 Privileged Access

Privileged access requires:
- Documented business justification
- Approval from the Founder
- Just-in-time elevation where technically feasible
- Logging of all privileged actions
- Quarterly review of all privileged accounts

### 4.4 Service Accounts

Service accounts must use rotated credentials managed via AWS Secrets Manager. Service account passwords are not subject to user password rotation requirements but are rotated every 90 days.

### 4.5 Access Provisioning and Deprovisioning

- New access is provisioned within 24 business hours of approval
- Access is revoked within 4 hours of termination, role change, or contract end
- Quarterly access reviews are conducted for all production system access

## 5. Roles and Responsibilities

- **Founder:** Approves all privileged access grants and exceptions
- **Engineering:** Implements technical access controls
- **All Personnel:** Use only their own credentials, report suspected credential compromise immediately

## 6. Enforcement

Unauthorized access attempts, credential sharing, or violations of MFA requirements are grounds for immediate access revocation and disciplinary action.

## 7. Review Cadence

Reviewed annually or upon material infrastructure change.
