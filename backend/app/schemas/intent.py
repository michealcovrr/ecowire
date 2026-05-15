from pydantic import BaseModel
from typing import Any


class IntentAnswers(BaseModel):
    # Q1: primary goal
    primary_goal: str          # "work" | "hire" | "business" | "financial" | "basic"
    # Q2: earns money from activity
    makes_money: bool = False
    # Q3: type of activity (only if makes_money=True)
    activity_type: str = ""    # "trade" | "service" | "transport" | "other"
    # Q4: wants to hire
    wants_to_hire: bool = False
    # Q5: needs financial support
    needs_financial_support: bool = False


class IntentSubmitRequest(BaseModel):
    answers: IntentAnswers
    # Optional free-text that ML can parse (voice/typed). Ignored if structured answers are present.
    raw_text: str = ""


class IntentResponse(BaseModel):
    active_role: str
    kyc_tier_required: int
    kyc_upgrade_needed: bool
    message: str
    answers: dict[str, Any]
