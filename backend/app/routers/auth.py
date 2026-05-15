import bcrypt
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt

from app.database import get_db
from app.models.user import User, KycRecord, SquadAccount
from app.schemas.auth import KYCUpgradeRequest, UserResponse
from app.schemas.common import ok
from app.services import squad_service
from app.services.otp_service import normalise_phone, send_otp, verify_otp
from app.services import kyc_service
from app.utils.security import create_access_token, get_current_user, settings
from app.utils.id_generator import generate_unique_user_id
from app.utils.qr_generator import generate_qr_base64
from app.utils.encryption import encrypt_value
from pydantic import BaseModel, field_validator
import re

router = APIRouter()

_TEMP_TOKEN_EXPIRY_MINUTES = 15


# ── Temp token helpers (short-lived JWT for post-OTP registration) ─────────────

def _create_temp_token(phone: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=_TEMP_TOKEN_EXPIRY_MINUTES)
    payload = {"sub": phone, "type": "otp_verified", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_temp_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "otp_verified":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        phone = payload.get("sub")
        if not phone:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return phone
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="OTP session expired. Please request a new code.")


def _hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def _verify_pin(pin: str, pin_hash: str) -> bool:
    try:
        return bcrypt.checkpw(pin.encode(), pin_hash.encode())
    except Exception:
        return False


# ── Request schemas ────────────────────────────────────────────────────────────

class SendOtpRequest(BaseModel):
    phone: str


class VerifyOtpRequest(BaseModel):
    phone: str
    code: str


class RegisterRequest(BaseModel):
    temp_token: str
    kyc_type: str
    kyc_value: str

    @field_validator("kyc_type")
    @classmethod
    def validate_kyc_type(cls, v: str) -> str:
        if v.upper() not in ("BVN", "NIN"):
            raise ValueError("kyc_type must be BVN or NIN")
        return v.upper()


class ChangePinRequest(BaseModel):
    old_pin: str
    new_pin: str

    @field_validator("old_pin", "new_pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        if not re.match(r"^\d{6}$", v):
            raise ValueError("PIN must be exactly 6 digits")
        return v


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/send-otp")
async def send_otp_endpoint(body: SendOtpRequest):
    """Send a 6-digit OTP to the phone number via WhatsApp."""
    phone = normalise_phone(body.phone)
    sent = await send_otp(phone)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please wait before requesting another code.",
        )
    return ok({"sent": True})


