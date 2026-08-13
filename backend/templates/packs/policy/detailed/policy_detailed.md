# Acceptable Use Policy

**Document Type:** Policy
**Variant:** Detailed — Comprehensive, long-form, every consideration covered. The template a regulated startup would use to over-prepare.

---

## Cover Page

[LOGO: organization_logo.png] *(centered, 2" × 2")*

**Acceptable Use Policy** — {{DOCUMENT_TITLE}}

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

## Purpose

The purpose of this Acceptable Use Policy is to provide comprehensive guidance regarding the authorized and prohibited uses of {{ORGANIZATION_NAME}}'s information technology resources, including but not limited to: corporate-issued endpoints, network infrastructure, cloud-hosted applications, email systems, collaboration platforms, code repositories, software development environments, customer-facing production systems, internal administrative systems, and any other digital asset owned, leased, licensed, or operated by the organization.

This policy applies to full-time employees, part-time employees, contractors, consultants, third-party vendors with system access, and any other authorized user as designated in writing by {{POLICY_OWNER}}. The intent of this policy is fourfold: (1) to protect organizational data from unauthorized disclosure, modification, or destruction; (2) to ensure productive and lawful use of computing resources during authorized work activities; (3) to maintain audit-readiness against applicable regulatory frameworks including but not limited to HIPAA, PCI DSS, SOC 2 Type II, ISO/IEC 27001:2022, NIST CSF 2.0, HITRUST CSF, and any contractual security obligations to which the organization has agreed; and (4) to establish a clear framework for the investigation, documentation, and remediation of policy violations.

This policy is one component of the organization's broader information security program. It should be read in conjunction with the Information Security Policy, the Access Control Policy, the Data Classification Policy, the Incident Response Plan, and any policy or procedure specifically referenced herein.

## Scope

This section delineates the personnel, devices, systems, data classes, and activities within the scope of this policy.

### Personnel in Scope

1. Full-time and part-time employees of {{ORGANIZATION_NAME}}, regardless of geographic location or work arrangement.
2. Contractors, consultants, and independent professionals engaged by the organization for any duration.
3. Interns, fellows, and other temporary workforce members.
4. Third-party vendors to whom system access has been granted in writing by an authorized representative of the organization.
5. Auditors, assessors, and inspectors engaged by the organization or its customers, subject to the terms of their engagement.

### Systems in Scope

1. Endpoint devices owned or leased by the organization, including laptops, desktops, tablets, mobile phones, and any peripheral device connected to organization networks.
2. Personal devices used for organization business under the Bring-Your-Own-Device Standard, including but not limited to mobile phones used for email and calendar access.
3. On-premises and cloud-hosted server infrastructure, whether operated directly by the organization or by a third-party provider on its behalf.
4. Network infrastructure including routers, switches, firewalls, wireless access points, and any VPN or zero-trust network access service.
5. Identity provider services and any system that performs authentication or authorization for organization resources.
6. Cloud-hosted applications, including productivity, collaboration, customer relationship management, financial, human resources, security monitoring, and engineering platforms.
7. Source code repositories, build systems, deployment pipelines, and any development or production environment owned by the organization.
8. Customer-facing production systems and the data they create, receive, maintain, or transmit.

### Data Classes in Scope

This policy applies to all data classes defined in the Data Classification Policy, with provisions tailored to the sensitivity of each class. The following data classes warrant heightened attention:

- **Restricted:** Protected Health Information as defined in 45 CFR § 160.103, payment card data within the scope of PCI DSS, government-classified information, attorney-client privileged communications, and any other class designated Restricted by {{POLICY_OWNER}}.
- **Confidential:** Non-public information of the organization, its customers, or its business partners, including but not limited to source code, financial records, customer lists, pricing, contracts, and strategy documents.
- **Internal:** Information intended for workforce use that does not warrant Restricted or Confidential designation.
- **Public:** Information explicitly approved for public release.

## Policy Statements

### Authorized Use

Authorized Users are expected to use the organization's information resources in the furtherance of legitimate business activities. Personal use of organization resources is permitted on a limited and incidental basis, provided that such use: (i) does not interfere with work performance; (ii) does not consume material organization resources; (iii) does not violate any provision of this policy; and (iv) does not create legal, regulatory, or reputational risk for the organization.

### Authentication and Credentials

1. Authorized Users shall authenticate to organization systems using credentials issued to them individually. Shared accounts are prohibited except where expressly authorized in writing under a documented compensating control.
2. Passwords, multi-factor authentication codes, hardware tokens, and session credentials shall not be disclosed, shared, written down in unsecured locations, or stored in unapproved password managers.
3. Authorized Users shall enable and use multi-factor authentication on every system that supports it, and shall not bypass or disable multi-factor authentication enforcement.
4. Compromise or suspected compromise of credentials shall be reported to {{SECURITY_CONTACT}} within four (4) business hours of discovery.

### Data Handling

1. Restricted and Confidential data shall be stored only in organization-approved systems as designated in the Data Storage Approved List maintained by the Information Security function.
2. Restricted and Confidential data in transit outside the organization's control shall be encrypted in accordance with the Encryption Standard.
3. Authorized Users shall not transmit Restricted or Confidential data through consumer messaging applications, personal email accounts, or any other unsanctioned channel.
4. Authorized Users shall not store Restricted or Confidential data on personal devices, personal cloud accounts, or removable media not approved by the Information Security function.
5. Authorized Users shall comply with all customer-specific data handling requirements communicated in writing.

### Endpoint Use

