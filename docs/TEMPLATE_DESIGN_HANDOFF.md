# Midnight Core — Document Template Design Handoff

**For:** a design-focused Claude session building the compliance-document template body/flow.
**From:** the engineering session that wired the template pipeline.
**Goal:** turn the generated `.docx` output into something that looks like it came from a top-tier GRC firm — and stays clean to edit in Word afterward.

---

## 1. Context (why this matters)

Midnight Core is a GRC SaaS. Its Studio generates compliance documents (policies, SOPs, risk assessments, incident runbooks, AI-governance frameworks, etc.) from a short intake, then renders them into a Word template. **The template is the product's moat** — anyone can wire an LLM to a form; the differentiator is output that reads and looks like a firm produced it. Content voice is already handled (four variants — formal/modern/detailed/executive — differ in register and length via the generation prompt). **Your job is the visual template: the cover, the flow, the typographic system, and the editability.**

Two document "sources" exist today:
1. **Pack shells** — `backend/templates/packs/<category>/<variant>/<category>_<variant>.docx` (9 categories × 4 variants). Hand-designed in Word, with `{{PLACEHOLDER}}` tokens and a cover page / Document Control / TOC. **These are style-flat** (all Calibri Light, variants visually identical) — the reason this handoff exists.
2. **Master template** — `backend/core/master_template.py`, a programmatic shell (current default, `USE_MASTER_TEMPLATE=1`). Designed but minimal. A reasonable starting point or a thing to replace.

You may improve **either path** (see §5). The hard contract in §2 is identical for both.

---

## 2. Integration contract — DO NOT BREAK

The engine treats a template as a *shell*: it keeps the front matter, fills placeholders, then **appends generated sections**. Everything here is enforced by `backend/api/routes.py::_build_docx` and `backend/core/template_engine.py`.

### 2.1 Front-matter boundary
- The engine keeps every body element **before the first numbered section heading** and deletes everything from that heading onward (`_strip_sample_sections`, `template_engine.py`).
- "First numbered section heading" = a paragraph whose **style name starts with `Heading`** and whose text matches `^\d+\.\s+\S` (e.g. `1. Purpose`, `1. Learning Objectives`).
- **Requirement:** put all cover / Document Control / Table of Contents content BEFORE a paragraph styled as a Heading beginning `1. …`. If you hand-author a `.docx` pack shell, include at least one `1. <something>` heading to mark where the sample body starts (its content will be dropped and replaced).

### 2.2 Placeholders (filled by `fill_template_placeholders`)
Use these exact tokens anywhere in the cover page, control tables, header, or footer. Body **and** header/footer **and** table cells are filled. Unmapped tokens are blanked (no raw braces reach output).

| Token | Value |
|---|---|
| `{{DOCUMENT_TITLE}}` | policy/document title |
| `{{ORGANIZATION_NAME}}` | tenant org name |
| `{{VERSION}}` | version (default 1.0) |
| `{{EFFECTIVE_DATE}}` | effective date |
| `{{NEXT_REVIEW_DATE}}` | next review date |
| `{{POLICY_OWNER}}` / `{{POLICY_OWNER_TITLE}}` | owner + title |
| `{{APPROVER_NAME}}` / `{{APPROVER_TITLE}}` | approver + title |
| `{{AUTHOR_NAME}}` | author (defaults to owner) |
| `{{CLASSIFICATION}}` | Internal / Confidential / etc. |

Category-specific tokens the pack shells also use (currently blanked, wire more values in `_build_docx` if you want them populated): `{{SECURITY_CONTACT}}`, `{{INFO_SEC_LEAD}}`, `{{CS_LEAD}}`, `{{ENGINEERING_LEAD}}`, `{{IT_OPS_LEAD}}`, `{{VENDOR_OWNER}}`, `{{ASSESSMENT_PERIOD}}`, `{{AUDIT_PERIOD_START}}`, `{{AUDIT_PERIOD_END}}`, `{{REMEDIATION_STATUS_DATE}}`.

