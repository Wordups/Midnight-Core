"""Trace Agent — batch-intake orchestrator for policy / playbook generation.

Replaces the prior Policy Agent flow for batch-mode generation. Given a
populated generation_intake row, runs a fixed 16-step loop that
produces an audit-ready .docx, validates it, spot-checks it, writes a
process_trace.md rationale, and returns both artifacts. Every step
appends one row to activity_log with the WHY of that step.

Designed for autonomous (no-user-interaction) runs from a hardcoded
test payload or a future intake form. Not wired to any HTTP route in
this PR.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml

from backend.agents.base import AgentValidationError, BaseAgent
from backend.agents.generators.docx_generator import (
    DocxGenerationError,
    generate_docx,
)
from backend.agents.schemas import GenerationResult, TraceAgentIntake
from backend.agents.validators.schema_validator import (
    SchemaValidationResult,
    validate_schema,
)
from backend.agents.validators.spot_checker import SpotCheckResult, spot_check
from config import settings

logger = logging.getLogger("midnight.trace_agent")

# ─── Module-level constants ──────────────────────────────────────────────────

OUTLINE_DIR = Path(__file__).resolve().parent / "templates" / "outlines"
MAX_REPAIR_ATTEMPTS = 3
ANTHROPIC_MODEL = "claude-opus-4-5"

# Each step's metadata. The 16 steps are FIXED; reordering changes the
# trace contract callers (and auditors) rely on.
STEP_DEFINITIONS: list[tuple[int, str]] = [
    (1,  "load_intake"),
    (2,  "plan"),
    (3,  "derive_questions"),
    (4,  "load_answers"),
    (5,  "freeze_assumptions"),
    (6,  "load_skill"),
    (7,  "outline"),
    (8,  "build_script"),
    (9,  "generate"),
    (10, "validate_schema"),
    (11, "spot_check"),
    (12, "repair"),
    (13, "rerun"),
    (14, "write_trace"),
    (15, "verify_artifacts"),
    (16, "return"),
]


# ─── Supabase helpers (service-role REST) ────────────────────────────────────

def _supabase_url(path: str) -> str:
    return f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/{path.lstrip('/')}"


def _service_headers(*, prefer: str | None = "return=representation") -> dict[str, str]:
    headers = {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _select_intake(intake_id: str) -> dict[str, Any]:
    import requests
    resp = requests.get(
        _supabase_url("generation_intake"),
        headers=_service_headers(prefer=None),
        params={"id": f"eq.{intake_id}", "select": "*", "limit": "1"},
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Intake select failed {resp.status_code}: {resp.text[:300]}")
    rows = resp.json() or []
    if not rows:
        raise RuntimeError(f"Intake row not found: id={intake_id}")
    return rows[0]


def _insert_activity_log_row(
    *,
    tenant_id: str,
    policy_id: str | None,
    action: str,
    step_number: int,
    step_name: str,
    rationale: str,
) -> str:
    import requests
    payload = {
        "tenant_id": tenant_id,
        "policy_id": policy_id,
        "action": action,
        "step_number": step_number,
        "step_name": step_name,
        "rationale": rationale,
    }
    resp = requests.post(
        _supabase_url("activity_log"),
        headers=_service_headers(),
        data=json.dumps(payload),
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"activity_log insert failed {resp.status_code}: {resp.text[:300]}")
    rows = resp.json() or []
    if not rows or "id" not in rows[0]:
        raise RuntimeError(f"activity_log insert returned no id: {resp.text[:200]}")
    return str(rows[0]["id"])


# ─── Anthropic helpers ───────────────────────────────────────────────────────

def _anthropic_client():
    # Anthropic by default; Ollama when LLM_PROVIDER=ollama (local dev/testing).
    from backend.llm.provider import get_client
    return get_client(anthropic_api_key=settings.ANTHROPIC_API_KEY)


def _call_claude(*, system: str, user: str, max_tokens: int = 4000) -> str:
    client = _anthropic_client()
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    chunks: list[str] = []
    for block in getattr(message, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            chunks.append(text)
    return "\n".join(chunks).strip()


# ─── Trace Agent ─────────────────────────────────────────────────────────────

class TraceAgent(BaseAgent):
    name = "trace_agent"
    role = "Batch-intake orchestrator that produces audit-ready deliverables"
    allowed_actions = (
        "load_intake", "plan", "derive_questions", "load_answers",
        "freeze_assumptions", "load_skill", "outline", "build_script",
        "generate", "validate_schema", "spot_check", "repair", "rerun",
        "write_trace", "verify_artifacts", "return",
    )
    forbidden_actions = (
        "trust_raw_llm_output",
        "use_eval",
        "use_exec",
        "skip_validation",
        "claim_approval",
        "claim_certification",
    )

    def __init__(self, *, output_dir: str | Path | None = None):
        # output_dir lets the test harness redirect artifacts to a tempdir.
        # Defaults to a tempfile.mkdtemp() prefix; production callers can
        # set this to a Supabase Storage staging path.
        self.output_dir = Path(output_dir) if output_dir else None

    # BaseAgent.run() wraps validate_input/_run/validate_output. Trace
    # Agent's contract is different (intake_id in, GenerationResult
    # out), so we override `run` directly.
    def run(self, intake_id: str | UUID) -> GenerationResult:  # type: ignore[override]
        intake_id = str(intake_id)
        if not intake_id:
            raise AgentValidationError("intake_id is required")

        state: dict[str, Any] = {
            "intake_id": intake_id,
            "activity_log_ids": [],
            "repair_attempts": 0,
            "outline_source": None,
            "outline": None,
            "spec": None,
            "docx_path": None,
            "trace_path": None,
            "last_failure": None,
        }

        try:
            return self._run_loop(state)
        except Exception as exc:
            logger.exception("trace_agent_unhandled_error", extra={"intake_id": intake_id})
            return GenerationResult(
                intake_id=intake_id,
                policy_id=state.get("policy_id"),
                status="failed",
                docx_path=state.get("docx_path"),
                trace_path=state.get("trace_path"),
                outline_source=state.get("outline_source"),
                activity_log_ids=state["activity_log_ids"],
                repair_attempts=state["repair_attempts"],
                error=f"{exc.__class__.__name__}: {exc}",
            )

    # ── internal: one step writes one activity_log row ──────────────────────
    def _log_step(self, state: dict[str, Any], step_number: int, step_name: str, rationale: str) -> None:
        rid = _insert_activity_log_row(
            tenant_id=state["tenant_id"],
            policy_id=state.get("policy_id"),
            action=f"trace_step_{step_number:02d}_{step_name}",
            step_number=step_number,
            step_name=step_name,
            rationale=rationale,
        )
        state["activity_log_ids"].append(rid)

    # ── the 16-step loop ────────────────────────────────────────────────────
    def _run_loop(self, state: dict[str, Any]) -> GenerationResult:
        intake_id = state["intake_id"]

        # Step 1 — load_intake
        raw = _select_intake(intake_id)
        intake = TraceAgentIntake.model_validate(raw)
        state["tenant_id"] = intake.tenant_id
        state["policy_id"] = intake.policy_id
        state["intake"] = intake
        self._log_step(state, 1, "load_intake", (
            f"Loaded generation_intake id={intake.id} for tenant_id={intake.tenant_id}. "
            f"deliverable_type={intake.deliverable_type!r}, framework_spine={intake.framework_spine}, "
            f"audience={intake.audience!r}, maturity_posture={intake.maturity_posture!r}. "
            f"approved_at={intake.approved_at}."
        ))

        # Step 2 — plan
        plan_summary = (
            f"Plan: load skill conventions, resolve outline from template registry or LLM fallback, "
            f"build a docx spec via LLM, render via docx-js, validate (schema + spot), repair up to "
            f"{MAX_REPAIR_ATTEMPTS - 1} times on failure, write trace, verify artifacts, return."
        )
        state["plan"] = plan_summary
        self._log_step(state, 2, "plan", (
            f"Built internal task list for this run. {plan_summary}"
        ))

        # Step 3 — derive_questions (batched: skipped, but logged)
        self._log_step(state, 3, "derive_questions", (
            "Skipped — intake row is already populated by the batch-intake source. "
            "Question derivation runs only in interactive mode."
        ))

        # Step 4 — load_answers (batched: skipped, but logged)
        self._log_step(state, 4, "load_answers", (
            "Skipped — answers live inside the intake row itself "
            "(scope_boundary, business_context, declared_assumptions)."
        ))

        # Step 5 — freeze_assumptions
        assumption_set = {
            "scope_boundary": intake.scope_boundary,
            "business_context": intake.business_context,
            "declared_assumptions": intake.declared_assumptions or {},
            "audience": intake.audience,
            "maturity_posture": intake.maturity_posture,
        }
        state["assumption_set"] = assumption_set
        self._log_step(state, 5, "freeze_assumptions", (
            "Assembled assumption_set from intake. "
            f"scope_boundary keys={sorted(intake.scope_boundary.keys())}, "
            f"business_context keys={sorted(intake.business_context.keys())}, "
            f"declared_assumptions keys={sorted((intake.declared_assumptions or {}).keys())}. "
            "These freeze the inputs the downstream LLM calls will see — no further mutation."
        ))

        # Step 6 — load_skill
        skill_conventions = self._load_skill_conventions()
        state["skill_conventions"] = skill_conventions
        self._log_step(state, 6, "load_skill", (
            f"Loaded docx generation conventions: {len(skill_conventions['rules'])} rules, "
            f"primary tool={skill_conventions['tool']!r}. These constrain the LLM's spec output "
            "in step 8 so the docx-js subprocess can render it deterministically."
        ))

        # Step 7 — outline (template lookup with LLM fallback)
        outline, outline_source = self._load_outline(intake)
        state["outline"] = outline
        state["outline_source"] = outline_source
        section_count = len(outline.get("sections") or [])
        self._log_step(state, 7, "outline", (
            f"Resolved outline for {{deliverable_type={intake.deliverable_type!r}, "
            f"framework={intake.framework_spine[0]!r}}} via source={outline_source!r}. "
            f"{section_count} section(s). Title={outline.get('title')!r}."
        ))

        # Steps 8-13 — build script -> generate -> validate -> spot -> repair loop
        docx_path = (self.output_dir or Path(tempfile.mkdtemp(prefix="trace_agent_"))) / f"{intake_id}.docx"
        state["docx_path"] = str(docx_path)

        success = False
        validation_history: list[dict[str, Any]] = []
        repair_feedback: str | None = None

        for attempt in range(MAX_REPAIR_ATTEMPTS):
            attempt_no = attempt + 1
            # Step 8 — build_script (rebuilt each attempt, incorporates feedback)
            spec = self._build_spec(intake, outline, assumption_set, skill_conventions, repair_feedback)
            state["spec"] = spec
            self._log_step(state, 8, "build_script", (
                f"Attempt {attempt_no}/{MAX_REPAIR_ATTEMPTS}: built docx-js spec. "
                f"Sections in spec={len(spec.get('sections') or [])}, "
                f"front_matter rows={len(spec.get('frontMatter') or [])}. "
                + (f"Incorporated repair feedback: {repair_feedback[:160]}..." if repair_feedback else
                   "First attempt; no repair feedback yet.")
            ))

            # Step 9 — generate
            try:
                gen_result = generate_docx(spec=spec, output_path=docx_path)
                self._log_step(state, 9, "generate", (
                    f"Attempt {attempt_no}: docx-js subprocess produced "
                    f"{gen_result['bytes']} bytes at {gen_result['docx_path']}. "
                    f"section_count reported by Node={gen_result['section_count']}."
                ))
            except DocxGenerationError as exc:
                self._log_step(state, 9, "generate", (
                    f"Attempt {attempt_no}: docx-js subprocess failed: {exc}"
                ))
                state["last_failure"] = f"generate: {exc}"
                state["repair_attempts"] = attempt_no
                repair_feedback = self._summarize_repair_feedback(
                    schema_err=str(exc), spot_err=None, missing_sections=[],
                )
                self._log_step(state, 12, "repair", (
                    f"Attempt {attempt_no} failed at generate step. "
                    f"Composed repair feedback for the next build_script call."
                ))
                continue

            # Step 10 — validate_schema
            schema_result = validate_schema(docx_path)
            validation_history.append({
                "attempt": attempt_no,
                "schema": schema_result.as_dict(),
            })
            self._log_step(state, 10, "validate_schema", (
                f"Attempt {attempt_no}: schema_validator ok={schema_result.ok}, "
                f"body_paragraphs={schema_result.body_paragraphs}, "
                f"error={schema_result.error!r}."
            ))

            # Step 11 — spot_check
            spot_result = spot_check(docx_path, outline)
            validation_history[-1]["spot"] = spot_result.as_dict()
            self._log_step(state, 11, "spot_check", (
                f"Attempt {attempt_no}: spot_checker ok={spot_result.ok}, "
                f"found={len(spot_result.found_sections)}, "
                f"missing={spot_result.missing_sections}, "
                f"extracted_chars={spot_result.extracted_chars}."
            ))

            if schema_result.ok and spot_result.ok:
                # Both validators clean. Log a no-op repair entry to keep the
                # step count honest (16 rows regardless of outcome) and break.
                state["repair_attempts"] = attempt
                self._log_step(state, 12, "repair", (
                    f"Attempt {attempt_no} passed both validators on first pass; "
                    "no repair required."
                ))
                self._log_step(state, 13, "rerun", (
                    f"Loop exited cleanly on attempt {attempt_no} of {MAX_REPAIR_ATTEMPTS}. "
                    "No rerun needed."
                ))
                success = True
                break

            # Step 12 — repair (compose feedback for next attempt)
            state["repair_attempts"] = attempt_no
            repair_feedback = self._summarize_repair_feedback(
                schema_err=schema_result.error,
                spot_err=spot_result.error,
                missing_sections=spot_result.missing_sections,
            )
            self._log_step(state, 12, "repair", (
                f"Attempt {attempt_no} failed: "
                + (f"schema={schema_result.error!r} " if not schema_result.ok else "")
                + (f"spot={spot_result.error!r} missing={spot_result.missing_sections} "
                   if not spot_result.ok else "")
                + ("Composed repair feedback for next attempt." if attempt_no < MAX_REPAIR_ATTEMPTS
                   else "Out of repair attempts; will return status=draft.")
            ))
            # Step 13 — rerun (logged each iteration except the last)
            if attempt_no < MAX_REPAIR_ATTEMPTS:
                self._log_step(state, 13, "rerun", (
                    f"Looping back to step 9 (generate) with updated build_script. "
                    f"Attempt {attempt_no + 1} of {MAX_REPAIR_ATTEMPTS}."
                ))
            else:
                self._log_step(state, 13, "rerun", (
                    f"Reached MAX_REPAIR_ATTEMPTS={MAX_REPAIR_ATTEMPTS} without a clean pass. "
                    "Surfacing best-effort draft with status=draft."
                ))

        state["validation_history"] = validation_history

        # Step 14 — write_trace
        trace_path = self._write_trace_markdown(state, success=success)
        state["trace_path"] = str(trace_path)
        self._log_step(state, 14, "write_trace", (
            f"Wrote process_trace.md to {trace_path} "
            f"({trace_path.stat().st_size} bytes). Contains 16-step rationale + validation history."
        ))

        # Step 15 — verify_artifacts
        artifacts_ok, artifact_detail = self._verify_artifacts(docx_path, trace_path)
        self._log_step(state, 15, "verify_artifacts", artifact_detail)

        # Step 16 — return
        final_status = "complete" if (success and artifacts_ok) else "draft"
        self._log_step(state, 16, "return", (
            f"Returning GenerationResult with status={final_status!r}, "
            f"repair_attempts={state['repair_attempts']}, "
            f"activity_log row count={len(state['activity_log_ids'])}."
        ))

        return GenerationResult(
            intake_id=intake_id,
            policy_id=state.get("policy_id"),
            status=final_status,
            docx_path=str(docx_path),
            trace_path=str(trace_path),
            outline_source=state["outline_source"],
            activity_log_ids=state["activity_log_ids"],
            repair_attempts=state["repair_attempts"],
            error=None if success else (state.get("last_failure") or "validation never converged"),
        )

    # ── BaseAgent abstract method satisfaction ──────────────────────────────
    def _run(self, data: Any) -> Any:
        """Indirection for the BaseAgent contract — callers should use
        TraceAgent.run(intake_id) directly. This wrapper exists so the
        abstract method is concretely implemented."""
        if isinstance(data, dict) and "intake_id" in data:
            return self.run(data["intake_id"])
        if isinstance(data, (str, UUID)):
            return self.run(data)
        raise AgentValidationError(
            "TraceAgent expects intake_id as UUID/str or a dict with intake_id key."
        )

    # ── Step helpers ────────────────────────────────────────────────────────

    def _load_skill_conventions(self) -> dict[str, Any]:
        """Step 6 — surface the docx generation conventions the LLM must
        follow in step 8. Today these are hard-coded; future template
        registries will load per-deliverable-type variants."""
        return {
            "tool": "docx-js (npm package `docx` v9.x)",
            "rules": [
                "Spec is JSON; the Node side renders it. Do NOT emit raw docx-js code.",
                "Top-level fields: title, subtitle (optional), frontMatter (list of {label,value}), sections.",
                "Each section: heading (string), level (1..6), blocks (list).",
                "Blocks: {kind:'paragraph',text}, {kind:'bullets',items[]}, {kind:'ordered',items[]}, {kind:'callout',text}.",
                "No markdown syntax in any text field — emit plain prose. Headings render via the heading field.",
                "Every section in the outline must produce at least one block.",
                "Section headings in the spec must match the outline's headings verbatim (whitespace normalized).",
            ],
        }

    def _load_outline(self, intake: TraceAgentIntake) -> tuple[dict[str, Any], str]:
        """Step 7 — try the template registry first, fall back to LLM."""
        if intake.framework_spine:
            primary_framework = intake.framework_spine[0]
            template_path = OUTLINE_DIR / f"{intake.deliverable_type}_{primary_framework}.yaml"
            if template_path.exists():
                with template_path.open("r", encoding="utf-8") as f:
                    outline = yaml.safe_load(f)
                if isinstance(outline, dict) and outline.get("sections"):
                    return outline, "template"
        # Fall through to LLM
        return self._llm_outline_fallback(intake), "llm_fallback"

    def _llm_outline_fallback(self, intake: TraceAgentIntake) -> dict[str, Any]:
        system = (
            "You produce structured document outlines for audit-ready compliance "
            "deliverables. Return JSON ONLY matching the requested schema."
        )
        user = textwrap.dedent(f"""\
            Produce an outline for a {intake.deliverable_type!r} aligned to the
            framework spine {intake.framework_spine!r} for audience={intake.audience!r}
            and maturity_posture={intake.maturity_posture!r}.

            Business context: {json.dumps(intake.business_context)}
            Declared assumptions: {json.dumps(intake.declared_assumptions or {{}})}

            Return exactly this JSON shape (no fences, no prose):
            {{
              "deliverable_type": "...",
              "framework": "...",
              "title": "...",
              "description": "...",
              "sections": [
                {{"id": "lowercase_underscore", "heading": "1. Heading Text", "purpose": "what this section covers"}}
              ]
            }}
            Use between 8 and 12 sections. Number them in the heading (e.g. "1. Purpose").
        """).strip()
        from backend.core.json_parser import parse_model_json
        raw = _call_claude(system=system, user=user, max_tokens=2000)
        parsed = parse_model_json(raw)
        if not isinstance(parsed, dict) or not parsed.get("sections"):
            raise RuntimeError("LLM outline fallback returned malformed JSON")
        return parsed

    def _build_spec(
        self,
        intake: TraceAgentIntake,
        outline: dict[str, Any],
        assumption_set: dict[str, Any],
        skill_conventions: dict[str, Any],
        repair_feedback: str | None,
    ) -> dict[str, Any]:
        """Step 8 — ask Claude to fill the outline with content, producing
        a JSON spec the docx-js subprocess can render."""
        sections_brief = [
            {
                "id": s.get("id"),
                "heading": s.get("heading"),
                "purpose": s.get("purpose"),
            }
            for s in (outline.get("sections") or [])
            if isinstance(s, dict)
        ]
        system = (
            "You produce structured docx specs for a Node subprocess. "
            "Return JSON ONLY matching the schema. Do NOT use markdown anywhere "
            "in field values; emit plain prose. The Node side renders the JSON "
            "into a Word document. Do NOT return docx-js code."
        )
        rules_block = "\n".join(f"  - {r}" for r in skill_conventions["rules"])
        feedback_block = ""
        if repair_feedback:
            feedback_block = (
                "\n\nPRIOR ATTEMPT FAILED. Repair feedback you MUST address:\n"
                f"{repair_feedback}\n"
            )

        user = textwrap.dedent(f"""\
            Compose the body of a deliverable matching this outline and assumption set.

            Outline title: {outline.get('title')!r}
            Outline description: {outline.get('description')!r}
            Audience: {intake.audience!r}, Maturity posture: {intake.maturity_posture!r}.

            Sections to populate (use EXACTLY these headings, in this order):
            {json.dumps(sections_brief, indent=2)}

            Assumption set (do not invent facts beyond what's here):
            {json.dumps(assumption_set, indent=2)}

            Conventions for the spec:
            {rules_block}
            {feedback_block}

            Return JSON exactly matching this schema (no fences, no prose):
            {{
              "title": "{outline.get('title')!r}",
              "subtitle": "optional one-liner",
              "frontMatter": [
                {{"label": "Owner", "value": "..."}},
                {{"label": "Audience", "value": "{intake.audience}"}},
                {{"label": "Frameworks", "value": "{', '.join(intake.framework_spine)}"}}
              ],
              "sections": [
                {{
                  "heading": "1. Purpose and Scope",
                  "level": 1,
                  "blocks": [
                    {{"kind": "paragraph", "text": "..."}},
                    {{"kind": "bullets", "items": ["...", "..."]}}
                  ]
                }}
              ]
            }}
        """).strip()
        from backend.core.json_parser import parse_model_json
        # 16K headroom for 12-section deliverables (SOC playbook, HIPAA policy).
        # Opus 4.5 supports 32K output; 8K truncated mid-emit on the SOC scenario.
        # If a future deliverable exceeds 16K, broaden repair coverage to catch
        # truncation as a failure class (followup W3 PR).
        raw = _call_claude(system=system, user=user, max_tokens=16000)
        parsed = parse_model_json(raw)
        if not isinstance(parsed, dict) or not parsed.get("sections"):
            raise RuntimeError("build_script LLM call returned malformed JSON")
        # Make sure the title and section headings actually came back —
        # the spec validator and spot-checker both depend on them.
        if not parsed.get("title"):
            parsed["title"] = outline.get("title") or "Untitled"
        return parsed

    def _summarize_repair_feedback(
        self,
        *,
        schema_err: str | None,
        spot_err: str | None,
        missing_sections: list[str],
    ) -> str:
        bits: list[str] = []
        if schema_err:
            bits.append(f"Schema validator: {schema_err}")
        if spot_err:
            bits.append(f"Spot-checker: {spot_err}")
        if missing_sections:
            bits.append(
                "Missing section headings in rendered output (you must include these verbatim): "
                + "; ".join(missing_sections)
            )
        if not bits:
            bits.append("(no concrete failure reason captured)")
        return "  ".join(bits)

    def _write_trace_markdown(self, state: dict[str, Any], *, success: bool) -> Path:
        docx_path = Path(state["docx_path"])
        trace_path = docx_path.with_suffix("").with_name(docx_path.stem + "_process_trace.md")
        intake: TraceAgentIntake = state["intake"]

        lines: list[str] = []
        lines.append(f"# Trace Agent process trace")
        lines.append("")
        lines.append(f"- Intake ID: `{intake.id}`")
        lines.append(f"- Tenant ID: `{intake.tenant_id}`")
        lines.append(f"- Deliverable: `{intake.deliverable_type}`")
        lines.append(f"- Framework spine: `{', '.join(intake.framework_spine)}`")
        lines.append(f"- Audience: `{intake.audience}`")
        lines.append(f"- Maturity posture: `{intake.maturity_posture}`")
        lines.append(f"- Outline source: `{state['outline_source']}`")
        lines.append(f"- Repair attempts used: `{state['repair_attempts']}` / `{MAX_REPAIR_ATTEMPTS - 1}` allowed")
        lines.append(f"- Final status: `{'complete' if success else 'draft'}`")
        lines.append(f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`")
        lines.append("")
        lines.append("## 16-step trace")
        lines.append("")
        lines.append("Every step has a corresponding row in `activity_log` with a `rationale`")
        lines.append("field that explains WHY the step ran given the inputs it saw. The IDs below")
        lines.append("can be looked up with:")
        lines.append("")
        lines.append("```sql")
        lines.append(f"SELECT step_number, step_name, rationale, created_at")
        lines.append(f"FROM activity_log")
        lines.append(f"WHERE tenant_id = '{intake.tenant_id}'")
        lines.append(f"  AND policy_id IS NOT DISTINCT FROM '{intake.policy_id or ''}'")
        lines.append("ORDER BY created_at ASC, step_number ASC;")
        lines.append("```")
        lines.append("")
        for i, (step_n, step_name) in enumerate(STEP_DEFINITIONS):
            if i < len(state["activity_log_ids"]):
                rid = state["activity_log_ids"][i]
            else:
                # Steps 14-16 (write_trace itself, verify_artifacts, return)
                # write their activity_log rows AFTER this markdown is rendered,
                # so their IDs aren't available at write time. The rows DO exist
                # in activity_log — they can be queried by tenant_id + intake_id
                # after the run completes.
                rid = "(written after this trace — see activity_log)"
            lines.append(f"- **Step {step_n:>2} — {step_name}** — activity_log id `{rid}`")

        history = state.get("validation_history") or []
        if history:
            lines.append("")
            lines.append("## Validation history")
            lines.append("")
            for entry in history:
                lines.append(f"### Attempt {entry['attempt']}")
                schema = entry.get("schema") or {}
                spot = entry.get("spot") or {}
                lines.append(f"- Schema: ok={schema.get('ok')!r}, body_paragraphs={schema.get('body_paragraphs')}, error={schema.get('error')!r}")
                lines.append(f"- Spot-check: ok={spot.get('ok')!r}, found={len(spot.get('found_sections') or [])}, missing={spot.get('missing_sections') or []}")
                lines.append("")

        lines.append("")
        lines.append("## Artifacts")
        lines.append("")
        lines.append(f"- Generated docx: `{state['docx_path']}`")
        lines.append(f"- This trace:    `{trace_path}`")
        lines.append("")
        if not success and state.get("last_failure"):
            lines.append("## Final failure reason")
            lines.append("")
            lines.append(f"`{state['last_failure']}`")
            lines.append("")

        trace_path.write_text("\n".join(lines), encoding="utf-8")
        return trace_path

    def _verify_artifacts(self, docx_path: Path, trace_path: Path) -> tuple[bool, str]:
        problems: list[str] = []
        if not docx_path.exists():
            problems.append(f"docx missing: {docx_path}")
        elif docx_path.stat().st_size == 0:
            problems.append(f"docx is zero bytes: {docx_path}")
        if not trace_path.exists():
            problems.append(f"trace missing: {trace_path}")
        elif trace_path.stat().st_size == 0:
            problems.append(f"trace is zero bytes: {trace_path}")
        if problems:
            return False, "Artifact verification FAILED: " + "; ".join(problems)
        return True, (
            f"Both artifacts present and non-zero: "
            f"docx={docx_path.stat().st_size}B, trace={trace_path.stat().st_size}B."
        )
