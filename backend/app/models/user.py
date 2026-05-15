import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Numeric, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(20), primary_key=True)
    phone_number = Column(String(15), unique=True, nullable=False)
    full_name = Column(String(100))
    kyc_type = Column(String(10))           # BVN or NIN
    kyc_value = Column(String(255))         # encrypted
    kyc_tier = Column(Integer, default=1)
    kyc_status = Column(String(20), default="tier_1")
    active_role = Column(String(20))        # worker, employer, business, financial, basic
    onboarding_channel = Column(String(10), default="self")
    agent_id = Column(String(20))
    location_lat = Column(Numeric(10, 8))
    location_lng = Column(Numeric(11, 8))
    location_lga = Column(String(100))
    preferred_language = Column(String(20), default="english")
    pin_hash = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KycRecord(Base):
    __tablename__ = "kyc_records"

    kyc_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    kyc_type = Column(String(10))
    kyc_value_encrypted = Column(Text)
    dojah_reference = Column(String(100))
    verified = Column(Boolean, default=False)
    tier = Column(Integer)
    verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class SquadAccount(Base):
    __tablename__ = "squad_accounts"

    account_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    squad_virtual_account_id = Column(String(100))
    squad_account_number = Column(String(20))
    squad_bank_name = Column(String(100))
    squad_customer_identifier = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class UserIntent(Base):
    __tablename__ = "user_intents"

    intent_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    intent_response = Column(JSONB)
    active_role = Column(String(20))
    kyc_tier_required = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
