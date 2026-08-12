"""License-safe public artifact library for document creation context.

The library is deliberately a context map, not a warehouse of copyrighted
standard text. Restricted sources may provide IDs, themes, citations, and
Midnight-authored summaries, but their raw source text is filtered out before
LLM generation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PUBLIC_TEXT_STATUSES = {"public_domain", "open_license", "attribution_required"}
RESTRICTED_STATUSES = {"restricted", "unknown"}
REQUIRED_LICENSE_FIELDS = {
    "status",
    "allowed_uses",
    "blocked_uses",
    "max_quote_chars",
    "attribution_required",
    "source_license_url",
}
REQUIRED_ARTIFACT_FIELDS = {
    "id",
    "source_id",
    "title",
    "domain",
    "themes",
    "doc_types",
    "citation",
    "source_url",
    "license_policy",
    "midnight_summary",
}


@dataclass
class ArtifactLibrary:
    artifacts: list[dict[str, Any]]
    sources: dict[str, dict[str, Any]]

    @classmethod
    def from_dir(cls, artifact_dir: str | Path) -> "ArtifactLibrary":
        base = Path(artifact_dir)
        sources_path = base / "sources.json"
        artifacts_path = base / "normalized_artifacts.json"
        sources_raw = json.loads(sources_path.read_text(encoding="utf-8"))
        artifacts = json.loads(artifacts_path.read_text(encoding="utf-8"))
        sources = {source["source_id"]: source for source in sources_raw}

        resolved: list[dict[str, Any]] = []
        for artifact in artifacts:
            item = dict(artifact)
            source = sources.get(item.get("source_id"), {})
            if "license_policy" not in item and source.get("license_policy"):
                item["license_policy"] = dict(source["license_policy"])
            resolved.append(item)
        return cls(artifacts=resolved, sources=sources)

    def match(self, *, doc_type: str, themes: list[str], max_items: int = 12) -> list[dict[str, Any]]:
        wanted_doc_type = doc_type.strip().lower()
        wanted_themes = {_normalize(value) for value in themes if value}
        scored: list[tuple[int, dict[str, Any]]] = []
        for artifact in self.artifacts:
            doc_types = {_normalize(value) for value in artifact.get("doc_types", [])}
            artifact_themes = {_normalize(value) for value in artifact.get("themes", [])}
            domain = _normalize(str(artifact.get("domain", "")))

            score = 0
            if wanted_doc_type in doc_types or "any" in doc_types:
                score += 4
            elif wanted_doc_type and doc_types:
                continue

            theme_hits = wanted_themes & artifact_themes
            score += len(theme_hits) * 3
            if domain in wanted_themes:
                score += 2

            if score > 0:
                scored.append((score, artifact))

        scored.sort(key=lambda pair: (-pair[0], pair[1].get("source_id", ""), pair[1].get("id", "")))
        return [artifact for _, artifact in scored[:max_items]]


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", "-").replace("-", " ").split())


def lint_artifact_library(artifacts: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    seen_ids: set[str] = set()
    for idx, artifact in enumerate(artifacts):
        artifact_id = artifact.get("id") or f"<index:{idx}>"
        if artifact_id in seen_ids:
            issues.append(f"duplicate artifact id {artifact_id}")
        seen_ids.add(str(artifact_id))

        for field in REQUIRED_ARTIFACT_FIELDS:
            if field not in artifact or artifact[field] in (None, "", []):
                issues.append(f"artifact {artifact_id} missing required field {field}")

        policy = artifact.get("license_policy") or {}
        for field in REQUIRED_LICENSE_FIELDS:
            if field not in policy:
                issues.append(f"artifact {artifact_id} license_policy missing {field}")

        status = policy.get("status")
        if status not in PUBLIC_TEXT_STATUSES | RESTRICTED_STATUSES:
            issues.append(f"artifact {artifact_id} has unknown license status {status!r}")

        allowed_uses = set(policy.get("allowed_uses") or [])
        blocked_uses = set(policy.get("blocked_uses") or [])
        if allowed_uses & blocked_uses:
            issues.append(f"artifact {artifact_id} has overlapping allowed_uses and blocked_uses")

        if status in RESTRICTED_STATUSES:
            if artifact.get("raw_text"):
                issues.append(f"restricted artifact {artifact_id} must not include raw_text")
            if "quote_full_text" in allowed_uses or "redistribute" in allowed_uses:
                issues.append(f"restricted artifact {artifact_id} must not allow full quoting or redistribution")
            if int(policy.get("max_quote_chars") or 0) > 0:
                issues.append(f"restricted artifact {artifact_id} must set max_quote_chars to 0")

    return issues


def build_generation_context(
    library: ArtifactLibrary,
    *,
    doc_type: str,
    themes: list[str],
    max_items: int = 12,
) -> dict[str, Any]:
    """Return LLM-safe artifact context for document generation.

    Restricted sources are metadata/summary/citation only. Public/open sources may
    include bounded snippets if the artifact carries raw_text and the license
    policy allows snippet retrieval.
    """
    matched = library.match(doc_type=doc_type, themes=themes, max_items=max_items)
    safe_items = [_generation_safe_artifact(artifact) for artifact in matched]
    return {
        "doc_type": doc_type,
        "themes": themes,
        "artifacts": safe_items,
        "generation_guardrails": (
            "Use IDs, themes, citations, and Midnight-authored summaries as context. "
            "Do not quote, closely paraphrase, redistribute, or template-clone restricted sources. "
            "Generate original operational guidance tailored to the customer context. "
            "Use alignment language such as 'maps to', 'supports', or 'aligned with'; do not claim certification."
        ),
    }


def _generation_safe_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    policy = artifact["license_policy"]
    status = policy["status"]
    item = {
        "id": artifact["id"],
        "source_id": artifact["source_id"],
        "title": artifact["title"],
        "domain": artifact["domain"],
        "themes": artifact.get("themes", []),
        "doc_types": artifact.get("doc_types", []),
        "citation": artifact["citation"],
        "source_url": artifact["source_url"],
        "license_status": status,
        "allowed_uses": policy.get("allowed_uses", []),
        "blocked_uses": policy.get("blocked_uses", []),
        "max_quote_chars": int(policy.get("max_quote_chars") or 0),
        "attribution_required": bool(policy.get("attribution_required")),
        "midnight_summary": artifact["midnight_summary"],
    }

    raw_text = artifact.get("raw_text")
    if raw_text and status in PUBLIC_TEXT_STATUSES and "retrieve_snippet" in set(policy.get("allowed_uses") or []):
        item["raw_text"] = str(raw_text)[: item["max_quote_chars"]]

    return item
