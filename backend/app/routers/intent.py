from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, UserIntent
from app.schemas.intent import IntentSubmitRequest, IntentResponse
from app.schemas.common import ok
from app.utils.security import get_current_user

router = APIRouter()

# Static question set — frontend uses this to render the step-by-step flow
QUESTIONS = [
    {
        "id": "primary_goal",
        "step": 1,
        "question": "What are you here to do?",
        "options": [
            {"value": "work",      "label": "Find work / offer my skills"},
            {"value": "hire",      "label": "Hire someone"},
            {"value": "business",  "label": "Manage my business"},
            {"value": "financial", "label": "Access financial services"},
            {"value": "basic",     "label": "Just send or receive money"},
        ],
    },
    {
        "id": "makes_money",
        "step": 2,
        "question": "Do you earn money from any activity?",
        "options": [
            {"value": True,  "label": "Yes"},
            {"value": False, "label": "No"},
        ],
    },
    {
        "id": "activity_type",
        "step": 3,
        "question": "What kind of activity do you earn from?",
        "show_if": {"makes_money": True},
        "options": [
            {"value": "trade",     "label": "Trading / buying and selling"},
            {"value": "service",   "label": "A skill or service"},
            {"value": "transport", "label": "Transport / delivery"},
            {"value": "other",     "label": "Something else"},
        ],
    },
    {
        "id": "wants_to_hire",
        "step": 4,
        "question": "Do you want to hire people for tasks?",
        "options": [
            {"value": True,  "label": "Yes"},
            {"value": False, "label": "No"},
        ],
    },
    {
        "id": "needs_financial_support",
        "step": 5,
        "question": "Do you need financial support (loans, savings, insurance)?",
        "options": [
            {"value": True,  "label": "Yes"},
            {"value": False, "label": "No"},
        ],
    },
]

# Role routing table
# primary_goal → (active_role, base_kyc_tier)
_ROLE_MAP = {
    "work":      ("worker",    1),
    "hire":      ("employer",  2),
    "business":  ("business",  2),
    "financial": ("financial", 2),
    "basic":     ("basic",     1),
}

_ROLE_MESSAGES = {
    "worker":    "Your profile is set up for finding work. You can now create a work profile and apply for jobs.",
    "employer":  "Your profile is set up for hiring. You can post jobs and use escrow payments.",
    "business":  "Your profile is set up for business management. You can track income, expenses, and access working capital.",
    "financial": "Your profile is set up for financial services. You can access savings, insurance, and loans when eligible.",
    "basic":     "Your profile is set up for sending and receiving money.",
}


def _compute_role(answers) -> tuple[str, int]:
    goal = (answers.primary_goal or "basic").lower().strip()
    role, tier = _ROLE_MAP.get(goal, ("basic", 1))

    # Escalate tier if extra needs require it
    if answers.wants_to_hire:
        tier = max(tier, 2)
    if answers.needs_financial_support:
        tier = max(tier, 2)

    return role, tier


@router.get("/questions")
async def get_questions():
    """Return the full intent question set for the frontend to render step-by-step."""
    return ok({"questions": QUESTIONS})


@router.post("/submit")
async def submit_intent(
    body: IntentSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit intent answers → compute active_role → save to DB → update user.
    Can be re-submitted at any time to change role (role is never permanent).
    """
    role, tier_required = _compute_role(body.answers)
    kyc_upgrade_needed = current_user.kyc_tier < tier_required

    answers_dict = body.answers.model_dump()

    # Upsert: update existing intent or create new one
    result = await db.execute(
        select(UserIntent).where(UserIntent.user_id == current_user.user_id)
        .order_by(UserIntent.created_at.desc())
        .limit(1)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.intent_response = answers_dict
        existing.active_role = role
        existing.kyc_tier_required = tier_required
        existing.updated_at = datetime.utcnow()
    else:
        intent = UserIntent(
            user_id=current_user.user_id,
            intent_response=answers_dict,
            active_role=role,
            kyc_tier_required=tier_required,
        )
        db.add(intent)

    # Update user's active_role
    current_user.active_role = role
    current_user.updated_at = datetime.utcnow()

    await db.commit()

    return ok(IntentResponse(
        active_role=role,
        kyc_tier_required=tier_required,
        kyc_upgrade_needed=kyc_upgrade_needed,
        message=_ROLE_MESSAGES[role],
        answers=answers_dict,
    ).model_dump())


@router.get("/me")
async def get_my_intent(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the user's current intent and role."""
    result = await db.execute(
        select(UserIntent).where(UserIntent.user_id == current_user.user_id)
        .order_by(UserIntent.created_at.desc())
        .limit(1)
    )
    intent = result.scalar_one_or_none()

    return ok({
        "active_role": current_user.active_role,
        "kyc_tier": current_user.kyc_tier,
        "intent": {
            "answers": intent.intent_response if intent else None,
            "kyc_tier_required": intent.kyc_tier_required if intent else None,
        } if intent else None,
    })
