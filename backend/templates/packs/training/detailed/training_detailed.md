# HIPAA Privacy Workforce Training

**Document Type:** Training Module
**Variant:** Detailed — Comprehensive, long-form, every consideration covered. The template a regulated startup would use to over-prepare.

---

## Cover Page

[LOGO: organization_logo.png] *(centered, 2" × 2")*

**HIPAA Privacy Workforce Training** — {{DOCUMENT_TITLE}}

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

## Learning Objectives

This module is structured around six (6) learning objectives, each tied to a specific knowledge or behavioral outcome. Upon completion, the Authorized User shall be able to:

1. Identify Protected Health Information ("PHI") as defined in 45 CFR Section 160.103, enumerate the eighteen (18) HIPAA identifiers listed at 45 CFR 164.514(b)(2), and distinguish PHI from de-identified information produced under either the Expert Determination method or the Safe Harbor method.
2. Articulate {{ORGANIZATION_NAME}}'s role as a HIPAA Business Associate, the obligations imposed by 45 CFR 164.504(e), and the corresponding flow-down obligations to subcontractors as Business Associate Subcontractors under 45 CFR 164.504(e)(1)(ii).
3. Apply the minimum-necessary standard at 45 CFR 164.502(b) to routine work activities, distinguishing between situations in which minimum-necessary applies and the four enumerated exceptions in 164.502(b)(2).
4. Distinguish between the categories of permitted uses and disclosures of PHI applicable to Business Associates and the categories requiring express written authorization from the Covered Entity or the data subject.
5. Recognize the signals of a suspected impermissible use or disclosure, a suspected security incident, and a suspected Breach as defined in 45 CFR 164.402, and report each through the appropriate channel within the timeframes specified in the Incident Response Plan and the Breach Notification Policy.
6. Describe the Authorized User's personal obligations under the Organization's sanctions policy, the anti-retaliation provisions of the Whistleblower Policy, and the consequences of policy violations under the Acceptable Use Policy.

## Target Audience

This module is required for all Authorized Users of {{ORGANIZATION_NAME}} whose work activities involve access to, handling of, or technical custody of PHI. The audience includes, without limitation:

- Engineering and platform operations staff, including software engineers, site reliability engineers, database administrators, and security engineers whose roles grant production access to systems holding PHI.
- Customer success staff with named access to customer tenants holding PHI, including customer success managers, support engineers, and implementation specialists.
- Data, analytics, and machine learning staff whose work product is derived from datasets that may contain PHI, even where the analytical output is intended to be aggregated or de-identified.
- Compliance, privacy, security, and legal staff with policy or oversight responsibilities affecting PHI.
- Contractors, consultants, and third-party vendors granted named individual access to systems holding PHI, regardless of engagement duration.

Members of the workforce whose role does not involve PHI shall complete the Organization's general security awareness module in lieu of this module, with a transition to this module triggered automatically upon any role change that grants access to PHI.

## Prerequisites

1. Successful completion of the Organization's general onboarding curriculum, including issuance of credentials to the learning management system.
2. Acknowledged receipt of the HIPAA Privacy Policy and the HIPAA Security Policy. Acknowledgement shall be recorded in the learning management system or its equivalent.
3. No prior healthcare or compliance background is assumed. The module is designed to be self-contained for workforce members with no prior exposure to healthcare privacy law.

## Module Content

### Section 1 — Foundations of HIPAA

This section introduces the statutory framework of the Health Insurance Portability and Accountability Act of 1996, as amended by the Health Information Technology for Economic and Clinical Health (HITECH) Act of 2009. The section presents the structure of the Privacy Rule (45 CFR Part 164, Subpart E), the Security Rule (45 CFR Part 164, Subpart C), and the Breach Notification Rule (45 CFR Part 164, Subpart D). The section describes the role of the Department of Health and Human Services Office for Civil Rights ("OCR") as the principal enforcement authority, the structure of OCR audits and complaint-driven investigations, and the publicly available enforcement actions database.

### Section 2 — Business Associates and BAAs

This section addresses the Business Associate construct. The section explains: (i) the definition of Business Associate under 45 CFR 160.103; (ii) the function performed by {{ORGANIZATION_NAME}} that triggers Business Associate status; (iii) the substantive obligations imposed by 45 CFR 164.504(e), including permitted-use restrictions, safeguards, reporting, subcontractor flow-down, and termination provisions; (iv) the structure of the Organization's standard Business Associate Agreement and the most common customer-specific deviations; and (v) the relationship between the BAA and the Master Service Agreement.

### Section 3 — Protected Health Information

This section presents the definition of PHI, the eighteen identifiers, and the distinction between PHI and de-identified information. The section walks the Authorized User through example datasets drawn from the Organization's product context, with each example annotated to identify the elements (if any) that render the dataset PHI. The section concludes with the Safe Harbor de-identification method, the Expert Determination method, and the practical implications of each method for the Organization's analytical and machine learning activities.

### Section 4 — Permitted Uses and Disclosures

This section enumerates the categories of uses and disclosures permitted to a Business Associate under the Privacy Rule and the Organization's BAAs, including: (i) treatment, payment, and healthcare operations uses performed on behalf of the Covered Entity; (ii) uses for the proper management and administration of the Business Associate's own operations consistent with 45 CFR 164.504(e)(2)(i)(A); (iii) reporting obligations applicable to security incidents and breaches under the BAA and the Breach Notification Rule; and (iv) disclosures to the Authorized User's own subcontractors under a Business Associate Subcontractor Agreement. The section then addresses the categories of use or disclosure that require express written authorization, with illustrative examples.

