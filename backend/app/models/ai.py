import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    interaction_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    input_type = Column(String(10))         # text or voice
    input_content = Column(Text)
    response_content = Column(Text)
    language_detected = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow)


class LearningPrompt(Base):
    __tablename__ = "learning_prompts"

    prompt_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    prompt_text = Column(Text)
    trigger_activity = Column(Text)
    shown_at = Column(DateTime)
    dismissed = Column(Boolean, default=False)
