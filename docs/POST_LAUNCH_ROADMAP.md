# Midnight — Post-Launch Roadmap

Ideas and initiatives outside the launch scope. New ideas go here, not into `LAUNCH_READY.md`.
Sequencing is post-launch based on customer demand and revenue signal — nothing here is
scheduled until after the launch scope ships complete.

Launch scope: [LAUNCH_READY.md](./LAUNCH_READY.md) · Strategy context: [STRATEGY.md §X, §XI](./STRATEGY.md)

---

## V2 — AI Governance Suite
*Target: 90 days post-launch*

Framework coverage for NIST AI RMF, ISO/IEC 42001, and EU AI Act. This is the headline V2
release — a marketing event, a press moment, and the primary tier upgrade catalyst for
Professional and Team customers.

The regulatory pressure is current and the category is unsettled (see `STRATEGY.md §X`). Vanta
and Drata have bolt-on AI governance modules roughly 18 months old. Midnight enters with a
natively-architected approach: corpus-expanding detection, agent-assisted policy generation,
framework mapping that learns from how tenants approach AI governance problems.

The architecture at launch must support adding this without a code restructure — the framework
taxonomy in `frameworks/*.json` is extensible by design. The V2 work is wiring and corpus
development, not architecture changes.

Scope includes: NIST AI RMF organizational and governance profile mapping, ISO 42001 control
library and gap analysis, EU AI Act risk classification (high-risk system identification, Annex
III mapping), AI usage policy generation via Trace Agent, sector-specific guidance for initial
launch (financial services, healthcare).

---

## V2 or V3 — Questionnaire Automation
*Sequencing based on customer signal after launch*

Automated response to security questionnaires: SIG Lite, CAIQ, custom enterprise questionnaires.
B2B buyers receive security questionnaires constantly. Completing them manually is one of the
highest-friction recurring tasks for a GRC analyst. Automating responses from the tenant's
existing policy corpus and Bird Eye findings addresses a clear, high-frequency pain point.

This is the Output stage of ILWAO expanded — the system uses what it knows about the tenant's
program (Logic) to generate questionnaire responses (Output) without requiring the analyst to
write each answer from scratch.

Sequencing between V2 and V3 depends on whether post-launch customers surface this as the
highest-friction remaining task. If AI governance demand is lower than expected at launch and
questionnaire automation comes up consistently in customer conversations, the order may flip.

---

## V3 — Vendor Management
*Post-first-hire*

Risk register, vendor security assessment, evidence collection from vendors, full GRC operations
platform. The natural expansion of the PM-for-compliance shape once the analyst + SME workflows
are established.

The GRC analyst who is managing their internal compliance program with Midnight will eventually
need to manage their vendor compliance program too. Vendor management extends the same PM
architecture (Input → Logic → Wedge → Automate → Output) outward: the "SME" is now an
external vendor, the "task" is a vendor assessment, the "output" is a vendor risk rating.

V3 timing is post-first-hire. It requires engineering bandwidth beyond what a solo founder can
sustain alongside the core product.

---

## Ongoing — Framework Expansion

New frameworks added quarterly post-launch as marketing events. Candidates based on
customer demand and regulatory timing:

- **PCI DSS 4.0** — high-demand for fintech and e-commerce customers
- **NIST 800-53** — required for federal contractors and FedRAMP candidates
- **CMMC 2.0** — Department of Defense contractor compliance, growing urgency
- **DORA** — EU financial services operational resilience regulation
- **CSRD / SEC Climate Disclosure** — sustainability reporting, large enterprise
- **State privacy laws** — combined coverage for California, Virginia, Colorado, and the
  proliferating state law landscape
- **Sector-specific AI regulations** — FDA AI/ML, FFIEC model risk, HHS AI guidance

Each new framework is a planned release: data work first (control library, mapping logic),
then corpus seeding, then public announcement.
