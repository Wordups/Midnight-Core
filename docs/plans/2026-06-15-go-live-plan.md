# Midnight Go-Live Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Move Midnight from current internal/beta state to a defensible public go-live where a new buyer can sign up, onboard, upload documents, get tenant-scoped results, upgrade through Stripe, and receive support without founder-only manual intervention.

**Architecture:** Treat go-live as a gate sequence, not a feature wishlist. Foundation gates must pass before polish gates: deploy provenance, auth, tenant isolation, onboarding, billing, webhook, parser/Bird Eye correctness, migration/secrets hygiene, observability, and final buyer-flow rehearsal. Control-plane green is not enough; every gate ends with external behavior proof from the live app.

**Tech Stack:** FastAPI, Supabase, Stripe, ECS/ECR, Docker, static frontend, pytest, AWS CLI, curl, GitHub, Render/ECS deployment context.

---

## Current State Snapshot — 2026-06-15

Known good:
- Repo: `C:\dev\midnight-core` / `/c/dev/midnight-core`
- Branch: `master`
- Latest go-live-adjacent commit: `a655a13 fix(onboarding): serve plan page after signup`
- ECS service: `default/midnightcore-78b3`
- Latest deployed task definition after onboarding fix: `default-midnightcore-78b3:25`
- Live health: `/health` returns `200`; `/ready` returns `200`
- Live onboarding static page exists: `/onboarding_plan.html` returns `200`
- Logged-out `/onboarding/plan` returns `307` as expected
- Local narrow regression set passed: onboarding, Stripe router, beta access

Known not done:
- `/onboarding/plan` is currently a holding onboarding page, not the full 3-question wizard required by `docs/LAUNCH_READY.md`.
- Stripe checkout is route-live but not fully proven with authenticated tenant flow.
- Stripe webhook is explicitly a stub in `backend/api/stripe_router.py`.
- Billing tiers in code are `starter`, `growth`, `enterprise`; launch doc says Free, Starter, Professional, Team, Enterprise. Tier taxonomy needs one decision.
- Rev 20 parser fixes remain open: SEC-P022 valid `.docx` extraction and JAMF sections/indexing.
- Bird Eye non-TKO tenant proof is still pending.
- Migration drift and Supabase service-role rotation confirmation are pending.
- `deploy.sh` is not trusted yet; recent deploys were manual.
- Dashboard visual polish is below launch bar.

---

## Non-Negotiable Go-Live Standard

Midnight is go-live only when this buyer path works live, in production, with a fresh account:

1. Visitor signs up with email/password.
2. App creates tenant, owner profile, and trial entitlement.
3. Visitor lands in onboarding, not the raw dashboard.
4. Visitor completes onboarding choices.
5. Dashboard reflects onboarding choices and shows useful first actions.
6. Visitor uploads at least one valid docx/pdf policy pack.
7. Parser extracts meaningful sections and increments indexed-doc counters.
8. Bird Eye produces tenant-scoped findings without TKO-only assumptions.
9. Gap/dashboard results are scoped to that tenant only.
10. Visitor upgrades through Stripe Checkout.
11. Stripe webhook updates `tenants.plan_type` and limits unlock.
12. Logs/metrics show no secret leakage, no 500s, and no cross-tenant data exposure.

If any of those fail, it is not public-launch ready.

---

## Phase 0: Freeze Scope and Create Launch Branch

**Objective:** Stop scope creep and isolate go-live work.

**Files:**
- Modify: `docs/LAUNCH_READY.md` if launch scope changes are required
- Create: `docs/plans/2026-06-15-go-live-plan.md`

**Steps:**
1. Confirm this plan is the active launch plan.
2. Create branch:
   ```bash
   git checkout master
   git pull origin master
   git checkout -b launch/go-live-hardening
   ```
3. No new feature outside this plan unless it directly unblocks the buyer path.
4. Put all nice-to-have ideas into `docs/POST_LAUNCH_ROADMAP.md`.
5. Commit plan:
   ```bash
   git add docs/plans/2026-06-15-go-live-plan.md
   git commit -m "docs: add go-live implementation plan"
   ```

