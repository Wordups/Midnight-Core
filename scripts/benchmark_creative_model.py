"""
Benchmark the creative-tier model for policy prose (Wave C).

Compares a baseline creative model against a candidate (e.g. claude-fable-5) on
the same policy-section prompt: latency, tokens, and estimated cost per section.
Structural sections stay on Haiku — this only measures the creative tier so you
can decide whether the prose/citation gain justifies the cost.

Run manually (needs a valid ANTHROPIC_API_KEY; costs a few cents):
    python scripts/benchmark_creative_model.py
    python scripts/benchmark_creative_model.py --baseline claude-opus-4-8 --candidate claude-fable-5 --runs 3

Not a pytest test — it makes live API calls.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

# Price per 1M tokens (input, output) — keep in sync with the catalog.
PRICING = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-fable-5": (10.0, 50.0),
}

SYSTEM = "You are Midnight's policy section generator. Write precise, auditor-grade compliance prose."
PROMPT = (
    "Write the 'Purpose' and 'Policy Statement' sections of an Access Control Policy for a "
    "healthcare SaaS company subject to HIPAA (45 CFR 164.312) and SOC 2 (CC6.1). "
    "Be specific, cite the relevant control ids accurately, and do not invent controls."
)


def _estimate_cost(model: str, in_tok: int, out_tok: int) -> float:
    pin, pout = PRICING.get(model, (0.0, 0.0))
    return (in_tok / 1_000_000) * pin + (out_tok / 1_000_000) * pout


def _run_once(client, model: str) -> tuple[float, int, int, str]:
    t0 = time.time()
    msg = client.messages.create(
        model=model, max_tokens=1100, system=SYSTEM,
        messages=[{"role": "user", "content": PROMPT}],
    )
    elapsed = time.time() - t0
    text = "".join(getattr(b, "text", "") for b in getattr(msg, "content", []) or [])
    usage = getattr(msg, "usage", None)
    return elapsed, getattr(usage, "input_tokens", 0), getattr(usage, "output_tokens", 0), text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default=os.getenv("CREATIVE_MODEL", "claude-opus-4-8"))
    ap.add_argument("--candidate", default="claude-fable-5")
    ap.add_argument("--runs", type=int, default=2)
    args = ap.parse_args()

    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        print("ANTHROPIC_API_KEY not set — cannot benchmark.", file=sys.stderr)
        return 2

    import anthropic
    client = anthropic.Anthropic(api_key=key, timeout=120.0, max_retries=2)

    for model in (args.baseline, args.candidate):
        lat, cin, cout, costs = [], 0, 0, 0.0
        sample = ""
        try:
            for _ in range(args.runs):
                elapsed, itok, otok, text = _run_once(client, model)
                lat.append(elapsed); cin += itok; cout += otok
                costs += _estimate_cost(model, itok, otok); sample = text
        except Exception as exc:  # noqa: BLE001
            print(f"\n{model}: FAILED — {type(exc).__name__}: {exc}")
            continue
        avg_lat = sum(lat) / len(lat) if lat else 0
        print(f"\n=== {model} ({args.runs} runs) ===")
        print(f"  avg latency : {avg_lat:.1f}s")
        print(f"  avg tokens  : in {cin // args.runs}, out {cout // args.runs}")
        print(f"  avg cost/section: ${costs / args.runs:.4f}")
        print(f"  sample (first 240 chars): {sample[:240].strip()!r}")

    print("\nDecision guide: adopt the candidate on the creative tier only if prose/citation")
    print("quality is clearly better AND cost/section stays acceptable. Keep Haiku on structural.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
