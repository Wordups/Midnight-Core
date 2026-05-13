# Identity and Authentication Standard

**Document ID:** TKO-STD-001
**Version:** 1.0
**Owner:** Brian Word, Founder
**Effective Date:** 2026-01-20
**Last Reviewed:** 2026-04-01
**Next Review:** 2027-04-01
**Frameworks:** SOC 2, NIST 800-53
**Status:** Active

---

## 1. Purpose

This standard defines technical implementation requirements for identity and authentication controls across Takeoff LLC systems.

## 2. Scope

Applies to all authentication systems used by Takeoff personnel, including AWS IAM, GitHub, Google Workspace, Stripe, and the Midnight admin console.

## 3. Definitions

- **Authentication:** The process of verifying the identity of a user or system
- **Multi-Factor Authentication (MFA):** Authentication using two or more independent factors
- **Privileged Identity:** An identity with administrative or elevated permissions

## 4. Standard Requirements

### 4.1 Authentication Requirements

All user accounts accessing Takeoff systems must use multi-factor authentication (MFA). MFA must be enforced via hardware token, authenticator app, or platform-managed passkey. SMS-based MFA is prohibited for privileged accounts.

### 4.2 Password Requirements

- Minimum password length: **12 characters**
- Must contain at least one uppercase letter, one lowercase letter, and one number
- Password rotation: every 90 days for all accounts
- Password reuse: previous 8 passwords prohibited
- Account lockout: 3 failed attempts within 10 minutes triggers a 60-minute lockout

### 4.3 Privileged Identity Management

Privileged accounts require:
- Documented business justification
- Approval from the Founder
- Just-in-time elevation where technically feasible
- Logging of all privileged actions
- Quarterly review of all privileged accounts

### 4.4 Session Management

- Idle session timeout: 30 minutes
- Maximum session duration: 12 hours
- Session tokens must be invalidated immediately upon logout

### 4.5 Service Account Credentials

Service accounts must use rotated credentials managed via AWS Secrets Manager. Service account passwords are rotated every 90 days.

## 5. Roles and Responsibilities

- **Founder:** Approves all privileged access grants
- **Engineering:** Implements technical controls in accordance with this standard

## 6. Enforcement

Non-compliant authentication configurations must be remediated within 30 days of identification.

## 7. Review Cadence

Reviewed annually.
