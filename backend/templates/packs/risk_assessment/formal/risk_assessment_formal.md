# Annual Security Risk Assessment

**Document Type:** Risk Assessment
**Variant:** Formal — Legalese voice, full structure, traditional enterprise. The template a Fortune 500 General Counsel would approve.

---

## Cover Page

[LOGO: organization_logo.png] *(centered, 2" × 2")*

**Annual Security Risk Assessment** — {{DOCUMENT_TITLE}}

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

## 1. Assessment Scope

This Risk Assessment (the "Assessment") evaluates the information security risks affecting {{ORGANIZATION_NAME}} ("Organization") during the assessment period {{ASSESSMENT_PERIOD}}. The Assessment is conducted pursuant to the Risk Management Policy and addresses considerations under the HIPAA Security Rule (45 CFR 164.308(a)(1)(ii)(A)), the SOC 2 Type II Trust Services Criterion CC3.1, and ISO/IEC 27001:2022 Clauses 6.1 and 8.2.

The Assessment covers all in-scope systems, processes, and third parties identified in the Asset Inventory in Section 3. Risks affecting business operations more generally (financial, legal, operational) are out of scope of this Assessment and are addressed in the Enterprise Risk Register maintained by the Finance function.

## 2. Methodology

The Assessment follows a structured five-step methodology: (i) asset inventory; (ii) threat identification; (iii) vulnerability assessment; (iv) risk evaluation; and (v) risk treatment. The methodology is consistent with NIST SP 800-30 and is supplemented by Organization-specific scoring rubrics maintained by the Information Security function.

Risks are scored on Likelihood and Impact, each on a five-point scale, producing a composite risk score. Composite scores map to four tiers (Low, Medium, High, Critical) per the Risk Scoring Rubric. Inherent risk (pre-control) and residual risk (post-control) are recorded for each risk.

## 3. Asset Inventory

The following assets are in scope of this Assessment. The asset inventory is derived from the Organization's authoritative asset register and reconciled against the cloud account inventory and the third-party vendor register.

| Asset ID | Asset | Classification | Owner |
| --- | --- | --- | --- |
| A-001 | Production application cluster | Restricted (PHI) | {{ENGINEERING_LEAD}} |
| A-002 | Primary database (PostgreSQL RDS) | Restricted (PHI) | {{ENGINEERING_LEAD}} |
| A-003 | Object storage (S3) — customer data | Restricted (PHI) | {{ENGINEERING_LEAD}} |
| A-004 | Identity provider tenant | Confidential | {{INFO_SEC_LEAD}} |
| A-005 | Source code repositories | Confidential | {{ENGINEERING_LEAD}} |
| A-006 | Workforce endpoints (managed laptops) | Confidential | {{IT_OPS_LEAD}} |
| A-007 | Customer success portal | Confidential | {{CS_LEAD}} |
| A-008 | Critical third-party processors (AWS, identity, CDN) | Restricted (PHI) | {{VENDOR_OWNER}} |

## 4. Threat Identification

Threats are identified from the Organization's threat library, which is updated quarterly from threat intelligence inputs and post-incident reviews. The following threat categories are evaluated in this Assessment:

1. External threat actors: financially motivated cybercriminals, state-sponsored actors, opportunistic attackers leveraging known vulnerabilities.
2. Insider threats: malicious workforce action, negligent workforce conduct, compromised workforce credentials.
3. Supply chain and third-party threats: subprocessor breach affecting customer data, vendor failure of a critical service.
4. Operational threats: misconfiguration, unintended data exposure, change-management failures.
5. Environmental threats: regional cloud outages, natural disasters affecting workforce availability.
6. Regulatory threats: changes in applicable law, audit-driven findings, customer contractual changes.

## 5. Vulnerability Assessment

Vulnerability inputs to this Assessment include: (i) the open-findings register of the Vulnerability Management Program; (ii) the most recent penetration test report; (iii) audit findings from the prior twelve months; (iv) the Bird Eye corpus review of the Organization's policy library; and (v) gap-analysis output against the in-scope frameworks. Vulnerabilities are linked to specific assets and threats in the Risk Register.