1. Authorized Users shall use organization-issued endpoints for activities involving Restricted or Confidential data.
2. Endpoints shall remain enrolled in the organization's mobile device management or endpoint detection and response solution at all times.
3. Authorized Users shall not disable, uninstall, or circumvent any endpoint security agent.
4. Operating system and application updates issued by the organization shall be installed within the timeframes specified by the Information Security function.
5. Lost or stolen endpoints shall be reported to {{SECURITY_CONTACT}} within four (4) business hours of discovery.

### Software Installation and Use

1. Authorized Users shall install software only from the organization's approved software catalog or through the formal software acquisition process.
2. Use of software-as-a-service applications for organization business shall be governed by the Vendor Management Policy.
3. Generative artificial intelligence services shall be used in accordance with the AI Acceptable Use Standard, with particular attention to the prohibition on submitting Restricted or Confidential data to consumer-tier generative AI services.
4. Use of personally licensed software for organization business is permitted only where the license expressly authorizes commercial use and where the software has been reviewed under the Vendor Management Policy.

### Communications

1. Email and collaboration platforms shall be used in a professional manner consistent with the organization's code of conduct.
2. External communications containing Restricted or Confidential data shall use organization-approved secure channels.
3. Authorized Users shall not represent themselves as speaking on behalf of the organization on public forums except as authorized by the Communications team.
4. Use of organization email for personal subscriptions, mailing lists, or commercial activity unrelated to organization business is prohibited.

### Monitoring and Privacy

1. The organization reserves the right to monitor, inspect, and audit use of its information resources at any time, without prior notice to the Authorized User, to the extent permitted by applicable law.
2. Monitoring is conducted for purposes including but not limited to security threat detection, policy compliance verification, regulatory and audit support, system performance management, and the protection of organizational data and assets.
3. Authorized Users should have no expectation of privacy in their use of organization information resources, except as expressly provided by applicable law.
4. Monitoring shall be conducted in accordance with the organization's privacy policies and applicable law, including data protection laws of the jurisdictions in which the organization and the Authorized User operate.

## Compliance and Enforcement

Compliance with this policy is a condition of continued authorization to access the organization's information resources. The organization's response to a suspected violation will depend on the nature, severity, intent, and impact of the violation, and on the Authorized User's history of prior conduct.

Possible responses include, in escalating order of severity: informal coaching, formal warning, mandatory retraining, suspension of access pending investigation, formal disciplinary action up to and including termination of employment or contract, civil action for damages, and referral to law enforcement where conduct may constitute a violation of criminal law.

Enforcement actions shall be documented and retained in accordance with the Document Retention Schedule. The Human Resources function shall be engaged for any enforcement action affecting an employee's employment status.

## Exceptions Process

Exceptions to specific provisions of this policy may be granted in writing under the following process:

1. The Authorized User or their manager shall submit an Exception Request Form to {{POLICY_OWNER}} setting forth: (a) the specific provision for which an exception is sought; (b) the business justification for the exception; (c) the alternative control(s) that will mitigate the risk addressed by the provision; (d) the proposed duration of the exception, not to exceed twelve (12) months without renewal; and (e) the proposed acceptance signatory.
2. {{POLICY_OWNER}} shall evaluate the request in consultation with the Information Security function within ten (10) business days of submission.
3. Material exceptions, as determined by {{POLICY_OWNER}}, shall be referred to {{APPROVER_NAME}} for approval.
4. Approved exceptions shall be documented in the Exception Register, including the alternative control, the acceptance signatory, the duration, and the review date.
5. Exceptions shall be reviewed at least every six (6) months. An exception that is not renewed shall lapse automatically.
6. No exception shall be effective absent written documentation. Verbal exceptions and informal approvals are of no effect.

## Definitions

- **"Authorized User"** means any individual with a documented authorization to access the organization's information resources, including the personnel categories enumerated in the Scope section.
- **"BYOD" (Bring-Your-Own-Device)** refers to the use of personal devices for organization business under the Bring-Your-Own-Device Standard.
- **"Confidential Information"** means any non-public information of the organization, its customers, or its business partners, including but not limited to source code, financial records, customer lists, pricing, contracts, and strategy documents.
- **"Information Resources"** includes all systems, devices, applications, networks, and data described in the Scope section.
- **"MFA" (Multi-Factor Authentication)** means an authentication method requiring two or more independent verification factors.
- **"PHI" (Protected Health Information)** has the meaning ascribed in 45 CFR § 160.103.
- **"Restricted Data"** refers to the highest classification level defined in the Data Classification Policy, including PHI, payment card data, government-classified information, and attorney-client privileged communications.


## Roles and Responsibilities

| Role | Responsibilities |
| --- | --- |
| Policy Owner ({{POLICY_OWNER}}) | Maintains this Policy, schedules reviews, processes exception requests, and approves minor revisions in accordance with the change control process. |
| Approver ({{APPROVER_NAME}}, {{APPROVER_TITLE}}) | Provides executive approval at issuance and at each annual review. Sponsors enforcement decisions arising from material policy violations. |
| Reviewer | Conducts substantive review at the scheduled cadence and documents the review outcome in the document control table. |
| Authorized User | Reads and complies with this Policy. Reports suspected violations and incidents through the channels defined herein. |

## Review and Maintenance

**Next review date:** {{NEXT_REVIEW_DATE}}

**Review frequency:** Annually, or upon a qualifying trigger.

**Review triggers:**

- A material change in applicable laws, regulations, or contractual obligations.
- Findings from an internal or external audit that affect this document.
- A security or privacy incident that exposes a gap in the document.
- An organizational change (acquisition, divestiture, new business line) that affects scope.

## Related Documents

- Information Security Policy
- Access Control Policy
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
