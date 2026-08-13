# Annual Security Risk Assessment

**Document Type:** Risk Assessment
**Variant:** Executive — One-page brief style, decision-maker focused, high-density. Shows up in board packs.

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

## Annual Risk Assessment — At a Glance

- **Period: **{{ASSESSMENT_PERIOD}}
- **Scope: **All systems and processes holding Restricted or Confidential data.
- **Method: **NIST 800-30-aligned. Likelihood × Impact (1-5 each). Inherent and residual recorded.
- **Owner: **{{POLICY_OWNER}} | Reviewed annually + quarterly for High/Critical residuals | Next: {{NEXT_REVIEW_DATE}}

## Top Risks

| Risk | Inherent | Treatment | Residual |
| --- | --- | --- | --- |
| Credential compromise → prod DB | High | Mitigate | Low |
| Customer-data bucket misconfigured | High | Mitigate | Low |
| Subprocessor incident → PHI | High | Mitigate + Transfer | Medium |
| Phishing → credential compromise | High | Mitigate | Medium |
| Stale governance at audit | Medium | Mitigate | Low |
| Insider exfil | Medium | Mitigate | Low |
| Regional cloud outage | Medium | Mitigate + Accept | Medium |
| Change-management privacy regression | Medium | Mitigate | Low |

## Residual Acceptances Requiring Signature

- Subprocessor incident — Medium residual.
- Workforce phishing — Medium residual.
- Regional cloud outage — Medium residual.
- Software supply-chain compromise — Medium residual.

## Sign-off

Approver signs the Assessment and each individual residual acceptance. Acceptances reviewed quarterly; renewed at next annual cycle.


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
