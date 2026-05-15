import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(36), primary_key=True, default=_uuid)
    sender_user_id = Column(String(20), ForeignKey("users.user_id"))
    receiver_user_id = Column(String(20), ForeignKey("users.user_id"))
    amount = Column(BigInteger, nullable=False)      # in kobo
    type = Column(String(20))                        # send, receive, cash_in, cash_out, escrow, release, loan, repayment
    channel = Column(String(10), default="self")     # self or agent
    squad_reference = Column(String(100))
    status = Column(String(20), default="pending")   # pending, completed, failed
    tagged_as = Column(String(20))                   # personal, business, job_payment
    job_id = Column(String(36))
    timestamp = Column(DateTime, default=datetime.utcnow)