**Exit gate:** Branch exists, plan committed, launch scope frozen.

---

## Phase 1: Billing End-to-End

### Task 1.1: Audit Current Billing Implementation

**Objective:** Get exact current billing behavior before changing code.

**Files:**
- Read: `backend/api/stripe_router.py`
- Read: `tests/test_stripe_router.py`
- Read: `backend/api/main.py`

**Commands:**
```bash
venv/Scripts/python.exe -m pytest tests/test_stripe_router.py -q
grep -R "billing_router\|billing_webhook_router" -n backend/api
```

**Expected:** Tests pass or fail with clear implementation gaps. Route inclusion is visible in `backend/api/main.py`.

**Exit gate:** Written notes identify checkout route behavior, webhook behavior, tier names, and required DB update path.

### Task 1.2: Decide Tier Taxonomy

**Objective:** Align code, Stripe prices, pricing UI, and launch docs.

**Decision needed:** Use one of these:
- Option A: `free`, `starter`, `professional`, `team`, `enterprise`
- Option B: `trial`, `starter`, `growth`, `enterprise`

**Recommended:** Option A for public launch, because `LAUNCH_READY.md` already names those tiers and buyer expectations are clearer.

**Files:**
- Modify: `backend/api/stripe_router.py`
- Modify: pricing/signup frontend files that call checkout
- Modify: tests in `tests/test_stripe_router.py`
- Modify: `.env.example` if present

**Exit gate:** One tier vocabulary exists everywhere. No `growth`/`professional` mismatch.

### Task 1.3: Add Checkout Metadata

**Objective:** Ensure checkout sessions can be mapped back to tenant/user/plan.

**Implementation requirement:** `stripe.checkout.Session.create()` must include:
- `client_reference_id`: tenant id
- `metadata.tenant_id`
- `metadata.user_id`
- `metadata.plan_type`
- `customer_email` when available

**Files:**
- Modify: `backend/api/stripe_router.py`
- Test: `tests/test_stripe_router.py`

**Test first:**
```bash
venv/Scripts/python.exe -m pytest tests/test_stripe_router.py::test_checkout_includes_tenant_metadata -q
```
Expected initial failure until implemented.

**Exit gate:** Mocked Stripe call shows metadata includes tenant id, user id, and plan type.

### Task 1.4: Implement Stripe Webhook Verification

**Objective:** Replace the stub webhook with real signature validation.

**Files:**
- Modify: `backend/api/stripe_router.py`
- Test: `tests/test_stripe_router.py`

**Required behavior:**
- Missing `STRIPE_WEBHOOK_SECRET` returns `503` in non-dev or logs clear config failure.
- Missing/invalid `stripe-signature` returns `400`.
- Valid event returns `200`.
- Unknown event types return `200` without side effects.

**Commands:**
```bash
venv/Scripts/python.exe -m pytest tests/test_stripe_router.py -q
```

**Exit gate:** Invalid webhook signatures fail closed. Stub is gone.

### Task 1.5: Implement Plan Activation on `checkout.session.completed`

**Objective:** Successful payment updates the tenant plan.

**Files:**
- Modify: `backend/api/stripe_router.py`
- Possibly modify: `backend/storage/file_store.py` for a reusable `update_tenant_plan(...)`
- Test: `tests/test_stripe_router.py`

**Required DB update:**
- Update `tenants.plan_type` to paid plan from event metadata.
- Persist Stripe customer/subscription ids if matching columns exist; if not, create migration in Phase 5.
- Add activity/audit log row if existing activity helper supports it.

**Exit gate:** Unit test proves webhook updates tenant plan using mocked Supabase/admin client.

### Task 1.6: Authenticated Live Checkout Smoke

**Objective:** Prove a real logged-in trial user can generate a Stripe Checkout URL.

**Manual steps:**
1. Log into live app as test account.
2. Trigger upgrade from UI or call API with session cookie.
3. Verify response `200` and `checkout_url` starts with Stripe Checkout URL.
4. Do not print session cookie or token.

