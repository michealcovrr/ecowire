"""
Module 8 — Job Chat & Agreement System
Module 9 — Escrow & Payment Release

REST polling-based chat (Socket.io can be layered on later).

Endpoints:
  GET  /chat/my                         — all chats for current user
  GET  /chat/{chat_id}/messages          — messages for a chat
  POST /chat/{chat_id}/messages          — send a message
  POST /chat/{chat_id}/agreement         — propose/update agreement terms
  POST /chat/{chat_id}/agreement/confirm — confirm agreement (both parties)
  GET  /chat/{chat_id}/escrow            — get escrow status for this chat's job
  POST /chat/{chat_id}/escrow/create     — employer creates escrow DVA
  POST /chat/{chat_id}/escrow/release    — employer releases payment to worker
  POST /chat/{chat_id}/complete          — worker marks job complete
  POST /chat/{chat_id}/dispute           — open a dispute
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, SquadAccount
from app.models.job import Job, JobChat, ChatMessage, JobAgreement, EscrowRecord, Dispute
from app.schemas.common import ok
from app.services import squad_service
from app.utils.security import get_current_user

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"


class AgreementRequest(BaseModel):
    agreed_price_kobo: int
    job_scope: str
    timeline: str
    conditions: str | None = None


class DisputeRequest(BaseModel):
    reason: str


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_chat_or_404(chat_id: str, db: AsyncSession) -> JobChat:
    result = await db.execute(select(JobChat).where(JobChat.chat_id == chat_id))
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


async def _assert_participant(chat: JobChat, user: User) -> None:
    if user.user_id not in (chat.employer_user_id, chat.worker_user_id):
        raise HTTPException(status_code=403, detail="Not a participant in this chat")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/my")
async def get_my_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(JobChat).where(
            (JobChat.employer_user_id == current_user.user_id) |
            (JobChat.worker_user_id == current_user.user_id)
        ).order_by(JobChat.created_at.desc())
    )
    chats = result.scalars().all()

    rows = []
    for c in chats:
        job_result = await db.execute(select(Job).where(Job.job_id == c.job_id))
        job = job_result.scalar_one_or_none()

        # latest message
        last_msg_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_id == c.chat_id)
            .order_by(ChatMessage.timestamp.desc())
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()

        other_user_id = c.worker_user_id if current_user.user_id == c.employer_user_id else c.employer_user_id
        other_result = await db.execute(select(User).where(User.user_id == other_user_id))
        other = other_result.scalar_one_or_none()

        rows.append({
            "chat_id": c.chat_id,
            "job_id": c.job_id,
            "job_description": job.job_description_raw[:80] if job else "",
            "job_status": job.status if job else "unknown",
            "role": "employer" if current_user.user_id == c.employer_user_id else "worker",
            "other_user_id": other_user_id,
            "other_user_name": other.full_name if other else other_user_id,
            "last_message": last_msg.content[:60] if last_msg else None,
            "last_message_at": last_msg.timestamp.isoformat() if last_msg else c.created_at.isoformat(),
            "created_at": c.created_at.isoformat(),
        })

    return ok({"chats": rows})


@router.get("/{chat_id}/messages")
async def get_messages(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await _get_chat_or_404(chat_id, db)
    await _assert_participant(chat, current_user)

    msgs_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.timestamp.asc())
    )
    msgs = msgs_result.scalars().all()

    job_result = await db.execute(select(Job).where(Job.job_id == chat.job_id))
    job = job_result.scalar_one_or_none()

    agreement_result = await db.execute(
        select(JobAgreement).where(JobAgreement.job_id == chat.job_id)
    )
    agreement = agreement_result.scalar_one_or_none()

    return ok({
        "chat_id": chat_id,
        "job_id": chat.job_id,
        "job_status": job.status if job else "unknown",
        "job_description": job.job_description_raw if job else "",
        "employer_user_id": chat.employer_user_id,
        "worker_user_id": chat.worker_user_id,
        "role": "employer" if current_user.user_id == chat.employer_user_id else "worker",
        "messages": [
            {
                "message_id": m.message_id,
                "sender_user_id": m.sender_user_id,
                "content": m.content,
                "message_type": m.message_type,
                "timestamp": m.timestamp.isoformat(),
                "is_mine": m.sender_user_id == current_user.user_id,
            }
            for m in msgs
        ],
        "agreement": {
            "agreed_price_kobo": agreement.agreed_price,
            "agreed_price_naira": agreement.agreed_price / 100 if agreement.agreed_price else None,
            "job_scope": agreement.job_scope_summary,
            "timeline": agreement.timeline,
            "conditions": agreement.conditions,
            "confirmed_by_employer": agreement.confirmed_by_employer,
            "confirmed_by_worker": agreement.confirmed_by_worker,
            "locked": bool(agreement.locked_at),
        } if agreement else None,
    })


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: str,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await _get_chat_or_404(chat_id, db)
    await _assert_participant(chat, current_user)

    # Block new messages after agreement is locked
    agreement_result = await db.execute(
        select(JobAgreement).where(JobAgreement.job_id == chat.job_id)
    )
    agreement = agreement_result.scalar_one_or_none()
    if agreement and agreement.locked_at:
        raise HTTPException(status_code=400, detail="Chat is locked after agreement was confirmed")

    msg = ChatMessage(
        chat_id=chat_id,
        sender_user_id=current_user.user_id,
        message_type=body.message_type,
        content=body.content,
        timestamp=datetime.utcnow(),
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    return ok({
        "message_id": msg.message_id,
        "sender_user_id": msg.sender_user_id,
        "content": msg.content,
        "timestamp": msg.timestamp.isoformat(),
        "is_mine": True,
    })


@router.post("/{chat_id}/agreement")
async def propose_agreement(
    chat_id: str,
    body: AgreementRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await _get_chat_or_404(chat_id, db)
    await _assert_participant(chat, current_user)

    existing = await db.execute(select(JobAgreement).where(JobAgreement.job_id == chat.job_id))
    agreement = existing.scalar_one_or_none()

    if agreement and agreement.locked_at:
        raise HTTPException(status_code=400, detail="Agreement already locked")

    if agreement:
        agreement.agreed_price = body.agreed_price_kobo
        agreement.job_scope_summary = body.job_scope
        agreement.timeline = body.timeline
        agreement.conditions = body.conditions
        agreement.confirmed_by_employer = False
        agreement.confirmed_by_worker = False
    else:
        agreement = JobAgreement(
            job_id=chat.job_id,
            agreed_price=body.agreed_price_kobo,
            job_scope_summary=body.job_scope,
            timeline=body.timeline,
            conditions=body.conditions,
        )
        db.add(agreement)

    # Post a system message
    sys_msg = ChatMessage(
        chat_id=chat_id,
        sender_user_id=current_user.user_id,
        message_type="system",
        content=f"Agreement proposed: ₦{body.agreed_price_kobo/100:,.0f} · {body.job_scope[:60]}",
        timestamp=datetime.utcnow(),
    )
    db.add(sys_msg)
    await db.commit()

    return ok({"message": "Agreement proposed. Both parties must confirm to lock."})


@router.post("/{chat_id}/agreement/confirm")
async def confirm_agreement(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await _get_chat_or_404(chat_id, db)
    await _assert_participant(chat, current_user)

    result = await db.execute(select(JobAgreement).where(JobAgreement.job_id == chat.job_id))
    agreement = result.scalar_one_or_none()
    if not agreement:
        raise HTTPException(status_code=400, detail="No agreement to confirm")
    if agreement.locked_at:
        raise HTTPException(status_code=400, detail="Already locked")

    if current_user.user_id == chat.employer_user_id:
        agreement.confirmed_by_employer = True
    else:
        agreement.confirmed_by_worker = True

    # Lock when both confirmed
    if agreement.confirmed_by_employer and agreement.confirmed_by_worker:
        agreement.locked_at = datetime.utcnow()
        job_result = await db.execute(select(Job).where(Job.job_id == chat.job_id))
        job = job_result.scalar_one_or_none()
        if job:
            job.status = "agreement_locked"
            job.updated_at = datetime.utcnow()

        sys_msg = ChatMessage(
            chat_id=chat_id,
            sender_user_id=current_user.user_id,
            message_type="system",
            content="Agreement locked by both parties. Employer should now fund escrow.",
            timestamp=datetime.utcnow(),
        )
        db.add(sys_msg)

    await db.commit()
    return ok({
        "confirmed_by_employer": agreement.confirmed_by_employer,
        "confirmed_by_worker": agreement.confirmed_by_worker,
        "locked": bool(agreement.locked_at),
    })


@router.get("/{chat_id}/escrow")
async def get_escrow(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await _get_chat_or_404(chat_id, db)
    await _assert_participant(chat, current_user)

    escrow_result = await db.execute(
        select(EscrowRecord).where(EscrowRecord.job_id == chat.job_id)
    )
    escrow = escrow_result.scalar_one_or_none()
    if not escrow:
        return ok({"escrow": None})

    return ok({
        "escrow": {
            "escrow_id": escrow.escrow_id,
            "status": escrow.status,
            "amount_kobo": escrow.amount,
            "amount_naira": escrow.amount / 100 if escrow.amount else None,
            "account_number": escrow.squad_dva_account_number,
            "funded_at": escrow.funded_at.isoformat() if escrow.funded_at else None,
            "auto_release_at": escrow.auto_release_at.isoformat() if escrow.auto_release_at else None,
        }
    })


@router.post("/{chat_id}/escrow/create")
async def create_escrow(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await _get_chat_or_404(chat_id, db)
    if current_user.user_id != chat.employer_user_id:
        raise HTTPException(status_code=403, detail="Only the employer can create escrow")

    agreement_result = await db.execute(
        select(JobAgreement).where(JobAgreement.job_id == chat.job_id).with_for_update()
    )
    agreement = agreement_result.scalar_one_or_none()
    if not agreement or not agreement.locked_at:
        raise HTTPException(status_code=400, detail="Agreement must be locked before creating escrow")

    # Check escrow doesn't exist
    existing = await db.execute(select(EscrowRecord).where(EscrowRecord.job_id == chat.job_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Escrow already exists for this job")

    try:
        dva_resp = await squad_service.create_dynamic_virtual_account(
            customer_identifier=f"escrow-{chat.job_id[:8]}",
            amount=agreement.agreed_price,
        )
        dva_data = dva_resp.get("data", {})
        acct_number = dva_data.get("virtual_account_number") or dva_data.get("account_number")
        dva_ref = dva_data.get("transaction_ref") or dva_data.get("virtual_account_number") or chat.job_id
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to create escrow account: {e}")

    escrow = EscrowRecord(
        job_id=chat.job_id,
        squad_dva_account_number=acct_number,
        squad_dva_reference=dva_ref,
        amount=agreement.agreed_price,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(escrow)

    sys_msg = ChatMessage(
        chat_id=chat_id,
        sender_user_id=current_user.user_id,
        message_type="system",
        content=f"Escrow created. Transfer ₦{agreement.agreed_price/100:,.0f} to {acct_number} to activate job.",
        timestamp=datetime.utcnow(),
    )
    db.add(sys_msg)
    await db.commit()

    return ok({
        "escrow_account": acct_number,
        "amount_naira": agreement.agreed_price / 100,
        "message": "Transfer this amount to the escrow account to activate the job.",
    })


@router.post("/{chat_id}/complete")
async def mark_complete(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await _get_chat_or_404(chat_id, db)
    if current_user.user_id != chat.worker_user_id:
        raise HTTPException(status_code=403, detail="Only the worker can mark job complete")

    job_result = await db.execute(select(Job).where(Job.job_id == chat.job_id))
    job = job_result.scalar_one_or_none()
    if not job or job.status not in ("funded", "active"):
        raise HTTPException(status_code=400, detail="Job must be funded/active before marking complete")

    job.status = "completed"
    job.updated_at = datetime.utcnow()

    sys_msg = ChatMessage(
        chat_id=chat_id,
        sender_user_id=current_user.user_id,
        message_type="system",
        content="Worker marked job as complete. Employer has 48 hours to confirm or dispute.",
        timestamp=datetime.utcnow(),
    )
    db.add(sys_msg)

    # Update escrow auto-release window
    escrow_result = await db.execute(
        select(EscrowRecord).where(EscrowRecord.job_id == chat.job_id).with_for_update()
    )
    escrow = escrow_result.scalar_one_or_none()
    if escrow and escrow.status == "funded":
        escrow.auto_release_at = datetime.utcnow() + timedelta(hours=48)

    await db.commit()
    return ok({"message": "Job marked complete. Awaiting employer confirmation."})


@router.post("/{chat_id}/escrow/release")
async def release_escrow(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await _get_chat_or_404(chat_id, db)
    if current_user.user_id != chat.employer_user_id:
        raise HTTPException(status_code=403, detail="Only the employer can release payment")

    escrow_result = await db.execute(
        select(EscrowRecord).where(EscrowRecord.job_id == chat.job_id).with_for_update()
    )
    escrow = escrow_result.scalar_one_or_none()
    if not escrow or escrow.status != "funded":
        raise HTTPException(status_code=400, detail="Escrow not funded yet")

    worker_squad = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == chat.worker_user_id)
    )
    worker_acct = worker_squad.scalar_one_or_none()
    if not worker_acct or not worker_acct.squad_account_number:
        raise HTTPException(status_code=400, detail="Worker has no active wallet")

    worker_result = await db.execute(select(User).where(User.user_id == chat.worker_user_id))
    worker = worker_result.scalar_one_or_none()

    try:
        await squad_service.transfer(
            account_number=worker_acct.squad_account_number,
            bank_code="000",
            account_name=worker.full_name or "alwi Worker",
            amount=escrow.amount,
            narration=f"alwi job payment — {chat.job_id[:8]}",
            transaction_ref=f"release-{escrow.escrow_id[:8]}",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transfer failed: {e}")

    escrow.status = "released"
    escrow.released_at = datetime.utcnow()

    job_result = await db.execute(select(Job).where(Job.job_id == chat.job_id))
    job = job_result.scalar_one_or_none()
    if job:
        job.status = "completed"
        job.updated_at = datetime.utcnow()

    sys_msg = ChatMessage(
        chat_id=chat_id,
        sender_user_id=current_user.user_id,
        message_type="system",
        content=f"Payment of ₦{escrow.amount/100:,.0f} released to worker. Job complete!",
        timestamp=datetime.utcnow(),
    )
    db.add(sys_msg)
    await db.commit()

    return ok({"message": "Payment released. Job completed!"})


@router.post("/{chat_id}/dispute")
async def open_dispute(
    chat_id: str,
    body: DisputeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = await _get_chat_or_404(chat_id, db)
    await _assert_participant(chat, current_user)

    escrow_result = await db.execute(
        select(EscrowRecord).where(EscrowRecord.job_id == chat.job_id).with_for_update()
    )
    escrow = escrow_result.scalar_one_or_none()
    if not escrow or escrow.status not in ("funded",):
        raise HTTPException(status_code=400, detail="Can only dispute funded escrow")

    escrow.status = "frozen"

    job_result = await db.execute(select(Job).where(Job.job_id == chat.job_id))
    job = job_result.scalar_one_or_none()
    if job:
        job.status = "disputed"

    dispute = Dispute(
        job_id=chat.job_id,
        escrow_id=escrow.escrow_id,
        opened_by_user_id=current_user.user_id,
        reason_text=body.reason,
        status="open",
        created_at=datetime.utcnow(),
    )
    db.add(dispute)

    sys_msg = ChatMessage(
        chat_id=chat_id,
        sender_user_id=current_user.user_id,
        message_type="system",
        content=f"Dispute opened. Escrow frozen. Reason: {body.reason[:80]}",
        timestamp=datetime.utcnow(),
    )
    db.add(sys_msg)
    await db.commit()

    return ok({"dispute_id": dispute.dispute_id, "message": "Dispute opened. Funds frozen pending review."})
