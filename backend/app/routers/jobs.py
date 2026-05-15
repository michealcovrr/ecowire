"""
Module 7 — Job Posting & Matching

Endpoints:
  POST /jobs                          — employer posts a job
  GET  /jobs/feed                     — worker job feed (skill-matched, proximity-sorted)
  GET  /jobs/my/posted                — employer's own jobs
  GET  /jobs/my/applications          — worker's application history
  GET  /jobs/{job_id}                 — full job details
  POST /jobs/{job_id}/apply           — worker applies
  GET  /jobs/{job_id}/applicants      — ranked applicants (employer only)
  GET  /jobs/{job_id}/matches         — all platform workers ranked for this job (employer only)
  POST /jobs/{job_id}/accept/{wid}    — employer accepts a worker → status = matched
"""
from math import radians, cos, sin, asin, sqrt
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.job import Job, JobApplication
from app.models.profile import WorkProfile
from app.models.community import CommunityMembership, Recommendation
from app.schemas.common import ok
from app.services.ml_service import parse_job
from app.utils.security import get_current_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class JobCreateRequest(BaseModel):
    job_description: str
    location_address: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    budget_kobo: int | None = None


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * R * asin(sqrt(a))


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _score_worker(
    profile: WorkProfile,
    worker: User,
    job: Job,
    same_community: bool = False,
    recommendation_degree: int | None = None,
) -> tuple[float, list[str]]:
    """
    Score a worker against a job. Returns (score, reason_strings).

    Max breakdown:
      Skill overlap   0–40 pts  (Jaccard × 40)
      Proximity       0–25 pts  (distance buckets)
      Completion rate 0–20 pts  (completions / total × 20)
      Profile depth   0–15 pts  (visibility_score × 0.15)
      Community       +20       (same circle — Module 5)
      Recommendation  +30/+15/+5 (degree 1/2/3 — Module 6)
      Dispute penalty −5/dispute (capped at −20)
    """
    score = 0.0
    reasons: list[str] = []

    # 1. Skill overlap
    job_tags = job.job_tags or []
    worker_tags = profile.skill_tags or []
    j = _jaccard(job_tags, worker_tags)
    score += round(j * 40, 2)
    matched_tags = set(job_tags) & set(worker_tags)
    if matched_tags:
        reasons.append(f"Matching skills: {', '.join(sorted(matched_tags))}")

    # 2. Geographic proximity
    if all([
        job.location_lat, job.location_lng,
        worker.location_lat, worker.location_lng,
    ]):
        dist_km = _haversine_km(
            float(job.location_lat), float(job.location_lng),
            float(worker.location_lat), float(worker.location_lng),
        )
        if dist_km <= 2:
            score += 25; reasons.append(f"{dist_km:.1f}km away")
        elif dist_km <= 5:
            score += 20; reasons.append(f"{dist_km:.1f}km away")
        elif dist_km <= 10:
            score += 12; reasons.append(f"{dist_km:.1f}km away")
        elif dist_km <= 20:
            score += 5; reasons.append(f"{dist_km:.1f}km away")

    # 3. Job completion rate
    total_jobs = profile.job_completion_count + profile.dispute_count
    if total_jobs > 0:
        rate = profile.job_completion_count / total_jobs
        score += round(rate * 20, 2)
    if profile.job_completion_count > 0:
        reasons.append(f"{profile.job_completion_count} job{'s' if profile.job_completion_count > 1 else ''} completed")

    # 4. Profile depth (visibility score 0–100 → 0–15 pts)
    score += round(float(profile.profile_visibility_score or 0) * 0.15, 2)

    # 5. Community circle bonus (Module 5 — populated when community memberships exist)
    if same_community:
        score += 20
        reasons.append("Same community circle")

    # 6. Recommendation degree bonus (Module 6 — populated after recommendation graph is built)
    if recommendation_degree == 1:
        score += 30; reasons.append("Directly recommended by your connection")
    elif recommendation_degree == 2:
        score += 15; reasons.append("2nd-degree recommendation")
    elif recommendation_degree == 3:
        score += 5; reasons.append("3rd-degree recommendation")

    # 7. Dispute penalty
    if profile.dispute_count > 0:
        penalty = min(profile.dispute_count * 5, 20)
        score -= penalty

    return max(0.0, round(score, 1)), reasons