**Command shape if using browser/devtools cookie manually:**
```bash
curl -sS -X POST https://app.midnightgrc.com/billing/checkout \
  -H 'content-type: application/json' \
  -H 'cookie: midnight_session=[REDACTED]' \
  -d '{"tier":"starter"}'
```

**Exit gate:** Live authenticated checkout returns real checkout URL.

---

## Phase 2: Onboarding Completion, Not Placeholder

### Task 2.1: Inspect Existing Onboarding Schema

**Objective:** Determine whether `onboarding_sessions` exists and what columns are live.

**Files:**
- Search: `supabase/migrations/`
- Search: `backend/storage/file_store.py`
- Search: `backend/api/main.py`

**Commands:**
```bash
grep -R "onboarding_sessions\|primary_objective\|build_method" -n supabase backend tests
```

**Exit gate:** Confirm whether schema exists or migration is needed.

### Task 2.2: Add Onboarding API

**Objective:** Persist the 3-question wizard choices.

**Routes:**
- `GET /onboarding/session` returns current session state.
- `POST /onboarding/session` validates and writes:
  - `frameworks`
  - `primary_objective`
  - `build_method`
  - `current_step = "complete"`
  - `completed = true`

**Files:**
- Modify: `backend/api/main.py` or create `backend/api/onboarding.py`
- Modify: `backend/storage/file_store.py`
- Test: `tests/test_onboarding_flow.py`

**Exit gate:** Tests prove authenticated user can save onboarding and unauthenticated user cannot.

### Task 2.3: Replace Holding Page with Real Wizard

**Objective:** Turn `frontend/onboarding_plan.html` into the launch onboarding flow.

**Files:**
- Modify: `frontend/onboarding_plan.html`

**Questions:**
1. Frameworks: SOC 2, HIPAA, ISO 27001, NIST CSF, AI Governance later disabled/post-launch unless ready.
2. Primary objective: audit prep, policy cleanup, evidence organization, AI governance readiness, general GRC program build.
3. Build method: upload existing docs, start from templates, guided review.

**Exit gate:** New signup lands on wizard, submits, then redirects to dashboard.

### Task 2.4: Dashboard Empty State Uses Onboarding Choices

**Objective:** Make the dashboard feel intentional immediately after signup.

**Files:**
- Modify: `frontend/midnight_dashboard.html` or dashboard JS files
- Modify: `backend/api/dashboard.py` if dashboard API needs onboarding data
- Test: Add/extend dashboard test if available

**Exit gate:** Fresh tenant with onboarding choices sees framework-specific suggested first docs/actions.

### Task 2.5: Live Fresh Signup Rehearsal

**Objective:** Prove the buyer path from signup through onboarding.

**Manual test:**
1. Create fresh email test account.
2. Confirm no raw dashboard drop-in.
3. Complete wizard in under 10 minutes.
4. Confirm `onboarding_sessions.completed = true` without printing secrets.
5. Confirm dashboard empty state matches selections.

**Exit gate:** Fresh-account onboarding works live end-to-end.

---

## Phase 3: Parser and Bird Eye Correctness

### Task 3.1: Reproduce SEC-P022 `.docx` Extraction Bug

**Objective:** Capture failing test for valid `.docx` showing “no extractable text.”

**Files:**
- Search/modify: parser/extractor modules under `backend/core/`
- Test: `tests/test_json_parser.py` or new parser extraction test

**Exit gate:** Failing test reproduces SEC-P022 with a sanitized fixture.

### Task 3.2: Fix `.docx` Fallback Extraction

**Objective:** Extract text from valid docx reliably.

**Likely areas:**
- `backend/core/extractor.py` if present
- docx/docx2txt usage
- fallback behavior for empty paragraphs/tables

**Exit gate:** SEC-P022 fixture produces non-empty text and expected section candidates.

### Task 3.3: Reproduce JAMF Sections/Indexing Bug

**Objective:** Capture bug where JAMF doc parses but `sections=0` and `docs_indexed` not incrementing.