### 2.3 Named styles the render path uses
Generated content is written with these **named styles** — they must exist and carry your design:
- **`Heading 1`** — section headings. Rendered as `N. <Section>` (e.g. `1. Purpose`). In the master, sections are Heading 1; in pack shells they're Heading 2 (see `section_heading_level`, §2.4).
- **`Heading 2`, `Heading 3`** — sub-sections (framework names under Framework Mappings render one level below the section level).
- **`Normal`** — body paragraphs.
- **`List Bullet`, `List Number`** — bullets/numbered lists (the engine registers these if missing).
- **`Table Grid`** — metadata / revision tables (engine registers if missing).
- **`Title`** — cover title (if used).
Design the **styles**, not one-off runs — content the user adds later in Word must inherit the look.

### 2.4 Shell signal attributes (set on the returned `Document`)
If you build in code (master path), set these; if you hand-author a `.docx`, the loader sets sensible defaults:
- `doc.is_template_shell = True` — marks it a real shell (skips the blank-fallback Calibri reset).
- `doc.is_master_template = True` — **skips the legacy default footer overwrite** so your designed footer/page-numbers survive.
- `doc.section_heading_level = 1` — sections render as Heading 1 (omit → pack shells default to Heading 2).

### 2.5 What the engine appends after front matter (in order)
1. Numbered body sections — one `Heading <section_level>` per generated section, then its content (markdown-aware: `#`/`##`, `*`/`-` bullets, `**bold**` are rendered into real Word formatting).
2. **Framework Mappings** — a numbered section; each framework a sub-heading; controls as bullets.
3. **Gap Analysis** (only if gaps present) — numbered section, bullets.
4. **Revision History** — numbered section + a 3-column `Table Grid` (Version / Date / Description).
Numbering is a single running counter (no collisions). Don't hard-code section numbers in the template body.

### 2.6 Fonts & fields (editability)
- **Fonts must render on any Word install** — use Office-standard families (Segoe UI, Calibri, Cambria, Georgia, Arial, Times New Roman, Aptos) or embed the font in the `.docx`. No CDN/webfonts. A missing font renders as an ugly fallback on the user's machine.
- **Table of Contents = a live field** (`TOC \o "1-3" \h \z \u`), not typed lines — it repaginates on right-click → Update Field.
- **Page numbers = `PAGE` / `NUMPAGES` fields** in the footer.
- Prefer paragraph/character **styles** over direct run formatting so local edits stay consistent.

---

## 3. Design brief (the creative part)

**Voice/positioning:** "Audit-ready, never compliant." Authoritative, precise, firm-grade — not startup-casual, not generic-corporate.

**Current design tokens** (from `master_template.py` — improve freely):
- Ink `#1A1B2E` · Midnight Violet `#7C5CD1` (accent, **overridden per-tenant** via brand color) · Slate `#5B5B76` · Hairline `#D8D8E4` · Mist `#F4F3F9`.
- Headings/eyebrows: Segoe UI (Semibold). Body: Calibri 10.5pt. Cover title: Segoe UI Light 30pt.

**What "flows" means here** — the current output is functional but sparse; make it read like a designed document:
- A **cover** that leads: category eyebrow, strong title, classification, a clean metadata block, tagline, tenant logo. Consider vertical rhythm and a confident title size.
- **Section hierarchy** a reader can scan: distinct H1/H2/H3 treatments, a rule or accent that separates sections, generous but disciplined whitespace, ~65–90 char measure for body.
- **Tables** that look intentional (hairline rows, subtle header fill, aligned numerics) — Document Control, metadata, revision history.
- **Front-to-body transition:** cover → (page break) → Contents → (page break) → Document Control → body. Page breaks in the right places.
- **Running header/footer:** doc title + classification + page numbers, quiet and consistent.
- Accent used **sparingly** (headings, rules, table headers) — it must still read on a tenant's custom brand color, so don't rely on one exact hue.

**Optional — visual variant differentiation:** content voice already differs by variant. If you want the *look* to differ too (e.g. formal = serif body, modern = sans, executive = tighter one-page rhythm), keep the same named styles but swap type/spacing per variant. Not required; the voice does the heavy lifting.

