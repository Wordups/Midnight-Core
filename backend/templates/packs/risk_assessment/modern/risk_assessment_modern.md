# Annual Security Risk Assessment

**Document Type:** Risk Assessment
**Variant:** Modern — Scannable, plain-language, modern enterprise. Short paragraphs, clear headings, designed for readability.

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

This is our annual look at the security risks facing the company during {{ASSESSMENT_PERIOD}}. We look at our in-scope systems, the threats against them, the vulnerabilities we know about, and what we're doing (or should be doing) about it.

Out of scope: financial, legal, and general business risk — those live in the Enterprise Risk Register that Finance owns.

## Methodology

Five steps, same as last year:

1. Inventory the assets in scope.
2. Identify the threats against them.
3. Look at known vulnerabilities (from VM program, pen test, audit findings, Bird Eye review).
4. Score risks on Likelihood × Impact, both 1-5, producing a tier (Low / Medium / High / Critical).
5. Decide treatment: Avoid / Mitigate / Transfer / Accept. Record residual.

## Asset Inventory

| Asset | Classification | Owner |
| --- | --- | --- |
| Production app cluster | Restricted | {{ENGINEERING_LEAD}} |
| Primary database | Restricted | {{ENGINEERING_LEAD}} |
| Customer data S3 buckets | Restricted | {{ENGINEERING_LEAD}} |
| Identity provider | Confidential | {{INFO_SEC_LEAD}} |
| Source code | Confidential | {{ENGINEERING_LEAD}} |
| Workforce laptops | Confidential | {{IT_OPS_LEAD}} |
| Critical third parties | Restricted | {{VENDOR_OWNER}} |

## Threats

- External attackers (financially motivated, state, opportunistic).
- Insider threats (malicious, negligent, compromised).
- Supply chain (subprocessor breach, vendor failure).
- Operational (misconfig, exposure, change-management failure).
- Environmental (cloud outage, disaster).
- Regulatory (law changes, customer contract changes).

## Vulnerabilities

Inputs: open VM findings, latest pen test, last-12 audit findings, Bird Eye policy review, framework gap analysis. Each vuln links to a specific asset and threat in the Risk Register.

## Risk Matrix (top risks)

| Risk | L | I | Tier |
| --- | --- | --- | --- |
| Credential compromise → prod DB access | 3 | 5 | High |
| Customer-data bucket misconfigured public | 2 | 5 | High |
| Subprocessor incident affecting PHI | 3 | 4 | High |
| Phishing → credential compromise | 4 | 3 | High |
| Stale governance at audit | 3 | 3 | Med |
| Insider exfil to personal cloud | 2 | 4 | Med |
| Regional cloud outage | 2 | 3 | Med |
| Change-management privacy regression | 3 | 3 | Med |

## Treatment Recommendations

- Top 4: Mitigate. Phishing-resistant MFA, posture management, subprocessor SOC 2 + BAA + cyber insurance, FIDO2 + reporting button.
- Stale governance: Mitigate. Continuous Bird Eye, quarterly review, named owners.
- Insider exfil: Mitigate. Endpoint DLP, classification on egress, block personal cloud.
- Cloud outage: Mitigate + Accept. Multi-region warm standby; residual accepted.
- Change-management: Mitigate. Approval gates, pre-prod privacy review, canary deploys.

## Residual Risk Acceptance

Anything residual Medium or higher needs a named executive acceptance. Signed in the Risk Register. Reviewed quarterly. {{APPROVER_NAME}} signs off on this Assessment overall.


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
