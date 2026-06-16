# Midnight features and selling points

## Positioning

Midnight is a compliance program builder for teams that are running GRC out of spreadsheets, shared drives, email threads, and half-finished policy folders.

It is not trying to be another checkbox monitor. The useful question is not "did we connect every SaaS app?" The useful question is "what do we have, what is missing, what should we fix first, and what artifact can we show leadership or an auditor?"

Core line:

"You're running compliance out of a spreadsheet. We were too. Then we built something better."

Short version:

Midnight turns scattered compliance work into a tenant-scoped, traceable program: documents in, findings out, next actions prioritized, artifacts ready to share.

## Primary buyers

### 1. Security engineer who inherited SOC 2

They did not ask to become the compliance owner. They need a system that tells them what to do next, not a platform that assumes they already know.

What to sell:
- Upload your existing docs.
- See what is stale, missing, duplicated, or conflicting.
- Get a prioritized repair list.
- Generate the policy sections you need.

### 2. First GRC hire walking into a mess

They inherit old policies, unknown owners, no source of truth, and leadership asking for progress.

What to sell:
- Build the current-state picture fast.
- Make ownership visible.
- Turn the policy folder into a program.
- Show leadership a clean summary without building a deck from scratch.

### 3. Founder or CTO with an enterprise deal on the line

They just learned SOC 2, HIPAA, ISO 27001, or a security questionnaire matters because a customer asked.

What to sell:
- Start from where you are.
- Build the first compliance operating layer.
- Avoid hiring a consultant just to understand the mess.
- Produce useful evidence and policy drafts faster.

### 4. Solo GRC consultant

They need repeatable program setup across multiple clients without rebuilding trackers every time.

What to sell:
- Multi-tenant workspace model.
- Standardized intake and findings workflow.
- Repeatable artifact generation.
- Cleaner client reporting.

## Feature set

### Self-serve signup and onboarding

Status: partially implemented; full wizard is launch-blocking.

What it does:
- Creates a tenant and owner profile for a new account.
- Starts the user on trial access.
- Routes new users into onboarding before the dashboard.
- Planned launch wizard collects framework targets, primary objective, and preferred build method.

Selling point:
- Users do not need a sales call to start building a compliance program.
- The onboarding flow gives Midnight enough context to make the dashboard useful immediately.

Buyer language:
"You can start with the framework you care about and the state you're actually in. Existing docs, no docs, audit prep, cleanup, whatever. Midnight adapts the first steps to that context."

### Tenant-scoped compliance workspace

Status: core architecture present; ongoing hardening required before public launch.

What it does:
- Every account belongs to a tenant.
- User, document, dashboard, billing, and analysis data are scoped to tenant context.
- Bird Eye and document intelligence are being hardened to remove old demo-tenant assumptions.

Selling point:
- Consultants and multi-client operators can use one system without data bleeding between clients.
- SMBs get a clean private workspace instead of a generic document processor.

Buyer language:
"Each company gets its own workspace. Documents, findings, tasks, and reports stay tied to that company. No shared spreadsheet problem. No mixed client folders."

### Document intake and policy library

Status: launch feature; parser fixes still required for reliable go-live.

What it does:
- Uploads policy and compliance documents.
- Extracts text and metadata.
- Stores documents in a structured library.
- Tracks document type, owner, version, framework mapping, and section count where available.

Supported document types:
- Policy
- Standard
- Procedure
- SOP
- Playbook
- Plan

Selling point:
- Turns the shared-drive policy folder into something the system can reason about.
- Gives the buyer a current-state picture without manually reading every document.

Buyer language:
"Upload the folder. Midnight reads it, organizes it, and starts showing what the documents actually say."

### Bird Eye document review

Status: launch-critical; non-TKO tenant proof required.

What it does:
Bird Eye runs document intelligence over the tenant's policy library. The core detectors are:
- Duplicate detection
- Conflict detection
- Stale governance detection
- Framework gap detection
- Orphan detection

Selling point:
- Finds the problems a reviewer would normally catch by reading everything manually.
- Helps identify stale policies, conflicting language, missing companion procedures, and framework coverage gaps.

Buyer language:
"Midnight does the first-pass review of your policy library. It finds the stuff that usually gets discovered late, when the auditor or customer is already asking."

### Gap analysis

Status: core capability.

