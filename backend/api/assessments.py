import json
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from backend.api.routes import ANTHROPIC_MODEL, _get_anthropic_client
from backend.core.json_parser import ParsedModelOutputError, parse_model_json

logger = logging.getLogger("midnight.assessments")


router = APIRouter(prefix="/api/v1", tags=["assessments"])

MAX_TEXT_LENGTH = 50000

ASSESSMENT_PROMPT = """Assess the following text against the {framework} framework.

Return JSON only with no markdown fences, no commentary, and no prose before or after the JSON.

Return an object with this exact schema:
{{
  "risk_score": 72,
  "risk_band": "medium",
  "framework": "{framework}",
  "top_findings": [
    "Finding 1",
    "Finding 2",
    "Finding 3"
  ],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2",
    "Recommendation 3"
  ]
}}

Constraints:
- risk_score must be an integer from 0 to 100
- risk_band must be one of: low, medium, high, critical
- framework must be exactly "{framework}"
- top_findings must contain 3 to 5 concise strings
- recommendations must contain 3 to 5 concise strings
- recommendations must have the same number of items as top_findings
- findings should identify the most material control, policy, or governance weaknesses
- recommendations should be concrete next actions that address those findings

Scoring guidance:
- 0-24 = critical
- 25-49 = high
- 50-74 = medium
- 75-100 = low

Text to assess:
---
{text}
---"""


class AssessmentRequest(BaseModel):
    text: str
    framework: Literal["soc2", "hipaa"] = "soc2"

    @field_validator("framework", mode="before")
    @classmethod
    def normalize_framework(cls, value):
        if value is None:
            return "soc2"
        return str(value).strip().lower()

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("text is required")
        return cleaned


class AssessmentResponse(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_band: Literal["low", "medium", "high", "critical"]
    framework: Literal["soc2", "hipaa"]
    top_findings: list[str]
    recommendations: list[str]

    @field_validator("top_findings", "recommendations")
    @classmethod
    def validate_string_lists(cls, value: list[str]) -> list[str]:
        if not 3 <= len(value) <= 5:
            raise ValueError("lists must contain 3 to 5 items")

        cleaned_items: list[str] = []
        for item in value:
            cleaned = str(item).strip()
            if not cleaned:
                raise ValueError("list items must be non-empty strings")
            cleaned_items.append(cleaned)
        return cleaned_items

    @model_validator(mode="after")
    def validate_matching_lengths(self):
        if len(self.top_findings) != len(self.recommendations):
            raise ValueError("top_findings and recommendations must have matching lengths")
        return self


@router.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(request: AssessmentRequest) -> AssessmentResponse:
    if len(request.text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=f"text must be {MAX_TEXT_LENGTH} characters or fewer.",
        )

    prompt = ASSESSMENT_PROMPT.format(
        framework=request.framework,
        text=request.text,
    )

    model_output: str | None = None
    try:
        client = _get_anthropic_client()
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        model_output = message.content[0].text
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - network / provider failures
        logger.warning("assessment_provider_unavailable", extra={"error": str(exc)})
        raise HTTPException(status_code=503, detail="AI provider unavailable.") from exc

    # Parse the model's response with the safe two-pass parser. On any
    # parser or schema failure return a controlled 502 instead of crashing
    # — the global handler in errors.py wraps it in the canonical envelope
    # {error, detail, request_id}. The raw model output is logged so we
    # can post-mortem the specific completion that broke.
    try:
        parsed_output = parse_model_json(model_output or "")
        return AssessmentResponse.model_validate(parsed_output)
    except (ParsedModelOutputError, json.JSONDecodeError) as exc:
        logger.warning(
            "assessment_parse_failed",
            extra={"error": str(exc), "raw_output": (model_output or "")[:2000]},
        )
        raise HTTPException(
            status_code=502,
            detail=f"Model returned unparseable JSON: {exc}",
        ) from exc
    except ValidationError as exc:
        logger.warning(
            "assessment_schema_invalid",
            extra={"error": exc.errors(), "raw_output": (model_output or "")[:2000]},
        )
        raise HTTPException(
            status_code=502,
            detail="Model output did not match the assessment schema.",
        ) from exc
