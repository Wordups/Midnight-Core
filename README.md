# Midnight Core
**Compliance System Builder + Audit Preparation Engine**
*Takeoff LLC — Private Repository*

---

## What this is

Midnight is a template-driven compliance document transformation engine. It ingests policy documents, maps them to compliance frameworks, identifies gaps, and generates audit-ready outputs — with humans in control at every step.

**Not a Vanta clone. Not a checkbox tool.**
We prepare you for audit and help you build the system.

---

## Architecture

See [`CLAUDE.md`](./CLAUDE.md) for the maintained architecture reference
(module layout, request flow, multi-tenancy). Short version:

```
upload/generate → framework-map → gap-analyze → render → store
```

- **Bird Eye** — ingests documents, embeds them, runs detectors (conflicts, duplicates, gaps, orphans, stale governance)
- **Create Studio** — generates new documents from template packs (python-docx)
- **Framework mapping** — HIPAA, ISO 27001, NIST CSF, PCI DSS, SOC 2
- **Gap engine** — required controls minus covered controls = gaps (deterministic, no AI)
- **Corpus** — answers security questionnaires from the document corpus, citations required, fails closed
- **Dashboard** — coverage, gaps, documents, activity — live from API

---

## Document types supported

Eight lanes exist in Create Studio; only **POLICY** has a live generate/export
path today. The rest (`procedure`, `standard`, `process_flow`, `training`,
`incident_runbook`, `risk_assessment`, `audit_package`) are gated "In
Development" in `frontend/create_studio.js` — template packs exist for them
on disk (`backend/templates/packs/`), but that's output examples, not a wired
Studio lane.

---

## Local setup

```bash
git clone https://github.com/Wordups/Midnight-Core
cd Midnight-Core

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r backend/requirements.txt

cp .env.example .env
# fill in .env with your keys

uvicorn backend.api.main:app --reload --port 8000
```

Run from the repo root — not `backend/`; `PYTHONPATH` assumes `backend.` imports.

Dashboard: open `http://localhost:8000/midnight_dashboard.html` after starting the backend.

---

## Environment variables

See `.env.example`. Never commit `.env`.

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude access for Smart Scan, migration, creation, and Bird Talk |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Supabase anon key (user-scoped client) |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service-role key (admin client) — `config.py` fails closed at boot without it |
| `ALLOWED_ORIGINS` | Recommended | Comma-separated list of allowed browser origins |
| `VOYAGE_API_KEY` | Optional | Corpus embeddings |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_PRICE_*` | Optional | Billing — see `backend/api/stripe_router.py` |
| `JIRA_SITE_URL` / `JIRA_EMAIL` / `JIRA_API_TOKEN` / `JIRA_PROJECT_KEY` | Optional | Jira integration env fallback |

---

## Deployment

Hosted on Render. Config in `render.yaml`.

- Backend: `https://midnight-core.onrender.com`
- Dashboard: `/midnight_dashboard.html` served from the same Render app origin

---

## Rules for this repo

1. **No client data** — no client names, policy numbers, or internal docs
2. **No giant service files** — one responsibility per module
3. **No template logic inside core engine** — templates are packs, not hardcode
4. **Validate in 2.0, productize in Core** — port only clean generalized logic
5. **Every output is a draft** — nothing is "compliant", everything is "prepared"

---

## Takeoff LLC

Private. All rights reserved.
Built by Brian Word.
