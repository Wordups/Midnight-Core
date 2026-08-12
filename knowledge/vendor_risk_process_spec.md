# Vendor Risk / Third-Party Risk — Neutral Process Specification

Operating context for LLM-assisted assessment features. This is a neutral
process specification — no company-specific SOP language. It grounds how the
corpus answer engine reasons about vendor/security assessments.

## Purpose

The vendor-risk process determines whether a third party introduces acceptable
security, privacy, operational, compliance, or business risk.

The objective is not simply to complete a questionnaire. The assessment must
establish whether applicable requirements are satisfied, identify unsupported
or deficient controls, collect appropriate evidence, and route exceptions to
the appropriate human decision-makers.

## 1. Vendor intake

Establish the vendor's context before determining what needs to be assessed.
Core intake questions:

- What product or service is being provided?
- Who is the internal business owner?
- What business function does the vendor support?
- Will the vendor access company systems? Production?
- Will the vendor process, transmit, or store company data? What types?
- Is PII involved? Regulated or sensitive data? Payment/cardholder data?
  Healthcare/ePHI?
- Is the service business-critical?
- Does the vendor use subprocessors or downstream third parties?
- Where is data stored or processed? What integrations are required?
- What would the business impact be if the vendor became unavailable?

These answers establish **scope and inherent risk**.

## 2. Assessment domains

The questionnaire should not ask every vendor every question. Questions are
selected by applicability and risk.

- **Governance** — security policies, ownership, governance structure, risk
  assessments, review cadence, training, audits, control monitoring.
- **Identity & access management** — MFA, SSO/federation, privileged access,
  RBAC, least privilege, joiner/mover/leaver, access reviews, service
  accounts, password requirements, admin-access monitoring.
- **Data protection** — encryption at rest/in transit, key management,
  classification, retention, secure deletion, backup protection, segregation,
  DLP, residency.
- **Application security** — secure SDLC, code review, SAST/DAST, dependency
  scanning, vulnerability management, pen testing, change management, secrets
  management, API security, production access controls.
- **Infrastructure / cloud** — providers, segmentation, firewalls, endpoint
  security, configuration management, logging, monitoring, hardening,
  scanning, patching.
- **Security operations** — monitoring, SIEM, IR plan, escalation, staffing,
  threat detection, log retention, tabletops, customer notification.
- **Privacy** — PII processing, privacy policies, data-subject rights, DPAs,
  retention, international transfers, subprocessors, PIAs, breach
  notification.
- **BC/DR** — BCP, DR, backup strategy, recovery testing, RTO, RPO, geographic
  redundancy, critical dependencies, exercises.
- **Supply chain / fourth-party** — subprocessors, vendor-management program,
  supplier assessments, critical suppliers, software supply-chain controls,
  dependency management, contractual security requirements.
- **Compliance** — SOC 2, ISO 27001, PCI DSS, HITRUST, NIST mappings,
  HIPAA documentation, independent assessments, regulatory attestations.

## 3. Evidence

**A "Yes" answer does not prove a control exists.** Distinguish:

```
CLAIM  ("We require MFA.")
  ↓
EVIDENCE  (policy, configuration, SOC report, audit evidence, screenshot,
           attestation)
  ↓
VALIDATION  (does the evidence actually support the claim?)
```

Evidence types: SOC reports, ISO certificates, PCI AOCs, HITRUST
certifications, security/privacy policies, pen-test reports, vulnerability
reports, architecture diagrams, BCP/DR documentation, IR plans, access-control
policies, encryption documentation, training records, independent audits.

Evaluate evidence for **relevance, scope, date, expiration/currentness,
source, and sufficiency**.

## 4. LLM questionnaire behavior

Conduct an assessment rather than blindly display a questionnaire:

```
Vendor context → determine applicability → applicable requirements
→ inspect existing evidence → what is already established?
→ what remains unknown? → ask question → interpret response
→ evidence sufficient?  YES → satisfied
                        NO  → follow-up → request evidence → reassess
```

## 5. Follow-up logic

Challenge vague responses. "We use industry-standard encryption" is not
sufficient — follow up for standards (at rest, in transit), then for
supporting documentation or independent validation. "Yes, we use MFA" may not
address the underlying requirement (e.g., privileged access specifically).
This is the difference between **question completion and control assessment**.

## 6. Standards / control corpus

Ground against a normalized control corpus. NIST requirements, SOC 2 criteria,
ISO 27001 controls, PCI requirements, and internal policies mapping to the
same underlying **security requirement** are one requirement, not five
questions. The job is: **determine whether the underlying requirement is
demonstrably satisfied**, not "does this vendor have SOC 2?"

## 7. Assessment outcomes

Every assessed requirement reaches a defined state:

```
SATISFIED · PARTIALLY SATISFIED · NOT SATISFIED · INSUFFICIENT EVIDENCE
NOT APPLICABLE · NEEDS FOLLOW-UP · NEEDS SME REVIEW
```

The LLM may **recommend** classification; consequential risk decisions remain
governed by deterministic rules and/or human review.

## 8. Findings and remediation

When a requirement isn't satisfied, capture: finding → affected
requirement/control → evidence/response → risk → recommended remediation →
owner → due date/SLA → status → evidence of remediation → review → closure.
Maps naturally into Jira, ServiceNow, or a GRC platform.

## 9. Human gates

Human involvement remains required for: material risk determinations, risk
acceptance, exceptions, ambiguous or conflicting evidence, high-risk findings,
compensating controls, final vendor approval/rejection, novel security
conditions.

> **Automate the work surrounding judgment, not eliminate judgment.**

## 10. ILAO model

- **INPUT** — what information and artifacts exist? (vendor info,
  questionnaires, documents, evidence, previous assessments, standards,
  policies, tickets)
- **LOGIC** — ASK: what are we trying to determine? TASK: what work must
  occur? DELIVERABLE: what evidence/result demonstrates completion?
  STANDARD: against what requirement is the deliverable evaluated?
- **AUTOMATION STRATEGY** — Python/JS: deterministic logic. REST APIs: system
  integration. LLM: unstructured interpretation/questioning. Workflow
  platforms: routing/approvals/SLAs. Human: judgment and authorization.
- **OUTPUT** — assessment, evidence, finding, risk, remediation, approval,
  audit trail, metrics.

## Core instruction

> Do not treat vendor risk as questionnaire completion. Determine what
> security requirements are applicable, identify what existing evidence
> already establishes, determine the unresolved requirements, ask targeted
> questions to resolve those requirements, request supporting evidence when
> necessary, and map each conclusion back to the applicable standard or
> control. Do not make consequential risk-acceptance or vendor-approval
> decisions without the designated human approval step.

Product mantra:

> **Do not ask a question that reliable existing evidence has already
> answered.**
