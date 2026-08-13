# AI System Governance Framework

**Document Type:** AI Governance
**Variant:** Executive — One-page brief style, decision-maker focused, high-density. Shows up in board packs.

---

## Cover Page

[LOGO: organization_logo.png] *(centered, 2" × 2")*

**AI System Governance Framework** — {{DOCUMENT_TITLE}}

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

## AI Governance Framework — At a Glance

- **Scope: **Every AI system we build, integrate, procure, or use. In-house, vendor SaaS, and agentic.
- **What it does: **Inventory + use-case approval + risk classification (EU AI Act-aligned) + human oversight + incident handling.
- **Why it matters: **AI governance is the fastest-evolving regulatory area we touch. Documentation is the moat.
- **Owner: **{{POLICY_OWNER}} | Reviewed annually + on each new use case | Next review: {{NEXT_REVIEW_DATE}}

## Tier Map

| Tier | Use Case | Approval |
| --- | --- | --- |
| 1 | Internal productivity, no individual impact. | Policy Owner |
| 2 | Customer-facing with disclosure obligations. | Policy Owner + Privacy |
| 3 | High-risk decisions about individuals. | Policy Owner + Privacy + Approver |
| 4 | Prohibited / restricted by law. Default: no. | Approver + Legal |

## Required Documentation Per System

- Inventory entry (unique ID, owner, tier, last review).
- Use Case Record (problem, population, alternatives, criteria, oversight).
- Model Card (intended use, training data, evaluation, failure modes, guardrails, monitoring).
- Agent Registry entry if agentic.

## Data Rules

No Restricted or Confidential data in unreviewed AI tools. Vendor must contractually ban training on customer data. Training data is cataloged. Models trained on Restricted data ARE Restricted.

## Incident Reporting

AI incidents → Incident Response Plan within 4 business hours. Categories: accuracy regression, bias, prompt injection, unintended agent action, privacy/regulatory implication, vendor incident.


## Roles and Responsibilities

| Role | Responsibilities |
| --- | --- |
| AI Governance Owner ({{POLICY_OWNER}}) | Maintains the framework, the AI system inventory, and the use-case approval pipeline. |
| Approver ({{APPROVER_NAME}}, {{APPROVER_TITLE}}) | Approves new AI use cases above the lightweight threshold; signs annual review. |
| Model / Use Case Owner (per system) | Owns documentation, monitoring, and incident response for a specific AI system or use case. |
| Privacy Officer / Legal | Reviews AI use cases involving personal data, automated decision-making, or high-risk classifications. |
| AI System Operator | Operates the AI system per documented procedures; escalates incidents through documented channels. |

## Review and Maintenance

**Next review date:** {{NEXT_REVIEW_DATE}}

**Review frequency:** Annually, or upon any new AI use case, change in EU AI Act guidance, or material model change.

**Review triggers:**

- A material change in applicable laws, regulations, or contractual obligations.
- Findings from an internal or external audit that affect this document.
- A security or privacy incident that exposes a gap in the document.
- An organizational change (acquisition, divestiture, new business line) that affects scope.

## Related Documents

- Acceptable Use Policy
- Vendor Management Policy
- Data Classification Policy
- Incident Response Plan

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
