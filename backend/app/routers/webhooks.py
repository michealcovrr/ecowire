from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.transaction import Transaction
from app.models.job import Job, EscrowRecord
from app.services.squad_service import verify_webhook_signature
from app.schemas.common import ok

router = APIRouter()


@router.post("/squad")
async def squad_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receives all Squad webhook events.
    HMAC-SHA512 signature is verified before any processing.
    """
    raw_body = await request.body()
    signature = request.headers.get("x-squad-encrypted-body", "")

    if not verify_webhook_signature(raw_body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("Event") or payload.get("event")

    if event == "charge_successful":
        await _handle_charge_successful(payload, db)
    elif event == "transfer_successful":
        await _handle_transfer_successful(payload, db)
    elif event == "transfer_failed":
        await _handle_transfer_failed(payload, db)

    return ok({"received": True})


async def _handle_charge_successful(payload: dict, db: AsyncSession) -> None:
    """
    Inbound payment confirmed — money arrived in a virtual account.
    If it's a job escrow DVA, update job status to 'funded' and start 48h auto-release timer.
    """
    data = payload.get("Body", payload.get("body", {}))
    transaction_ref = data.get("transaction_ref") or data.get("transactionRef")
    amount = int(data.get("amount", 0))                 # kobo
    virtual_account = data.get("virtual_account_number") or data.get("account_number")

    # Check idempotency: If we already processed this reference, ignore duplicate webhook
    existing_txn = await db.execute(
        select(Transaction).where(Transaction.squad_reference == transaction_ref)
    )
    if existing_txn.scalar_one_or_none():
        return

    # Check if this is an escrow DVA
    escrow_result = await db.execute(
        select(EscrowRecord).where(EscrowRecord.squad_dva_account_number == virtual_account)
    )
    escrow = escrow_result.scalar_one_or_none()

    if escrow and escrow.status == "pending":
        now = datetime.utcnow()
        escrow.status = "funded"
        escrow.funded_at = now
        escrow.auto_release_at = now + timedelta(hours=48)

        job_result = await db.execute(select(Job).where(Job.job_id == escrow.job_id))
        job = job_result.scalar_one_or_none()
        if job:
            job.status = "funded"
            job.updated_at = now

    # Always log the inbound transaction
    txn = Transaction(
        amount=amount,
        type="receive",
        channel="self",
        squad_reference=transaction_ref,
        status="completed",
        timestamp=datetime.utcnow(),
    )
    db.add(txn)
    await db.commit()


async def _handle_transfer_successful(payload: dict, db: AsyncSession) -> None:
    """Outbound payout confirmed — mark matching transaction as completed."""
    data = payload.get("Body", payload.get("body", {}))
    transaction_ref = data.get("transaction_ref") or data.get("transactionRef")

    if transaction_ref:
        result = await db.execute(
            select(Transaction).where(Transaction.squad_reference == transaction_ref)
        )
        txn = result.scalar_one_or_none()
        if txn and txn.status == "pending":
            txn.status = "completed"
            await db.commit()


async def _handle_transfer_failed(payload: dict, db: AsyncSession) -> None:
    """Outbound payout failed — mark transaction as failed."""
    data = payload.get("Body", payload.get("body", {}))
    transaction_ref = data.get("transaction_ref") or data.get("transactionRef")

    if transaction_ref:
        result = await db.execute(
            select(Transaction).where(Transaction.squad_reference == transaction_ref)
        )
        txn = result.scalar_one_or_none()
        if txn:
            txn.status = "failed"
            await db.commit()
