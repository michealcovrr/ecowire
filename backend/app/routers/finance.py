"""
Modules 11, 12 & 13 — Financial Tracking, Behavioral Identity, and Financial Products

MODULE 11 — FINANCIAL TRACKING
  POST /finance/log              — log income/expense/debt (text)
  POST /finance/log/voice        — log from voice recording
  GET  /finance/logs             — list all logs with running totals
  GET  /finance/summary          — period summary (weekly/monthly)
  POST /finance/import-squad     — auto-import Squad wallet transactions
  POST /finance/debt             — record an informal debt
  GET  /finance/debts            — list debt records
  PATCH /finance/debt/{id}/settle — mark debt as settled

MODULE 12 — BEHAVIORAL FINANCIAL IDENTITY
  GET  /finance/identity         — full score breakdown + eligible products + suggestions
  POST /finance/identity/refresh — recalculate and persist score

MODULE 13 — FINANCIAL PRODUCTS
  GET  /finance/products         — all products with locked/unlocked state + progress bars

  POST /finance/loans/apply      — apply for a micro-loan (Squad disbursal)
  GET  /finance/loans            — list my loans
  POST /finance/loans/{id}/repay — make a repayment (Squad transfer)

  POST /finance/savings          — create a savings plan
  GET  /finance/savings          — list savings plans
  PATCH /finance/savings/{id}/pause — pause auto-debit

  POST /finance/insurance        — activate a micro-insurance policy
  GET  /finance/insurance        — list active policies
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, SquadAccount
from app.models.financial import (
    FinancialLog, DebtRecord, FinancialIdentity,
    Loan, SavingsPlan, InsurancePolicy,
)
from app.models.profile import WorkProfile
from app.models.transaction import Transaction
from app.models.community import Recommendation
from app.schemas.common import ok
from app.services import squad_service
from app.services.ml_service import (
    categorise_financial_entry, transcribe, financial_suggestions,
)
from app.utils.security import get_current_user

router = APIRouter()


# ============================================================
# PREDEFINED INSURANCE PRODUCTS (Module 13)
# ============================================================

_INSURANCE_PRODUCTS = {
    "health_cover": {
        "product_name": "EcoNet Health Cover",
        "provider": "Curacel Partners",
        "premium_kobo": 50_000,        # ₦500/month
        "frequency": "monthly",
        "description": "Basic outpatient and emergency health cover",
    },
    "life_cover": {
        "product_name": "EcoNet Life Cover",
        "provider": "Casava Insurance",
        "premium_kobo": 100_000,       # ₦1,000/month
        "frequency": "monthly",
        "description": "Life insurance up to ₦500,000",
    },
    "equipment_cover": {
        "product_name": "EcoNet Equipment Cover",
        "provider": "AXA Mansard",
        "premium_kobo": 75_000,        # ₦750/month
        "frequency": "monthly",
        "description": "Covers tools and work equipment up to ₦200,000",
    },
}


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class LogEntryRequest(BaseModel):
    text: str                          # "I sold 10 bags of rice for ₦45,000"


class VoiceLogRequest(BaseModel):
    audio_url: str


class DebtRequest(BaseModel):
    debtor_name: str
    amount_kobo: int
    reason: str
    debtor_user_id: Optional[str] = None


class LoanApplyRequest(BaseModel):
    amount_kobo: int
    purpose: str
    repayment_months: int = 2          # 1, 2, or 3


class SavingsCreateRequest(BaseModel):
    target_amount_kobo: int
    frequency: str                     # "daily" or "weekly"
    auto_debit_amount_kobo: int
    goal_description: Optional[str] = None


class InsuranceActivateRequest(BaseModel):
    product_key: str                   # "health_cover", "life_cover", "equipment_cover"


class RepayRequest(BaseModel):
    amount_kobo: int


# ============================================================
# SCORING ENGINE (Module 12)
# ============================================================

async def _build_identity(db: AsyncSession, user: User) -> dict:
    """
    Query all relevant tables and compute the full financial identity.
    Returns a dict with all component scores, composite, eligible products,
    progress metrics, and a list of locked products with progress percentages.
    """
    now = datetime.utcnow()
    days_on_platform = max(1, (now - user.created_at).days) if user.created_at else 1

    # --- Work profile ---
    prof_result = await db.execute(
        select(WorkProfile).where(WorkProfile.user_id == user.user_id)
    )
    profile = prof_result.scalar_one_or_none()
    completion_count = profile.job_completion_count if profile else 0
    dispute_count = profile.dispute_count if profile else 0

    # --- Wallet transactions (last 90 days) ---
    ninety_ago = now - timedelta(days=90)
    txn_result = await db.execute(
        select(Transaction).where(
            (Transaction.sender_user_id == user.user_id) |
            (Transaction.receiver_user_id == user.user_id),
            Transaction.timestamp >= ninety_ago,
            Transaction.status == "completed",
        )
    )
    recent_txns = txn_result.scalars().all()
    txn_count = len(recent_txns)

    # --- Financial log entries ---
    log_result = await db.execute(
        select(FinancialLog).where(FinancialLog.user_id == user.user_id)
    )
    all_logs = log_result.scalars().all()
    log_count = len(all_logs)
    income_total = sum(l.amount or 0 for l in all_logs if l.entry_type == "income")
    expense_total = sum(l.amount or 0 for l in all_logs if l.entry_type == "expense")

    # --- Loan repayment history ---
    loan_result = await db.execute(
        select(Loan).where(Loan.user_id == user.user_id)
    )
    loans = loan_result.scalars().all()
    if loans:
        total_owed = sum(l.amount or 0 for l in loans)
        total_repaid = sum(l.amount_repaid or 0 for l in loans)
        repayment_rate = min(1.0, total_repaid / total_owed) if total_owed > 0 else 1.0
        has_defaulted = any(l.status == "defaulted" for l in loans)
        if has_defaulted:
            repayment_rate *= 0.5
    else:
        repayment_rate = 0.5           # neutral — no history yet

    # --- Community trust (recommendations received) ---
    rec_result = await db.execute(
        select(func.count()).where(Recommendation.worker_user_id == user.user_id)
    )
    recommendation_count = rec_result.scalar() or 0

    # ---- SCORE COMPONENTS ----

    # 1. Transaction score (0-100): wallet activity + financial log consistency
    txn_score = min(txn_count * 4, 60) + min(log_count * 4, 40)
    txn_score = min(float(txn_score), 100.0)

    # 2. Job completion score (0-100)
    total_jobs = completion_count + dispute_count
    if total_jobs > 0:
        rate = completion_count / total_jobs
        job_score = rate * 80 + min(completion_count * 4, 20)
    else:
        job_score = 0.0

    # 3. Dispute score (0-100) — higher means fewer disputes
    dispute_score = max(0.0, 100.0 - dispute_count * 25)

    # 4. Repayment score (0-100)
    repayment_score = round(repayment_rate * 100, 2)

    # 5. Community trust score (0-100)
    community_score = min(float(recommendation_count * 25), 100.0)

    # 6. Engagement score (0-100): platform age + log regularity
    age_score = min(days_on_platform / 180 * 60, 60.0)
    regularity_score = min(log_count * 4, 40.0)
    engagement_score = age_score + regularity_score

    # Composite (weighted)
    composite = round(
        txn_score        * 0.25 +
        job_score        * 0.20 +
        dispute_score    * 0.15 +
        repayment_score  * 0.15 +
        community_score  * 0.15 +
        engagement_score * 0.10,
        2,
    )

    # ---- PRODUCT ELIGIBILITY ----
    eligible: list[str] = []
    locked: list[str] = []

    _products = [
        ("micro_savings",    composite >= 20 and days_on_platform >= 30),
        ("micro_insurance",  composite >= 40 and days_on_platform >= 90 and dispute_count <= 1),
        ("micro_loan",       composite >= 60 and days_on_platform >= 180 and user.kyc_tier >= 2),
        ("working_capital",  composite >= 80 and user.kyc_tier >= 3 and user.active_role in ("business", "employer")),
    ]
    for name, unlocked in _products:
        (eligible if unlocked else locked).append(name)

    # ---- PROGRESS TOWARD NEXT LOCK ----
    def _pct(actual, required):
        return min(100, round(actual / required * 100)) if required else 100

    product_progress = {
        "micro_savings": {
            "score": _pct(composite, 20),
            "days": _pct(days_on_platform, 30),
        },
        "micro_insurance": {
            "score": _pct(composite, 40),
            "days": _pct(days_on_platform, 90),
            "disputes_ok": dispute_count <= 1,
        },
        "micro_loan": {
            "score": _pct(composite, 60),
            "days": _pct(days_on_platform, 180),
            "kyc_tier": _pct(user.kyc_tier, 2),
        },
        "working_capital": {
            "score": _pct(composite, 80),
            "kyc_tier": _pct(user.kyc_tier, 3),
            "business_role": user.active_role in ("business", "employer"),
        },
    }

    # ---- MAX LOAN ELIGIBILITY ----
    if "micro_loan" in eligible:
        if composite >= 90:
            max_loan_kobo = 10_000_000   # ₦100k
            interest_rate = 5.0
        elif composite >= 80:
            max_loan_kobo = 5_000_000    # ₦50k
            interest_rate = 6.0
        elif composite >= 70:
            max_loan_kobo = 2_500_000    # ₦25k
            interest_rate = 8.0
        else:
            max_loan_kobo = 1_000_000    # ₦10k
            interest_rate = 10.0
    else:
        max_loan_kobo = 0
        interest_rate = 0.0

    return {
        "composite_score": composite,
        "transaction_score": round(txn_score, 2),
        "job_completion_score": round(job_score, 2),
        "dispute_score": round(dispute_score, 2),
        "repayment_score": round(repayment_score, 2),
        "community_trust_score": round(community_score, 2),
        "engagement_score": round(engagement_score, 2),
        "eligible_products": eligible,
        "locked_products": locked,
        "product_progress": product_progress,
        "days_on_platform": days_on_platform,
        "income_total_naira": round(income_total / 100, 2),
        "expense_total_naira": round(expense_total / 100, 2),
        "max_loan_naira": max_loan_kobo / 100,
        "loan_interest_rate": interest_rate,
        "max_loan_kobo": max_loan_kobo,
    }


# ============================================================
# MODULE 11 — FINANCIAL TRACKING
# ============================================================

@router.post("/log")
async def log_entry(
    body: LogEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log a financial entry from free-form text.
    Claude extracts: type (income/expense/debt), amount, category, and tags.
    Example: "I sold 10 bags of rice for ₦45,000"
    """
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    parsed = await categorise_financial_entry(body.text)

    entry = FinancialLog(
        user_id=current_user.user_id,
        entry_type=parsed.get("type", "income"),
        amount=parsed.get("amount", 0),
        category=parsed.get("category", "general"),
        description_raw=body.text,
        ai_extracted_tags=parsed.get("tags", {}),
        source="manual",
    )
    db.add(entry)
    await db.commit()

    return ok({
        "log_id": entry.log_id,
        "entry_type": entry.entry_type,
        "amount_naira": entry.amount / 100 if entry.amount else 0,
        "category": entry.category,
        "tags": entry.ai_extracted_tags,
        "timestamp": entry.timestamp.isoformat(),
    })


