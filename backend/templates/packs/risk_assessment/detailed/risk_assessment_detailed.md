# Annual Security Risk Assessment

**Document Type:** Risk Assessment
**Variant:** Detailed — Comprehensive, long-form, every consideration covered. The template a regulated startup would use to over-prepare.

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

## Assessment Scope

This Risk Assessment evaluates the information security risks affecting {{ORGANIZATION_NAME}} during the assessment period {{ASSESSMENT_PERIOD}}. The Assessment is conducted pursuant to the Risk Management Policy and is structured to satisfy considerations under the HIPAA Security Rule's requirement for a risk analysis at 45 CFR 164.308(a)(1)(ii)(A), the SOC 2 Type II Trust Services Criterion CC3.1 (the entity identifies risks to the achievement of its objectives), ISO/IEC 27001:2022 Clauses 6.1 (actions to address risks and opportunities) and 8.2 (information security risk assessment), NIST CSF 2.0 GV.RM (risk management strategy) and ID.RA (risk assessment), and the underlying NIST SP 800-30 risk-assessment methodology.

In scope: all systems holding Restricted or Confidential data, all processes involving such data, all third parties processing such data on behalf of the Organization, and the workforce members and procedures supporting those systems and processes. Out of scope: enterprise-level risks (financial, legal, operational, strategic) addressed in the Enterprise Risk Register maintained by the Finance function; physical-facility risks below the threshold tracked by the Office Manager; and individual project-level risks tracked within project plans.

## Methodology

The Assessment follows a structured five-step methodology, applied consistently across all in-scope assets and threats. The methodology is documented in the Risk Management Policy and is calibrated annually based on observed effectiveness in prior cycles.

### Step 1 — Asset Inventory

The asset inventory is derived from the Organization's authoritative asset register, reconciled against the cloud account inventory exported from AWS Config, the third-party vendor register maintained by the Vendor Management function, and the workforce roster maintained by Human Resources. Each in-scope asset receives an Asset Identifier, a brief description, a classification (per the Data Classification Policy), and an assigned owner.

### Step 2 — Threat Identification

Threats are identified from the Organization's threat library, supplemented by threat intelligence inputs received during the assessment period from industry information-sharing organizations, security vendors, and the post-incident reviews of incidents observed in the prior twelve months.

### Step 3 — Vulnerability Assessment

Vulnerabilities are derived from multiple inputs: the open-findings register of the Vulnerability Management Program; the most recent annual penetration test report; audit findings from internal and external audits in the prior twelve months; the Bird Eye corpus review identifying duplicates, conflicts, stale governance, framework gaps, and orphaned references; and the framework-gap analysis comparing the Organization's control implementation against in-scope framework requirements.

### Step 4 — Risk Evaluation

Each plausible threat-vulnerability-asset combination is evaluated as a candidate risk. Risks are scored on Likelihood and Impact, each on a five-point scale defined in the Risk Scoring Rubric, producing a composite risk score that maps to a tier (Low, Medium, High, Critical). Both inherent risk (the risk in the absence of controls) and residual risk (the risk after consideration of in-place controls) are recorded.

### Step 5 — Risk Treatment

Each risk receives a documented treatment plan. Treatment options are: (a) Avoid — modify the activity such that the risk no longer applies; (b) Mitigate — implement additional controls to reduce likelihood or impact; (c) Transfer — shift the financial impact via insurance or contractual indemnity; or (d) Accept — acknowledge the residual risk in writing, signed by an executive named on the risk record.

## Asset Inventory

The following assets are in scope. The inventory is current as of {{ASSESSMENT_PERIOD_START}} and is reconciled against system-of-record exports.

