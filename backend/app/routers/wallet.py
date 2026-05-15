from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, SquadAccount
from app.models.transaction import Transaction
from app.models.agent import Agent, AgentTransaction
from app.schemas.wallet import SendMoneyRequest, CashInRequest, CashOutRequest, LookupRequest
from app.schemas.common import ok, err
from app.services import squad_service
from app.utils.security import get_current_user

router = APIRouter()


@router.get("/balance")
async def get_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch the user's Squad virtual account balance."""
    squad_result = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == current_user.user_id)
    )
    squad_acct = squad_result.scalar_one_or_none()
    if not squad_acct:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Squad account found")

    try:
        resp = await squad_service.get_wallet_balance()
        # Squad merchant balance is in kobo
        balance_kobo = resp.get("data", {}).get("balance", 0)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Balance fetch failed: {e}")

    return ok({
        "balance_kobo": balance_kobo,
        "balance_naira": balance_kobo / 100,
        "account_number": squad_acct.squad_account_number,
        "bank_name": squad_acct.squad_bank_name,
    })


@router.post("/lookup")
async def lookup_account(
    body: LookupRequest,
    current_user: User = Depends(get_current_user),
):
    """Verify a bank account name before sending money."""
    try:
        resp = await squad_service.lookup_account(body.account_number, body.bank_code)
        account_name = resp.get("data", {}).get("account_name") or resp.get("data", {}).get("accountName")
        return ok({"account_name": account_name, "account_number": body.account_number, "bank_code": body.bank_code})
    except Exception as e:
        err_text = str(e)
        if hasattr(e, "response"):
            err_text = e.response.text
        # Squad sandbox restricts this endpoint — degrade gracefully
        if "not eligible" in err_text.lower() or "400" in err_text:
            return ok({"account_name": None, "account_number": body.account_number, "bank_code": body.bank_code, "note": "Account name verification unavailable in sandbox"})
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Lookup failed: {err_text}")


@router.post("/send")
async def send_money(
    body: SendMoneyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send money to another alwi user by their ECO-XXXX-XXXX ID.
    Looks up the recipient's Squad virtual account and calls the Transfer API.
    """
    if body.recipient_id == current_user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot send money to yourself")

    # Resolve recipient
    recipient_result = await db.execute(select(User).where(User.user_id == body.recipient_id))
    recipient = recipient_result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    recipient_squad = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == recipient.user_id)
    )
    recipient_acct = recipient_squad.scalar_one_or_none()
    if not recipient_acct or not recipient_acct.squad_account_number:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient has no active wallet")

    # Lock sender account to prevent concurrent double-spends
    sender_squad = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == current_user.user_id).with_for_update()
    )
    sender_acct = sender_squad.scalar_one_or_none()
    if not sender_acct:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sender has no active wallet")

    # Log the transaction as pending before calling Squad
    txn = Transaction(
        sender_user_id=current_user.user_id,
        receiver_user_id=recipient.user_id,
        amount=body.amount_kobo,
        type="send",
        channel="self",
        status="pending",
        tagged_as="personal",
        timestamp=datetime.utcnow(),
    )
    db.add(txn)
    await db.flush()

    # Execute transfer via Squad
    try:
        squad_resp = await squad_service.transfer(
            account_number=recipient_acct.squad_account_number,
            bank_code="000",   # Squad internal bank code for virtual accounts
            account_name=recipient.full_name or "alwi User",
            amount=body.amount_kobo,
            narration=body.narration,
            transaction_ref=txn.transaction_id,
        )
        squad_ref = squad_resp.get("data", {}).get("transaction_ref") or txn.transaction_id
        txn.squad_reference = squad_ref
        txn.status = "completed"
    except Exception as e:
        txn.status = "failed"
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Transfer failed: {e}")

    await db.commit()

    return ok({
        "transaction_id": txn.transaction_id,
        "amount_naira": body.amount_naira,
        "recipient": body.recipient_id,
        "recipient_name": recipient.full_name,
        "status": "completed",
        "squad_reference": txn.squad_reference,
    })


@router.get("/transactions")
async def get_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return transaction history from Squad + local log."""
    squad_result = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == current_user.user_id)
    )
    squad_acct = squad_result.scalar_one_or_none()

    squad_txns = []
    if squad_acct:
        try:
            resp = await squad_service.get_transactions(squad_acct.squad_customer_identifier)
            squad_txns = resp.get("data", {}).get("transactions", [])
        except Exception:
            pass

    # Local transaction records
    local_result = await db.execute(
        select(Transaction)
        .where(
            (Transaction.sender_user_id == current_user.user_id)
            | (Transaction.receiver_user_id == current_user.user_id)
        )
        .order_by(Transaction.timestamp.desc())
        .limit(50)
    )
    local_txns = local_result.scalars().all()

    return ok({
        "squad_transactions": squad_txns,
        "local_transactions": [
            {
                "transaction_id": t.transaction_id,
                "type": t.type,
                "amount_kobo": t.amount,
                "amount_naira": t.amount / 100,
                "status": t.status,
                "squad_reference": t.squad_reference,
                "tagged_as": t.tagged_as,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
            }
            for t in local_txns
        ],
    })


