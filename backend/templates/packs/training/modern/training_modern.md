# HIPAA Privacy Workforce Training

**Document Type:** Training Module
**Variant:** Modern — Scannable, plain-language, modern enterprise. Short paragraphs, clear headings, designed for readability.

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

After this training, you'll be able to:

- Spot PHI when you see it. Know the 18 HIPAA identifiers.
- Explain why we're a Business Associate and what our BAA obligations are.
- Apply minimum-necessary in your daily work.
- Know when something is a "permitted use" vs needs authorization.
- Report a suspected incident properly — what channel, what timeline.

## Target Audience

Everyone who could see PHI in their work. That's most of engineering, customer success, ops, and security. Non-PHI roles take the general security awareness module instead.

## Prerequisites

- You've finished onboarding and have access to the LMS.
- You've read the HIPAA Privacy Policy and acknowledged it.
- No prior healthcare experience required.

## Module Content

### What is HIPAA, and what are we?

HIPAA is the federal law governing protected health information. Our customers are Covered Entities. We're their Business Associate. Our obligations come from the BAA we signed with them and from 45 CFR 164.504(e).

### What is PHI?

Health information tied to one of 18 identifiers (name, MRN, address, dates, SSN, etc.). De-identified data — health info with identifiers stripped per the Safe Harbor rule — is not PHI.

### Permitted uses

We can use PHI to deliver our service to the Covered Entity, to manage our own operations within the BAA limits, and to report incidents. Anything else needs written authorization.

### Minimum necessary

Access only what you need. Our role-based access and just-in-time grants enforce this technically. Don't bulk-export tenant data unless you have written justification.

### When to report

If you see something off — accidental disclosure, suspicious access, lost device with data — tell {{SECURITY_CONTACT}}. Slack #sec-incidents works. Most reports turn out to be nothing; we'd rather hear them anyway. We don't retaliate.

## Knowledge Check

1. Which of these is PHI? (a) patient name + appointment, (b) aggregated ZIP-3 utilization, (c) workforce email, (d) MRN + diagnosis. Pick all that apply.
2. Give two examples of minimum-necessary in a customer success workflow.
3. You see a coworker downloading a tenant data extract to personal Dropbox. What do you do and how fast?
4. Are we a Covered Entity or a Business Associate? Name two obligations that come with our role.
5. What's the difference between an "incident" and a "Breach"?

## Completion Criteria

- Finish every section.
- Score 80% or better on the knowledge check.
- Acknowledge the Privacy Policy and this module in the LMS.
- Completion lands in your training record.

## Recertification Cadence

Once a year. Includes any material updates since the last cycle. Miss the recert by 30 days and your manager gets pinged.


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