**Files:**
- `backend/bird_eye/ingestion.py`
- `backend/bird_eye/orchestrator.py`
- `backend/storage/file_store.py`
- `tests/test_bird_eye_upload.py`

**Exit gate:** Test fails before fix and proves missing sections/index counter.

### Task 3.4: Fix JAMF Section and Index Accounting

**Objective:** Ensure valid docs create sections and increment indexed doc metrics.

**Exit gate:** JAMF fixture creates sections > 0 and increments `docs_indexed` exactly once.

### Task 3.5: Non-TKO Bird Eye Tenant Proof

**Objective:** Prove Bird Eye no longer depends on TKO policy IDs or tenant names.

**Commands:**
```bash
grep -R "TKO-\|TKO-POL" -n backend/bird_eye tests
venv/Scripts/python.exe -m pytest tests/test_bird_eye_upload.py tests/test_tenant_isolation.py -q
```

**Manual proof:** Upload a non-TKO doc under a non-TKO tenant and confirm applicable detectors produce findings.

**Exit gate:** Non-TKO tenant gets real Bird Eye findings; no cross-tenant contamination.

---

## Phase 4: Tenant Isolation and Auth Hardening

### Task 4.1: Kill Production Backdoors

**Objective:** Remove hardcoded tool passwords and production bypasses.

**Commands:**
```bash
grep -R "TOOL_PASSWORD\|backdoor\|dev bypass\|bypass" -n backend frontend tests
```

**Exit gate:** No production path uses a hardcoded password or auth bypass.

### Task 4.2: Tenant Isolation Test Sweep

**Objective:** Prove tenant scoping across critical APIs.

**Files:**
- Test: `tests/test_tenant_isolation.py`
- Critical APIs: documents, Bird Eye, dashboard, billing, onboarding, requests if present

**Exit gate:** Tenant A cannot see Tenant B data through list, get, dashboard, or analysis endpoints.

### Task 4.3: Plan Limit Enforcement

**Objective:** Ensure trial/paid limits match plan after webhook upgrade.

**Files:**
- Search for `TRIAL_MAX_UPLOADS`, `TRIAL_MAX_FRAMEWORKS`, plan enforcement paths
- Add tests around upload/framework/user limits

**Exit gate:** Trial limits apply before upgrade and paid limits apply after webhook update.

---

## Phase 5: Database, Migrations, and Secrets

### Task 5.1: Migration Drift Audit

**Objective:** Compare live Supabase migrations with repo migrations before applying anything.

**Rules:**
- Do not print connection strings or service-role keys.
- Do not apply migrations until drift is understood.

**Commands shape:**
```bash
# Use existing Supabase CLI/project tooling if configured.
# Otherwise query schema_migrations through a safe script that redacts credentials.
```

**Exit gate:** Written table of applied/missing/out-of-order migrations.

### Task 5.2: Add Missing Billing/Onboarding Columns

**Objective:** Add only required schema for go-live.

**Potential columns/tables:**
- `onboarding_sessions` if absent
- Stripe customer/subscription ids if absent
- subscription status/current period if needed for cancellation/downgrade

**Files:**
- Create: `supabase/migrations/YYYYMMDDHHMMSS_go_live_billing_onboarding.sql`

**Exit gate:** Migration applies locally/staging and is represented in repo.

### Task 5.3: Secrets Hygiene Audit

**Objective:** Confirm no secrets in repo and prod task definition uses managed secrets where possible.

**Commands:**
```bash
git status --short
git grep -n "sk-ant\|service_role\|postgres://\|STRIPE_SECRET_KEY\|STRIPE_WEBHOOK_SECRET" -- ':!*.example' ':!docs/plans/2026-06-15-go-live-plan.md'
```

**ECS check:** Inspect task definition without printing values. Report only whether values are plaintext env vars or Secrets Manager refs.

**Exit gate:** No committed secrets; prod secret handling documented; old Supabase service-role key rotation confirmed.

---

## Phase 6: Deploy Script Hardening