@router.post("/log/voice")
async def log_entry_voice(
    body: VoiceLogRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Log a financial entry from a voice recording.
    Whisper transcribes → Claude extracts the financial data.
    Audio must already be uploaded to Cloudinary; pass the URL.
    """
    if not body.audio_url.strip():
        raise HTTPException(status_code=400, detail="audio_url is required")

    transcription = await transcribe(body.audio_url)
    text = transcription.get("text", "").strip()
    if not text:
        raise HTTPException(
            status_code=422,
            detail="Could not transcribe audio — file may be silent or unsupported",
        )

    parsed = await categorise_financial_entry(text)

    entry = FinancialLog(
        user_id=current_user.user_id,
        entry_type=parsed.get("type", "income"),
        amount=parsed.get("amount", 0),
        category=parsed.get("category", "general"),
        description_raw=text,
        ai_extracted_tags={**(parsed.get("tags") or {}), "source_language": transcription.get("language", "en")},
        source="manual",
    )
    db.add(entry)
    await db.commit()

    return ok({
        "log_id": entry.log_id,
        "transcribed_text": text,
        "entry_type": entry.entry_type,
        "amount_naira": entry.amount / 100 if entry.amount else 0,
        "category": entry.category,
        "tags": entry.ai_extracted_tags,
    })


@router.get("/logs")
async def get_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, le=200),
    entry_type: Optional[str] = Query(None),
):
    """List all financial log entries with running income/expense totals."""
    query = select(FinancialLog).where(FinancialLog.user_id == current_user.user_id)
    if entry_type:
        query = query.where(FinancialLog.entry_type == entry_type)
    query = query.order_by(FinancialLog.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    all_result = await db.execute(
        select(FinancialLog).where(FinancialLog.user_id == current_user.user_id)
    )
    all_logs = all_result.scalars().all()
    income_total = sum(l.amount or 0 for l in all_logs if l.entry_type == "income")
    expense_total = sum(l.amount or 0 for l in all_logs if l.entry_type == "expense")

    return ok({
        "totals": {
            "income_naira": round(income_total / 100, 2),
            "expense_naira": round(expense_total / 100, 2),
            "net_naira": round((income_total - expense_total) / 100, 2),
        },
        "logs": [
            {
                "log_id": l.log_id,
                "entry_type": l.entry_type,
                "amount_naira": l.amount / 100 if l.amount else 0,
                "category": l.category,
                "description": l.description_raw,
                "tags": l.ai_extracted_tags,
                "source": l.source,
                "timestamp": l.timestamp.isoformat(),
            }
            for l in logs
        ],
    })


@router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    period: str = Query("monthly", regex="^(weekly|monthly)$"),
):
    """Income/expense summary grouped by category for the current period."""
    now = datetime.utcnow()
    if period == "weekly":
        start = now - timedelta(days=7)
        label = "Last 7 days"
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = now.strftime("%B %Y")

    result = await db.execute(
        select(FinancialLog).where(
            FinancialLog.user_id == current_user.user_id,
            FinancialLog.timestamp >= start,
        )
    )
    logs = result.scalars().all()

    by_category: dict[str, dict] = {}
    for l in logs:
        cat = l.category or "general"
        if cat not in by_category:
            by_category[cat] = {"income": 0, "expense": 0}
        if l.entry_type == "income":
            by_category[cat]["income"] += l.amount or 0
        elif l.entry_type == "expense":
            by_category[cat]["expense"] += l.amount or 0

    total_income = sum(l.amount or 0 for l in logs if l.entry_type == "income")
    total_expense = sum(l.amount or 0 for l in logs if l.entry_type == "expense")

    return ok({
        "period": label,
        "total_income_naira": round(total_income / 100, 2),
        "total_expense_naira": round(total_expense / 100, 2),
        "net_naira": round((total_income - total_expense) / 100, 2),
        "by_category": {
            cat: {
                "income_naira": round(v["income"] / 100, 2),
                "expense_naira": round(v["expense"] / 100, 2),
            }
            for cat, v in by_category.items()
        },
    })


@router.post("/import-squad")
async def import_squad_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pull the user's Squad transaction history and import any entries
    not yet in the financial log (deduped by squad transaction ID).
    Tagged as source='squad_auto'.
    """
    squad_result = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == current_user.user_id)
    )
    squad_acct = squad_result.scalar_one_or_none()
    if not squad_acct:
        raise HTTPException(status_code=404, detail="No Squad account found")

    try:
        resp = await squad_service.get_transactions(squad_acct.squad_customer_identifier)
        squad_txns = resp.get("data", {}).get("transactions", []) or []
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch Squad transactions: {exc}")

    imported = 0
    for txn in squad_txns:
        txn_id = txn.get("transaction_ref") or txn.get("id") or txn.get("reference")
        if not txn_id:
            continue

        # Check if already imported (stored in ai_extracted_tags)
        existing = await db.execute(
            select(FinancialLog).where(
                FinancialLog.user_id == current_user.user_id,
                FinancialLog.source == "squad_auto",
                FinancialLog.ai_extracted_tags["squad_txn_id"].astext == txn_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Determine direction: credit = income, debit = expense
        txn_type = txn.get("transaction_type", "").lower()
        amount_raw = txn.get("amount", 0)
        try:
            amount_kobo = int(float(amount_raw))
        except (ValueError, TypeError):
            amount_kobo = 0

        entry_type = "income" if "credit" in txn_type or txn_type == "inflow" else "expense"

        entry = FinancialLog(
            user_id=current_user.user_id,
            entry_type=entry_type,
            amount=amount_kobo,
            category="general",
            description_raw=txn.get("narration") or txn.get("description") or "Squad transaction",
            ai_extracted_tags={"squad_txn_id": txn_id, "squad_type": txn_type},
            source="squad_auto",
            timestamp=datetime.utcnow(),
        )
        db.add(entry)
        imported += 1

    await db.commit()
    return ok({"imported": imported, "message": f"{imported} Squad transactions imported."})


@router.post("/debt")
async def log_debt(
    body: DebtRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log an informal debt — either someone owes you or you owe someone."""
    debt = DebtRecord(
        creditor_user_id=current_user.user_id,
        debtor_name=body.debtor_name,
        debtor_user_id=body.debtor_user_id,
        amount=body.amount_kobo,
        reason=body.reason,
        status="outstanding",
    )
    db.add(debt)
    await db.commit()

    return ok({
        "debt_id": debt.debt_id,
        "debtor_name": debt.debtor_name,
        "amount_naira": debt.amount / 100,
        "reason": debt.reason,
        "status": debt.status,
        "created_at": debt.created_at.isoformat(),
    })


@router.get("/debts")
async def get_debts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
):
    """List all informal debts logged by the user."""
    query = select(DebtRecord).where(DebtRecord.creditor_user_id == current_user.user_id)
    if status:
        query = query.where(DebtRecord.status == status)
    query = query.order_by(DebtRecord.created_at.desc())

    result = await db.execute(query)
    debts = result.scalars().all()
    outstanding_total = sum(d.amount or 0 for d in debts if d.status == "outstanding")

    return ok({
        "outstanding_total_naira": round(outstanding_total / 100, 2),
        "debts": [
            {
                "debt_id": d.debt_id,
                "debtor_name": d.debtor_name,
                "debtor_user_id": d.debtor_user_id,
                "amount_naira": d.amount / 100 if d.amount else 0,
                "reason": d.reason,
                "status": d.status,
                "created_at": d.created_at.isoformat(),
            }
            for d in debts
        ],
    })


@router.patch("/debt/{debt_id}/settle")
async def settle_debt(
    debt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark an informal debt as settled."""
    result = await db.execute(
        select(DebtRecord).where(
            DebtRecord.debt_id == debt_id,
            DebtRecord.creditor_user_id == current_user.user_id,
        )
    )
    debt = result.scalar_one_or_none()
    if not debt:
        raise HTTPException(status_code=404, detail="Debt record not found")
    if debt.status == "settled":
        raise HTTPException(status_code=400, detail="Already settled")

    debt.status = "settled"
    await db.commit()
    return ok({"debt_id": debt_id, "status": "settled"})


# ============================================================
# MODULE 12 — BEHAVIORAL FINANCIAL IDENTITY
# ============================================================

@router.get("/identity")
async def get_identity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the user's full financial identity: component scores, composite,
    eligible/locked products with progress bars, and AI improvement suggestions.
    Score is NOT shown as a raw number to the user — use product_progress for the UI.
    """
    scores = await _build_identity(db, current_user)

    # Fetch AI suggestions from ML service
    suggestions = await financial_suggestions({
        "composite_score": scores["composite_score"],
        "transaction_score": scores["transaction_score"],
        "job_completion_score": scores["job_completion_score"],
        "dispute_score": scores["dispute_score"],
        "repayment_score": scores["repayment_score"],
        "community_trust_score": scores["community_trust_score"],
        "engagement_score": scores["engagement_score"],
        "days_on_platform": scores["days_on_platform"],
        "eligible_products": scores["eligible_products"],
        "locked_products": scores["locked_products"],
    })

    return ok({**scores, "improvement_suggestions": suggestions})


@router.post("/identity/refresh")
async def refresh_identity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recompute and persist the user's financial identity score.
    Called automatically after major events (job completion, loan repayment).
    Can also be called manually.
    """
    scores = await _build_identity(db, current_user)

    identity_result = await db.execute(
        select(FinancialIdentity).where(FinancialIdentity.user_id == current_user.user_id)
    )
    identity = identity_result.scalar_one_or_none()

    if identity:
        identity.transaction_score = scores["transaction_score"]
        identity.job_completion_score = scores["job_completion_score"]
        identity.dispute_score = scores["dispute_score"]
        identity.repayment_score = scores["repayment_score"]
        identity.community_trust_score = scores["community_trust_score"]
        identity.engagement_score = scores["engagement_score"]
        identity.composite_score = scores["composite_score"]
        identity.eligible_products = scores["eligible_products"]
        identity.last_updated = datetime.utcnow()
    else:
        identity = FinancialIdentity(
            user_id=current_user.user_id,
            transaction_score=scores["transaction_score"],
            job_completion_score=scores["job_completion_score"],
            dispute_score=scores["dispute_score"],
            repayment_score=scores["repayment_score"],
            community_trust_score=scores["community_trust_score"],
            engagement_score=scores["engagement_score"],
            composite_score=scores["composite_score"],
            eligible_products=scores["eligible_products"],
        )
        db.add(identity)

    await db.commit()
    return ok({"message": "Identity score refreshed.", **scores})


# ============================================================
# MODULE 13 — FINANCIAL PRODUCTS
# ============================================================

@router.get("/products")
async def get_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Show all financial products with locked/unlocked state and progress bars.
    This is the main financial products dashboard view.
    """
    scores = await _build_identity(db, current_user)
    eligible = set(scores["eligible_products"])

    products = [
        {
            "key": "micro_savings",
            "name": "Micro-Savings",
            "description": "Set aside money automatically every day or week toward a goal.",
            "unlocked": "micro_savings" in eligible,
            "progress": scores["product_progress"]["micro_savings"],
            "requirements": "30 days on platform + basic activity",
        },
        {
            "key": "micro_insurance",
            "name": "Micro-Insurance",
            "description": "Affordable health, life, or equipment cover from ₦500/month.",
            "unlocked": "micro_insurance" in eligible,
            "progress": scores["product_progress"]["micro_insurance"],
            "requirements": "90 days on platform + score ≥ 40 + max 1 dispute",
        },
        {
            "key": "micro_loan",
            "name": "Micro-Loan",
            "description": f"Borrow up to ₦{scores['max_loan_naira']:,.0f} based on your activity record.",
            "unlocked": "micro_loan" in eligible,
            "progress": scores["product_progress"]["micro_loan"],
            "requirements": "180 days on platform + score ≥ 60 + Tier 2 KYC",
            "max_amount_naira": scores["max_loan_naira"],
            "interest_rate_pct": scores["loan_interest_rate"],
        },
        {
            "key": "working_capital",
            "name": "Working Capital",
            "description": "Larger business loans for verified traders and employers.",
            "unlocked": "working_capital" in eligible,
            "progress": scores["product_progress"]["working_capital"],
            "requirements": "Score ≥ 80 + Tier 3 KYC + business/employer role",
        },
    ]

    return ok({
        "composite_score": scores["composite_score"],
        "days_on_platform": scores["days_on_platform"],
        "products": products,
    })


# ---- LOANS ----

@router.post("/loans/apply")
async def apply_for_loan(
    body: LoanApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Apply for a micro-loan. Eligibility is checked against the financial identity score.
    Funds are disbursed to the user's Squad virtual account via Transfer API.
    """
    scores = await _build_identity(db, current_user)

    if "micro_loan" not in scores["eligible_products"] and "working_capital" not in scores["eligible_products"]:
        raise HTTPException(
            status_code=403,
            detail=f"Not yet eligible for a loan. Current score: {scores['composite_score']}/100. "
                   f"You need 60+ and 180 days on platform with Tier 2 KYC.",
        )

    max_kobo = scores["max_loan_kobo"]
    if body.amount_kobo > max_kobo:
        raise HTTPException(
            status_code=400,
            detail=f"Requested amount ₦{body.amount_kobo/100:,.2f} exceeds your maximum of ₦{max_kobo/100:,.0f}.",
        )
    if body.repayment_months not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="repayment_months must be 1, 2, or 3")

    # Check no active loan already outstanding
    active_loan = await db.execute(
        select(Loan).where(Loan.user_id == current_user.user_id, Loan.status == "active")
    )
    if active_loan.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You already have an active loan. Repay it before applying for another.")

    interest_rate = scores["loan_interest_rate"]
    monthly_rate = interest_rate / 100
    total_repayable = int(body.amount_kobo * (1 + monthly_rate * body.repayment_months))
    monthly_payment = total_repayable // body.repayment_months

    repayment_schedule = [
        {
            "month": i + 1,
            "due_date": (datetime.utcnow() + timedelta(days=30 * (i + 1))).strftime("%Y-%m-%d"),
            "amount_kobo": monthly_payment,
            "amount_naira": round(monthly_payment / 100, 2),
        }
        for i in range(body.repayment_months)
    ]

    # Disburse via Squad Transfer API
    squad_acct = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == current_user.user_id)
    )
    squad_account = squad_acct.scalar_one_or_none()
    if not squad_account or not squad_account.squad_account_number:
        raise HTTPException(status_code=404, detail="No Squad account found for this user")

    loan = Loan(
        user_id=current_user.user_id,
        amount=body.amount_kobo,
        interest_rate=interest_rate,
        repayment_schedule=repayment_schedule,
        amount_repaid=0,
        status="active",
        disbursed_at=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=30 * body.repayment_months),
    )
    db.add(loan)
    await db.flush()

    try:
        await squad_service.transfer(
            account_number=squad_account.squad_account_number,
            bank_code="000",
            account_name=current_user.full_name or "EcoNet User",
            amount=body.amount_kobo,
            narration=f"EcoNet Micro-Loan — {body.purpose}",
            transaction_ref=loan.loan_id,
        )
        disbursal_status = "disbursed"
    except Exception as exc:
        disbursal_status = "pending"
        print(f"[WARN] Loan Squad transfer failed for {loan.loan_id}: {exc}", flush=True)

    # Log as a transaction
    txn = Transaction(
        receiver_user_id=current_user.user_id,
        amount=body.amount_kobo,
        type="loan",
        channel="self",
        status="completed" if disbursal_status == "disbursed" else "pending",
        tagged_as="personal",
        timestamp=datetime.utcnow(),
    )
    db.add(txn)
    await db.commit()

    return ok({
        "loan_id": loan.loan_id,
        "amount_naira": body.amount_kobo / 100,
        "interest_rate_pct": interest_rate,
        "total_repayable_naira": total_repayable / 100,
        "monthly_payment_naira": monthly_payment / 100,
        "repayment_months": body.repayment_months,
        "repayment_schedule": repayment_schedule,
        "disbursal_status": disbursal_status,
        "due_date": loan.due_date.strftime("%Y-%m-%d"),
    })


