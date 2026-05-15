import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Numeric, DateTime, ForeignKey
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    agent_status = Column(String(20), default="active")     # active, suspended
    location_lga = Column(String(100))
    commission_rate = Column(Numeric(5, 4), default=0.005)  # 0.5%
    total_earned = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentTransaction(Base):
    __tablename__ = "agent_transactions"

    agent_txn_id = Column(String(36), primary_key=True, default=_uuid)
    agent_id = Column(String(36), ForeignKey("agents.agent_id"), nullable=False)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    transaction_type = Column(String(20))   # cash_in, cash_out, onboarding
    amount = Column(BigInteger)
    commission_earned = Column(BigInteger)
    timestamp = Column(DateTime, default=datetime.utcnow)
