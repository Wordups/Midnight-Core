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

```
upload → extract → transform → classify → map → validate → render → store
```

- **Extraction** — parses .docx / .txt / .md into structured data
- **Framework mapping** — HIPAA, HITRUST, PCI DSS, ISO 27001, NIST CSF, CoBIT, SOC 2
- **Gap engine** — required controls minus covered controls = gaps
- **Template engine** — maps normalized content into customer template packs
- **Renderers** — pixel-accurate .docx and branded PDF output
- **Dashboard** — coverage, gaps, documents, activity — live from API

---

## Document types supported

| Type | Description |
|------|-------------|
| POLICY | High-level intent, executive approved |
| STANDARD | Specific measurable requirements |
| PROCEDURE | How to implement a standard |
| SOP | Step-by-step operational execution |
| PLAYBOOK | Event-driven response flows |
| PLAN | Strategic scenario-based documents |

---

## Local setup

```bash
git clone https://github.com/your-org/midnight-core
cd midnight-core

python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

pip install -r backend/requirements.txt

cp .env.example .env
# fill in .env with your keys

cd backend
uvicorn api.main:app --reload --port 8000
```

Dashboard: open `http://localhost:8000/midnight_dashboard.html` after starting the backend.

---

## Environment variables

See `.env.example`. Never commit `.env`.

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude access for Smart Scan, migration, creation, and Bird Talk |
| `TOOL_PASSWORD` | Yes | Dashboard access gate |
| `ALLOWED_ORIGINS` | Recommended | Comma-separated list of allowed browser origins |
| `SUPABASE_URL` | Phase 2 | Document + gap storage |
| `SUPABASE_KEY` | Phase 2 | Supabase anon key |

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