@router.post("/verify-otp")
async def verify_otp_endpoint(body: VerifyOtpRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify the OTP.
    - Existing user → returns full auth token (login complete).
    - New user → returns a short-lived temp_token to be used with /register.
    """
    phone = normalise_phone(body.phone)
    valid = await verify_otp(phone, body.code)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired OTP. Please try again.")

    result = await db.execute(select(User).where(User.phone_number == phone))
    user = result.scalar_one_or_none()

    if user:
        squad_result = await db.execute(
            select(SquadAccount).where(SquadAccount.user_id == user.user_id)
        )
        squad_acct = squad_result.scalar_one_or_none()
        token = create_access_token(user.user_id)
        qr_code = generate_qr_base64(user.user_id)
        return ok({
            "exists": True,
            "token": token,
            "user": UserResponse(
                user_id=user.user_id,
                phone_number=user.phone_number,
                full_name=user.full_name,
                kyc_tier=user.kyc_tier,
                kyc_status=user.kyc_status,
                active_role=user.active_role,
                preferred_language=user.preferred_language,
                onboarding_channel=user.onboarding_channel,
            ).model_dump(),
            "squad_account_number": squad_acct.squad_account_number if squad_acct else None,
            "squad_bank_name": squad_acct.squad_bank_name if squad_acct else None,
            "qr_code": qr_code,
        })

    # New user — issue temp token for registration
    temp_token = _create_temp_token(phone)
    return ok({"exists": False, "temp_token": temp_token})


@router.post("/register")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Complete registration after OTP verification.
    Requires a valid temp_token from /verify-otp.
    """
    phone = _decode_temp_token(body.temp_token)

    existing = await db.execute(select(User).where(User.phone_number == phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Account already exists. Please log in.")

    try:
        if body.kyc_type == "BVN":
            kyc_result = await kyc_service.verify_bvn(body.kyc_value, phone)
        else:
            kyc_result = await kyc_service.verify_nin(body.kyc_value)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"KYC verification failed: {e.response.text}")

    entity = kyc_result.get("entity", {})
    first_name = entity.get("first_name", "").strip()
    last_name = entity.get("last_name", "").strip()
    full_name = f"{first_name} {last_name}".strip() or "EcoNet User"

    def _to_squad_dob(s: str) -> str:
        if not s:
            return "01/01/1990"
        from datetime import datetime as _dt
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return _dt.strptime(s, fmt).strftime("%m/%d/%Y")
            except ValueError:
                continue
        return "01/01/1990"

    dob = _to_squad_dob(entity.get("date_of_birth", ""))
    address = entity.get("address") or "Not provided"
    gender_letter = (entity.get("gender") or "M").upper()
    gender = "2" if gender_letter == "F" else "1"
    dojah_ref = entity.get("reference") or "ref"

    user_id = await generate_unique_user_id(db)
    encrypted_kyc = encrypt_value(body.kyc_value)

    user = User(
        user_id=user_id,
        phone_number=phone,
        full_name=full_name,
        kyc_type=body.kyc_type,
        kyc_value=encrypted_kyc,
        kyc_tier=1,
        kyc_status="tier_1",
        onboarding_channel="self",
    )
    db.add(user)
    await db.flush()

    kyc_record = KycRecord(
        user_id=user_id,
        kyc_type=body.kyc_type,
        kyc_value_encrypted=encrypted_kyc,
        dojah_reference=dojah_ref,
        verified=True,
        tier=1,
        verified_at=datetime.utcnow(),
    )
    db.add(kyc_record)
    await db.flush()

    squad_acct_number = None
    squad_bank_name = None
    try:
        squad_resp = await squad_service.create_virtual_account(
            customer_identifier=user_id,
            first_name=first_name or "EcoNet",
            last_name=last_name or "User",
            mobile_num=phone,
            email=f"{user_id.lower()}@econet.app",
            bvn=body.kyc_value if body.kyc_type == "BVN" else "00000000000",
            dob=dob,
            address=address,
            gender=gender,
        )
        va_data = squad_resp.get("data", {})
        squad_acct_number = va_data.get("account_number") or va_data.get("virtual_account_number")
        _BANK_CODES = {"058": "GTBank", "044": "Access Bank", "011": "First Bank",
                       "057": "Zenith Bank", "232": "Sterling Bank"}
        bank_code = va_data.get("bank_code", "")
        squad_bank_name = (va_data.get("bank_name") or _BANK_CODES.get(bank_code)
                           or f"Bank ({bank_code})")

        squad_acct = SquadAccount(
            user_id=user_id,
            squad_virtual_account_id=va_data.get("id") or va_data.get("virtual_account_id"),
            squad_account_number=squad_acct_number,
            squad_bank_name=squad_bank_name,
            squad_customer_identifier=user_id,
        )
        db.add(squad_acct)
    except Exception as e:
        print(f"[WARN] Squad VA failed for {user_id}: {type(e).__name__}: {e}", flush=True)

    await db.commit()

    token = create_access_token(user_id)
    qr_code = generate_qr_base64(user_id)

    return ok({
        "token": token,
        "user": UserResponse(
            user_id=user_id,
            phone_number=phone,
            full_name=full_name,
            kyc_tier=1,
            kyc_status="tier_1",
            active_role=None,
            preferred_language="english",
            onboarding_channel="self",
        ).model_dump(),
        "squad_account_number": squad_acct_number,
        "squad_bank_name": squad_bank_name,
        "qr_code": qr_code,
    })


@router.post("/change-pin")
async def change_pin(
    body: ChangePinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.pin_hash or not _verify_pin(body.old_pin, current_user.pin_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current PIN is incorrect")
    current_user.pin_hash = _hash_pin(body.new_pin)
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    return ok({"message": "PIN updated successfully"})


@router.post("/kyc/upgrade")
async def upgrade_kyc(
    body: KYCUpgradeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.kyc_tier >= 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already at maximum KYC tier")

    target_tier = current_user.kyc_tier + 1
    try:
        if body.kyc_type == "BVN":
            kyc_result = await kyc_service.verify_bvn(body.kyc_value, current_user.phone_number)
        else:
            kyc_result = await kyc_service.verify_nin(body.kyc_value)
        kyc_ref = kyc_result.get("entity", {}).get("reference") or "ref"
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"KYC verification failed: {e.response.text}")

    encrypted_kyc = encrypt_value(body.kyc_value)
    kyc_record = KycRecord(
        user_id=current_user.user_id,
        kyc_type=body.kyc_type,
        kyc_value_encrypted=encrypted_kyc,
        dojah_reference=kyc_ref,
        verified=True,
        tier=target_tier,
        verified_at=datetime.utcnow(),
    )
    db.add(kyc_record)
    current_user.kyc_tier = target_tier
    current_user.kyc_status = f"tier_{target_tier}"
    current_user.updated_at = datetime.utcnow()
    await db.commit()

    return ok({
        "message": f"KYC upgraded to Tier {target_tier}",
        "kyc_tier": target_tier,
        "kyc_status": f"tier_{target_tier}",
    })


@router.get("/me")
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    squad_result = await db.execute(
        select(SquadAccount).where(SquadAccount.user_id == current_user.user_id)
    )
    squad_acct = squad_result.scalar_one_or_none()
    qr_code = generate_qr_base64(current_user.user_id)

    return ok({
        "user": UserResponse(
            user_id=current_user.user_id,
            phone_number=current_user.phone_number,
            full_name=current_user.full_name,
            kyc_tier=current_user.kyc_tier,
            kyc_status=current_user.kyc_status,
            active_role=current_user.active_role,
            preferred_language=current_user.preferred_language,
            onboarding_channel=current_user.onboarding_channel,
        ).model_dump(),
        "squad_account_number": squad_acct.squad_account_number if squad_acct else None,
        "squad_bank_name": squad_acct.squad_bank_name if squad_acct else None,
        "qr_code": qr_code,
    })