**Body scaffolding (the "it needs body" note):** the owner wants example/scaffold body content in the template. The library's `.md` files are the source of truth for structure and per-variant voice — see §4. You may seed section skeletons / example clauses so a freshly generated doc never looks empty, but remember the engine replaces the body with generated content, so scaffolding matters most for the *shell preview* and for hand-edited/offline use.

---

## 4. Reference material

- **Existing template library (outside the repo):** `C:\Users\bword\Documents\midnight-template-build\` — 36 templates (`<category>/<variant>/<category>_<variant>.docx` + `.md` + `manifest.json`). The `.md` files hold the real per-variant body content and voice; `manifest.json` has canonical `description` + `word_count` per variant. **This is the owner's hand-built IP — mine it for structure and voice, don't discard it.**
- **Variant profiles (already transcribed):** `backend/core/template_voice.py` — formal ≈1200w legalese, modern ≈725w plain, detailed ≈2000w exhaustive, executive ≈500w brief.
- **Category slot structure:** `backend/api/routes.py` — `POLICY_SLOT_SPECS`, `SOP_SLOT_SPECS`, … `DOC_TYPE_SLOT_SPECS` (the section list per doc type the generator fills).
- **Current master:** `backend/core/master_template.py` (`build_master_shell`, `_cover`, `_contents`, `_document_control`, `_header_footer`, `_configure_styles`).
- **Fill / boundary logic:** `backend/core/template_engine.py` (`fill_template_placeholders`, `_strip_sample_sections`, `_clean_cover`, `load_template_shell`).
- **Render/assembly:** `backend/api/routes.py::_build_docx`.

---

## 5. Deliverable options & where to put them

**Path A — hand-authored `.docx` (recommended if you want pixel control in Word):**
Design in Word, use the §2 placeholders + named styles, include a `1. …` heading to mark the body boundary, save to `backend/templates/packs/<category>/<variant>/<category>_<variant>.docx`. Set `USE_MASTER_TEMPLATE=0` (Render env var) so the engine uses pack shells. The engine keeps your front matter, fills tokens, and renders generated sections in your styles.

**Path B — programmatic master (recommended for one reusable, parametric system):**
Extend `backend/core/master_template.py`. Keep it the default (`USE_MASTER_TEMPLATE=1`). Advantage: one source of truth, tenant-accent parametric, no binary drift.

Either way, keep the pandoc pack shells working as a fallback.

---

## 6. Acceptance criteria (how "done" is verified)

1. **No raw tokens:** no `{{` in any part of the output `.docx` XML (cover, header, footer, tables). Test: zip-scan every `*.xml`.
2. **Opens clean in Word** (Mac + Windows), no repair prompt, no missing-font substitution.
3. **Live TOC:** right-click → Update Field builds a correct multi-level contents.
4. **Page numbers** render (`PAGE of NUMPAGES`) on body pages.
5. **Generated sections inherit named styles** — editing/adding a section in Word matches the design.
6. **Numbering is sequential** with no duplicates across body + Framework Mappings + Revision History.
7. **Round-trips** through `python-docx` (`Document(io.BytesIO(raw))`) without error.
8. **Tenant accent** flows: passing a brand color recolors headings/rules; output still legible.
9. **Tests updated/added:** extend `tests/test_master_template.py` and/or `tests/test_template_engine.py`; full suite green (`pytest tests/ --ignore=tests/test_tenant_isolation.py --ignore=tests/test_document_isolation.py`, env stubs `ANTHROPIC_API_KEY=sk-test SUPABASE_URL=… SUPABASE_ANON_KEY=test SUPABASE_SERVICE_ROLE_KEY=test ENVIRONMENT=dev`).

## 7. Guardrails
- Don't change the engine contract (§2) without updating `_build_docx` + tests.
- Don't introduce non-Office fonts without embedding them.
- Don't hard-code section numbers or the tenant color (accent is passed in).
- Keep a working fallback (pack shell or blank Document) so a template failure never fails the export.
- The repo is public — no secrets, no `docs/interview-audit`.

---

*Baseline state at handoff: front-matter preservation + placeholder fill + voice wiring + a minimal designed master are shipped and green (238 tests). What's missing is the elevated visual design and body flow described in §3.*
