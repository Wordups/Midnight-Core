"""
backend/api/smart_scan.py
Midnight Core — Smart Scan (Bird Eye) Router
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.core.smart_scan_engine import (
    run_smart_scan,
    run_smart_scan_preflight,
    learn_template,
    REQUIRED_SECTIONS,
    SmartScanResult,
)

router = APIRouter(prefix="/api/smart-scan", tags=["Smart Scan"])


def _validate_docx(file: UploadFile) -> None:
    if not file.filename.endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail=f"Smart Scan requires .docx files. Got: '{file.filename}'"
        )


def _quality_warning(score: int) -> str | None:
    if score < 30:
        return (
            "Source document quality is critically low. "
            "Midnight rebuilt what it could and flagged all gaps. "
            "This reflects your current policy state — not a system error."
        )
    if score < 55:
        return (
            "Source document is weakly structured. "
            "Several required sections are missing or incomplete. "
            "Review flagged gaps before using for audit purposes."
        )
    return None


def _priority_gaps(result: SmartScanResult) -> list[dict]:
    severity_map = {"policy_statement": "critical", "procedures": "critical"}
    return [
        {
            "section":  s.replace("_", " ").title(),
            "severity": severity_map.get(s, "high"),
            "action":   f"Generate {s.replace('_', ' ')} section",
        }
        for s in REQUIRED_SECTIONS
        if s in result.missing_sections
    ][:3]


def _build_output(result: SmartScanResult, meta: dict) -> dict:
    output                  = result.to_dict()
    output["priority_gaps"] = _priority_gaps(result)
    output["meta"]          = meta
    warning = _quality_warning(result.quality_score)
    if warning:
        output["source_quality_warning"] = warning
    return output


# ---------------------------------------------------------------------------
# POST /api/smart-scan/preflight
# Single-file scan. No template needed. Called from Migrate Document.
# ---------------------------------------------------------------------------

@router.post("/preflight")
async def preflight_scan(
    source_doc: UploadFile = File(...),
    tenant_id:  str        = Form(default="default"),
    doc_type:   str        = Form(default="policy"),
    industry:   str        = Form(default=""),
):
    """Bird Eye pre-flight — runs against built-in schema. No template required."""
    _validate_docx(source_doc)
    source_bytes = await source_doc.read()
    if not source_bytes:
        raise HTTPException(status_code=400, detail="Source document is empty.")

    try:
        result: SmartScanResult = await run_smart_scan_preflight(
            source_bytes=source_bytes,
            source_filename=source_doc.filename,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bird Eye error: {str(e)}")

    return JSONResponse(content=_build_output(result, {
        "source_filename": source_doc.filename,
        "tenant_id":       tenant_id,
        "doc_type":        doc_type,
        "industry":        industry,
        "engine":          "Bird Eye",
        "mode":            "preflight",
    }))


# ---------------------------------------------------------------------------
# POST /api/smart-scan/run  (full scan with template)
# ---------------------------------------------------------------------------

@router.post("/run")
async def run_scan(
    source_doc:   UploadFile = File(...),
    template_doc: UploadFile = File(...),
    tenant_id:    str        = Form(default="default"),
    doc_type:     str        = Form(default="policy"),
    industry:     str        = Form(default=""),
):
    _validate_docx(source_doc)
    _validate_docx(template_doc)
    source_bytes   = await source_doc.read()
    template_bytes = await template_doc.read()
    if not source_bytes:
        raise HTTPException(status_code=400, detail="Source document is empty.")
    if not template_bytes:
        raise HTTPException(status_code=400, detail="Template document is empty.")

    try:
        result: SmartScanResult = await run_smart_scan(
            source_bytes=source_bytes,
            template_bytes=template_bytes,
            source_filename=source_doc.filename,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Smart Scan error: {str(e)}")

    return JSONResponse(content=_build_output(result, {
        "source_filename":   source_doc.filename,
        "template_filename": template_doc.filename,
        "tenant_id":         tenant_id,
        "doc_type":          doc_type,
        "industry":          industry,
        "engine":            "Bird Eye",
        "mode":              "full",
    }))


# ---------------------------------------------------------------------------
# POST /api/smart-scan/learn-template
# ---------------------------------------------------------------------------

@router.post("/learn-template")
async def learn_template_endpoint(
    template_doc: UploadFile = File(...),
    tenant_id:    str        = Form(default="default"),
):
    _validate_docx(template_doc)
    template_bytes = await template_doc.read()
    if not template_bytes:
        raise HTTPException(status_code=400, detail="Template document is empty.")
    schema = learn_template(template_bytes)
    return JSONResponse(content={
        "template_hash":      schema["hash"],
        "sections_detected":  len(schema["sections"]),
        "section_ids":        [s["id"]      for s in schema["sections"]],
        "unmatched_headings": [s["heading"] for s in schema["sections"] if not s["matched"]],
        "styles":             schema.get("styles", {}),
        "tenant_id":          tenant_id,
    })


# ---------------------------------------------------------------------------
# GET /api/smart-scan/health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    return {"status": "operational", "engine": "Smart Scan (Bird Eye)", "version": "core"}
