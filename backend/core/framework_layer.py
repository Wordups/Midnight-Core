from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import json


FRAMEWORK_DIR = Path(__file__).resolve().parents[2] / "frameworks"

PUBLIC_FRAMEWORK_FILES = {
    "HIPAA": "hipaa.json",
    "NIST CSF": "nist.json",
    "PCI DSS": "pci.json",
    "SOC 2": "soc2.json",
}

FRAMEWORK_ALIASES = {
    "HIPAA": "HIPAA",
    "NIST": "NIST CSF",
    "NIST CSF": "NIST CSF",
    "PCI": "PCI DSS",
    "PCI DSS": "PCI DSS",
    "SOC2": "SOC 2",
    "SOC 2": "SOC 2",
    "SOC 2 TYPE II": "SOC 2",
    "HITRUST": "HITRUST",
    "HITRUST DOMAINS": "HITRUST",
    "HITRUST-ALIGNED DOMAINS": "HITRUST",
    "HITRUST ALIGNED DOMAINS": "HITRUST",
    "HITRUST V11": "HITRUST",
    "HITRUST V11.0": "HITRUST",
}

HITRUST_DOMAINS = [
    "Access Control",
    "Risk Management",
    "Vendor Management",
    "Logging & Monitoring",
    "Incident Response",
    "Data Protection",
]


@lru_cache(maxsize=1)
def load_public_frameworks() -> dict[str, list[dict]]:
    frameworks: dict[str, list[dict]] = {}
    for name, filename in PUBLIC_FRAMEWORK_FILES.items():
        path = FRAMEWORK_DIR / filename
        frameworks[name] = json.loads(path.read_text(encoding="utf-8"))
    return frameworks


def normalize_framework_name(name: str) -> str | None:
    value = (name or "").strip().upper()
    return FRAMEWORK_ALIASES.get(value)


def build_framework_prompt_context(selected_frameworks: list[str]) -> tuple[list[str], list[str]]:
    frameworks = load_public_frameworks()
    normalized: list[str] = []
    prompt_blocks: list[str] = []

    for requested in selected_frameworks:
        canonical = normalize_framework_name(requested)
        if not canonical or canonical in normalized:
            continue
        normalized.append(canonical)

        if canonical == "HITRUST":
            prompt_blocks.append(
                "HITRUST Domains (alignment only, not compliance): "
                + ", ".join(HITRUST_DOMAINS)
            )
            continue

        controls = frameworks.get(canonical, [])
        control_lines = [
            f"{control['id']} | {control['name']} | {control['category']} | {control['description']}"
            for control in controls
        ]
        prompt_blocks.append(f"{canonical} Controls:\n" + "\n".join(control_lines))

    return normalized, prompt_blocks


def build_framework_mapping_rules(selected_frameworks: list[str]) -> str:
    normalized, _ = build_framework_prompt_context(selected_frameworks)
    rules = [
        "Only map against provided framework controls. Do not invent new controls.",
        "If a requested framework has no matching evidence in the source, return an empty list for that framework.",
    ]
    if "HITRUST" in normalized:
        rules.append(
            "For HITRUST, do not claim compliance or certification. Use only HITRUST-aligned domains based on the provided domain list."
        )
    return " ".join(rules)
