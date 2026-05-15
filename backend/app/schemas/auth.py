from pydantic import BaseModel, field_validator
import re


class SendOTPRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"\s+", "", v)
        if not re.match(r"^\+?[0-9]{10,15}$", cleaned):
            raise ValueError("Invalid phone number format")
        return cleaned


class VerifyOTPRequest(BaseModel):
    phone: str
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not re.match(r"^\d{6}$", v):
            raise ValueError("OTP must be 6 digits")
        return v


class KYCSubmitRequest(BaseModel):
    kyc_type: str           # BVN or NIN
    kyc_value: str
    temp_token: str

    @field_validator("kyc_type")
    @classmethod
    def validate_kyc_type(cls, v: str) -> str:
        if v.upper() not in ("BVN", "NIN"):
            raise ValueError("kyc_type must be BVN or NIN")
        return v.upper()


class KYCUpgradeRequest(BaseModel):
    """Tier 2 and Tier 3 upgrade requests."""
    kyc_type: str
    kyc_value: str
    government_id_url: str | None = None    # Tier 2
    liveness_image_url: str | None = None   # Tier 3


class UserResponse(BaseModel):
    user_id: str
    phone_number: str
    full_name: str | None
    kyc_tier: int
    kyc_status: str
    active_role: str | None
    preferred_language: str
    onboarding_channel: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse
    squad_account_number: str | None = None
    squad_bank_name: str | None = None
    qr_code: str | None = None              # base64 PNG
