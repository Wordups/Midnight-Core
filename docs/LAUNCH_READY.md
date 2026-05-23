# Midnight — Launch-Ready List

This is what "everything done before launch" means concretely. The list stops growing when this
file is committed. Ideas that arrive during the build go into `POST_LAUNCH_ROADMAP.md`, not here.

Strategy context: [STRATEGY.md](./STRATEGY.md) · Current gap inventory: [MULTI_TENANT_SPEC.md §6](./MULTI_TENANT_SPEC.md)

---

## Foundation

*Multi-tenant correctness, auth, secrets, and payments. Nothing ships until this layer is solid.*

**1. Multi-tenant correctness**

Remove TKO-* filters from `bird_eye/detectors.py` (×5 detectors) and `bird_eye/orchestrator.py`
(×1 documents_reviewed count). Generalize `ORPHAN_CUES` from policy-number-based matching to
document-type + keyword matching. Remove `number == "TKO-POL-004"` hardcode from
`detect_framework_gaps`.

*Definition of done:* Run the TKO corpus through Bird Eye post-fix. Output matches
`files/00_VALIDATION_KEY.md`. Then run a non-TKO document through Bird Eye and confirm all 5
detectors produce findings where applicable. Zero TKO-\* strings remaining in
`bird_eye/detectors.py` or `bird_eye/orchestrator.py` outside of comments.

**2. Organization name fix**

Replace `"organization": "Takeoff LLC"` hardcode at `bird_eye/ingestion.py:359` with
`tenant.name` fetched from the `tenants` table.

*Definition of done:* Ingest a document as a non-TKO tenant. The document row in `policies`
shows the correct org name. TKO documents continue to show "Takeoff LLC."

**3. Self-serve onboarding**

Build the 3-question onboarding wizard at `/onboarding/plan`. Wizard writes `frameworks`,
`primary_objective`, `build_method` to `onboarding_sessions`. Sets `current_step = "complete"`
and `completed = true` on submit. Redirects to `/midnight_dashboard.html`. Dashboard empty state
reads `onboarding_sessions.frameworks` and shows framework-specific suggested first documents.

*Definition of done:* New account created via signup. Wizard appears after signup without
redirection back to signup form. Wizard completes. `onboarding_sessions` row has `completed = true`
and populated JSONB columns. Dashboard shows framework-specific empty-state prompts. Full flow
takes under 10 minutes for a first-time user.

**4. Real auth**

Remove hardcoded `TOOL_PASSWORD` or equivalent backdoor from all production paths.

*Definition of done:* `grep -r "TOOL_PASSWORD" backend/` returns nothing in non-test code. All
authenticated routes require a valid Supabase JWT cookie (`midnight_session`). Dev environment
still works via standard email/password login.

**5. Secrets hygiene**

All production credentials stored in AWS Secrets Manager. Nothing sensitive in environment files
committed to the repo or present in ECS task environment variables as plaintext.

*Definition of done:* `grep -r "sk-ant\|service_role\|postgres://" backend/` returns nothing
outside `.env.example`. ECS task definition references Secrets Manager ARNs, not plaintext values.
Secret rotation documented.

**6. Stripe checkout end-to-end**

Stripe checkout wired at Free, Starter, Professional, Team, and Enterprise tiers. Successful
purchase updates `plan_type` in the `tenants` row. Plan-tier enforcement (`TRIAL_MAX_UPLOADS`,
`TRIAL_MAX_FRAMEWORKS`, user cap) adjusts based on the new `plan_type`. Downgrade and cancellation
handled gracefully.

*Definition of done:* Test card purchase at each paid tier succeeds. `tenants.plan_type` updates
immediately. Trial limits no longer apply after upgrade. Stripe webhook delivers reliably in
production environment.

---

## PM Layer

*The request/task workflow that makes Midnight a program management system, not just an analysis
tool. This is what distinguishes the product from Bird Eye + Trace Agent running standalone.*

**7. Request/task data model and API**

Schema for requests: id, tenant_id, creator_id, assignee_id (SME), title, description, framework,
control_id (optional), due_date, status, created_at, updated_at. API endpoints: create, list,
get, update status, delete.