What it does:
- Maps uploaded documents to framework controls.
- Computes required controls minus covered controls.
- Shows where the tenant's documentation does not cover the framework target.

Selling point:
- Replaces a manual spreadsheet coverage exercise.
- Gives practitioners a defensible starting point for remediation.

Buyer language:
"Instead of staring at a framework and guessing what your docs cover, Midnight gives you the gap list."

### Prioritized next actions

Status: product direction; must be wired cleanly for launch surfaces.

What it does:
- Converts findings into an ordered repair path.
- Moves the user from "here are all your problems" to "fix this first."

Selling point:
- This is the difference between analysis and operational help.
- Most tools find issues. Midnight should tell the user what to do next.

Buyer language:
"A long list of findings is just another spreadsheet. Midnight turns the list into a work plan."

### Trace Agent policy generation

Status: core agent capability; should remain human-reviewed.

What it does:
- Generates audit-preparation policy drafts through a fixed multi-step process.
- Uses framework requirements and tenant context.
- Produces draft language, not legal/compliance certification.

Selling point:
- Cuts policy drafting time.
- Gives teams a starting point when they have no policy or an outdated one.
- Keeps humans in control for review and approval.

Buyer language:
"Midnight drafts the policy section. Your team reviews it, adjusts it, and approves it. You are not starting from a blank page."

Compliance-safe wording:
- Say: "draft," "prepared," "readiness," "gap analysis," "review-ready."
- Do not say: "guaranteed compliant," "certified," or "audit passed."

### GRC Card

Status: strategic/launch artifact; implementation status must be verified before selling as live.

What it does:
- Summarizes the compliance program in a leadership-ready format.
- Shows framework coverage, open findings, pending tasks, recent activity, and program health.
- Planned distribution sends the card on a cadence to leadership or stakeholders.

Selling point:
- Makes invisible compliance work visible.
- Gives the practitioner a recurring artifact they can send without rebuilding a deck every month.
- Creates habit and retention because the reporting workflow lives in Midnight.

Buyer language:
"When someone asks where the program stands, you should not have to build a status deck from scratch. The GRC Card is the answer."

### SME request and task workflow

Status: launch-ready list item; implementation must be confirmed.

What it does:
- Lets the GRC owner create requests for SMEs.
- Assigns work to engineering, HR, legal, finance, or infrastructure owners.
- Tracks status from open to in review to complete.
- Planned email notifications and invite flow.

Selling point:
- Compliance work stops disappearing into inboxes.
- The analyst can see who owes what and what is blocked.

Buyer language:
"The problem is not that SMEs refuse to help. The problem is that the request has no context, no owner, and no tracking. Midnight fixes that."

### Audit log and traceability

Status: launch requirement.

What it does:
- Records meaningful actions: uploads, findings, requests, task updates, generated drafts, and distributed artifacts.
- Ties actions to actor, tenant, action type, and timestamp.

Selling point:
- Helps answer "who changed this, when, and why?"
- Reduces audit panic because decisions are captured as they happen.

Buyer language:
"Audit prep gets ugly when everyone has to reconstruct decisions from old emails. Midnight keeps the trail while the work happens."

### Billing and plan enforcement

Status: checkout route exists; webhook completion is launch-blocking.

What it does:
- Authenticated checkout creates Stripe sessions.
- Planned webhook updates tenant plan after purchase.
- Plan limits should adjust based on trial or paid status.

Selling point:
- Self-serve upgrade path.
- No founder intervention required to move from trial to paid.

Buyer language:
"Start on trial. Upgrade when the product is doing real work for you."

## Top selling points

### 1. Midnight starts where the buyer actually is

Most early compliance programs are messy. Policies are in Word. Evidence is in email. Ownership is unclear. Midnight does not require the buyer to clean all of that before starting. The mess is the input.

### 2. It makes compliance work visible

The strongest emotional value is not time savings. It is proof. The practitioner can show what exists, what is missing, what changed, and what needs attention.

### 3. It turns documents into a program

A folder of policies is not a compliance program. Midnight reads the documents, maps them to frameworks, finds gaps, and creates a repair path.

### 4. It gives the next action, not just the finding

A finding list still leaves the user with decision fatigue. Midnight's wedge is prioritization: what to do first and why.

### 5. It helps practitioners look prepared

The buyer wants to look on top of things to leadership, auditors, customers, and internal SMEs. Midnight gives them artifacts and traceability before someone asks.

