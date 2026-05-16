"""P0 engine-lockdown ship gate — Option C (5 real + 15 mocked).

15 mocked scenarios exercise the parser + validator + quality_flag
functions over varied LLM-output shapes. 5 real Anthropic metadata
generations exercise the load-bearing path against live Claude.

Pass criteria (per spec):
  - Zero 500s
  - Zero unexpected repair-pass invocations (or each one documented)
  - All 20 outputs valid against schema (status_code == "PASS")
  - quality_flags populated correctly on the 4 mocked thin-section cases
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(REPO_ROOT / ".env", override=True)

# Env scaffolding so config + routes import cleanly.
os.environ.setdefault("ENVIRONMENT", os.environ.get("ENVIRONMENT", "dev"))

from fastapi import HTTPException  # noqa: E402

# These imports stand up the whole app; we use individual functions.
from backend.api.routes import (  # noqa: E402
    POLICY_SLOT_SPECS,
    _call_model_json_object,
    _compute_quality_flags,
    _validate_generated_section,
    _validate_policy_metadata,
    CreatePolicyRequest,
)
from backend.core.json_parser import (  # noqa: E402
    ParsedModelOutputError,
    PolicySchemaError,
    parse_model_json,
)


# ─── Reporting helpers ──────────────────────────────────────────────────────

class Result:
    def __init__(self, run_id: str, name: str):
        self.run_id = run_id
        self.name = name
        self.status: str = "PENDING"
        self.detail: str = ""
        self.duration_ms: int = 0
        self.parser_repair_used: bool = False
        self.quality_flags: list[dict] = []
        self.error: Exception | None = None

    def __repr__(self):
        flags_short = ",".join(f["flag"] for f in self.quality_flags) or "-"
        return (
            f"[{self.status:4s}] {self.run_id:>3s} {self.name:<48s} "
            f"{self.duration_ms:>5d}ms  flags={flags_short}  {self.detail}"
        )


RESULTS: list[Result] = []


def _run(run_id: str, name: str):
    """Decorator-style context: time + capture + record."""
    class _Ctx:
        def __init__(self):
            self.result = Result(run_id, name)
        def __enter__(self):
            self.start = time.perf_counter()
            RESULTS.append(self.result)
            return self.result
        def __exit__(self, exc_type, exc, tb):
            self.result.duration_ms = int((time.perf_counter() - self.start) * 1000)
            if self.result.status == "PENDING":
                # Wasn't explicitly set inside the block -> default by exc state
                self.result.status = "FAIL" if exc else "PASS"
            if exc:
                self.result.error = exc
                self.result.detail = f"{exc.__class__.__name__}: {exc}"
                # Swallow the exception so we keep running the remaining scenarios
                return True
            return False
    return _Ctx()


# ─── Mocked Anthropic helpers ───────────────────────────────────────────────

class _FakeBlock:
    def __init__(self, text: str):
        self.text = text
        self.type = "text"


class _FakeMessage:
    def __init__(self, text: str, stop_reason: str = "end_turn"):
        self.content = [_FakeBlock(text)]
        self.stop_reason = stop_reason


class _ScriptedMessages:
    """messages.create() pops the next scripted response from the queue."""
    def __init__(self, queue: list[_FakeMessage]):
        self._queue = list(queue)
        self.calls: list[dict] = []
    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._queue:
            raise RuntimeError("Scripted Anthropic client ran out of responses")
        return self._queue.pop(0)


class _ScriptedClient:
    def __init__(self, responses: list[_FakeMessage]):
        self.messages = _ScriptedMessages(responses)


# ─── Fixture helpers ────────────────────────────────────────────────────────

_FAT_BODY = (
    "This policy establishes operational, technical, and administrative "
    "requirements for the program. It applies to all personnel, contractors, "
    "and authorized third parties. Compliance is mandatory and tracked "
    "through quarterly review cycles documented by the security team and "
    "reviewed annually by leadership."
)


def _make_request(policy_name: str = "Test Policy",
                  doc_type: str = "POLICY",
                  frameworks: list[str] | None = None) -> CreatePolicyRequest:
    return CreatePolicyRequest(
        policy_name=policy_name,
        doc_type=doc_type,
        industry="Technology",
        frameworks=frameworks or ["SOC_2"],
        owner="Security Lead",
    )


_DEFAULT = object()


def _metadata_json(title: str = "Test Policy",
                   selected_frameworks=_DEFAULT,
                   omit: set | None = None) -> str:
    # Sentinel pattern so an explicit empty list isn't collapsed back to
    # the default by `selected_frameworks or [...]`.
    frameworks = ["SOC_2"] if selected_frameworks is _DEFAULT else selected_frameworks
    omit = omit or set()
    obj = {
        "title": title,
        "organization": "Test Org",
        "owner": "Security Lead",
        "document_type": "Policy",
        "status": "Draft",
        "schema_version": "1.0",
        "selected_frameworks": frameworks,
    }
    for k in omit:
        obj.pop(k, None)
    return json.dumps(obj)


# ─-- 15 mocked scenarios --──────────────────────────────────────────────────

def scenario_01_clean_happy_path():
    raw = _metadata_json(title="Acceptable Use Policy", selected_frameworks=["SOC_2"])
    parsed = parse_model_json(raw)
    meta = _validate_policy_metadata(parsed, request=_make_request(), organization_hint="Test Org", normalized_frameworks=["SOC_2"])
    return {"ok": True, "title": meta["title"], "frameworks": meta["selected_frameworks"]}


def scenario_02_prose_wrapped():
    raw = (
        "Here is your metadata:\n\n```json\n"
        + _metadata_json(title="IT Asset Disposal Policy", selected_frameworks=["HIPAA","HITRUST"])
        + "\n```\nLet me know if you want changes."
    )
    parsed = parse_model_json(raw)
    meta = _validate_policy_metadata(parsed, request=_make_request(policy_name="IT Asset Disposal Policy", frameworks=["HIPAA","HITRUST"]), organization_hint="Test Org", normalized_frameworks=["HIPAA","HITRUST"])
    return {"ok": True, "title": meta["title"]}


def scenario_03_trailing_commas_smart_quotes():
    raw = (
        '{\n'
        '  “title”: “Trailing Comma Policy”,\n'
        '  “organization”: “Test Org”,\n'
        '  “owner”: “Sec Lead”,\n'
        '  “document_type”: “Policy”,\n'
        '  “status”: “Draft”,\n'
        '  “schema_version”: “1.0”,\n'
        '  “selected_frameworks”: [“SOC_2”,],\n'
        '}'
    )
    parsed = parse_model_json(raw)
    meta = _validate_policy_metadata(parsed, request=_make_request(), organization_hint="Test Org", normalized_frameworks=["SOC_2"])
    return {"ok": True}


def scenario_04_unquoted_keys():
    raw = (
        "{title: \"Unquoted Keys Policy\", organization: \"Test Org\", "
        "owner: \"X\", document_type: \"Policy\", status: \"Draft\", "
        "schema_version: \"1.0\", selected_frameworks: [\"SOC_2\"]}"
    )
    parsed = parse_model_json(raw)
    meta = _validate_policy_metadata(parsed, request=_make_request(), organization_hint="Test Org", normalized_frameworks=["SOC_2"])
    return {"ok": True}


def scenario_05_unrecognized_framework_rejected():
    raw = _metadata_json(selected_frameworks=["HIPAA", "MARS_2024"])
    parsed = parse_model_json(raw)
    try:
        _validate_policy_metadata(parsed, request=_make_request(), organization_hint="Test Org", normalized_frameworks=["HIPAA"])
    except HTTPException as exc:
        if exc.status_code == 422 and "MARS_2024" in exc.detail:
            return {"ok": True, "expected_422": True}
        raise AssertionError(f"Expected 422 with MARS_2024 detail, got {exc.status_code}: {exc.detail}")
    raise AssertionError("Validator should have raised 422")


def scenario_06_empty_frameworks_rejected():
    raw = _metadata_json(selected_frameworks=[])
    parsed = parse_model_json(raw)
    try:
        _validate_policy_metadata(parsed, request=_make_request(), organization_hint="Test Org", normalized_frameworks=[])
    except HTTPException as exc:
        if exc.status_code == 422 and "non-empty" in exc.detail.lower():
            return {"ok": True, "expected_422": True}
        raise AssertionError(f"Expected 422 non-empty, got {exc.status_code}: {exc.detail}")
    raise AssertionError("Validator should have raised 422")


def scenario_07_missing_title_rejected():
    # Construct metadata with empty title AND blank request.policy_name fallback.
    raw = json.dumps({
        "title": "",
        "organization": "Test Org",
        "owner": "X",
        "document_type": "Policy",
        "status": "Draft",
        "schema_version": "1.0",
        "selected_frameworks": ["SOC_2"],
    })
    parsed = parse_model_json(raw)
    try:
        _validate_policy_metadata(parsed, request=_make_request(policy_name="   "), organization_hint="", normalized_frameworks=["SOC_2"])
    except HTTPException as exc:
        if exc.status_code == 422 and "title" in exc.detail.lower():
            return {"ok": True, "expected_422": True}
        raise AssertionError(f"Expected 422 title, got {exc.status_code}: {exc.detail}")
    raise AssertionError("Validator should have raised 422")


def scenario_08_four_thin_sections_fail_thin():
    sections = [
        {"slot_id": "purpose", "heading": "Purpose", "content": "short"},          # thin
        {"slot_id": "scope", "heading": "Scope", "content": "short"},              # thin
        {"slot_id": "defs", "heading": "Definitions", "content": "short"},         # thin
        {"slot_id": "roles", "heading": "Roles", "content": "short"},              # thin
        {"slot_id": "policy_statement", "heading": "PS", "content": _FAT_BODY},
        {"slot_id": "standards", "heading": "Std", "content": _FAT_BODY},
        {"slot_id": "procedures", "heading": "Proc", "content": _FAT_BODY},
        {"slot_id": "compliance", "heading": "Comp", "content": _FAT_BODY},
        {"slot_id": "approval", "heading": "Appr", "content": _FAT_BODY},
    ]
    flags = _compute_quality_flags(sections=sections, tenant_id="t", policy_id="p")
    flag_ids = [f["flag"] for f in flags]
    if flag_ids.count("thin_section") == 4 and "fail_thin" in flag_ids:
        return {"ok": True, "flag_count": len(flags), "flag_ids": flag_ids}
    raise AssertionError(f"Expected 4 thin + fail_thin, got {flag_ids}")


def scenario_09_broken_placeholder_section():
    sections = [{"slot_id": "scope", "heading": "Scope", "content": "{{org_name}}"}]
    sections += [
        {"slot_id": f"s{i}", "heading": f"S{i}", "content": _FAT_BODY}
        for i in range(8)
    ]
    flags = _compute_quality_flags(sections=sections, tenant_id="t", policy_id="p")
    flag_ids = [f["flag"] for f in flags]
    if "broken_section" in flag_ids:
        return {"ok": True, "flag_ids": flag_ids}
    raise AssertionError(f"Expected broken_section flag, got {flag_ids}")


def scenario_10_two_sections_thin_policy():
    sections = [
        {"slot_id": "purpose", "heading": "Purpose", "content": _FAT_BODY},
        {"slot_id": "scope", "heading": "Scope", "content": _FAT_BODY},
    ]
    flags = _compute_quality_flags(sections=sections, tenant_id="t", policy_id="p")
    flag_ids = [f["flag"] for f in flags]
    if "thin_policy" in flag_ids:
        return {"ok": True, "flag_ids": flag_ids}
    raise AssertionError(f"Expected thin_policy flag, got {flag_ids}")


def scenario_11_truncation_triggers_repair_then_succeeds():
    """Anthropic returns max_tokens stop on attempt 1; succeeds on attempt 2."""
    truncated = _metadata_json()[: 100]  # cut off mid-JSON
    full = _metadata_json(title="Recovered After Truncation")
    client = _ScriptedClient([
        _FakeMessage(truncated, stop_reason="max_tokens"),
        _FakeMessage(full, stop_reason="end_turn"),
    ])
    # Patch _get_anthropic_client briefly
    import backend.api.routes as routes_mod
    real = routes_mod._get_anthropic_client
    routes_mod._get_anthropic_client = lambda: client
    try:
        result = _call_model_json_object(
            system_prompt="sys",
            user_prompt="usr",
            flow="ship_gate_truncation",
            context={},
            max_tokens=100,
        )
    finally:
        routes_mod._get_anthropic_client = real
    if result["title"] == "Recovered After Truncation" and len(client.messages.calls) == 2:
        return {"ok": True, "repair_used": True, "anthropic_calls": 2}
    raise AssertionError(f"Repair pass didn't recover correctly: {result}")


def scenario_12_truncation_persistent_502():
    """Both attempts truncate; should raise HTTPException(502) after repair."""
    truncated = _metadata_json()[: 50]
    client = _ScriptedClient([
        _FakeMessage(truncated, stop_reason="max_tokens"),
        _FakeMessage(truncated, stop_reason="max_tokens"),
    ])
    import backend.api.routes as routes_mod
    real = routes_mod._get_anthropic_client
    routes_mod._get_anthropic_client = lambda: client
    try:
        try:
            _call_model_json_object(
                system_prompt="sys",
                user_prompt="usr",
                flow="ship_gate_persistent_trunc",
                context={},
                max_tokens=50,
            )
        except HTTPException as exc:
            if exc.status_code == 502:
                return {"ok": True, "expected_502": True, "anthropic_calls": len(client.messages.calls)}
            raise AssertionError(f"Expected 502, got {exc.status_code}")
    finally:
        routes_mod._get_anthropic_client = real
    raise AssertionError("Should have raised 502")


def scenario_13_multi_framework_valid():
    raw = _metadata_json(selected_frameworks=["HIPAA", "PCI_DSS", "SOC_2"])
    parsed = parse_model_json(raw)
    meta = _validate_policy_metadata(parsed, request=_make_request(frameworks=["HIPAA","PCI_DSS","SOC_2"]), organization_hint="Test Org", normalized_frameworks=["HIPAA","PCI_DSS","SOC_2"])
    if sorted(meta["selected_frameworks"]) == ["HIPAA", "PCI_DSS", "SOC_2"]:
        return {"ok": True, "frameworks": meta["selected_frameworks"]}
    raise AssertionError(f"Unexpected: {meta['selected_frameworks']}")


def scenario_14_loose_framework_forms_canonicalize():
    raw = _metadata_json(selected_frameworks=["soc 2", "pci-dss", "ISO 27001"])
    parsed = parse_model_json(raw)
    meta = _validate_policy_metadata(parsed, request=_make_request(frameworks=["SOC_2","PCI_DSS","ISO_27001"]), organization_hint="Test Org", normalized_frameworks=["SOC_2","PCI_DSS","ISO_27001"])
    if sorted(meta["selected_frameworks"]) == ["ISO_27001", "PCI_DSS", "SOC_2"]:
        return {"ok": True, "canonicalized": meta["selected_frameworks"]}
    raise AssertionError(f"Canonicalization failed: {meta['selected_frameworks']}")


def scenario_15_section_validator_rejects_long_content():
    """A section body over the SECTION_CONTENT_LIMIT raises PolicySchemaError.
    Confirms graceful behavior (caller catches + records section_error)."""
    from backend.api.routes import SECTION_CONTENT_LIMIT
    long_content = "x" * (SECTION_CONTENT_LIMIT + 10)
    slot_spec = POLICY_SLOT_SPECS[0]
    try:
        _validate_generated_section(
            {"slot_id": slot_spec["slot_id"], "heading": slot_spec["heading"], "content": long_content},
            slot_spec=slot_spec,
        )
    except PolicySchemaError as exc:
        if "exceeded" in str(exc).lower():
            return {"ok": True, "expected_PolicySchemaError": True}
        raise AssertionError(f"Wrong error message: {exc}")
    raise AssertionError("Validator should have rejected oversized content")


MOCKED_SCENARIOS = [
    ("m01", "clean happy path",                        scenario_01_clean_happy_path),
    ("m02", "prose-wrapped (IT Asset Disposal shape)", scenario_02_prose_wrapped),
    ("m03", "trailing commas + smart quotes",          scenario_03_trailing_commas_smart_quotes),
    ("m04", "unquoted keys",                           scenario_04_unquoted_keys),
    ("m05", "unrecognized framework rejected (422)",   scenario_05_unrecognized_framework_rejected),
    ("m06", "empty frameworks rejected (422)",         scenario_06_empty_frameworks_rejected),
    ("m07", "missing title rejected (422)",            scenario_07_missing_title_rejected),
    ("m08", "4 thin sections -> fail_thin",            scenario_08_four_thin_sections_fail_thin),
    ("m09", "broken placeholder -> broken_section",    scenario_09_broken_placeholder_section),
    ("m10", "2 sections -> thin_policy",               scenario_10_two_sections_thin_policy),
    ("m11", "truncation -> repair pass succeeds",      scenario_11_truncation_triggers_repair_then_succeeds),
    ("m12", "persistent truncation -> 502",            scenario_12_truncation_persistent_502),
    ("m13", "multi-framework HIPAA+PCI_DSS+SOC_2",     scenario_13_multi_framework_valid),
    ("m14", "loose framework forms canonicalize",      scenario_14_loose_framework_forms_canonicalize),
    ("m15", "oversized section rejected",              scenario_15_section_validator_rejects_long_content),
]


# ─── 5 real Anthropic metadata-only generations ─────────────────────────────

REAL_RUNS = [
    ("r01", "Acceptable Use Policy",       ["SOC_2"]),
    ("r02", "Incident Response Policy",    ["HIPAA", "NIST_CSF"]),
    ("r03", "Data Classification Policy",  ["ISO_27001", "SOC_2"]),
    ("r04", "Vendor Management Policy",    ["HITRUST", "SOC_2"]),
    ("r05", "AI Governance Policy",        ["NIST_CSF"]),
]


def _run_real_metadata(policy_name: str, frameworks: list[str]) -> dict:
    """Hit real Anthropic for ONE metadata call, parse, validate. Returns
    metadata + a flag indicating whether the repair pass fired."""
    request = _make_request(policy_name=policy_name, frameworks=frameworks)
    # Import the prompt builder
    from backend.api.routes import _build_metadata_prompt
    prompt = _build_metadata_prompt(request, organization_hint="ShipGate Test Org", normalized_frameworks=frameworks)

    # We need to detect whether the repair pass fires inside
    # _call_model_json_object. Instrument by wrapping _get_anthropic_client.
    import backend.api.routes as routes_mod
    call_count = {"n": 0}
    real_factory = routes_mod._get_anthropic_client
    real_client = real_factory()

    class _CountingMessages:
        def __init__(self, inner):
            self._inner = inner
        def create(self, **kwargs):
            call_count["n"] += 1
            return self._inner.create(**kwargs)

    class _CountingClient:
        def __init__(self, inner):
            self.messages = _CountingMessages(inner.messages)

    routes_mod._get_anthropic_client = lambda: _CountingClient(real_client)
    try:
        metadata_raw = _call_model_json_object(
            system_prompt="You are Midnight's policy metadata generator. Return JSON only.",
            user_prompt=prompt,
            flow="ship_gate_real",
            context={"policy_name": policy_name},
            max_tokens=700,
        )
    finally:
        routes_mod._get_anthropic_client = real_factory

    metadata = _validate_policy_metadata(
        metadata_raw,
        request=request,
        organization_hint="ShipGate Test Org",
        normalized_frameworks=frameworks,
    )
    return {
        "ok": True,
        "title": metadata["title"],
        "frameworks": metadata["selected_frameworks"],
        "anthropic_calls": call_count["n"],
        "repair_used": call_count["n"] > 1,
    }


# ─── Run everything ─────────────────────────────────────────────────────────

def main():
    print("=" * 100)
    print("P0 ENGINE LOCKDOWN — SHIP GATE (Option C: 15 mocked + 5 real)")
    print("=" * 100)

    print("\n-- 15 mocked scenarios --")
    for run_id, name, fn in MOCKED_SCENARIOS:
        with _run(run_id, name) as r:
            payload = fn()
            r.status = "PASS"
            if isinstance(payload, dict):
                if payload.get("repair_used"):
                    r.parser_repair_used = True
                # collect quality_flags context for the 4 thin-section cases
                if "flag_ids" in payload:
                    r.quality_flags = [{"flag": fid} for fid in payload["flag_ids"]]
                r.detail = json.dumps({k: v for k, v in payload.items() if k != "ok"}, default=str)[:120]
        print("  " + repr(RESULTS[-1]))

    print("\n-- 5 real Anthropic metadata generations --")
    for run_id, policy_name, frameworks in REAL_RUNS:
        with _run(run_id, f"REAL: {policy_name}") as r:
            payload = _run_real_metadata(policy_name, frameworks)
            r.status = "PASS"
            r.parser_repair_used = payload.get("repair_used", False)
            r.detail = (
                f"title={payload['title'][:40]} "
                f"frameworks={payload['frameworks']} "
                f"anthropic_calls={payload['anthropic_calls']}"
            )
        print("  " + repr(RESULTS[-1]))

    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    total = len(RESULTS)
    passed = sum(1 for r in RESULTS if r.status == "PASS")
    failed = total - passed
    repairs = sum(1 for r in RESULTS if r.parser_repair_used)
    expected_repairs = 1  # scenario_11 deliberately exercises the repair pass

    print(f"  Total runs        : {total}")
    print(f"  Passed            : {passed}")
    print(f"  Failed            : {failed}")
    print(f"  Repair-pass fires : {repairs}  (expected = {expected_repairs}, from scenario m11)")

    unexpected_repairs = [r for r in RESULTS if r.parser_repair_used and r.run_id != "m11"]
    if unexpected_repairs:
        print(f"\n  UNEXPECTED repair-pass invocations:")
        for r in unexpected_repairs:
            print(f"    - {r.run_id}: {r.name}")

    if failed:
        print(f"\n  FAILURES:")
        for r in RESULTS:
            if r.status != "PASS":
                print(f"    - {r.run_id} {r.name}")
                print(f"      {r.detail}")

    print()
    overall = "PASS" if (failed == 0 and len(unexpected_repairs) == 0) else "FAIL"
    print(f"  Overall ship-gate status: {overall}")
    print("=" * 100)
    sys.exit(0 if overall == "PASS" else 1)


if __name__ == "__main__":
    main()