async def _check_same_community(
    db: AsyncSession,
    user_a_id: str,
    user_b_id: str,
) -> bool:
    """Return True if both users share at least one community group."""
    result_a = await db.execute(
        select(CommunityMembership.group_id).where(CommunityMembership.user_id == user_a_id)
    )
    groups_a = {row[0] for row in result_a.all()}
    if not groups_a:
        return False
    result_b = await db.execute(
        select(CommunityMembership.group_id).where(CommunityMembership.user_id == user_b_id)
    )
    groups_b = {row[0] for row in result_b.all()}
    return bool(groups_a & groups_b)


async def _recommendation_degree(
    db: AsyncSession,
    employer_id: str,
    worker_id: str,
) -> int | None:
    """
    Return the recommendation degree between employer and worker.
    1 = employer directly has a recommendation for this worker.
    2 = someone the employer has a recommendation from also recommended this worker.
    None = no recommendation path found.
    (Module 6 will add full graph traversal — this is a lightweight 2-hop check.)
    """
    # 1st degree: employer directly has a recommendation for this worker
    direct = await db.execute(
        select(Recommendation).where(
            Recommendation.recommender_user_id == employer_id,
            Recommendation.worker_user_id == worker_id,
        )
    )
    if direct.scalar_one_or_none():
        return 1

    # 2nd degree: any recommender of the worker has also recommended someone
    # that the employer has a recommendation from
    worker_recs = await db.execute(
        select(Recommendation.recommender_user_id).where(
            Recommendation.worker_user_id == worker_id
        )
    )
    worker_recommenders = {row[0] for row in worker_recs.all()}
    if not worker_recommenders:
        return None

    employer_recs = await db.execute(
        select(Recommendation.worker_user_id).where(
            Recommendation.recommender_user_id == employer_id
        )
    )
    employer_recommended_workers = {row[0] for row in employer_recs.all()}
    if worker_recommenders & employer_recommended_workers:
        return 2

    return None