| Asset ID | Asset Description | Classification | Owner | System of Record |
| --- | --- | --- | --- | --- |
| A-001 | Production application cluster (web tier + worker tier) | Restricted (PHI) | {{ENGINEERING_LEAD}} | AWS ECS cluster registry |
| A-002 | Primary database (PostgreSQL RDS multi-AZ) | Restricted (PHI) | {{ENGINEERING_LEAD}} | AWS RDS console |
| A-003 | Object storage (S3) — customer-tenant data | Restricted (PHI) | {{ENGINEERING_LEAD}} | AWS S3 inventory |
| A-004 | Identity provider tenant (Okta) | Confidential | {{INFO_SEC_LEAD}} | Okta administrative directory |
| A-005 | Source code repositories (GitHub Enterprise) | Confidential | {{ENGINEERING_LEAD}} | GitHub organization roster |
| A-006 | Workforce endpoints (managed laptops, mobile) | Confidential | {{IT_OPS_LEAD}} | MDM device roster |
| A-007 | Customer success portal and ticketing | Confidential | {{CS_LEAD}} | Zendesk + portal admin |
| A-008 | Critical third-party processors (AWS, Okta, CDN, monitoring) | Restricted (PHI) | {{VENDOR_OWNER}} | Vendor register |
| A-009 | Backup and archival systems | Restricted (PHI) | {{INFO_SEC_LEAD}} | AWS Backup vault inventory |
| A-010 | Cryptographic key management service | Restricted (controls all PHI) | {{INFO_SEC_LEAD}} | AWS KMS key inventory |

## Threat Identification

The threat catalog below was applied to each in-scope asset. The catalog reflects the current revision of the Organization's threat library plus incremental threats observed during the assessment period.

1. External Threat Actors — Financially Motivated: ransomware operators, business-email-compromise actors, credential-theft operators selling on illicit markets, cryptocurrency-targeted cloud-resource theft.
2. External Threat Actors — State-Sponsored: targeted intrusion against the healthcare supply chain, espionage motivated by customer-base composition. Lower probability for the Organization's current size and visibility, but evaluated for completeness.
3. External Threat Actors — Opportunistic: automated scanning leveraging recently disclosed CVEs, supply-chain compromise via popular open-source dependencies, account takeover via credential stuffing.
4. Insider Threats — Malicious: workforce member with privileged access exfiltrates data; departing workforce member retains credentials; contractor with limited oversight misuses access.
5. Insider Threats — Negligent: workforce member misconfigures a system, falls for phishing, uses unapproved tools, or stores data improperly.
6. Insider Threats — Compromised Credentials: workforce credentials phished, reused from a third-party breach, or stolen via endpoint compromise.
7. Supply Chain and Third-Party Threats: subprocessor security incident; vendor failure of a critical service; subprocessor inadvertently exposing customer data; software-supply-chain compromise.
8. Operational Threats: change-management failure deploying privacy or security regression; misconfiguration of cloud resource exposing data; backup or recovery failure during an actual restoration event.
9. Environmental Threats: regional cloud provider outage affecting availability; natural disaster affecting workforce availability or office facility.
10. Regulatory and Contractual Threats: material change in applicable law; audit-driven finding requiring rapid remediation; customer contractual change requiring rapid control implementation.

## Vulnerability Assessment

The following vulnerability inputs were considered. The Vulnerability Register linked to this Assessment contains the line-item vulnerabilities; the summary below reflects the inputs and the broad patterns observed.

- Vulnerability Management Program register: {{VULN_OPEN_COUNT}} open findings as of assessment start, of which {{VULN_HIGH_COUNT}} are rated High or Critical.
- Annual penetration test report ({{PENTEST_DATE}}): {{PENTEST_FINDINGS_COUNT}} findings; remediation tracked in the VM register.
- Internal and external audit findings (prior 12 months): {{AUDIT_FINDINGS_COUNT}} findings affecting in-scope assets; remediation in progress per the audit response plan.
- Bird Eye corpus review: {{BIRD_EYE_FINDINGS_COUNT}} findings spanning duplicates, conflicts, stale governance, framework gaps, and orphans.
- Framework gap analysis: gaps identified primarily in {{TOP_GAP_AREAS}}, tracked in the framework-readiness register.

## Risk Matrix

The following matrix presents the top inherent risks identified in the Assessment. Each entry is linked to a full risk record in the Risk Register; this matrix is the executive summary.