### 6. It is built for teams before they have a mature GRC function

The target is not the Fortune 500 compliance department. It is the company crossing the threshold: first enterprise deal, first audit, first GRC hire, first serious questionnaire.

### 7. It has a path into AI governance

AI governance is the wedge for V2. The architecture can support evolving frameworks, policy generation, and corpus-based reasoning. The public launch should not oversell this as fully live unless the module is actually shipped.

## One-liners

- Compliance work is invisible until something goes wrong. Midnight makes it visible before that.
- Upload your policy folder. Midnight tells you what it sees.
- Stop running audit prep out of a spreadsheet.
- Your policy library should know what framework it supports.
- Findings are useful. Prioritized fixes are better.
- The GRC Card is the status deck you should not have to rebuild every month.
- Midnight is the first operating layer for a compliance program that does not have one yet.
- Vanta tells you a control is failing. Midnight helps you build the thing that satisfies it.
- For the security engineer who inherited SOC 2 and needs a plan by Friday.
- For the first GRC hire walking into a shared drive full of old policies.

## Website section copy

### Hero

Stop running compliance out of a spreadsheet.

Midnight turns policy folders, SME requests, and framework requirements into a working compliance program. Upload documents, find gaps, prioritize fixes, and generate review-ready artifacts without rebuilding your process from scratch.

CTA:
Start a trial

Secondary CTA:
See how it works

### Pain section

Compliance work usually lives in the wrong places: spreadsheets, shared drives, Slack threads, email follow-ups, and old policy documents nobody fully trusts.

That works until a customer asks for SOC 2, an auditor asks why a control was scoped that way, or leadership asks where the program stands.

Midnight gives that work a home.

### Product section

Midnight reads your policy library, maps it against the frameworks you care about, and shows what is stale, missing, conflicting, or duplicated. Then it helps turn those findings into action: draft the missing policy section, assign the SME request, update the dashboard, and produce the status artifact.

### Security posture section

Midnight is built as a multi-tenant compliance system. Tenant data is scoped by workspace, protected routes require authenticated sessions, and launch gates include tenant-isolation tests, secret handling checks, Stripe webhook validation, and live deployment proof.

Do not overstate this section until every go-live security gate passes.

## Demo script

Goal: complete one ILWAO loop in 15 minutes.

1. Input: Upload a policy document.
2. Logic: Show Bird Eye findings.
3. Wedge: Show what Midnight recommends fixing first.
4. Automate: Generate or draft the missing policy section.
5. Output: Show the GRC Card or dashboard summary.

Close with:
"Which part of that loop is most broken for you right now? Getting the work in, knowing what it means, knowing what to fix first, doing the work, or reporting it?"

## Objection handling

### "We don't have policies yet."

That is a reason to start, not a reason to wait. Midnight can help generate the first draft, map it to the framework, and keep the review trail in one place.

### "We're already using Vanta."

Vanta is useful for monitoring. It does not solve the side-spreadsheet problem: policy drafting, SME coordination, prioritization, and leadership reporting. Midnight should sit where that manual work still exists.

### "We don't have a compliance person."

That is the use case. Midnight gives the security owner or founder a starting operating layer until they can hire one.

### "This is too expensive."

Compare it to the alternatives: consultant hours, a full-time GRC hire, lost enterprise deals, delayed audits, and internal engineering time spent chasing evidence.

### "Can it make us compliant?"

No product should promise that. Midnight helps build, document, review, and operate the program. Compliance still requires human review, management approval, implementation evidence, and auditor judgment.

## Launch-safe claims

Safe:
- "Helps prepare for audits."
- "Maps documents to framework requirements."
- "Identifies likely gaps and stale governance issues."
- "Generates review-ready policy drafts."
- "Keeps tenant workspaces separate."
- "Creates a traceable compliance workflow."

Unsafe unless proven and legally reviewed:
- "Makes you compliant."
- "Guarantees audit readiness."
- "Certified SOC 2/HIPAA/ISO compliance."
- "Replaces your auditor."
- "Fully automated compliance."
- "No human review needed."

## What to build marketing around first

1. Spreadsheet replacement.
2. Policy folder intelligence.
3. Prioritized remediation.
4. GRC Card / leadership visibility.
5. First compliance operating layer for companies before mature GRC.
6. AI governance as V2 wedge, not V1 overclaim.
