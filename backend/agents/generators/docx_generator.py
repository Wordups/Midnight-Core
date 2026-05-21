"""Python wrapper around build_docx.js — runs Node as a subprocess.

The spec dict produced by Trace Agent step 8 (build_script) is serialized
as JSON, piped to `node build_docx.js <output_path>`, and the resulting
file is read back. The Node side handles all docx-js calls; this module
never touches python-docx (by design — see the Phase 0 markdown-bleed
work).
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("midnight.trace_agent.docx_generator")

GENERATOR_DIR = Path(__file__).resolve().parent
BUILD_SCRIPT = GENERATOR_DIR / "build_docx.js"


class DocxGenerationError(RuntimeError):
    """Raised when the Node subprocess fails or returns a malformed result."""


def _resolve_node_executable() -> str:
    """Find the `node` binary, preferring whatever is on PATH."""
    env_node = os.environ.get("MIDNIGHT_NODE_BIN")
    if env_node and Path(env_node).exists():
        return env_node
    on_path = shutil.which("node")
    if on_path:
        return on_path
    raise DocxGenerationError(
        "Node.js executable not found. Install Node 20.x and ensure `node` is on PATH, "
        "or set MIDNIGHT_NODE_BIN to the absolute path."
    )


def _ensure_dependencies_installed() -> None:
    """Verify that `node_modules/docx` is present. If not, run `npm install`
    on first use. This keeps the generator self-bootstrapping in dev; in
    prod the Dockerfile runs npm install at image build time."""
    node_modules = GENERATOR_DIR / "node_modules" / "docx"
    if node_modules.exists():
        return
    npm = shutil.which("npm")
    if not npm:
        raise DocxGenerationError(
            "npm not found on PATH and node_modules/docx not pre-installed. "
            "Run `npm install` in backend/agents/generators/ once."
        )
    logger.info("npm_install_first_run", extra={"cwd": str(GENERATOR_DIR)})
    proc = subprocess.run(
        [npm, "install", "--no-audit", "--no-fund", "--loglevel=error"],
        cwd=str(GENERATOR_DIR),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        raise DocxGenerationError(
            f"npm install failed (rc={proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
        )


def generate_docx(*, spec: dict[str, Any], output_path: str | Path, timeout_sec: int = 60) -> dict[str, Any]:
    """Render a .docx from a structured spec.

    Args:
        spec: Dict with keys title, subtitle, frontMatter, sections (see
            build_docx.js for the shape).
        output_path: Where to write the .docx. Parent dir is created.
        timeout_sec: Hard timeout for the subprocess.

    Returns:
        Dict with {ok, docx_path, bytes, section_count} from the Node side.

    Raises:
        DocxGenerationError: subprocess failed, malformed stdout, missing
            output, or zero-byte output.
    """
    if not BUILD_SCRIPT.exists():
        raise DocxGenerationError(f"build_docx.js missing at {BUILD_SCRIPT}")
    if not isinstance(spec, dict):
        raise DocxGenerationError("spec must be a dict matching the documented shape.")

    _ensure_dependencies_installed()
    node = _resolve_node_executable()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    spec_json = json.dumps(spec, ensure_ascii=False)
    try:
        # Pin encoding='utf-8' on both stdin AND stdout/stderr. Without it,
        # subprocess uses locale.getpreferredencoding(False), which on Windows
        # defaults to cp1252. The Node side reads stdin as UTF-8 (see
        # build_docx.js: process.stdin.setEncoding('utf8')), so any non-ASCII
        # character in the spec (em-dash, smart quote, en-dash, ...) round-trips
        # as U+FFFD because cp1252 encodes them to bytes that aren't valid
        # UTF-8. On Linux this works by accident (locale is usually UTF-8),
        # but pinning makes the behavior identical everywhere.
        proc = subprocess.run(
            [node, str(BUILD_SCRIPT), str(output_path)],
            input=spec_json,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_sec,
            cwd=str(GENERATOR_DIR),
        )
    except subprocess.TimeoutExpired as exc:
        raise DocxGenerationError(
            f"docx-js subprocess timed out after {timeout_sec}s"
        ) from exc

    if proc.returncode != 0:
        raise DocxGenerationError(
            f"docx-js subprocess failed (rc={proc.returncode}): {proc.stderr.strip()[:2000]}"
        )

    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise DocxGenerationError(
            f"docx-js subprocess returned malformed stdout: {proc.stdout[:500]!r}"
        ) from exc

    if not result.get("ok"):
        raise DocxGenerationError(f"docx-js reported failure: {result}")

    if not output_path.exists():
        raise DocxGenerationError(f"docx-js claimed success but {output_path} is missing")
    if output_path.stat().st_size == 0:
        raise DocxGenerationError(f"docx-js produced empty file at {output_path}")

    result["docx_path"] = str(output_path)
    return result