### Section 5 — Minimum Necessary

This section addresses the minimum-necessary standard at 45 CFR 164.502(b). The section presents the four enumerated exceptions to minimum-necessary, the Organization's operational implementation of the standard (role-based access controls, just-in-time access grants, the prohibition on bulk PHI export absent express business justification, and the quarterly access review), and the Authorized User's personal responsibility to limit their use of PHI to what is needed for the task at hand.

### Section 6 — Incident Recognition and Reporting

This section presents the categories of incident that warrant reporting and the corresponding channels, timeframes, and downstream procedures. The section addresses: (i) the distinction between an event, an incident, and a Breach as those terms are used in the Privacy Rule and the Organization's policies; (ii) the immediate reporting channels (the security email, the Slack incident channel, the PagerDuty escalation); (iii) the four-factor risk assessment under 45 CFR 164.402(2); and (iv) the Organization's anti-retaliation commitment under the Whistleblower Policy.

## Knowledge Check Questions

1. Which of the following datasets constitute PHI? Select all that apply: (a) a list of patient names paired with appointment times; (b) a count of appointments by ZIP-3 region with no individual identifiers; (c) a workforce member's email address used to log in to the LMS; (d) a list of medical record numbers paired with diagnosis codes; (e) a de-identified extract produced under Safe Harbor.
2. You are a customer success engineer responding to a customer escalation. The customer asks you to "pull the full schedule for Dr. Smith's panel for the last six months so we can investigate a billing anomaly." Identify two ways the minimum-necessary standard applies to this request and the action you would take.
3. A coworker, while screen-sharing during a routine working session, accidentally exposes a customer's patient list to a third party who is on the call. Describe: (a) whether this is an incident, a Breach, or possibly neither; (b) the channels and timeframes within which this event should be reported; and (c) the immediate steps the coworker should take.
4. State {{ORGANIZATION_NAME}}'s role under HIPAA, and identify three specific obligations arising from that role. For each obligation, name the corresponding policy or procedure in the Organization's policy library that operationalizes it.
5. Distinguish between an "incident" and a "Breach" as those terms are used in the Organization's policies and the Privacy Rule. Apply the four-factor risk assessment to a scenario in which an internal email containing five (5) patient names was forwarded inadvertently to an unintended workforce recipient who immediately deleted it.
6. A Business Associate Subcontractor of the Organization reports that they have discovered a misconfigured S3 bucket containing PHI for which they have not yet confirmed external access. Describe the Organization's obligations and the next three actions you would take.

## Completion Criteria

1. The Authorized User shall complete each of the six (6) content sections in sequence. Sections may be paused and resumed; sections may not be skipped.
2. The Authorized User shall achieve a passing score of at least eighty percent (80%) on the Knowledge Check, computed as the percentage of questions for which the User selects the correct answer (or, for free-response questions, for which the User's response is graded acceptable by the rubric).
3. The Authorized User shall acknowledge the HIPAA Privacy Policy and this module in the learning management system. Acknowledgement is a separate completion event from the Knowledge Check.
4. Completion shall be recorded in the workforce member's training record. The Office Manager / HR Coordinator shall confirm completion in the monthly training report.
5. Authorized Users who do not achieve a passing score on the Knowledge Check shall be offered the opportunity to review the relevant content sections and re-attempt the Knowledge Check. Three (3) failed attempts within ninety (90) days shall trigger an instructor-led review session with the HIPAA Privacy Officer.

## Recertification Cadence

Authorized Users shall recertify by completing this module at least once every twelve (12) months, computed from the initial completion date. The recertification module shall include: (i) any material updates to the Privacy Rule, OCR guidance, or applicable case law since the prior cycle; (ii) any material updates to the Organization's policies, procedures, or BAA template; (iii) any role-specific scenarios drawn from incidents observed during the prior cycle, anonymized as appropriate. Failure to complete recertification within thirty (30) days of the recertification due date shall trigger escalation to the Authorized User's manager. Failure to complete recertification within sixty (60) days shall be evaluated by {{POLICY_OWNER}} for potential suspension of access pending completion.


## Roles and Responsibilities

| Role | Responsibilities |
| --- | --- |
| Training Owner ({{POLICY_OWNER}}) | Maintains this module, schedules reviews, and signs off on annual content updates. |
| Approver ({{APPROVER_NAME}}, {{APPROVER_TITLE}}) | Provides executive approval at issuance and annual review. |
| HIPAA Privacy Officer | Subject-matter authority for content; reviews any material change to the Privacy Rule references. |
| Workforce Member (Learner) | Completes the module within the assigned window; acknowledges completion in the learning system. |
| Office Manager / HR Coordinator | Tracks completion; chases overdue completions; reports completion to the Approver quarterly. |

## Review and Maintenance

**Next review date:** {{NEXT_REVIEW_DATE}}

**Review frequency:** Annually, or upon material change to HIPAA Privacy Rule guidance, the Organization's BAA template, or workforce composition.

**Review triggers:**

- A material change in applicable laws, regulations, or contractual obligations.
- Findings from an internal or external audit that affect this document.
- A security or privacy incident that exposes a gap in the document.
- An organizational change (acquisition, divestiture, new business line) that affects scope.

## Related Documents

- HIPAA Privacy Policy
- Acceptable Use Policy
- Information Security Policy
- Breach Notification Policy

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