@router.get("/loans")
async def get_loans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all loans for the current user."""
    result = await db.execute(
        select(Loan).where(Loan.user_id == current_user.user_id).order_by(Loan.disbursed_at.desc())
    )
    loans = result.scalars().all()
    return ok({
        "loans": [
            {
                "loan_id": l.loan_id,
                "amount_naira": l.amount / 100 if l.amount else 0,
                "amount_repaid_naira": l.amount_repaid / 100 if l.amount_repaid else 0,
                "outstanding_naira": max(0, (l.amount or 0) - (l.amount_repaid or 0)) / 100,
                "interest_rate": float(l.interest_rate) if l.interest_rate else 0,
                "status": l.status,
                "repayment_schedule": l.repayment_schedule,
                "disbursed_at": l.disbursed_at.isoformat() if l.disbursed_at else None,
                "due_date": l.due_date.isoformat() if l.due_date else None,
            }
            for l in loans
        ]
    })


@router.post("/loans/{loan_id}/repay")
async def repay_loan(
    loan_id: str,
    body: RepayRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Make a loan repayment. Debits the user's Squad wallet.
    Triggers an identity score refresh after successful repayment.
    """
    result = await db.execute(
        select(Loan).where(Loan.loan_id == loan_id, Loan.user_id == current_user.user_id)
    )
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.status != "active":
        raise HTTPException(status_code=400, detail=f"Loan is already {loan.status}")

    outstanding = (loan.amount or 0) - (loan.amount_repaid or 0)
    amount_to_repay = min(body.amount_kobo, outstanding)

    squad_acct_result = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == current_user.user_id)
    )
    squad_account = squad_acct_result.scalar_one_or_none()

    try:
        await squad_service.transfer(
            account_number=squad_account.squad_account_number if squad_account else "0000000000",
            bank_code="000",
            account_name="EcoNet Loan Repayment",
            amount=amount_to_repay,
            narration=f"Loan repayment — {loan_id[:8]}",
            transaction_ref=f"repay-{loan_id}-{int(datetime.utcnow().timestamp())}",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Repayment transfer failed: {exc}")

    loan.amount_repaid = (loan.amount_repaid or 0) + amount_to_repay
    new_outstanding = (loan.amount or 0) - loan.amount_repaid

    if new_outstanding <= 0:
        loan.status = "completed"

    txn = Transaction(
        sender_user_id=current_user.user_id,
        amount=amount_to_repay,
        type="repayment",
        channel="self",
        status="completed",
        tagged_as="personal",
        timestamp=datetime.utcnow(),
    )
    db.add(txn)
    await db.commit()

    return ok({
        "loan_id": loan_id,
        "amount_repaid_naira": amount_to_repay / 100,
        "total_repaid_naira": loan.amount_repaid / 100,
        "outstanding_naira": max(0, new_outstanding) / 100,
        "loan_status": loan.status,
    })


# ---- SAVINGS ----

@router.post("/savings")
async def create_savings_plan(
    body: SavingsCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a savings plan with automatic debit on a daily or weekly schedule.
    Eligibility: micro_savings product must be unlocked.
    """
    scores = await _build_identity(db, current_user)
    if "micro_savings" not in scores["eligible_products"]:
        raise HTTPException(
            status_code=403,
            detail="Savings not yet unlocked. Keep using the platform for 30 days with consistent activity.",
        )
    if body.frequency not in ("daily", "weekly"):
        raise HTTPException(status_code=400, detail="frequency must be 'daily' or 'weekly'")

    plan = SavingsPlan(
        user_id=current_user.user_id,
        target_amount=body.target_amount_kobo,
        current_amount=0,
        frequency=body.frequency,
        auto_debit_amount=body.auto_debit_amount_kobo,
        goal_description=body.goal_description,
        status="active",
    )
    db.add(plan)
    await db.commit()

    return ok({
        "savings_id": plan.savings_id,
        "target_naira": body.target_amount_kobo / 100,
        "auto_debit_naira": body.auto_debit_amount_kobo / 100,
        "frequency": body.frequency,
        "goal": body.goal_description,
        "status": "active",
        "message": f"Savings plan created. ₦{body.auto_debit_amount_kobo/100:,.2f} will be saved {body.frequency}.",
    })


@router.get("/savings")
async def get_savings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all savings plans."""
    result = await db.execute(
        select(SavingsPlan).where(SavingsPlan.user_id == current_user.user_id)
        .order_by(SavingsPlan.created_at.desc())
    )
    plans = result.scalars().all()
    return ok({
        "plans": [
            {
                "savings_id": p.savings_id,
                "goal": p.goal_description,
                "target_naira": p.target_amount / 100 if p.target_amount else 0,
                "current_naira": p.current_amount / 100 if p.current_amount else 0,
                "progress_pct": round(
                    (p.current_amount or 0) / (p.target_amount or 1) * 100, 1
                ),
                "auto_debit_naira": p.auto_debit_amount / 100 if p.auto_debit_amount else 0,
                "frequency": p.frequency,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in plans
        ]
    })


@router.patch("/savings/{savings_id}/pause")
async def pause_savings(
    savings_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause or resume a savings plan's auto-debit."""
    result = await db.execute(
        select(SavingsPlan).where(
            SavingsPlan.savings_id == savings_id,
            SavingsPlan.user_id == current_user.user_id,
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Savings plan not found")

    plan.status = "paused" if plan.status == "active" else "active"
    await db.commit()
    return ok({"savings_id": savings_id, "status": plan.status})


# ---- INSURANCE ----

@router.post("/insurance")
async def activate_insurance(
    body: InsuranceActivateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Activate a micro-insurance policy. First premium is debited immediately from the Squad wallet.
    Requires micro_insurance to be unlocked.
    """
    scores = await _build_identity(db, current_user)
    if "micro_insurance" not in scores["eligible_products"]:
        raise HTTPException(
            status_code=403,
            detail="Insurance not yet unlocked. You need 90 days on platform, score ≥ 40, and max 1 dispute.",
        )

    product = _INSURANCE_PRODUCTS.get(body.product_key)
    if not product:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown product key. Valid options: {', '.join(_INSURANCE_PRODUCTS.keys())}",
        )

    # Check if already active
    existing = await db.execute(
        select(InsurancePolicy).where(
            InsurancePolicy.user_id == current_user.user_id,
            InsurancePolicy.product_name == product["product_name"],
            InsurancePolicy.status == "active",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You already have an active policy for this product")

    squad_acct_result = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == current_user.user_id)
    )
    squad_account = squad_acct_result.scalar_one_or_none()

    # Debit first premium
    premium = product["premium_kobo"]
    try:
        await squad_service.transfer(
            account_number=squad_account.squad_account_number if squad_account else "0000000000",
            bank_code="000",
            account_name=product["provider"],
            amount=premium,
            narration=f"Insurance premium — {product['product_name']}",
            transaction_ref=f"ins-{current_user.user_id}-{int(datetime.utcnow().timestamp())}",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Premium payment failed: {exc}")

    policy = InsurancePolicy(
        user_id=current_user.user_id,
        product_name=product["product_name"],
        provider=product["provider"],
        premium_amount=premium,
        frequency=product["frequency"],
        status="active",
    )
    db.add(policy)
    await db.commit()

    return ok({
        "policy_id": policy.policy_id,
        "product_name": policy.product_name,
        "provider": policy.provider,
        "premium_naira": premium / 100,
        "frequency": policy.frequency,
        "status": "active",
        "started_at": policy.started_at.isoformat(),
        "message": f"Policy activated. First premium of ₦{premium/100:,.2f} has been charged.",
    })


@router.get("/insurance")
async def get_insurance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all insurance policies plus available products."""
    result = await db.execute(
        select(InsurancePolicy).where(InsurancePolicy.user_id == current_user.user_id)
        .order_by(InsurancePolicy.started_at.desc())
    )
    policies = result.scalars().all()

    return ok({
        "policies": [
            {
                "policy_id": p.policy_id,
                "product_name": p.product_name,
                "provider": p.provider,
                "premium_naira": p.premium_amount / 100 if p.premium_amount else 0,
                "frequency": p.frequency,
                "status": p.status,
                "started_at": p.started_at.isoformat(),
            }
            for p in policies
        ],
        "available_products": [
            {
                "key": k,
                "name": v["product_name"],
                "provider": v["provider"],
                "premium_naira": v["premium_kobo"] / 100,
                "frequency": v["frequency"],
                "description": v["description"],
            }
            for k, v in _INSURANCE_PRODUCTS.items()
        ],
    })
