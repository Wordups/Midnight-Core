# AI System Governance Framework

**Document Type:** AI Governance
**Variant:** Detailed — Comprehensive, long-form, every consideration covered. The template a regulated startup would use to over-prepare.

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

This AI Governance Framework establishes the governance baseline for artificial intelligence ("AI") systems developed, deployed, integrated, procured, or otherwise operated by or on behalf of {{ORGANIZATION_NAME}}. The Framework applies to: (i) AI systems built in-house by the Organization's engineering or data-science functions; (ii) third-party AI systems integrated into the Organization's products or operational stack; (iii) AI features within third-party SaaS applications used by workforce members; and (iv) AI agents that take actions on the Organization's behalf, including autonomous and semi-autonomous agentic systems.

The Organization shall maintain an AI System Inventory comprising every in-scope AI system. The Inventory is the authoritative record for use-case approval, risk classification, governance review, and external reporting (regulatory or customer due-diligence). New AI systems shall not be placed in production absent an approved Inventory entry. Existing systems lacking an Inventory entry as of the effective date of this Framework shall be remediated within ninety (90) days through retroactive entry and risk classification.

The Inventory shall record, for each AI system: a unique system identifier in the format AI-YYYY-NNNN; the use case (succinct natural-language statement and category); the model(s) employed (foundation model identifier and version, fine-tuned variants); the training data summary (in-house collection, public dataset, pre-trained source); the data classes processed (Restricted, Confidential, Internal, Public); the inference channel (real-time API, batch processing, agentic execution, in-app chat); the assigned Model Owner and accountable executive; the risk classification under the Tiers in this Framework; the date of most recent governance review; and the date of next scheduled review.

## Use Case Documentation

Each AI use case shall be documented in a Use Case Record prior to development (for in-house systems) or procurement (for vendor systems). The Use Case Record is reviewed and approved according to the risk classification in Section "Risk Classification" below. The Use Case Record shall set forth, at minimum:

1. Business Problem: a clear statement of the problem the AI system is intended to address, the customers or workforce members it serves, and the business outcomes intended.
2. Population and Decision Impact: identification of the populations whose data is processed, the populations affected by the AI system's outputs, and the nature of any decisions or recommendations produced.
3. Alternatives Considered: a description of the non-AI approaches considered (rules-based logic, human review, simpler statistical methods) and the rationale for selecting AI.
4. Success and Failure Criteria: quantitative and qualitative measures by which the system's performance and impact will be assessed; thresholds at which the system should be reviewed, retrained, or retired.
5. Data Flow: a description of the data inputs, intermediate processing, outputs, and downstream consumers; identification of any third-party services or vendor models in the data path.
6. Human Oversight Model: the specific human-in-the-loop, human-on-the-loop, or human-out-of-the-loop posture, with the operational checkpoints documented.
7. Failure Modes: identified failure modes including accuracy regressions, observed or anticipated biases, prompt-injection or jailbreak vulnerabilities for generative systems, and the operational impact of each.
8. Mitigations: the specific controls, guardrails, and procedures that address identified failure modes.
9. Regulatory and Ethical Considerations: any applicable law or guidance (EU AI Act tier, HIPAA implications for clinical-decision support, sectoral regulation), and any ethical considerations flagged by Privacy or Legal.

## Risk Classification

Each AI use case shall be classified into one of four tiers. The tiers are derived from analogous categories in the EU Artificial Intelligence Act and from the NIST AI Risk Management Framework, adapted for the Organization's context. Classification shall be performed by the Model Owner, reviewed by {{POLICY_OWNER}}, and concurred by Legal for Tier 3 and Tier 4 use cases.

| Tier | Description | Examples | Approval Path |
| --- | --- | --- | --- |
| Tier 1 | Minimal-risk: internal productivity uses with no decisional impact on individuals. | Text summarization for internal review; code suggestion in dev environments; meeting transcription for internal use. | {{POLICY_OWNER}} |
| Tier 2 | Limited-risk: customer-facing assistance with transparency obligations. | Customer-facing chatbots; generative content with disclosure; AI-suggested responses reviewed by humans. | {{POLICY_OWNER}} + Privacy Officer |
| Tier 3 | High-risk under analogous EU AI Act criteria: significant decisions affecting individuals. | Eligibility determinations; credit/risk scoring; clinical-decision support; resume screening with automated rejection; biometric identification. | {{POLICY_OWNER}} + Privacy Officer + Approver |
| Tier 4 | Prohibited or restricted under applicable law. | Social scoring of natural persons; manipulative subliminal AI; real-time biometric identification in public spaces (subject to exceptions). | Approver + Legal (default: not approved) |

Classification is reassessed at each governance review, upon any material change to the system or its operational context, and upon any change in applicable law or guidance. A change in classification shall be documented in the Inventory entry with the rationale.

## Data Governance for AI

1. Restricted or Confidential data shall not be submitted to AI systems that have not been reviewed under the Vendor Management Policy and that do not contractually prohibit the training of vendor models on submitted data. The vendor's contractual representation shall be specific (not merely a general data-confidentiality clause) and shall be reviewed by Legal where the data class is Restricted.
2. Training data used for in-house AI systems shall be cataloged in the Training Data Register. Each dataset entry shall include: provenance (in-house collection with consent record, public dataset with license terms, third-party purchase with contract reference); time period; classification of the data; consent basis (where personal data is involved); and any known limitations or biases.
3. Personally identifiable training data shall be subject to the same retention and disposal rules applicable to the underlying source under the Data Retention and Disposal Policy. Where the source has a retention limit, the trained model may need to be retrained or retired in advance of the limit.
4. Models trained on Restricted or Confidential data shall be treated as Restricted artifacts in their own right. Access to model weights, fine-tuned variants, embedding stores, and inference logs shall be controlled per the Access Control Policy.
5. Output filtering shall be applied to prevent generative AI systems from emitting Restricted data that was present in the training data; the filtering approach shall be documented in the Model Card.
6. Data subject rights requests (access, deletion, rectification) affecting training data shall be processed in accordance with the Customer Data Subject Access Request Procedure, with specific attention to the practical implications of deletion requests on already-trained models.