## 6. Risk Matrix

The following risk matrix presents the top inherent risks identified in the Assessment. Risks are reviewed in detail in the Risk Register; this matrix is the executive view.

| Risk ID | Risk Statement | Likelihood | Impact | Inherent |
| --- | --- | --- | --- | --- |
| R-101 | Unauthorized access to production database via compromised credential | 3 | 5 | High |
| R-102 | Misconfiguration of customer-data S3 bucket exposing data to internet | 2 | 5 | High |
| R-103 | Subprocessor security incident affecting customer PHI | 3 | 4 | High |
| R-104 | Workforce phishing leading to credential compromise | 4 | 3 | High |
| R-105 | Stale governance: critical policies expired or unowned at audit | 3 | 3 | Medium |
| R-106 | Insider data exfiltration to personal cloud storage | 2 | 4 | Medium |
| R-107 | Regional cloud provider outage affecting service availability | 2 | 3 | Medium |
| R-108 | Change-management failure deploying privacy regression | 3 | 3 | Medium |

## 7. Risk Treatment Recommendations

Each risk receives a documented treatment plan. Treatment options are Avoid, Mitigate, Transfer, and Accept. The following table summarizes recommended treatment for the highest inherent risks.

| Risk ID | Treatment | Action | Residual |
| --- | --- | --- | --- |
| R-101 | Mitigate | Enforce phishing-resistant MFA for all production access; quarterly access review; database activity monitoring with anomaly alerting. | Low |
| R-102 | Mitigate | Cloud security posture management with policy-as-code; automated remediation of bucket-policy drift; bi-weekly external scan. | Low |
| R-103 | Mitigate + Transfer | Subprocessor SOC 2 review and BAA in place; cyber insurance maintained. | Medium |
| R-104 | Mitigate | Quarterly phishing simulation; FIDO2 MFA; suspicious-email reporting button in email client. | Medium |
| R-105 | Mitigate | Continuous Bird Eye review; quarterly governance check; named owner per policy. | Low |
| R-106 | Mitigate | Endpoint DLP; data-classification enforcement on egress; managed personal-cloud-blocking on managed endpoints. | Low |
| R-107 | Mitigate + Accept | Multi-region warm standby; documented RTO/RPO; residual accepted. | Medium |
| R-108 | Mitigate | Change-management approval gates; pre-prod privacy review; canary deployments. | Low |

## 8. Residual Risk Acceptance

Residual risks rated Medium or higher require written acceptance by an executive named on each risk record. Acceptances are documented in the Risk Register and reviewed at each quarterly risk review. An acceptance shall not be effective absent the named signatory and shall lapse upon material change to the underlying control environment.

The Approver shall sign off on this Assessment in its entirety and on each individual residual risk acceptance of Medium severity or higher.


## Roles and Responsibilities

| Role | Responsibilities |
| --- | --- |
| Assessment Owner ({{POLICY_OWNER}}) | Maintains the methodology, schedules the assessment, and produces the annual report. |
| Approver ({{APPROVER_NAME}}, {{APPROVER_TITLE}}) | Approves the assessment and acceptances of residual risk. |
| Risk Workshop Participants | Engineering, Customer Success, Legal, Finance, HR leads providing in-scope context. |
| Information Security | Owns the threat library, vulnerability inputs, and risk-scoring rubric. |
| Risk Acceptor (per risk) | Executive named on the risk record who accepts residual risk. |

## Review and Maintenance

**Next review date:** {{NEXT_REVIEW_DATE}}

**Review frequency:** Annually; risks of High or Critical residual rating reviewed quarterly.

**Review triggers:**

- A material change in applicable laws, regulations, or contractual obligations.
- Findings from an internal or external audit that affect this document.
- A security or privacy incident that exposes a gap in the document.
- An organizational change (acquisition, divestiture, new business line) that affects scope.

## Related Documents

- Risk Management Policy
- Information Security Policy
- Vendor Management Policy
- Business Continuity Plan

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
