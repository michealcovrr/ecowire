"""
Module 7 ML endpoint — Job Parsing

/ml/parse-job  — plain-language job description → skill tags + location + budget (Claude)
"""
import json

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()
router = APIRouter()


class ParseJobRequest(BaseModel):
    description: str


_PARSE_JOB_SYSTEM = """You are a Nigerian job marketplace AI.
Read a plain-language job description — which may be in English, Pidgin, or other Nigerian languages —
and extract structured information.

Return ONLY valid JSON with exactly this structure (no markdown, no explanation):
{
  "tags": ["snake_case_skill_tag", ...],
  "location": "extracted location string or empty string",
  "budget": budget_as_integer_in_kobo_or_0
}

Rules:
- tags: max 6 lowercase snake_case skill tags required to do this job
- location: extract any Nigerian location mentioned (e.g. "Yaba", "Ikeja GRA", "Aba"), empty string if none
- budget: if a naira amount is mentioned, multiply by 100 to convert to kobo; 0 if not mentioned
- Handle informal language: "50k" = 50000 naira = 5000000 kobo

Examples:
  Input:  "I need an electrician in Yaba to install AC and wiring, budget is 50k"
  Output: {"tags":["electrical","installation","air_conditioning","wiring"],"location":"Yaba","budget":5000000}

  Input:  "Who fit do plumbing for me for Surulere? Budget 30,000"
  Output: {"tags":["plumbing","pipe_fitting"],"location":"Surulere","budget":3000000}

  Input:  "Need tailor to sew 10 shirts urgently"
  Output: {"tags":["tailoring","sewing"],"location":"","budget":0}
"""


@router.post("/parse-job")
async def parse_job(body: ParseJobRequest):
    """
    Extract skill tags, location, and budget from a plain-language job description.
    Handles English, Pidgin, and informal Nigerian language.
    Returns {tags, location, budget}.
    """
    if not settings.anthropic_api_key:
        return {"tags": [], "location": "", "budget": 0}

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=_PARSE_JOB_SYSTEM,
            messages=[{"role": "user", "content": body.description}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1].lstrip("json").strip()
        result = json.loads(raw)

        tags = [str(t).lower().replace(" ", "_") for t in result.get("tags", [])]
        location = str(result.get("location", "")).strip()
        budget = int(result.get("budget", 0))

        return {"tags": tags, "location": location, "budget": budget}

    except Exception as exc:
        return {"tags": [], "location": "", "budget": 0, "_error": str(exc)}
