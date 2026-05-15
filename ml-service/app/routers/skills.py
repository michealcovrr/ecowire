"""
Module 4 ML endpoints — Work Profile & Skill System

/ml/transcribe      — audio URL → text + language (OpenAI Whisper)
/ml/extract-skills  — free-form text → skill tags (Claude)
/ml/analyse-media   — image URL → human presence + activity tags (Claude Vision)
"""
import io
import json
import base64

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()
router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class TranscribeRequest(BaseModel):
    audio_url: str


class ExtractSkillsRequest(BaseModel):
    text: str


class AnalyseMediaRequest(BaseModel):
    media_url: str
    claimed_skills: list[str] = []


# ---------------------------------------------------------------------------
# Skill extraction — Claude system prompt
# ---------------------------------------------------------------------------

_SKILL_EXTRACTION_SYSTEM = """You are a Nigerian labour-market skill extraction AI.
Read the person's description — which may be English, Nigerian Pidgin, Yoruba, Igbo, or Hausa —
and return a JSON array of lowercase snake_case skill tags. Nothing else.

Rules:
- Max 8 tags
- Map local language to standard tags: "I sabi fix motor" → ["vehicle_repair"]
- Be specific: ["electrical", "installation"] beats ["general_labour"]
- If no specific skill is identifiable, return ["general_labour"]

Examples:
  Input:  "I fix electrical wiring and install fans and AC"
  Output: ["electrical","wiring","installation","fan_fitting","air_conditioning"]

  Input:  "I sabi cook very well, I do catering for owambe and party"
  Output: ["catering","cooking","event_catering","food_preparation"]

  Input:  "I drive Keke and sometimes deliver goods for shops"
  Output: ["driving","transport","delivery","logistics"]

  Input:  "I dey do plumbing, I fix pipe and bathroom"
  Output: ["plumbing","pipe_fitting","bathroom_installation"]
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json_array(raw: str) -> list[str]:
    """Strip markdown fences and parse a JSON array from Claude's response."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        # parts[1] is the code block content (may start with "json\n")
        raw = parts[1].lstrip("json").strip()
    return json.loads(raw)


def _parse_json_object(raw: str) -> dict:
    """Strip markdown fences and parse a JSON object from Claude's response."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip()
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/transcribe")
async def transcribe_audio(body: TranscribeRequest):
    """
    Download audio from a URL and transcribe it with OpenAI Whisper.
    Returns {text, language}.
    """
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    # Download audio
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(body.audio_url)
            resp.raise_for_status()
            audio_bytes = resp.content
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not download audio: {exc}")

    # Transcribe — openai SDK is sync; run in thread to avoid blocking event loop
    try:
        import openai
        from anyio import to_thread

        def _run_whisper():
            oai = openai.OpenAI(api_key=settings.openai_api_key)
            buf = io.BytesIO(audio_bytes)
            buf.name = "audio.mp3"
            return oai.audio.transcriptions.create(
                model="whisper-1",
                file=buf,
                response_format="verbose_json",
            )

        result = await to_thread.run_sync(_run_whisper)
        return {
            "text": result.text,
            "language": getattr(result, "language", "en") or "en",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}")


@router.post("/extract-skills")
async def extract_skills(body: ExtractSkillsRequest):
    """
    Extract skill tags from free-form text using Claude.
    Handles English, Pidgin, Yoruba, Igbo, and Hausa.
    Returns {tags: string[]}.
    """
    if not settings.anthropic_api_key:
        # Hard fallback — return a single generic tag so downstream never errors
        return {"tags": ["general_labour"]}

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=_SKILL_EXTRACTION_SYSTEM,
            messages=[{"role": "user", "content": body.text}],
        )
        raw = message.content[0].text
        tags = _parse_json_array(raw)
        if not isinstance(tags, list) or not tags:
            tags = ["general_labour"]
        # Sanitise: lowercase, no spaces
        tags = [str(t).lower().replace(" ", "_") for t in tags]
        return {"tags": tags}

    except Exception as exc:
        # Never fail hard — return fallback so the profile save still works
        return {"tags": ["general_labour"], "_error": str(exc)}


@router.post("/analyse-media")
async def analyse_media(body: AnalyseMediaRequest):
    """
    Analyse a proof-of-work image using Claude Vision.
    Detects: human presence, visible activities, confidence vs claimed skills.
    Returns {human_present, detected_activities, confidence}.

    Videos are not supported by vision models — we return a low-confidence
    passthrough in that case so the upload still succeeds.
    """
    if not settings.anthropic_api_key:
        return {
            "human_present": True,
            "detected_activities": body.claimed_skills,
            "confidence": 0.5,
        }

    # Fetch the media
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(body.media_url)
            resp.raise_for_status()
            media_bytes = resp.content
            content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not download media: {exc}")

    # Videos: vision models can't analyse them — passthrough with low confidence
    if "video" in content_type:
        return {
            "human_present": True,
            "detected_activities": body.claimed_skills,
            "confidence": 0.4,
            "note": "Video analysis not supported — using claimed skills as detected activities",
        }

    # Only a subset of MIME types are accepted by Claude Vision
    _SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if content_type not in _SUPPORTED_IMAGE_TYPES:
        content_type = "image/jpeg"  # best guess for unknown types

    try:
        import anthropic

        media_b64 = base64.standard_b64encode(media_bytes).decode("utf-8")
        claimed_str = ", ".join(body.claimed_skills) if body.claimed_skills else "not specified"

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": media_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                f"Analyse this image as proof of a worker's skill.\n"
                                f"Claimed skills: {claimed_str}\n\n"
                                "Respond ONLY with valid JSON — no markdown, no explanation:\n"
                                "{\n"
                                '  "human_present": true or false,\n'
                                '  "detected_activities": ["snake_case_tag", ...],\n'
                                '  "confidence": 0.0 to 1.0,\n'
                                '  "activity_matches_claim": true or false\n'
                                "}\n\n"
                                "detected_activities must be lowercase snake_case skill tags "
                                "visible in the image."
                            ),
                        },
                    ],
                }
            ],
        )

        result = _parse_json_object(message.content[0].text)
        return {
            "human_present": bool(result.get("human_present", False)),
            "detected_activities": result.get("detected_activities", []),
            "confidence": float(result.get("confidence", 0.5)),
            "activity_matches_claim": bool(result.get("activity_matches_claim", False)),
        }

    except Exception as exc:
        # Soft fail — the upload succeeds but with claimed skills as detected
        return {
            "human_present": True,
            "detected_activities": body.claimed_skills,
            "confidence": 0.5,
            "_error": str(exc),
        }
