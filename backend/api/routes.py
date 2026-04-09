"""
Midnight Core — Pipeline Routes
Takeoff LLC
"""
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import os
from groq import Groq
import docx2txt
import json

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

FRAMEWORK_PROMPT = """
You are a senior GRC consultant and compliance architect with 15 years of enterprise experience. 
You have been given extracted text from a policy or compliance document.

Analyze this document against the following frameworks: {frameworks}

For EACH framework provide:
1. A coverage score (0-100)
2. A detailed 2-3 paragraph analysis that covers:
   - What the document does well relative to this framework
   - Specific gaps or missing controls with control IDs where applicable
   - Concrete remediation recommendations a compliance team can act on immediately
3. A list of the top 3 critical gaps with severity (Critical/High/Medium)

Write like a compliance consultant presenting findings to a CISO — specific, direct, and actionable. 
Never be vague. Reference actual control IDs (e.g. HIPAA 164.308, PCI DSS 3.4, NIST PR.AC-1).

Return ONLY valid JSON in this exact structure:
{{
  "overall_score": 0-100,
  "frameworks": {{
    "FRAMEWORK_NAME": {{
      "score": 0-100,
      "analysis": "detailed paragraph analysis here",
      "critical_gaps": [
        {{
          "control_id": "e.g. HIPAA 164.308(a)(1)",
          "description": "specific gap description",
          "severity": "Critical|High|Medium",
          "recommendation": "specific action to take"
        }}
      ]
    }}
  }},
  "executive_summary": "2-3 paragraph executive summary of overall compliance posture"
}}
"""

class CreatePolicyRequest(BaseModel):
    policy_name: str
    doc_type: str
    industry: str
    frameworks: list[str]
    owner: str
    description: Optional[str] = None

@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    frameworks: str = "HIPAA,PCI DSS,NIST CSF"
):
    # Step 1 — Extract text from uploaded doc
    contents = await file.read()
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(contents)

    try:
        extracted_text = docx2txt.process(temp_path)
    except Exception as e:
        return {"status": "error", "message": f"Could not extract text: {str(e)}"}

    if not extracted_text or len(extracted_text.strip()) < 50:
        return {"status": "error", "message": "Document appears empty or unreadable"}

    # Step 2 — Build framework list
    fw_list = [f.strip() for f in frameworks.split(",")]
    fw_string = ", ".join(fw_list)

    # Step 3 — Send to Groq
    prompt = FRAMEWORK_PROMPT.format(frameworks=fw_string)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Document text:\n\n{extracted_text[:8000]}"}
            ],
            temperature=0.3,
            max_tokens=4000
        )

        raw = response.choices[0].message.content
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)

        return {
            "status": "success",
            "filename": file.filename,
            "frameworks_analyzed": fw_list,
            "report": result
        }

    except json.JSONDecodeError:
        return {
            "status": "partial",
            "raw_analysis": raw,
            "message": "Analysis complete but could not parse as JSON"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/migrate")
async def migrate_document(
    file: UploadFile = File(...),
    template: str = "generic_policy"
):
    # TODO: extractor → transformer → framework_mapper → gap_engine → renderer
    return {"status": "received", "filename": file.filename, "template": template}

@router.post("/create")
async def create_document(request: CreatePolicyRequest):
    # TODO: template_engine → renderer
    return {"status": "received", "policy_name": request.policy_name}
