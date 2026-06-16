# Midnight Go-Live Security Measures and Protocol

**Purpose:** Define the security controls that must be implemented, verified, and operated before Midnight is exposed to public self-serve users.

**Scope:** Production app, Supabase, ECS/ECR, Stripe billing, onboarding, document ingestion, Bird Eye analysis, logs, deploy workflow, AI-agent usage, and founder/operator procedures.

**Rule:** No control is considered done until it has a live verification step. “Looks configured” is not enough.

---

## 1. Launch Security Standard

Midnight can go live only when these are true:

1. Every authenticated request is tied to a valid Supabase JWT session cookie.
2. Every tenant-owned query is scoped by `tenant_id`.
3. Tenant A cannot read, infer, modify, bill, or analyze Tenant B data.
4. Production secrets are not committed, logged, pasted into AI chat, or written into repo-root artifacts.
5. Stripe webhooks are signature-validated and fail closed.
6. Upload parsing and Bird Eye analysis cannot cross tenant boundaries.
7. Deployed image provenance is proven before and after deploy.
8. Logs contain enough context for incident response but no credentials/tokens/customer secrets.
9. A rollback path is tested or explicitly accepted as risk.
10. A fresh-account production dress rehearsal passes without manual DB edits.

---

## 2. Security Gates Before Public Launch

### Gate A — Auth and Session Security

**Measures:**
- Require `midnight_session` Supabase JWT cookie for every protected route.
- Reject missing, expired, invalid, or mismatched sessions.
- Do not accept user id, tenant id, role, or plan from client-controlled payloads.
- Server derives tenant/user/role from verified token and profile lookup.
- Remove all production bypasses, demo passwords, `TOOL_PASSWORD`, and “dev-only” shortcuts from live paths.

**Verification:**
```bash
grep -R "TOOL_PASSWORD\|backdoor\|bypass\|dev only\|mock user" -n backend frontend tests
venv/Scripts/python.exe -m pytest tests/test_beta_access.py tests/test_onboarding_flow.py -q
```

**Live proof:**
- Logged-out `/onboarding/plan` redirects to signup.
- Logged-out `/billing/checkout` returns `401`.
- Authenticated test user can access only their tenant context.

**No-go:** Any protected route works without a valid session.

---

### Gate B — Tenant Isolation / Multi-Tenant Hardening

**Measures:**
- Every table holding customer data has `tenant_id` or an equivalent tenant-owned relationship.
- Every select/update/delete path includes tenant scoping.
- Supabase RLS must be enabled on tenant-owned tables where direct client access is possible.
- Bird Eye detectors must not filter by `TKO-*`, demo IDs, hardcoded org names, or demo policy numbers.
- Ingestion must use actual tenant/org metadata, not Takeoff/TKO defaults.

**Verification:**
```bash
grep -R "TKO-\|TKO-POL\|Takeoff LLC" -n backend/bird_eye backend/storage backend/api tests
grep -R "\.from(\|select(\|update(\|delete(" -n backend --include="*.py"
venv/Scripts/python.exe -m pytest tests/test_tenant_isolation.py tests/test_bird_eye_upload.py -q
```

**Live proof:**
- Create Tenant A and Tenant B.
- Upload a doc to Tenant A.
- Tenant B sees zero Tenant A docs/findings/dashboard data.
- Non-TKO tenant gets Bird Eye findings where applicable.

**No-go:** Any unscoped query, hardcoded demo tenant filter, or cross-tenant read/write.

---

### Gate C — Secrets Handling

**Measures:**
- No secrets in Git history going forward.
- No task definition JSON with plaintext secrets in repo root.
- `.gitignore` must block task definition artifacts.
- Production secrets live in AWS/Supabase/Stripe secret stores or ECS secrets references where possible.
- AI chat is treated as tier-1.5 secret exposure: never paste keys, cookies, JWTs, Stripe secrets, Supabase service-role keys, DB URLs, or ECS env var dumps.
- Any suspected pasted secret gets rotated.

**Verification:**
```bash
git status --short
git grep -n "sk-ant\|service_role\|postgres://\|STRIPE_SECRET_KEY\|STRIPE_WEBHOOK_SECRET\|SUPABASE_SERVICE_ROLE_KEY" -- ':!*.example' ':!docs/SECURITY_PROTOCOL_GO_LIVE.md'
git check-ignore task-def.json midnight_task_def.json
```

**ECS verification protocol:**
- Inspect whether secrets are plaintext env vars or secrets refs.
- Report only key names and storage mode.
- Never print values.

**No-go:** Secret value in repo, logs, screenshots, AI transcript, or task definition artifact.

---