*Definition of done:* GRC analyst can POST a new request via API. Request persists to DB with
all required fields. GET /requests returns all requests for the tenant scoped by tenant_id.
Status transitions (open → in_review → complete) enforced.

**8. GRC analyst PM workspace**

UI surface in the dashboard for the GRC analyst: task queue (all open requests, filterable by
status and framework), SME directory (list of all SME profiles on the tenant), request creation
form (title, description, framework, assignee, due date).

*Definition of done:* Analyst can create a request, assign it to an SME from the directory, set
a due date, and see it appear in the task queue. Task queue updates in real time or on refresh.
No placeholder or "coming soon" state in any of these UI elements.

**9. SME workspace**

Minimal UI for SMEs — separate from the GRC analyst's full dashboard. SME sees: assigned tasks
(with context: what's needed, why, due date), a response submission form, a mark-complete action.
SME does not need access to Bird Eye, Gap Analysis, or any analytical surface.

*Definition of done:* SME logs in, sees only assigned tasks. Submits a response (text + optional
file attachment). Marks task complete. GRC analyst's task queue reflects the updated status.

**10. Email notifications**

Transactional email: SME receives email when a task is assigned to them (subject, description,
due date, direct link). GRC analyst receives email when an SME marks a task complete.

*Definition of done:* Assign a task to an SME with a real email address. SME receives email within
2 minutes. SME marks task complete. Analyst receives completion notification within 2 minutes.
Emails render correctly in Gmail and Outlook.

**11. Invite flow**

GRC analyst can invite an SME by email address. Invitee receives email with an accept link.
Accept link creates a `profiles` row for the invitee linked to the tenant, with `role = "sme"`.
Invitee can log in and access the SME workspace immediately after accepting.

*Definition of done:* Invite sent, email received, link clicked, account created, SME workspace
accessible without any manual DB intervention. Analyst sees the new SME in their directory.
Invite tokens expire after 7 days.

**12. Pre-built request templates**

At least one template per launch framework (SOC 2, HIPAA, ISO 27001). Templates pre-populate
the request title, description, and relevant control ID. Analyst selects a template from a
dropdown when creating a request.

*Definition of done:* Analyst creates a request from a SOC 2 template. Request fields are
pre-populated with accurate control context. Template content reviewed for accuracy against the
framework control text.

**13. Audit log**

Every significant action appends a row to `activity_log`: request created, request assigned,
SME response submitted, task marked complete, policy uploaded, Bird Eye run completed, GRC Card
distributed. Each row includes: actor (user_id), tenant_id, action type, action detail, timestamp.

*Definition of done:* Run through a full request cycle. `activity_log` table shows a row for
each action with the correct actor, timestamp, and action type. Log is visible in the UI (even
as a simple list) for the GRC analyst.

---

## Empowerment Artifacts

*The GRC Card and distribution infrastructure. This is the retention layer and the marketing
flywheel.*

**14. GRC Card as central dashboard surface**

The GRC Card replaces or overlays the current dashboard as the primary view for GRC analysts.
Content: framework coverage percentages (from `core/gap_engine.py`), open Bird Eye findings count
by severity, pending SME task count, upcoming audit calendar events, recent activity feed,
program health trend.

*Definition of done:* GRC analyst lands on the GRC Card view after login. All metrics reflect
live data for the tenant — no hardcoded values, no empty states for tenants with data. Coverage
percentages match the gap engine output. Findings count matches Bird Eye output.

**15. Excel import**

Upload a CSV or XLSX file from an existing GRC spreadsheet. System maps columns to the request/
policy schema (guided mapping UI with column-to-field assignment). Imported items appear in the
PM workspace as tasks or in the policy library as documents.

*Definition of done:* Upload a real GRC spreadsheet. Map columns. Imported items appear in the
correct surface. No data loss, no silent failures. Error state shown for rows that can't be
parsed.

**16. GRC Card distribution**

Configurable distribution: cadence (weekly on a day, monthly on a day-of-month, custom
cron-style), distro list (one or more email addresses). Each send: HTML email body with GRC Card
content, PDF attachment of the card, Midnight watermark in the footer. Analyst can configure and
send a test to their own email before enabling.

*Definition of done:* Configure a weekly cadence to two email addresses. Wait for the send or
trigger a test send. HTML email received, PDF attachment present, Midnight watermark visible in
footer. GRC Card content matches the live tenant state at time of send.

**17. PDF export**

Any GRC Card, Bird Eye findings report, or gap analysis output can be exported as a PDF. PDF
includes: Midnight header, tenant name, date generated, report content, Midnight footer watermark.

*Definition of done:* Click "Export PDF" on the GRC Card, on a Bird Eye findings view, and on
a gap analysis view. All three produce a downloadable PDF. Content renders correctly in the PDF
(no truncation, no broken tables). PDF is print-ready.

---

## Polish

*The product must not read as AI-generated or unfinished. Compliance buyers are detail-oriented.
A single "coming soon" button or an AI-flavored visual signals "not ready."*

**18. Dashboard visual polish**

A full design pass on the dashboard — not incremental fixes, a separate design workflow:
references → mocks → approval → implementation. The current dashboard reads AI-generated.
The launched product cannot.

*Definition of done:* Design spec completed and approved. Implementation matches approved mocks.
No element reads AI-generated or placeholder. Reviewed by at least one person outside the build
process before signing off.

**19. Status page**

A public status page that reflects live service health (API, database, Bird Eye, email
delivery). Backs the "always online" principle with a verifiable artifact. URL documented in
customer-facing docs.

*Definition of done:* Status page is publicly accessible. Shows current status and incident
history. Notifies subscribers on incidents. URL is linked from the product footer and from
customer-facing documentation.

**20. Customer-facing documentation**

At minimum, written documentation covering: getting started (signup through first finding),
uploading documents to Bird Eye, running a Bird Eye analysis, creating a policy with Trace Agent,
inviting a team member. Hosted and accessible from within the product.

*Definition of done:* All five topics documented. A new user with no prior knowledge can
complete each flow using only the documentation. No broken links. Documentation reflects the
current product, not a planned state.

**21. Founder origin story landing page**

Landing page copy reflects: the Excel-spreadsheet buyer as the primary persona, the founder's
personal witness as the authenticity anchor, the practitioner's pain as the problem being solved.
No "AI-powered" language, no competitor names, no generic SaaS copy.

*Definition of done:* Landing page copy reviewed against the positioning in `STRATEGY.md §VIII`.
Copy passes the test: does a GRC analyst landing on this page recognize themselves in the
problem description? Does the copy lead with practitioner authenticity, not product features?

---

## Launch Frameworks

*Deep at launch means: framework mapping, gap analysis, and policy generation all produce
accurate, useful output. Not partial coverage. Not placeholder controls.*

**22. SOC 2 Type II**

Full framework coverage for SOC 2 Trust Service Criteria (Security, Availability, Confidentiality,
Processing Integrity, Privacy — at minimum Security as required, others as applicable to tenant).

*Definition of done:* Upload a representative SOC 2 policy set. `core/framework_mapper.py`
produces accurate control-to-document mappings. `core/gap_engine.py` surfaces real gaps against
the SOC 2 control library in `frameworks/soc2.json`. Trace Agent generates a policy document
that addresses a real SOC 2 control gap. Founder reviews output against known SOC 2 audit
evidence requirements.

**23. HIPAA**

Full framework coverage for HIPAA Administrative, Physical, and Technical Safeguards.

*Definition of done:* Same standard as SOC 2. Upload a representative HIPAA policy set. Mapping,
gap analysis, and generation all produce accurate output. Founder reviews against known HIPAA
audit evidence requirements.

**24. ISO 27001**

Full framework coverage for ISO 27001:2022 Annex A controls.

*Definition of done:* Same standard as SOC 2 and HIPAA. ISO 27001:2022 control library
confirmed current in `frameworks/` directory. Mapping, gap analysis, and generation produce
accurate output.

---

*Post-launch additions: [POST_LAUNCH_ROADMAP.md](./POST_LAUNCH_ROADMAP.md)*