| ID | Risk Statement | Likelihood | Impact | Inherent |
| --- | --- | --- | --- | --- |
| R-101 | Unauthorized access to production database via compromised credential | 3 | 5 | High |
| R-102 | Misconfiguration of customer-data S3 bucket exposing data to internet | 2 | 5 | High |
| R-103 | Subprocessor security incident affecting customer PHI | 3 | 4 | High |
| R-104 | Workforce phishing leading to credential compromise | 4 | 3 | High |
| R-105 | Stale governance: critical policies expired or unowned at audit | 3 | 3 | Medium |
| R-106 | Insider data exfiltration to personal cloud storage | 2 | 4 | Medium |
| R-107 | Regional cloud provider outage affecting service availability | 2 | 3 | Medium |
| R-108 | Change-management failure deploying privacy regression | 3 | 3 | Medium |
| R-109 | Backup or recovery failure during a real restoration event | 2 | 4 | Medium |
| R-110 | Software supply-chain compromise via dependency vulnerability | 2 | 4 | Medium |

## Risk Treatment Recommendations

Each risk receives a documented treatment plan. The following table summarizes the recommended treatment for each of the top risks identified above. Each treatment is linked to a specific control or control set, and the control owner is named in the Risk Register.

| ID | Treatment | Specific Actions | Residual |
| --- | --- | --- | --- |
| R-101 | Mitigate | Phishing-resistant MFA for all production access; quarterly access review; database activity monitoring with anomaly alerting; just-in-time access grants. | Low |
| R-102 | Mitigate | Cloud security posture management with policy-as-code enforcement; automated remediation of bucket-policy drift; bi-weekly external scan against customer-facing buckets. | Low |
| R-103 | Mitigate + Transfer | Subprocessor SOC 2 Type II review on annual cycle; BAAs in place with all PHI-handling subprocessors; cyber insurance maintained with adequate coverage limit. | Medium |
| R-104 | Mitigate | Quarterly phishing simulation; FIDO2 MFA enforced; suspicious-email reporting button in the email client; mandatory awareness training annually. | Medium |
| R-105 | Mitigate | Continuous Bird Eye review; quarterly governance check; named owner per policy with backup; integration of governance metadata into the Risk Register. | Low |
| R-106 | Mitigate | Endpoint DLP with classification-based egress controls; managed-personal-cloud blocking on managed endpoints; quarterly review of egress logs for anomalies. | Low |
| R-107 | Mitigate + Accept | Multi-region warm standby with documented RTO of 4 hours and RPO of 15 minutes; tabletop drill annually; residual accepted by {{APPROVER_NAME}}. | Medium |
| R-108 | Mitigate | Change-management approval gates; mandatory pre-prod privacy review for changes affecting PHI flows; canary deployments with automated rollback on regression detection. | Low |
| R-109 | Mitigate | Quarterly backup-restore drills with documented validation; cross-region replication; immutable storage tier for critical backups. | Low |
| R-110 | Mitigate | Dependency-scanning in CI with severity-based blocking; centralized base-image registry; restricted package-manager configuration; SBOM generation per release. | Medium |

## Residual Risk Acceptance

Residual risks rated Medium or higher require written acceptance by an executive named on each risk record. The acceptances below are presented for the Approver's signature. Each acceptance shall be effective only upon execution by the named signatory and shall lapse upon any material change to the underlying control environment, at which point the risk is re-evaluated.

1. R-103 (Subprocessor security incident) — Medium residual after subprocessor SOC 2 review, BAA, and cyber insurance. Accepted by {{APPROVER_NAME}}.
2. R-104 (Workforce phishing) — Medium residual after MFA, training, and reporting tooling. Accepted by {{APPROVER_NAME}}.
3. R-107 (Regional cloud outage) — Medium residual after multi-region warm standby; accepted because elimination would require active-active architecture not yet justified by customer SLA. Accepted by {{APPROVER_NAME}}.
4. R-110 (Software supply-chain compromise) — Medium residual after dependency-scanning, base-image registry, and SBOM. Accepted by {{APPROVER_NAME}}; reviewed quarterly given the evolving threat landscape.

The Approver shall sign off on this Assessment in its entirety and on each individual residual risk acceptance enumerated above. Acceptances shall be reviewed at each quarterly risk review and renewed annually as part of the next Risk Assessment cycle.


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
