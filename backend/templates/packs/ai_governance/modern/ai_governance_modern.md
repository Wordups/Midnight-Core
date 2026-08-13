# AI System Governance Framework

**Document Type:** AI Governance
**Variant:** Modern — Scannable, plain-language, modern enterprise. Short paragraphs, clear headings, designed for readability.

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

## AI System Inventory

Every AI system we build, integrate, or use lives in the AI System Inventory. New systems don't go to production without an entry, an assigned owner, and an approved use case.

The Inventory captures: what the system is, what it does, what data it touches, who owns it, its risk tier, and the date of last review.

## Use Case Documentation

Every use case has a Use Case Record. Required fields:

- What problem are we solving?
- Who does the AI system affect, and how?
- What non-AI alternatives did we consider, and why this?
- Success and failure criteria.
- The data flow.
- The human-oversight model.

Signed by the Model Owner, approved by {{POLICY_OWNER}} before development (for in-house) or before procurement (for vendor systems).

## Risk Classification

Per the EU AI Act and NIST AI RMF, we sort use cases into tiers:

| Tier | What it is | Who approves |
| --- | --- | --- |
| 1 | Internal productivity, no individual impact (summarize-for-me). | Policy Owner |
| 2 | Customer-facing assistance with disclosure obligations. | Policy Owner + Privacy Officer |
| 3 | High-risk: real decisions about individuals (eligibility, scoring, clinical). | Policy Owner + Privacy Officer + Approver |
| 4 | Prohibited or restricted by law. Default: don't. | Approver + Legal |

## Data Governance for AI

- Don't paste Restricted or Confidential data into an AI tool that hasn't been vendor-reviewed and that doesn't contractually ban training on it.
- Training data for in-house systems gets cataloged: provenance, classification, consent basis.
- Personally identifiable training data follows the same retention rules as the source.
- Models trained on Restricted data are themselves Restricted artifacts.

## Model Documentation Requirements

Every system has a Model Card with: intended use, training data summary, evaluation results, known failure modes, guardrails, monitoring metrics, version history.

## Human Oversight

- Tier 2+: human-in-loop or human-on-loop documented in the Use Case Record.
- Agentic AI (takes actions, not just generates): registered, scoped, revocable.
- Operators get training on the system's capabilities and limits.

## Incident and Bias Reporting

AI incidents — accuracy regressions, observed bias, prompt injection, unintended agent actions, anything with regulatory implications — go through the Incident Response Plan within 4 business hours.

## Vendor AI Risk Management

Vendor AI follows the Vendor Management Policy plus: ask about training-data practices; get their model docs; AI-specific incident notification in the contract; re-review on material model or data changes.


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
