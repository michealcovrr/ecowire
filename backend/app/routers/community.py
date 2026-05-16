"""
Module 5 — Community Circles

Endpoints:
  GET /community/groups   — groups the user belongs to (auto-joins their LGA group if missing)
  GET /community/nearby   — users in the same area + recommended workers across the platform
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import aliased

from app.database import get_db
from app.models.user import User
from app.models.profile import WorkProfile
from app.models.community import (
    CommunityGroup, CommunityMembership, Recommendation, UserConnection,
)
from app.schemas.common import ok
from app.utils.security import get_current_user

router = APIRouter()


@router.get("/groups")
async def get_my_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all community groups the user belongs to.
    If the user has an LGA but isn't in any group, auto-join them.
    If they have no groups at all, return all top-level groups instead so the UI isn't empty.
    """
    # Auto-join LGA group if user has an LGA
    if current_user.location_lga:
        lga_group_result = await db.execute(
            select(CommunityGroup).where(CommunityGroup.lga == current_user.location_lga)
        )
        lga_group = lga_group_result.scalar_one_or_none()
        if lga_group:
            existing = await db.execute(
                select(CommunityMembership).where(
                    (CommunityMembership.user_id == current_user.user_id) &
                    (CommunityMembership.group_id == lga_group.group_id)
                )
            )
            if not existing.scalar_one_or_none():
                db.add(CommunityMembership(user_id=current_user.user_id, group_id=lga_group.group_id))
                await db.commit()

    # Fetch user's groups
    result = await db.execute(
        select(CommunityGroup, func.count(CommunityMembership.user_id).label("member_count"))
        .join(CommunityMembership, CommunityMembership.group_id == CommunityGroup.group_id)
        .where(CommunityGroup.group_id.in_(
            select(CommunityMembership.group_id).where(CommunityMembership.user_id == current_user.user_id)
        ))
        .group_by(CommunityGroup.group_id)
    )
    rows = result.all()

    # If still none, return the most active groups so the UI shows something
    if not rows:
        result = await db.execute(
            select(CommunityGroup, func.count(CommunityMembership.user_id).label("member_count"))
            .join(CommunityMembership, CommunityMembership.group_id == CommunityGroup.group_id, isouter=True)
            .group_by(CommunityGroup.group_id)
            .order_by(func.count(CommunityMembership.user_id).desc())
            .limit(5)
        )
        rows = result.all()

    return ok({
        "groups": [
            {
                "group_id": g.group_id,
                "group_name": g.group_name,
                "lga": g.lga,
                "member_count": int(count or 0),
            }
            for g, count in rows
        ]
    })


@router.get("/nearby")
async def get_nearby_members(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 30,
):
    """
    Return nearby members ranked by:
      1. Same LGA as current user
      2. Has a work profile (more useful to display)
      3. Has recommendations / completed jobs
    Falls back to platform-wide active users if current user has no LGA.
    """
    # Direct connections (1st degree) - for degree calculation
    direct_result = await db.execute(
        select(UserConnection.user_b_id).where(UserConnection.user_a_id == current_user.user_id)
        .union(
            select(UserConnection.user_a_id).where(UserConnection.user_b_id == current_user.user_id)
        )
    )
    direct_ids = {r[0] for r in direct_result.fetchall()}

    # Pull users with work profiles first (more interesting to display)
    same_lga_users = []
    if current_user.location_lga:
        result = await db.execute(
            select(User, WorkProfile)
            .join(WorkProfile, WorkProfile.user_id == User.user_id, isouter=True)
            .where(
                (User.location_lga == current_user.location_lga) &
                (User.user_id != current_user.user_id)
            )
            .limit(limit)
        )
        same_lga_users = result.all()

    # If too few, top up with platform-wide users (with profiles preferred)
    members = list(same_lga_users)
    seen_ids = {u.user_id for u, _ in members}
    if len(members) < limit:
        result = await db.execute(
            select(User, WorkProfile)
            .join(WorkProfile, WorkProfile.user_id == User.user_id, isouter=True)
            .where(User.user_id != current_user.user_id)
            .order_by(WorkProfile.profile_visibility_score.desc().nullslast())
            .limit(limit * 2)
        )
        for u, p in result.all():
            if u.user_id in seen_ids:
                continue
            members.append((u, p))
            seen_ids.add(u.user_id)
            if len(members) >= limit:
                break

    out = []
    for user, profile in members[:limit]:
        # Recommendation count
        rec_result = await db.execute(
            select(func.count(Recommendation.recommendation_id)).where(
                Recommendation.worker_user_id == user.user_id
            )
        )
        rec_count = rec_result.scalar() or 0

        # Connection degree
        if user.user_id in direct_ids:
            degree = 1
        else:
            # Check 2nd-degree: any of my connections connect to them?
            second_result = await db.execute(
                select(func.count()).select_from(UserConnection).where(
                    ((UserConnection.user_a_id == user.user_id) & UserConnection.user_b_id.in_(direct_ids)) |
                    ((UserConnection.user_b_id == user.user_id) & UserConnection.user_a_id.in_(direct_ids))
                )
            )
            degree = 2 if (second_result.scalar() or 0) > 0 else None

        out.append({
            "user_id": user.user_id,
            "full_name": user.full_name,
            "location_lga": user.location_lga,
            "skill_tags": (profile.skill_tags if profile else []) or [],
            "recommendation_count": int(rec_count),
            "job_completion_count": int(profile.job_completion_count) if profile else 0,
            "connection_degree": degree,
        })

    return ok({"members": out})