### Task 6.1: Rewrite `deploy.sh` Around Proven Manual Flow

**Objective:** Stop relying on risky manual deploys.

**Files:**
- Modify: `deploy.sh`

**Required behavior:**
- Fail fast: `set -euo pipefail`
- Require clean git tree or explicit override.
- Build with unique tag.
- Support `--no-cache`.
- Log into ECR.
- Build image.
- Verify image content with explicit grep/check command.
- Push only after verification.
- Register ECS task definition using tempfile outside repo root.
- Never write secret-bearing task definitions to repo root.
- Update ECS service.
- Wait for stable.
- Probe `/health`, `/ready`, and changed route.
- Fail if live route proof fails.

**Exit gate:** Dry-run or staging deploy proves script works without creating tracked/untracked secret artifacts.

### Task 6.2: Add Deploy Verification Checklist

**Objective:** Make future deploys repeatable.

**Files:**
- Create: `docs/DEPLOY_CHECKLIST.md`

**Exit gate:** Checklist includes image tag, image proof, ECS task def, live probes, rollback command.

---

## Phase 7: Observability, Error Handling, and Support Readiness

### Task 7.1: Request/Error Log Review

**Objective:** Make production failures debuggable without leaking secrets.

**Required fields:**
- request id
- route
- method
- status
- latency
- tenant id where available
- user id where available

**Exit gate:** 4xx/5xx logs are actionable and redacted.

### Task 7.2: Fix Watchdog Noise or Route It Properly

**Objective:** Stop `/agents/status` 404 spam if it pollutes logs.

**Options:**
- Add real lightweight `/agents/status` endpoint.
- Update `midnightcore-listener-watchdog` to hit `/health` or `/ready`.

**Exit gate:** No recurring meaningless 404s in production logs.

### Task 7.3: Create Founder Support Runbook

**Objective:** Know what to do when first users hit issues.

**Files:**
- Create: `docs/RUNBOOK_GO_LIVE.md`

**Must include:**
- How to check ECS state
- How to check latest task image
- How to probe auth/billing/onboarding
- How to inspect Stripe webhook failures
- How to rollback ECS task definition
- What never to paste into AI chat

**Exit gate:** Runbook exists and can be followed in 10 minutes under stress.

---

## Phase 8: Product Polish Gate

### Task 8.1: Remove Placeholder/AI-Generated Surfaces

**Objective:** Prevent obvious buyer confidence killers.

**Searches:**
```bash
grep -R "coming soon\|placeholder\|lorem\|TODO\|demo" -n frontend backend docs
```

**Exit gate:** No visible placeholder UI in public buyer path.

### Task 8.2: Dashboard Design Pass Minimum

**Objective:** Improve first impression enough for public launch, even if full redesign is post-launch.

**Scope:**
- Fresh tenant empty state
- Upload call-to-action
- Billing/upgrade call-to-action
- Onboarding completion confirmation
- No confusing dead buttons

**Exit gate:** Founder review says dashboard no longer screams AI-generated for the initial trial path.

### Task 8.3: Copy and Legal Guardrails

**Objective:** Avoid overclaiming compliance.

**Searches:**
```bash
grep -R "compliant\|certified\|guarantee\|audit-ready" -n frontend docs backend
```

**Required language:** Use “draft,” “prepared,” “readiness,” “gap analysis,” not “you are compliant.”

**Exit gate:** No customer-facing overclaiming.

---

## Phase 9: Full Production Dress Rehearsal

### Task 9.1: Fresh Account Buyer Journey

**Objective:** Run the exact path a real buyer will run.

**Use:** a fresh test email, not an existing founder/admin account.

**Script:**
1. Visit live site.
2. Sign up.
3. Confirm onboarding appears.
4. Complete onboarding.
5. Land on dashboard.
6. Upload sample policy docx.
7. Confirm sections/indexing.
8. Run Bird Eye.
9. Confirm findings.
10. Run gap/dashboard view.
11. Upgrade via Stripe test card.
12. Confirm webhook updates plan.
13. Confirm paid limits unlock.
14. Log out/log in again.
15. Confirm state persists.

