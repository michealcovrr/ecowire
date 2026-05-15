import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class WorkProfile(Base):
    __tablename__ = "work_profiles"

    profile_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    skill_description_raw = Column(Text)
    skill_tags = Column(ARRAY(String))
    profile_visibility_score = Column(Numeric(5, 2), default=0)
    job_completion_count = Column(Integer, default=0)
    dispute_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProofMedia(Base):
    __tablename__ = "proof_media"

    media_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    media_url = Column(Text)
    media_type = Column(String(10))         # image or video
    human_present = Column(Boolean)
    detected_activity_tags = Column(ARRAY(String))
    confidence_score = Column(Numeric(5, 2))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
