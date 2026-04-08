"""
Midnight Core — Pipeline Routes
Takeoff LLC

POST /pipeline/migrate   → upload + transform existing doc
POST /pipeline/create    → create new doc from intake
POST /pipeline/analyze   → gap analysis on uploaded doc
"""
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

class CreatePolicyRequest(BaseModel):
    policy_name: str
    doc_type: str
    industry: str
    frameworks: list[str]
    owner: str
    description: Optional[str] = None

@router.post("/migrate")
async def migrate_document(file: UploadFile = File(...), template: str = "generic_policy"):
    # TODO: extractor → transformer → framework_mapper → gap_engine → renderer
    return {"status": "received", "filename": file.filename, "template": template}

@router.post("/create")
async def create_document(request: CreatePolicyRequest):
    # TODO: template_engine → renderer
    return {"status": "received", "policy_name": request.policy_name}

@router.post("/analyze")
async def analyze_document(file: UploadFile = File(...), frameworks: str = "HIPAA,PCI DSS,NIST CSF"):
    fw_list = [f.strip() for f in frameworks.split(",")]
    # TODO: extractor → framework_mapper → gap_engine
    return {"status": "received", "frameworks": fw_list}