### Gate D — Stripe / Billing Security

**Measures:**
- Checkout route requires authenticated tenant/user.
- Checkout request accepts only allowed tiers.
- Server resolves price IDs from env; client never supplies price IDs.
- Checkout session metadata includes tenant id, user id, and plan type.
- Webhook verifies `stripe-signature` using `STRIPE_WEBHOOK_SECRET`.
- Invalid signature returns `400` and performs no side effect.
- `checkout.session.completed` updates only the tenant from trusted Stripe metadata.
- Webhook handler is idempotent or safe on duplicate events.

**Verification:**
```bash
venv/Scripts/python.exe -m pytest tests/test_stripe_router.py -q
```

**Live proof:**
- Authenticated trial user creates checkout URL.
- Stripe test card completes payment.
- Webhook updates `tenants.plan_type`.
- Trial limits unlock.
- Invalid webhook signature is rejected.

**No-go:** Stub webhook, unsigned webhook acceptance, client-supplied price ID, or manual DB update required after payment.

---

### Gate E — Upload / Parser / Document Intelligence Security

**Measures:**
- Enforce upload size/type limits.
- Reject unsupported file types with clear 4xx error.
- Do not execute uploaded content.
- Extract text only through controlled libraries.
- Store documents under tenant-scoped paths/rows.
- Parser failures should not leak stack traces or raw internals to users.
- Bird Eye analysis must run only on the requesting tenant’s documents.

**Verification:**
```bash
venv/Scripts/python.exe -m pytest tests/test_bird_eye_upload.py tests/test_json_parser.py -q
```

**Manual proof:**
- Upload valid `.docx` and confirm extractable sections.
- Upload invalid file type and confirm safe rejection.
- Upload same named docs across two tenants and confirm separation.

**No-go:** Valid `.docx` cannot parse, invalid uploads cause 500s, or analysis reads another tenant’s docs.

---

### Gate F — Database and Migration Safety

**Measures:**
- Run migration drift audit before applying prod migrations.
- Back up or snapshot before high-risk schema changes.
- Migrations must be idempotent where practical.
- Never run blind prod migrations from memory.
- Service-role use is server-side only.

**Verification:**
- Compare live migration table with `supabase/migrations/`.
- Document missing/applied/out-of-order migrations.
- Apply only reviewed migrations.

**No-go:** Unknown drift with pending production schema changes.

---

### Gate G — Deployment Security and Provenance

**Measures:**
- Build with unique immutable tag.
- Use `--no-cache` for recovery/security-sensitive deploys.
- Prove image contains intended code before push when environment permits.
- Push only verified image.
- Register ECS task definition through temp file outside repo root.
- Do not leave generated task definitions in repo root.
- Wait for ECS stability.
- Verify live route behavior after deploy.

**Verification:**
```bash
git status --short
docker build --no-cache -t "$IMAGE" .
# image-content grep/check when permitted
aws ecs wait services-stable --cluster default --services midnightcore-78b3 --region us-east-1
curl -sS https://app.midnightgrc.com/health
curl -sS https://app.midnightgrc.com/ready
```

**Live proof:**
- ECS running task definition uses intended image tag.
- Changed route exhibits expected behavior.

**No-go:** Deploy cannot prove intended code is live.

---

### Gate H — Logging, Monitoring, and Privacy

**Measures:**
- Logs include request id, route, method, status, latency, user id, tenant id where available.
- Logs do not include JWTs, cookies, API keys, DB URLs, service-role keys, uploaded document text, or Stripe secrets.
- Expected user errors return 4xx, not 500.
- Watchdog noise is fixed or routed to a valid health endpoint.
- Error alerts have enough context to triage.

**Verification:**
- Review recent ECS/app logs after dress rehearsal.
- Confirm no token-like values are emitted.
- Confirm no recurring unexplained 500s or `/agents/status` 404 spam.

**No-go:** Secret leakage in logs or recurring unexplained production errors.

---

## 3. Operator Protocols

### Protocol 1 — Handling Secrets

1. Never paste raw secrets into AI chat, GitHub issues, Slack, docs, or terminal transcripts intended for sharing.
2. If a key appears in any of those places, treat it as compromised.
3. Rotate immediately.
4. Deploy rotated value.
5. Verify old key fails.
6. Document only: key name, rotation time, verification status. Never document value.

**Redaction standard:** Replace values with `[REDACTED]`.

### Protocol 2 — Production Deploy

1. Confirm clean git tree.
2. Run relevant tests.
3. Build unique image tag.
4. Verify image content if permitted.
5. Push image.
6. Register ECS task definition without writing secrets to repo root.
7. Update service.
8. Wait stable.
9. Probe health/readiness.
10. Probe changed route.
11. Record image tag/task revision/status.
12. Roll back immediately if live route proof fails.