@router.post("/cashin")
async def cash_in(body: CashInRequest, db: AsyncSession = Depends(get_db)):
    """
    Agent-triggered cash-in: agent receives physical cash and credits the user's wallet.
    Requires agent authentication (simplified here — full agent auth in Module 15).
    """
    agent_result = await db.execute(select(Agent).where(Agent.agent_id == body.agent_id))
    agent = agent_result.scalar_one_or_none()
    if not agent or agent.agent_status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or inactive agent")

    user_result = await db.execute(select(User).where(User.user_id == body.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Log the cash-in transaction
    txn = Transaction(
        receiver_user_id=body.user_id,
        amount=body.amount_kobo,
        type="cash_in",
        channel="agent",
        status="pending",
        tagged_as="personal",
        timestamp=datetime.utcnow(),
    )
    db.add(txn)

    commission = int(body.amount_kobo * float(agent.commission_rate))
    agent_txn = AgentTransaction(
        agent_id=agent.agent_id,
        user_id=body.user_id,
        transaction_type="cash_in",
        amount=body.amount_kobo,
        commission_earned=commission,
    )
    db.add(agent_txn)
    agent.total_earned += commission

    # Mark completed — actual Squad credit comes via charge_successful webhook
    # when the agent transfers to the user's virtual account number
    txn.status = "completed"
    await db.commit()

    return ok({
        "transaction_id": txn.transaction_id,
        "amount_naira": body.amount_naira,
        "user_id": body.user_id,
        "agent_commission_naira": commission / 100,
        "status": "completed",
        "message": "Agent cash-in recorded. Wallet credited on Squad confirmation.",
    })


@router.post("/cashout")
async def cash_out(
    body: CashOutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cash-out: debit user's Squad wallet and disburse via agent or direct bank transfer.
    """
    agent_result = await db.execute(select(Agent).where(Agent.agent_id == body.agent_id))
    agent = agent_result.scalar_one_or_none()
    if not agent or agent.agent_status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or inactive agent")

    squad_result = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == current_user.user_id).with_for_update()
    )
    squad_acct = squad_result.scalar_one_or_none()
    if not squad_acct:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Squad account found")

    txn = Transaction(
        sender_user_id=current_user.user_id,
        amount=body.amount_kobo,
        type="cash_out",
        channel="agent",
        status="pending",
        tagged_as="personal",
        timestamp=datetime.utcnow(),
    )
    db.add(txn)
    await db.flush()

    try:
        dest_account = body.destination_account or squad_acct.squad_account_number
        dest_bank = body.destination_bank_code or "000"

        squad_resp = await squad_service.transfer(
            account_number=dest_account,
            bank_code=dest_bank,
            account_name=current_user.full_name or "alwi User",
            amount=body.amount_kobo,
            narration="alwi cash-out",
            transaction_ref=txn.transaction_id,
        )
        txn.squad_reference = squad_resp.get("data", {}).get("transaction_ref")
        txn.status = "completed"
    except Exception as e:
        txn.status = "failed"
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Cash-out failed: {e}")

    commission = int(body.amount_kobo * float(agent.commission_rate))
    agent_txn = AgentTransaction(
        agent_id=agent.agent_id,
        user_id=current_user.user_id,
        transaction_type="cash_out",
        amount=body.amount_kobo,
        commission_earned=commission,
    )
    db.add(agent_txn)
    agent.total_earned += commission

    await db.commit()

    return ok({
        "transaction_id": txn.transaction_id,
        "amount_naira": body.amount_naira,
        "status": "completed",
        "squad_reference": txn.squad_reference,
    })
