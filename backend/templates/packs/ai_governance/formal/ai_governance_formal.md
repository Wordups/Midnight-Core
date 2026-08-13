# AI System Governance Framework

**Document Type:** AI Governance
**Variant:** Formal — Legalese voice, full structure, traditional enterprise. The template a Fortune 500 General Counsel would approve.

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

## 1. AI System Inventory

This Framework establishes governance for artificial intelligence ("AI") systems developed, deployed, integrated, or otherwise operated by or on behalf of {{ORGANIZATION_NAME}} ("Organization"). The Organization shall maintain an AI System Inventory comprising every in-scope AI system; the Inventory shall be the authoritative record for use-case approval, risk classification, and reporting. New AI systems shall not be placed in production absent an Inventory entry approved in accordance with this Framework.

The Inventory shall record for each AI system: a unique system identifier; the use case; the model(s) employed; the training data or pre-trained source; the data classes processed; the inference channel (real-time, batch, agentic); the assigned Model Owner; the risk classification under Section 3; and the date of most recent governance review.

## 2. Use Case Documentation

Each AI use case shall be documented in a Use Case Record. The Record shall set forth: the business problem the AI system addresses; the population and decision affected; the alternative non-AI approaches considered and the rationale for selecting AI; the success and failure criteria; the data flow; and the planned human-oversight model. Use Case Records shall be signed by the Model Owner and approved by {{POLICY_OWNER}} prior to development commencement for in-house systems and prior to procurement commencement for vendor systems.

## 3. Risk Classification

Each AI use case shall be classified according to the following tiers, derived from the EU Artificial Intelligence Act and the NIST AI Risk Management Framework. Classification shall be made by the Model Owner and reviewed by {{POLICY_OWNER}}; classifications of Tier 3 or Tier 4 require concurrence by Legal.

| Tier | Description | Approval Requirement |
| --- | --- | --- |
| Tier 1 | Minimal-risk: internal productivity uses with no decisional impact on individuals (e.g., text summarization for internal review). | {{POLICY_OWNER}} |
| Tier 2 | Limited-risk: customer-facing assistance with transparency obligations (e.g., chatbots, generative content with disclosure). | {{POLICY_OWNER}} + Privacy Officer |
| Tier 3 | High-risk under analogous EU AI Act criteria: significant decisions affecting individuals (e.g., eligibility, scoring, clinical-decision support). | {{POLICY_OWNER}} + Privacy Officer + Approver |
| Tier 4 | Prohibited or restricted under applicable law (e.g., manipulative AI, social scoring); no Organization use unless explicitly approved by Legal. | Approver + Legal |

## 4. Data Governance for AI

1. Restricted or Confidential data shall not be submitted to AI systems that have not been reviewed under the Vendor Management Policy and that do not contractually prohibit training on submitted data.
2. Training data used for in-house AI systems shall be cataloged, with provenance, classification, and consent basis recorded for each dataset.
3. Personally identifiable training data shall be subject to the same retention and disposal rules applicable to the underlying source under the Data Retention and Disposal Policy.
4. Models trained on Restricted or Confidential data shall be treated as Restricted artifacts; access to model weights, fine-tuned variants, and embedding stores shall be controlled per the Access Control Policy.

## 5. Model Documentation Requirements

For each AI system in the Inventory, the Model Owner shall maintain a Model Card containing, at minimum:

1. Intended use, intended users, and out-of-scope uses.
2. Training data summary, including provenance, time period, and known limitations.
3. Evaluation results, including accuracy, fairness across applicable subgroups, and robustness considerations.
4. Known failure modes and observed biases.
5. Operational guardrails: input validation, output filtering, rate limits, and human-in-the-loop checkpoints.
6. Monitoring and drift-detection metrics with target thresholds.
7. Version history and material change log.

## 6. Human Oversight Procedures

1. For Tier 2 and higher use cases, a documented human-in-the-loop or human-on-the-loop control shall be operational. The control shall be described in the Use Case Record and shall be subject to periodic review.
2. For agentic AI systems (those that take actions on the Organization's behalf rather than only generating content), an approved agent registry entry is required. The registry shall record permitted action scope, authentication mechanism, and revocation procedure.
3. Workforce members operating AI systems shall complete role-appropriate training on the system's capabilities and limitations.

## 7. Incident and Bias Reporting

AI system incidents — including but not limited to material accuracy regressions, observed bias affecting protected populations, prompt-injection or jailbreak events with material impact, unintended autonomous actions by agentic systems, and any incident implicating regulatory notification — shall be reported through the Incident Response Plan within four (4) business hours of identification. The Model Owner shall participate in the post-incident review.

## 8. Vendor AI Risk Management

Third-party AI systems and AI features within third-party products shall be subject to the Vendor Management Policy with the following AI-specific additions: (i) the vendor shall represent its training-data practices, particularly any use of customer data for training; (ii) the vendor shall provide its applicable model documentation; (iii) the vendor shall agree contractually to AI-specific incident notification; and (iv) the use case shall be classified under Section 3 with the vendor system's risk profile considered. Vendor AI use cases shall be re-reviewed upon material change to the vendor's model or data practices.


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