### Protocol 3 — Incident Response

Severity levels:

**SEV-1:** data exposure, auth bypass, secret leak, billing corruption, destructive data loss.
- Freeze deploys.
- Preserve logs.
- Rotate implicated secrets.
- Disable affected route if needed.
- Patch and deploy.
- Verify containment.
- Write incident record.

**SEV-2:** outage, broken signup/onboarding/billing, parser failure affecting all users.
- Triage logs.
- Roll back if recent deploy caused it.
- Patch with regression test.
- Verify live behavior.

**SEV-3:** degraded UX, isolated 4xx, cosmetic bug, noisy logs.
- File issue.
- Batch into next hardening pass unless it affects buyer path.

### Protocol 4 — AI Assistant / Agent Use

Allowed:
- Code review
- Test writing
- Architecture analysis
- Redacted log review
- Redacted config shape review

Not allowed:
- Raw secrets
- JWT/session cookies
- Supabase service-role keys
- Stripe secret/webhook keys
- AWS credentials
- Customer documents unless explicitly sanitized
- Full ECS task env dumps

If needed, provide structure only:
```text
STRIPE_SECRET_KEY=[REDACTED]
SUPABASE_SERVICE_ROLE_KEY=[REDACTED]
DATABASE_URL=[REDACTED]
```

### Protocol 5 — Customer Data Handling

1. Use test/sanitized documents for development.
2. Do not commit customer uploads.
3. Do not paste customer document contents into AI chat without explicit sanitization and approval.
4. Keep tenant data scoped in storage paths and DB rows.
5. Delete test accounts/data after launch rehearsal unless needed for audit evidence.

---

## 4. Security Test Commands

Run before launch candidate deploy:

```bash
venv/Scripts/python.exe -m pytest tests/test_beta_access.py tests/test_onboarding_flow.py tests/test_stripe_router.py tests/test_tenant_isolation.py tests/test_bird_eye_upload.py -q
```

Run code searches:

```bash
git grep -n "TOOL_PASSWORD\|backdoor\|bypass" -- backend frontend tests
git grep -n "TKO-\|TKO-POL\|Takeoff LLC" -- backend/bird_eye backend/storage backend/api tests
git grep -n "sk-ant\|service_role\|postgres://\|STRIPE_SECRET_KEY\|STRIPE_WEBHOOK_SECRET\|SUPABASE_SERVICE_ROLE_KEY" -- ':!*.example' ':!docs/SECURITY_PROTOCOL_GO_LIVE.md'
```

Run live probes after deploy:

```bash
curl -sS https://app.midnightgrc.com/health
curl -sS https://app.midnightgrc.com/ready
curl -sS -o /dev/null -w '%{http_code}\n' https://app.midnightgrc.com/onboarding/plan
```

Expected logged-out `/onboarding/plan`: `307`.
Expected logged-out `/billing/checkout` POST: `401`.

---

## 5. Launch Security Checklist

- [ ] Auth required on protected routes.
- [ ] No production auth bypasses.
- [ ] Tenant isolation tests pass.
- [ ] Non-TKO Bird Eye proof complete.
- [ ] Upload parser handles valid `.docx` safely.
- [ ] Invalid uploads reject safely.
- [ ] Stripe checkout authenticated and metadata-bound.
- [ ] Stripe webhook signature validation implemented.
- [ ] Stripe webhook updates tenant plan.
- [ ] Webhook invalid signature rejects with no side effects.
- [ ] Migration drift audit complete.
- [ ] Supabase service-role rotation confirmed.
- [ ] No secrets in repo or task artifacts.
- [ ] ECS task definition secret posture reviewed without printing values.
- [ ] Deploy provenance proven by image tag and live route behavior.
- [ ] Logs redacted and useful.
- [ ] Watchdog noise resolved or accepted.
- [ ] Rollback protocol documented.
- [ ] Incident response protocol documented.
- [ ] AI/chat secret handling protocol understood.

---

## 6. Final No-Go Security Conditions

Do not launch if any are true:

- Any cross-tenant read/write is possible.
- Any protected endpoint works without valid auth.
- Any secret appears in Git, logs, task JSON, or AI chat.
- Stripe webhook is still a stub or accepts unsigned requests.
- Buyer can pay but tenant plan does not update automatically.
- Valid customer documents cannot be parsed reliably.
- Bird Eye still depends on TKO/demo naming.
- Deploy path cannot identify exactly what code is live.

Security bar: boring, repeatable, verified. If it depends on founder memory, it is not a control.