**Exit gate:** Entire flow completes without manual DB edits.

### Task 9.2: Negative Path Rehearsal

**Objective:** Ensure failures are safe and understandable.

**Test:**
- Invalid login
- Expired/invalid session
- Invalid upload type
- Stripe checkout cancel
- Invalid webhook signature
- Trial limit exceeded
- Tenant A attempting Tenant B resource id

**Exit gate:** Failures are clear, safe, and logged; no 500s for expected user errors.

### Task 9.3: Rollback Rehearsal

**Objective:** Prove rollback before launch day.

**Commands shape:**
```bash
aws ecs update-service --cluster default --service midnightcore-78b3 --task-definition default-midnightcore-78b3:<previous-good-revision> --region us-east-1
aws ecs wait services-stable --cluster default --services midnightcore-78b3 --region us-east-1
curl -sS https://app.midnightgrc.com/health
```

**Exit gate:** Rollback procedure documented and tested or explicitly accepted as untested risk.

---

## Phase 10: Launch Decision

### Launch Readiness Checklist

Public go-live is approved only when all are true:

- [ ] Fresh signup lands in real onboarding wizard.
- [ ] Onboarding persists and dashboard reflects it.
- [ ] Authenticated checkout creates Stripe Checkout session.
- [ ] Stripe webhook validates signatures and updates plan.
- [ ] Trial/paid plan limits enforce correctly.
- [ ] SEC-P022 `.docx` parser bug fixed.
- [ ] JAMF sections/indexing bug fixed.
- [ ] Non-TKO Bird Eye tenant verified live.
- [ ] Tenant isolation tests pass.
- [ ] Migration drift resolved or consciously accepted.
- [ ] Supabase service-role rotation confirmed.
- [ ] No secret-bearing task definition files in repo.
- [ ] Deploy script or documented manual deploy flow is reliable.
- [ ] Live `/health` and `/ready` green.
- [ ] Production logs show no recurring unexplained 500s/404 spam.
- [ ] Dashboard public buyer path has no placeholder/dead UI.
- [ ] Support/rollback runbook exists.
- [ ] Full production dress rehearsal passes without manual DB edits.

### No-Go Conditions

Any one of these blocks public launch:

- Cross-tenant data exposure or unscoped query.
- Stripe webhook cannot update tenant plan.
- Fresh signup skips onboarding or hits broken onboarding.
- Parser cannot handle valid uploaded `.docx` documents.
- Bird Eye only works for TKO-shaped docs.
- Secret/key appears in repo, logs, task definition artifact, or AI transcript.
- Deploy path cannot prove exact intended code is live.

---

## Recommended Execution Order

Run in this exact order:

1. Billing checkout + webhook.
2. Real onboarding wizard + dashboard empty state.
3. Parser SEC-P022/JAMF fixes.
4. Bird Eye non-TKO proof + tenant isolation sweep.
5. Migration/secrets audit.
6. Deploy script hardening.
7. Observability/runbook.
8. Product polish.
9. Full production dress rehearsal.
10. Launch/no-launch call.

Reason: billing/onboarding are buyer-path blockers; parser/Bird Eye are product-value blockers; migrations/secrets/deploy are operational risk blockers; polish comes after the flow is real.

---

## First 10 Concrete Tasks to Start Now

1. Run `venv/Scripts/python.exe -m pytest tests/test_stripe_router.py -q`.
2. Replace webhook stub in `backend/api/stripe_router.py` with signature validation tests.
3. Add checkout metadata tests and implementation.
4. Decide tier taxonomy and align env names/tests/UI.
5. Implement `checkout.session.completed` tenant plan update.
6. Live authenticated checkout smoke with redacted session cookie.
7. Inspect/create onboarding session schema.
8. Add `GET/POST /onboarding/session` tests and implementation.
9. Replace holding page with real 3-question wizard.
10. Run fresh-signup live rehearsal.

Do not move to parser/Bird Eye until checkout + webhook + onboarding pass in production.
