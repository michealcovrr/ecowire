import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Boolean, Numeric, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String(36), primary_key=True, default=_uuid)
    employer_user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    worker_user_id = Column(String(20))
    job_description_raw = Column(Text)
    job_tags = Column(ARRAY(String))
    location_lat = Column(Numeric(10, 8))
    location_lng = Column(Numeric(11, 8))
    location_address = Column(Text)
    budget = Column(BigInteger)             # in kobo
    status = Column(String(20), default="open")
    # open, matched, agreement_locked, funded, active, completed, disputed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobApplication(Base):
    __tablename__ = "job_applications"

    application_id = Column(String(36), primary_key=True, default=_uuid)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    worker_user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    status = Column(String(20), default="applied")  # applied, shortlisted, accepted, rejected
    applied_at = Column(DateTime, default=datetime.utcnow)


class JobChat(Base):
    __tablename__ = "job_chats"

    chat_id = Column(String(36), primary_key=True, default=_uuid)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    employer_user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    worker_user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    chat_type = Column(String(20), default="job_chat")  # job_chat or verification_request
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(String(36), primary_key=True, default=_uuid)
    chat_id = Column(String(36), ForeignKey("job_chats.chat_id"), nullable=False)
    sender_user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    message_type = Column(String(10))   # text, voice, image, file, system
    content = Column(Text)              # text content or media URL
    timestamp = Column(DateTime, default=datetime.utcnow)


class JobAgreement(Base):
    __tablename__ = "job_agreements"

    agreement_id = Column(String(36), primary_key=True, default=_uuid)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    agreed_price = Column(BigInteger)   # in kobo
    job_scope_summary = Column(Text)
    timeline = Column(Text)
    conditions = Column(Text)
    confirmed_by_employer = Column(Boolean, default=False)
    confirmed_by_worker = Column(Boolean, default=False)
    locked_at = Column(DateTime)


class EscrowRecord(Base):
    __tablename__ = "escrow_records"

    escrow_id = Column(String(36), primary_key=True, default=_uuid)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    squad_dva_account_number = Column(String(20))
    squad_dva_reference = Column(String(100))
    amount = Column(BigInteger)         # in kobo
    status = Column(String(20), default="pending")
    # pending, funded, released, frozen, refunded
    funded_at = Column(DateTime)
    released_at = Column(DateTime)
    auto_release_at = Column(DateTime)  # funded_at + 48h
    created_at = Column(DateTime, default=datetime.utcnow)


class Dispute(Base):
    __tablename__ = "disputes"

    dispute_id = Column(String(36), primary_key=True, default=_uuid)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    escrow_id = Column(String(36), ForeignKey("escrow_records.escrow_id"))
    opened_by_user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    reason_text = Column(Text)
    ai_summary = Column(Text)
    ai_recommendation = Column(String(20))  # worker_wins, employer_wins, escalate
    ai_confidence = Column(Numeric(5, 2))
    status = Column(String(20), default="open")     # open, under_review, resolved
    resolution = Column(String(20))                 # worker_wins, employer_wins, split, escalated
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class DisputeEvidence(Base):
    __tablename__ = "dispute_evidence"

    evidence_id = Column(String(36), primary_key=True, default=_uuid)
    dispute_id = Column(String(36), ForeignKey("disputes.dispute_id"), nullable=False)
    submitted_by_user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    content_type = Column(String(10))   # text, image, video
    content = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
