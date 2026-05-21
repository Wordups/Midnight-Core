"""Trace Agent generator backends.

`docx_generator` wraps the docx-js (`docx` npm package, v9.x) Node script
in `build_docx.js` via subprocess. This keeps native Word formatting on
the Node side and avoids the python-docx markdown-bleed failure mode the
Phase 0 work hardened against."""
