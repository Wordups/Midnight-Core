# Vendor Management Policy

**Document ID:** TKO-POL-006
**Version:** 1.0
**Owner:** Brian Word, Founder
**Effective Date:** 2026-03-01
**Last Reviewed:** 2026-03-01
**Next Review:** 2027-03-01
**Frameworks:** SOC 2
**Status:** Active

---

## 1. Purpose

This policy establishes requirements for evaluating, onboarding, and managing third-party vendors that process Takeoff LLC data or have access to Takeoff systems.

## 2. Scope

Applies to all third-party vendors, suppliers, and service providers with access to:
- Takeoff production infrastructure
- Customer data, including PHI processed under HIPAA Business Associate Agreements
- Source code repositories
- Financial or operational systems

## 3. Definitions

- **Critical Vendor:** A vendor whose failure or compromise would materially impact Takeoff operations or customer data
- **Business Associate:** Under HIPAA, a vendor that creates, receives, maintains, or transmits Protected Health Information on behalf of Takeoff or its customers
- **Vendor Risk Tier:** Classification of vendor risk based on data access, system access, and business criticality

## 4. Policy Statements

### 4.1 Vendor Assessment

Prior to engagement, all vendors must complete a security assessment including:
- Review of vendor SOC 2 Type II report (or equivalent)
- Completion of Takeoff vendor security questionnaire
- Review of data processing locations and sub-processors
- Verification of breach notification commitments

### 4.2 Critical Vendors

The following are designated Critical Vendors for Takeoff:
- AWS (production infrastructure)
- Anthropic (LLM provider for policy generation)
- Voyage AI (embeddings provider)
- Stripe (payment processing)
- GitHub (source code repository)

### 4.3 Contractual Requirements

All vendors processing customer data must execute:
- Master Services Agreement
- Data Processing Addendum
- Business Associate Agreement (where PHI is processed)
- Security addendum incorporating Takeoff minimum security requirements

### 4.4 Ongoing Monitoring

- Annual review of vendor SOC 2 reports
- Quarterly review of vendor security posture for Critical Vendors
- Notification within 24 hours of any vendor security incident affecting Takeoff data

### 4.5 Vendor Offboarding

Upon termination of a vendor relationship:
- All Takeoff data must be returned or destroyed within 30 days
- Vendor access to Takeoff systems revoked within 24 hours
- Certificate of destruction obtained where applicable

## 5. Roles and Responsibilities

- **Founder:** Approves all Critical Vendor engagements and exceptions
- **Engineering:** Maintains vendor inventory and conducts technical assessments

## 6. Enforcement

Engagement with vendors that have not completed required assessments is prohibited.

## 7. Review Cadence

Reviewed annually.