## Model Documentation Requirements

For each AI system in the Inventory, the Model Owner shall maintain a Model Card. The Model Card is a structured artifact, retained and versioned in the same library as the Use Case Record. The Model Card shall contain, at minimum:

1. Intended use, intended users, and explicitly out-of-scope uses (the latter is often the most useful section for downstream consumers).
2. Training data summary, with provenance, time period, classification, and known limitations or biases identified during data preparation.
3. Architecture summary including model family, parameter count where applicable, foundation model and version for derivative systems, fine-tuning approach, and prompt-engineering approach for prompt-only systems.
4. Evaluation results including accuracy on representative test sets, fairness across applicable subgroups (where the use case affects individuals), robustness to representative perturbations, and any benchmark comparisons.
5. Known failure modes and observed biases with quantitative characterization where available.
6. Operational guardrails: input validation rules, output filtering rules, rate limits, human-in-the-loop checkpoints, and the actions taken in response to monitoring alerts.
7. Monitoring and drift-detection metrics with target thresholds. Where monitoring is in place, the alerting routes and on-call ownership are documented.
8. Version history and material change log, including any retraining events, model swaps, or guardrail updates.
9. Regulatory considerations specific to the use case (e.g., HIPAA implications for clinical-decision support, EU AI Act tier rationale, state-law disclosure requirements for automated decision-making).

## Human Oversight Procedures

Human oversight is a primary control under this Framework. The required posture varies by tier.

1. Tier 1 systems may operate without explicit human-in-the-loop controls beyond standard operational oversight, but the Model Owner remains accountable for output quality and shall sample outputs periodically.
2. Tier 2 systems shall have a documented human-on-the-loop control. The control may be implemented as: pre-publication human review of outputs; post-publication monitoring of representative samples with feedback channels for end users; or a confidence-threshold gate that routes uncertain outputs to human review.
3. Tier 3 systems shall have a documented human-in-the-loop control for each material decision. The control is: human review of the AI output before action is taken; named decision-makers with authority to override the AI output; documented criteria for when to override; and a feedback loop into model retraining.
4. Agentic AI systems — those that take actions on the Organization's behalf rather than only generating content — require an entry in the Agent Registry. The Registry entry shall record: permitted action scope (specific tools or API endpoints); authentication mechanism (typically a service-account credential scoped to the registered action set); revocation procedure; and the escalation path for unintended actions. Agent capabilities shall be reviewed at least quarterly.
5. Workforce members operating AI systems shall complete role-appropriate training. Training shall cover the system's capabilities, its known limitations, the human-oversight procedures applicable to their role, and the incident reporting procedures in Section "Incident and Bias Reporting" below.

## Incident and Bias Reporting

AI system incidents shall be reported through the Incident Response Plan within four (4) business hours of identification. Reportable incidents include, without limitation:

1. Material accuracy regressions: a degradation in measured accuracy exceeding the threshold defined in the Model Card.
2. Observed bias affecting protected populations: a measurable disparate impact, or a credible report of bias from an end user, customer, or external researcher.
3. Prompt-injection or jailbreak events with material impact: an event in which a generative system produced output outside its intended scope due to adversarial input.
4. Unintended autonomous actions by agentic systems: actions taken by an agent outside the permitted scope recorded in the Agent Registry, or with effects materially different from those anticipated.
5. Privacy or regulatory implications: any incident implicating personal data, automated decision-making notification obligations, or sectoral-regulator notification.
6. Vendor AI incidents: incidents reported by vendor AI systems affecting the Organization's use of those systems.

The Model Owner shall participate in the post-incident review and shall produce, where appropriate, a Model Card update, a Use Case Record revision, or a retirement recommendation. AI incident metrics shall be reported quarterly to {{APPROVER_NAME}}.

## Vendor AI Risk Management

Third-party AI systems and AI features within third-party SaaS products are subject to the Vendor Management Policy with the following AI-specific additions, applied during vendor selection and reviewed on the standard vendor-review cadence:

1. Training Data Representations: the vendor shall represent its training-data practices, particularly whether customer data submitted to the service is used for training of vendor models. For Restricted-data use cases, the vendor's representation shall be specific and contractually binding.
2. Model Documentation: the vendor shall provide its applicable model documentation, including a model card or equivalent. The Organization shall obtain documentation sufficient to perform a meaningful risk classification under Section "Risk Classification".
3. AI-Specific Incident Notification: the vendor shall agree contractually to notify the Organization of material AI incidents affecting the service, with timelines consistent with other security-incident notification provisions.
4. Subprocessor AI: where the vendor relies on subprocessor AI (for example, hosting on a foundation-model provider), the vendor shall disclose the relationship and shall flow down applicable obligations.
5. Tier Classification: each vendor AI use case shall be classified under this Framework with the vendor system's risk profile considered. Tier classification of vendor systems shall be reassessed upon material change to the vendor's model, data practices, or subprocessor arrangements.
6. Termination Provisions: contracts with vendor AI providers shall include provisions for the return or destruction of customer data upon termination, with specific attention to data that may have been incorporated into vendor model training in violation of contract.


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
