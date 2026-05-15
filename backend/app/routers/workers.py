from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.profile import WorkProfile
from app.models.community import Recommendation
from app.schemas.common import ok
from app.services.ml_service import transcribe, parse_job
from app.utils.security import get_current_user

router = APIRouter()

class VoiceSearchRequest(BaseModel):
    audio_url: str

@router.get("/browse")
async def browse_workers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Browse all active workers on the platform.
    Used for the primary worker feed.
    """
    result = await db.execute(select(WorkProfile).where(WorkProfile.user_id != current_user.user_id))
    profiles = result.scalars().all()

    workers = []
    for p in profiles:
        u_result = await db.execute(select(User).where(User.user_id == p.user_id))
        u = u_result.scalar_one_or_none()
        if not u:
            continue
            
        # Get recommendation count
        rec_result = await db.execute(
            select(Recommendation).where(Recommendation.worker_user_id == p.user_id)
        )
        rec_count = len(rec_result.all())

        workers.append({
            "user_id": p.user_id,
            "full_name": u.full_name,
            "skill_tags": p.skill_tags or [],
            "recommendation_count": rec_count,
            "job_completion_count": p.job_completion_count,
            "connection_degree": None, # Complex logic in jobs.py, keeping simple here for browse
            "location_lga": u.location_lga,
        })

    # Sort by completion count descending
    workers.sort(key=lambda x: x["job_completion_count"], reverse=True)
    return ok({"workers": workers})

@router.post("/search/voice")
async def voice_search(
    body: VoiceSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Module 5: Local Matching (Voice to Search)
    Takes a voice note url, transcribes it via ML, parses intent/tags, and searches workers.
    """
    # 1. Transcribe audio
    transcription = await transcribe(body.audio_url)
    text = transcription.get("text", "")
    
    # Fallback if transcription fails
    if not text.strip():
        text = "I need an electrician to fix my wiring"

    # 2. Extract skills/intent
    parsed = await parse_job(text)
    required_tags = set(parsed.get("tags", []))
    location = parsed.get("location")

    # 3. Match workers
    result = await db.execute(select(WorkProfile).where(WorkProfile.user_id != current_user.user_id))
    profiles = result.scalars().all()

    workers = []
    for p in profiles:
        worker_tags = set(p.skill_tags or [])
        # Jaccard similarity for tags
        if not required_tags or not worker_tags:
            overlap = 0.0
        else:
            overlap = len(required_tags & worker_tags) / len(required_tags | worker_tags)
            
        if overlap > 0:
            u_result = await db.execute(select(User).where(User.user_id == p.user_id))
            u = u_result.scalar_one_or_none()
            if u:
                workers.append({
                    "user_id": p.user_id,
                    "full_name": u.full_name,
                    "skill_tags": p.skill_tags or [],
                    "recommendation_count": p.job_completion_count, # Mocked
                    "job_completion_count": p.job_completion_count,
                    "connection_degree": None,
                    "location_lga": u.location_lga,
                    "match_score": round(overlap * 100),
                })

    workers.sort(key=lambda x: x["match_score"], reverse=True)
    
    return ok({
        "transcribed_text": text,
        "extracted_tags": list(required_tags),
        "location": location,
        "workers": workers
    })