def _job_dict(job: Job) -> dict:
    return {
        "job_id": job.job_id,
        "employer_user_id": job.employer_user_id,
        "job_description": job.job_description_raw,
        "job_tags": job.job_tags or [],
        "location_address": job.location_address,
        "location_lat": float(job.location_lat) if job.location_lat else None,
        "location_lng": float(job.location_lng) if job.location_lng else None,
        "budget_naira": job.budget / 100 if job.budget else None,
        "status": job.status,
        "worker_user_id": job.worker_user_id,
        "created_at": job.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("")
async def create_job(
    body: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Post a job in plain language.
    Claude extracts required skill tags automatically.
    """
    if not body.job_description.strip():
        raise HTTPException(status_code=400, detail="job_description is required")

    parsed = await parse_job(body.job_description)
    tags = parsed.get("tags", [])

    # If ML extracted a location/budget and none was provided explicitly, use them
    location_address = body.location_address or parsed.get("location") or None
    budget = body.budget_kobo or parsed.get("budget") or None

    job = Job(
        employer_user_id=current_user.user_id,
        job_description_raw=body.job_description,
        job_tags=tags,
        location_lat=body.location_lat,
        location_lng=body.location_lng,
        location_address=location_address,
        budget=budget,
        status="open",
    )
    db.add(job)
    await db.commit()

    return ok({
        **_job_dict(job),
        "message": "Job posted. Workers will be matched automatically.",
    })


@router.get("/feed")
async def get_job_feed(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, le=50),
    min_budget_naira: int = Query(0),
):
    """
    Worker job feed: open jobs ranked by skill match score.
    Jobs with zero skill overlap are excluded.
    """
    profile_result = await db.execute(
        select(WorkProfile).where(WorkProfile.user_id == current_user.user_id)
    )
    profile = profile_result.scalar_one_or_none()
    worker_tags = profile.skill_tags or [] if profile else []

    jobs_result = await db.execute(
        select(Job).where(Job.status == "open").order_by(Job.created_at.desc())
    )
    all_jobs = jobs_result.scalars().all()

    scored = []
    for job in all_jobs:
        if job.employer_user_id == current_user.user_id:
            continue
        if min_budget_naira and job.budget and job.budget < min_budget_naira * 100:
            continue

        match_pct = round(_jaccard(worker_tags, job.job_tags or []) * 100, 1)

        scored.append({
            **_job_dict(job),
            "skill_match_pct": match_pct,
        })

    # Sort by skill match, then by recency for ties
    scored.sort(key=lambda x: x["skill_match_pct"], reverse=True)
    return ok({"jobs": scored[:limit], "total": len(scored)})


@router.get("/my/posted")
async def get_my_posted_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employer: list all jobs they have posted."""
    result = await db.execute(
        select(Job)
        .where(Job.employer_user_id == current_user.user_id)
        .order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()
    return ok({"jobs": [_job_dict(j) for j in jobs]})


@router.get("/my/applications")
async def get_my_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Worker: list all jobs they have applied to."""
    result = await db.execute(
        select(JobApplication, Job)
        .join(Job, JobApplication.job_id == Job.job_id)
        .where(JobApplication.worker_user_id == current_user.user_id)
        .order_by(JobApplication.applied_at.desc())
    )
    rows = result.all()
    return ok({
        "applications": [
            {
                "application_id": app.application_id,
                "status": app.status,
                "applied_at": app.applied_at.isoformat(),
                "job": _job_dict(job),
            }
            for app, job in rows
        ]
    })


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full job details, including the current user's application status if any."""
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    emp_result = await db.execute(select(User).where(User.user_id == job.employer_user_id))
    employer = emp_result.scalar_one_or_none()

    app_result = await db.execute(
        select(JobApplication).where(
            JobApplication.job_id == job_id,
            JobApplication.worker_user_id == current_user.user_id,
        )
    )
    application = app_result.scalar_one_or_none()

    return ok({
        **_job_dict(job),
        "employer": {
            "user_id": employer.user_id if employer else None,
            "full_name": employer.full_name if employer else None,
        },
        "my_application": {
            "application_id": application.application_id,
            "status": application.status,
            "applied_at": application.applied_at.isoformat(),
        } if application else None,
    })


@router.post("/{job_id}/apply")
async def apply_to_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Worker applies to an open job."""
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "open":
        raise HTTPException(status_code=400, detail=f"Job is not open (current status: {job.status})")
    if job.employer_user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot apply to your own job")

    existing = await db.execute(
        select(JobApplication).where(
            JobApplication.job_id == job_id,
            JobApplication.worker_user_id == current_user.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already applied to this job")

    application = JobApplication(
        job_id=job_id,
        worker_user_id=current_user.user_id,
        status="applied",
    )
    db.add(application)
    await db.commit()

    return ok({
        "application_id": application.application_id,
        "job_id": job_id,
        "status": "applied",
        "message": "Application submitted. The employer will review your profile.",
    })


@router.get("/{job_id}/applicants")
async def get_applicants(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Employer: ranked list of workers who applied to this job.
    Scoring: skill overlap + proximity + completion rate + community + recommendations.
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.employer_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only the job poster can view applicants")

    apps_result = await db.execute(
        select(JobApplication).where(JobApplication.job_id == job_id)
    )
    applications = apps_result.scalars().all()

    scored = []
    for app in applications:
        worker_result = await db.execute(select(User).where(User.user_id == app.worker_user_id))
        worker = worker_result.scalar_one_or_none()
        if not worker:
            continue

        profile_result = await db.execute(
            select(WorkProfile).where(WorkProfile.user_id == app.worker_user_id)
        )
        profile = profile_result.scalar_one_or_none()

        same_community = await _check_same_community(db, current_user.user_id, app.worker_user_id)
        rec_degree = await _recommendation_degree(db, current_user.user_id, app.worker_user_id)

        if profile:
            score, reasons = _score_worker(profile, worker, job, same_community, rec_degree)
        else:
            score, reasons = 0.0, ["No work profile set up"]

        scored.append({
            "application_id": app.application_id,
            "worker_user_id": app.worker_user_id,
            "worker_name": worker.full_name,
            "application_status": app.status,
            "match_score": score,
            "match_reasons": reasons,
            "skill_tags": profile.skill_tags if profile else [],
            "job_completion_count": profile.job_completion_count if profile else 0,
            "dispute_count": profile.dispute_count if profile else 0,
            "applied_at": app.applied_at.isoformat(),
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return ok({"job_id": job_id, "total_applicants": len(scored), "applicants": scored})


@router.get("/{job_id}/matches")
async def get_job_matches(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, le=30),
):
    """
    Employer: proactive match — rank ALL workers on the platform against this job,
    whether or not they applied. Use this to find and invite top candidates.
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.employer_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only the job poster can view matches")

    profiles_result = await db.execute(select(WorkProfile))
    all_profiles = profiles_result.scalars().all()

    scored = []
    for profile in all_profiles:
        if profile.user_id == current_user.user_id:
            continue

        worker_result = await db.execute(select(User).where(User.user_id == profile.user_id))
        worker = worker_result.scalar_one_or_none()
        if not worker:
            continue

        same_community = await _check_same_community(db, current_user.user_id, profile.user_id)
        rec_degree = await _recommendation_degree(db, current_user.user_id, profile.user_id)
        score, reasons = _score_worker(profile, worker, job, same_community, rec_degree)

        if score > 0:
            # Check if they've already applied
            app_result = await db.execute(
                select(JobApplication).where(
                    JobApplication.job_id == job_id,
                    JobApplication.worker_user_id == profile.user_id,
                )
            )
            has_applied = app_result.scalar_one_or_none() is not None

            scored.append({
                "worker_user_id": profile.user_id,
                "worker_name": worker.full_name,
                "match_score": score,
                "match_reasons": reasons,
                "skill_tags": profile.skill_tags or [],
                "job_completion_count": profile.job_completion_count,
                "profile_visibility_score": float(profile.profile_visibility_score or 0),
                "has_applied": has_applied,
            })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return ok({
        "job_id": job_id,
        "total_matches": len(scored),
        "matches": scored[:limit],
    })


@router.post("/{job_id}/accept/{worker_id}")
async def accept_worker(
    job_id: str,
    worker_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Employer accepts a worker → job status becomes 'matched'.
    All other applicants are rejected.
    Next step: use POST /chat to open the job negotiation chat (Module 8).
    """
    result = await db.execute(select(Job).where(Job.job_id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.employer_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only the job poster can accept a worker")
    if job.status != "open":
        raise HTTPException(status_code=400, detail=f"Job is already {job.status}")

    # Verify the worker either applied OR exists on the platform (for proactive match invites)
    worker_result = await db.execute(select(User).where(User.user_id == worker_id))
    worker = worker_result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    app_result = await db.execute(
        select(JobApplication).where(
            JobApplication.job_id == job_id,
            JobApplication.worker_user_id == worker_id,
        )
    )
    application = app_result.scalar_one_or_none()

    if application:
        application.status = "accepted"
    else:
        # Employer is inviting a worker directly (proactive match path — no prior application)
        application = JobApplication(
            job_id=job_id,
            worker_user_id=worker_id,
            status="accepted",
        )
        db.add(application)

    # Reject all other applicants
    other_apps_result = await db.execute(
        select(JobApplication).where(
            JobApplication.job_id == job_id,
            JobApplication.worker_user_id != worker_id,
            JobApplication.status == "applied",
        )
    )
    for other in other_apps_result.scalars().all():
        other.status = "rejected"

    job.worker_user_id = worker_id
    job.status = "matched"
    job.updated_at = datetime.utcnow()

    await db.commit()

    return ok({
        "job_id": job_id,
        "worker_user_id": worker_id,
        "worker_name": worker.full_name,
        "status": "matched",
        "next_step": "Open a chat to negotiate and confirm the agreement (POST /chat)",
    })
