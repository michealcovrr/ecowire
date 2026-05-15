import re
import httpx
from app.config import get_settings

settings = get_settings()

# Fallback keyword lists for skill extraction when ML service is unavailable
_SKILL_KEYWORDS: dict[str, list[str]] = {
    "electrical": ["electric", "wiring", "wire", "power", "socket", "inverter", "generator", "light", "bulb", "fan", "ac", "air condition"],
    "plumbing": ["plumb", "pipe", "water", "tap", "toilet", "bathroom", "drainage", "leak"],
    "carpentry": ["carpenter", "wood", "furniture", "table", "chair", "door", "window", "cabinet"],
    "tailoring": ["tailor", "sew", "cloth", "fashion", "fabric", "dress", "trouser", "shirt"],
    "catering": ["cook", "food", "catering", "chef", "rice", "soup", "meal", "bake", "bread", "cake", "snack"],
    "driving": ["drive", "driver", "car", "vehicle", "transport", "delivery", "uber", "bolt", "logistics"],
    "trading": ["sell", "buy", "trade", "market", "provision", "shop", "store", "goods", "wholesale", "retail"],
    "cleaning": ["clean", "wash", "laundry", "sweep", "mop", "housekeep", "domestic"],
    "painting": ["paint", "decor", "colour", "color", "wall"],
    "welding": ["weld", "metal", "iron", "fabricat", "steel"],
    "mechanic": ["mechanic", "engine", "car repair", "auto", "oil change", "brake", "tyre"],
    "barbing": ["barb", "hair cut", "haircut", "shave", "salon"],
    "photography": ["photo", "camera", "video", "film", "record", "shoot"],
    "teaching": ["teach", "tutor", "lesson", "school", "class", "educate"],
    "phone_repair": ["phone repair", "screen repair", "mobile repair", "iphone", "android repair", "laptop repair", "computer repair"],
    "farming": ["farm", "crop", "harvest", "plant", "agriculture", "fish"],
    "security": ["security", "guard", "watch", "protect"],
    "makeup": ["makeup", "beauty", "cosmetic", "lash", "brow", "gele"],
}


def _fallback_extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for tag, keywords in _SKILL_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(tag)
    return found or ["general_labour"]


async def extract_skills(text: str) -> list[str]:
    """Call ML service for skill extraction; fall back to keyword matching."""
    if not settings.ml_service_url or settings.ml_service_url == "http://localhost:8001":
        return _fallback_extract_skills(text)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.ml_service_url}/ml/extract-skills",
                json={"text": text},
            )
            if resp.status_code == 200:
                return resp.json().get("tags", [])
    except Exception:
        pass
    return _fallback_extract_skills(text)


async def parse_job(description: str) -> dict:
    """Extract job tags, location, and budget from a plain-language job description."""
    if not settings.ml_service_url:
        return {"tags": _fallback_extract_skills(description), "location": "", "budget": 0}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.ml_service_url}/ml/parse-job",
                json={"description": description},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return {"tags": _fallback_extract_skills(description), "location": "", "budget": 0}


async def categorise_financial_entry(text: str) -> dict:
    """Categorise a free-text financial entry."""
    if not settings.ml_service_url:
        return _fallback_categorise(text)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.ml_service_url}/ml/categorise-entry",
                json={"text": text},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return _fallback_categorise(text)


async def financial_suggestions(score_data: dict) -> list[str]:
    """Call ML service for plain-language improvement suggestions."""
    if not settings.ml_service_url:
        return []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{settings.ml_service_url}/ml/financial-suggestions",
                json=score_data,
            )
            if resp.status_code == 200:
                return resp.json().get("suggestions", [])
    except Exception:
        pass
    return []


async def transcribe(audio_url: str) -> dict:
    """Call ML service to transcribe audio; fall back to empty text on failure."""
    if not settings.ml_service_url:
        return {"text": "", "language": "en"}
    try:
        async with httpx.AsyncClient(timeout=40) as client:
            resp = await client.post(
                f"{settings.ml_service_url}/ml/transcribe",
                json={"audio_url": audio_url},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return {"text": "", "language": "en"}


async def analyse_media(media_url: str, claimed_skills: list[str]) -> dict:
    """Call ML service for proof-media analysis; soft-fail so uploads never break."""
    fallback = {
        "human_present": True,
        "detected_activities": claimed_skills,
        "confidence": 0.5,
    }
    if not settings.ml_service_url:
        return fallback
    try:
        async with httpx.AsyncClient(timeout=40) as client:
            resp = await client.post(
                f"{settings.ml_service_url}/ml/analyse-media",
                json={"media_url": media_url, "claimed_skills": claimed_skills},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return fallback


def _fallback_categorise(text: str) -> dict:
    text_lower = text.lower()
    amount = 0
    # Simple amount extraction: find numbers optionally preceded by ₦ or N
    matches = re.findall(r"[₦#]?\s*(\d[\d,]*)", text_lower)
    if matches:
        amount = int(matches[-1].replace(",", ""))

    entry_type = "income"
    if any(w in text_lower for w in ["bought", "spent", "paid", "expense", "buy"]):
        entry_type = "expense"
    elif any(w in text_lower for w in ["owe", "lend", "borrow"]):
        entry_type = "debt_owing"

    category = "general"
    if any(w in text_lower for w in ["rice", "food", "provision", "market", "sell", "sold"]):
        category = "trade"
    elif any(w in text_lower for w in ["transport", "delivery", "fuel", "drive"]):
        category = "transport"
    elif any(w in text_lower for w in ["job", "work", "service", "fix", "repair"]):
        category = "service"

    return {"type": entry_type, "amount": amount, "category": category, "tags": {}}
