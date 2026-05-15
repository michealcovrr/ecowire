"""
Modules 11 & 12 ML endpoints — Financial Tracking & Identity

/ml/categorise-entry        — free-form text → structured financial log entry (Claude)
/ml/financial-suggestions   — score breakdown → plain-language improvement tips (Claude)
"""
import json
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CategoriseEntryRequest(BaseModel):
    text: str


class FinancialSuggestionsRequest(BaseModel):
    composite_score: float
    transaction_score: float
    job_completion_score: float
    dispute_score: float
    repayment_score: float
    community_trust_score: float
    engagement_score: float
    days_on_platform: int
    eligible_products: list[str]
    locked_products: list[str]


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_CATEGORISE_SYSTEM = """You are a Nigerian financial assistant.
Read a free-form text entry about money — which may be in English, Pidgin, Yoruba, Igbo, or Hausa —
and extract structured financial data.

Return ONLY valid JSON with exactly this structure:
{
  "type": "income" | "expense" | "debt_owed" | "debt_owing",
  "amount": integer_in_kobo,
  "category": "trade" | "service" | "transport" | "food" | "rent" | "salary" | "loan" | "general",
  "tags": { "item": "...", "quantity": number_or_null, "counterparty": "name_or_null" }
}

Rules:
- amount is ALWAYS in kobo (multiply naira by 100). "45k" = 45000 naira = 4500000 kobo
- type: income if money came IN, expense if money went OUT, debt_owed if someone owes you, debt_owing if you owe someone
- Handle: "k" = thousand, "m" = million, "₦" prefix, informal amounts
- Pidgin: "I sell am for 5k" = income 5000 naira; "I buy am" = expense

Examples:
  Input:  "I sold 10 bags of rice for ₦45,000"
  Output: {"type":"income","amount":4500000,"category":"trade","tags":{"item":"rice","quantity":10,"counterparty":null}}

  Input:  "I spent 3k on fuel for my keke today"
  Output: {"type":"expense","amount":300000,"category":"transport","tags":{"item":"fuel","quantity":null,"counterparty":null}}

  Input:  "Emeka owes me 8,000 for the chairs I gave him"
  Output: {"type":"debt_owed","amount":800000,"category":"trade","tags":{"item":"chairs","quantity":null,"counterparty":"Emeka"}}

  Input:  "I use 15k do payment for the generator I buy on credit"
  Output: {"type":"expense","amount":1500000,"category":"general","tags":{"item":"generator","quantity":null,"counterparty":null}}
"""

_SUGGESTIONS_SYSTEM = """You are a friendly Nigerian financial coach.
Given a user's financial identity score breakdown, write 3 specific, actionable improvement suggestions.

Rules:
- Write in simple, clear English (no jargon)
- Be specific: mention actual numbers and actions
- Focus on the lowest-scoring components that block the next product unlock
- Keep each suggestion to one sentence
- Return ONLY a JSON array of 3 strings, nothing else

The products unlock at these thresholds:
- micro_savings: score >= 20, 30+ days on platform
- micro_insurance: score >= 40, 90+ days, max 1 dispute
- micro_loan: score >= 60, 180+ days, Tier 2 KYC
- working_capital: score >= 80, Tier 3 KYC, business role
"""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/categorise-entry")
async def categorise_entry(body: CategoriseEntryRequest):
    """
    Extract structured financial data from a free-form text entry.
    Handles English, Pidgin, Yoruba, Igbo, and Hausa.
    Returns {type, amount, category, tags}.
    """
    if not settings.anthropic_api_key:
        return {"type": "income", "amount": 0, "category": "general", "tags": {}}

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=_CATEGORISE_SYSTEM,
            messages=[{"role": "user", "content": body.text}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1].lstrip("json").strip()
        result = json.loads(raw)

        return {
            "type": result.get("type", "income"),
            "amount": int(result.get("amount", 0)),
            "category": result.get("category", "general"),
            "tags": result.get("tags", {}),
        }

    except Exception as exc:
        return {"type": "income", "amount": 0, "category": "general", "tags": {}, "_error": str(exc)}


@router.post("/financial-suggestions")
async def financial_suggestions(body: FinancialSuggestionsRequest):
    """
    Generate 3 plain-language improvement suggestions from a user's score breakdown.
    Returns {suggestions: string[]}.
    """
    if not settings.anthropic_api_key:
        return {"suggestions": [
            "Log your income and expenses regularly to improve your financial score.",
            "Complete more jobs on the platform to build your job completion record.",
            "Build community connections to unlock more financial products.",
        ]}

    try:
        import anthropic

        score_summary = f"""
Composite score: {body.composite_score}/100
Days on platform: {body.days_on_platform}
Component scores:
- Transaction activity: {body.transaction_score}/100
- Job completion: {body.job_completion_score}/100
- Dispute record: {body.dispute_score}/100 (higher = fewer disputes)
- Loan repayment: {body.repayment_score}/100
- Community trust: {body.community_trust_score}/100
- Platform engagement: {body.engagement_score}/100

Products already unlocked: {', '.join(body.eligible_products) or 'none yet'}
Products still locked: {', '.join(body.locked_products) or 'none'}
"""
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=_SUGGESTIONS_SYSTEM,
            messages=[{"role": "user", "content": score_summary}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1].lstrip("json").strip()
        suggestions = json.loads(raw)
        if not isinstance(suggestions, list):
            suggestions = [str(suggestions)]
        return {"suggestions": suggestions[:3]}

    except Exception as exc:
        return {
            "suggestions": [
                "Log your transactions consistently every week to build your financial record.",
                "Complete more jobs without disputes to strengthen your profile.",
                "Invite community connections to build trust signals.",
            ],
            "_error": str(exc),
        }
