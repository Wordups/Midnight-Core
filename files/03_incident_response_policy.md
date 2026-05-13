# Incident Response Policy

**Document ID:** TKO-POL-003
**Version:** 1.0
**Owner:** Brian Word, Founder
**Effective Date:** 2026-02-01
**Last Reviewed:** 2026-04-01
**Next Review:** 2027-04-01
**Frameworks:** SOC 2, NIST CSF 2.0, HIPAA
**Status:** Active

---

## 1. Purpose

This policy establishes the framework for detecting, responding to, and recovering from security incidents affecting Takeoff LLC systems and the Midnight platform.

## 2. Scope

Applies to all security incidents, including but not limited to: unauthorized access, data exposure, malware infection, denial of service, account compromise, and cross-tenant data leakage in Midnight.

## 3. Definitions

- **Security Incident:** Any event that compromises the confidentiality, integrity, or availability of Takeoff systems or customer data
- **Critical Incident:** An incident involving confirmed customer data exposure, multi-tenant boundary violation, or production outage exceeding 1 hour
- **Containment:** Actions taken to limit the scope of an active incident

## 4. Policy Statements

### 4.1 Incident Classification

Incidents are classified by severity:
- **Critical:** Customer data exposure, cross-tenant violation, ransomware, prolonged outage
- **High:** Confirmed unauthorized access without data exposure, significant service degradation
- **Medium:** Failed but persistent attack patterns, isolated misconfigurations
- **Low:** Minor policy violations, single failed login attempts

### 4.2 Incident Response Phases

1. **Detection:** Identify the incident through monitoring, customer report, or third-party notification
2. **Triage:** Assign severity within 30 minutes of detection
3. **Containment:** Isolate affected systems within 1 hour for Critical, 4 hours for High
4. **Eradication:** Remove the root cause
5. **Recovery:** Restore services and verify normal operation
6. **Lessons Learned:** Conduct post-incident review within 5 business days

### 4.3 Customer Notification

Customers affected by a Critical incident involving their data are notified within **72 hours** of confirmed exposure, in accordance with applicable regulatory requirements including HIPAA Breach Notification Rule and state breach notification laws.

### 4.4 Evidence Preservation

All incident artifacts (logs, system images, communications) are preserved for a minimum of 7 years from incident closure.

### 4.5 External Reporting

Incidents involving regulated data may require notification to regulators, law enforcement, or contractual partners. The Founder approves all external communications.

## 5. Roles and Responsibilities

- **Founder:** Incident Commander for Critical incidents; approves external communications
- **Engineering:** Executes containment, eradication, and recovery procedures
- **All Personnel:** Report suspected incidents within 1 hour of discovery to the Founder

## 6. Enforcement

Failure to report suspected incidents is a violation of this policy and grounds for disciplinary action.

## 7. Review Cadence

Reviewed annually and after each Critical incident.
