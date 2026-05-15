from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.profile import WorkProfile, ProofMedia
from app.schemas.common import ok
from app.services.ml_service import extract_skills, transcribe, analyse_media
from app.utils.security import get_current_user

router = APIRouter()


class ProfileCreateRequest(BaseModel):
    skill_description: str


class VoiceProfileRequest(BaseModel):
    audio_url: str


class ProofMediaRequest(BaseModel):
    media_url: str
    media_type: str = "image"    # "image" or "video"
    claimed_skills: list[str] = []


def _visibility_score(profile: WorkProfile, media_count: int) -> float:
    score = 0.0
    if profile.skill_description_raw:
        score += 20.0
    if profile.skill_tags:
        score += min(len(profile.skill_tags) * 5.0, 20.0)
    score += min(profile.job_completion_count * 5.0, 30.0)
    score -= min(profile.dispute_count * 10.0, 20.0)
    score += min(media_count * 5.0, 10.0)
    return max(0.0, min(score, 100.0))


@router.post("")
async def create_or_update_profile(
    body: ProfileCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create or update the authenticated user's work profile.
    Skill tags are extracted automatically from the description.
    """
    if not body.skill_description.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skill description cannot be empty")

    tags = await extract_skills(body.skill_description)

    result = await db.execute(
        select(WorkProfile).where(WorkProfile.user_id == current_user.user_id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        profile.skill_description_raw = body.skill_description
        profile.skill_tags = tags
        profile.updated_at = datetime.utcnow()
    else:
        profile = WorkProfile(
            user_id=current_user.user_id,
            skill_description_raw=body.skill_description,
            skill_tags=tags,
        )
        db.add(profile)

    await db.flush()

    media_result = await db.execute(
        select(ProofMedia).where(ProofMedia.user_id == current_user.user_id)
    )
    media_count = len(media_result.scalars().all())
    profile.profile_visibility_score = _visibility_score(profile, media_count)

    await db.commit()

    return ok({
        "profile_id": profile.profile_id,
        "user_id": current_user.user_id,
        "full_name": current_user.full_name,
        "skill_description": profile.skill_description_raw,
        "skill_tags": profile.skill_tags,
        "profile_visibility_score": float(profile.profile_visibility_score),
        "job_completion_count": profile.job_completion_count,
        "dispute_count": profile.dispute_count,
    })


@router.post("/voice")
async def create_profile_from_voice(
    body: VoiceProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create or update a work profile from a voice recording.
    Transcribes audio via Whisper, then extracts skill tags via Claude.
    The audio must already be uploaded to Cloudinary (or similar) — pass the URL.
    """
    if not body.audio_url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="audio_url is required")

    # Step 1: transcribe
    transcription = await transcribe(body.audio_url)
    text = transcription.get("text", "").strip()
    language = transcription.get("language", "en")

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not transcribe audio — file may be silent or unsupported",
        )

    # Step 2: extract skill tags from the transcript
    tags = await extract_skills(text)

    # Step 3: upsert work profile
    result = await db.execute(
        select(WorkProfile).where(WorkProfile.user_id == current_user.user_id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        profile.skill_description_raw = text
        profile.skill_tags = tags
        profile.updated_at = datetime.utcnow()
    else:
        profile = WorkProfile(
            user_id=current_user.user_id,
            skill_description_raw=text,
            skill_tags=tags,
        )
        db.add(profile)

    await db.flush()

    media_result = await db.execute(
        select(ProofMedia).where(ProofMedia.user_id == current_user.user_id)
    )
    media_count = len(media_result.scalars().all())
    profile.profile_visibility_score = _visibility_score(profile, media_count)

    # Persist detected language preference if not English
    if language and language not in ("en", "english") and current_user.preferred_language == "english":
        current_user.preferred_language = language
        current_user.updated_at = datetime.utcnow()

    await db.commit()

    return ok({
        "profile_id": profile.profile_id,
        "user_id": current_user.user_id,
        "full_name": current_user.full_name,
        "transcribed_text": text,
        "detected_language": language,
        "skill_tags": profile.skill_tags,
        "profile_visibility_score": float(profile.profile_visibility_score),
    })


@router.get("/me")
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the authenticated user's full work profile including proof media."""
    result = await db.execute(
        select(WorkProfile).where(WorkProfile.user_id == current_user.user_id)
    )
    profile = result.scalar_one_or_none()

    media_result = await db.execute(
        select(ProofMedia).where(ProofMedia.user_id == current_user.user_id)
    )
    media = media_result.scalars().all()

    return ok({
        "user_id": current_user.user_id,
        "full_name": current_user.full_name,
        "profile": {
            "skill_description": profile.skill_description_raw if profile else None,
            "skill_tags": profile.skill_tags if profile else [],
            "profile_visibility_score": float(profile.profile_visibility_score) if profile else 0.0,
            "job_completion_count": profile.job_completion_count if profile else 0,
            "dispute_count": profile.dispute_count if profile else 0,
        } if profile else None,
        "proof_media": [
            {
                "media_id": m.media_id,
                "media_url": m.media_url,
                "media_type": m.media_type,
                "detected_activity_tags": m.detected_activity_tags,
                "confidence_score": float(m.confidence_score) if m.confidence_score else None,
                "uploaded_at": m.uploaded_at.isoformat(),
            }
            for m in media
        ],
    })


@router.get("/{user_id}")
async def get_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View another user's public work profile."""
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(select(WorkProfile).where(WorkProfile.user_id == user_id))
    profile = result.scalar_one_or_none()

    media_result = await db.execute(select(ProofMedia).where(ProofMedia.user_id == user_id))
    media = media_result.scalars().all()

    return ok({
        "user_id": user.user_id,
        "full_name": user.full_name,
        "profile": {
            "skill_tags": profile.skill_tags if profile else [],
            "profile_visibility_score": float(profile.profile_visibility_score) if profile else 0.0,
            "job_completion_count": profile.job_completion_count if profile else 0,
        } if profile else None,
        "proof_media": [
            {
                "media_id": m.media_id,
                "media_url": m.media_url,
                "media_type": m.media_type,
                "detected_activity_tags": m.detected_activity_tags,
                "confidence_score": float(m.confidence_score) if m.confidence_score else None,
            }
            for m in media
        ],
    })


@router.post("/media")
async def add_proof_media(
    body: ProofMediaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add proof media to work profile.
    The URL must already be uploaded to Cloudinary or similar.
    ML analysis (Claude Vision) runs immediately and populates
    human_present, detected_activity_tags, and confidence_score.
    """
    # Run ML analysis before saving so the record is immediately enriched
    analysis = await analyse_media(body.media_url, body.claimed_skills)

    media = ProofMedia(
        user_id=current_user.user_id,
        media_url=body.media_url,
        media_type=body.media_type,
        human_present=analysis.get("human_present", True),
        detected_activity_tags=analysis.get("detected_activities") or body.claimed_skills,
        confidence_score=analysis.get("confidence", 0.5),
    )
    db.add(media)

    # Refresh profile visibility score
    profile_result = await db.execute(
        select(WorkProfile).where(WorkProfile.user_id == current_user.user_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        media_count_result = await db.execute(
            select(ProofMedia).where(ProofMedia.user_id == current_user.user_id)
        )
        media_count = len(media_count_result.scalars().all()) + 1
        profile.profile_visibility_score = _visibility_score(profile, media_count)

    await db.commit()

    return ok({
        "media_id": media.media_id,
        "media_url": media.media_url,
        "media_type": media.media_type,
        "human_present": media.human_present,
        "detected_activity_tags": media.detected_activity_tags,
        "confidence_score": float(media.confidence_score) if media.confidence_score else None,
        "activity_matches_claim": analysis.get("activity_matches_claim"),
    })
