import uuid
from datetime import datetime
from sqlalchemy import Column, String, BigInteger, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class FinancialLog(Base):
    __tablename__ = "financial_logs"

    log_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    entry_type = Column(String(20))         # income, expense, debt_owed, debt_owing
    amount = Column(BigInteger)             # in kobo
    category = Column(String(50))
    description_raw = Column(Text)
    ai_extracted_tags = Column(JSONB)
    source = Column(String(20), default="manual")   # manual or squad_auto
    timestamp = Column(DateTime, default=datetime.utcnow)


class DebtRecord(Base):
    __tablename__ = "debt_records"

    debt_id = Column(String(36), primary_key=True, default=_uuid)
    creditor_user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    debtor_name = Column(String(100))
    debtor_user_id = Column(String(20))     # null if debtor is not on platform
    amount = Column(BigInteger)             # in kobo
    reason = Column(Text)
    status = Column(String(20), default="outstanding")  # outstanding, settled
    created_at = Column(DateTime, default=datetime.utcnow)


class FinancialIdentity(Base):
    __tablename__ = "financial_identities"

    identity_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    transaction_score = Column(Numeric(5, 2), default=0)
    job_completion_score = Column(Numeric(5, 2), default=0)
    dispute_score = Column(Numeric(5, 2), default=0)
    repayment_score = Column(Numeric(5, 2), default=0)
    community_trust_score = Column(Numeric(5, 2), default=0)
    engagement_score = Column(Numeric(5, 2), default=0)
    composite_score = Column(Numeric(5, 2), default=0)
    eligible_products = Column(ARRAY(String), default=list)
    last_updated = Column(DateTime, default=datetime.utcnow)


class Loan(Base):
    __tablename__ = "loans"

    loan_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    amount = Column(BigInteger)             # in kobo
    interest_rate = Column(Numeric(5, 2))
    repayment_schedule = Column(JSONB)
    amount_repaid = Column(BigInteger, default=0)
    status = Column(String(20), default="active")   # active, completed, defaulted
    disbursed_at = Column(DateTime)
    due_date = Column(DateTime)


class SavingsPlan(Base):
    __tablename__ = "savings_plans"

    savings_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    squad_savings_account_id = Column(String(100))
    target_amount = Column(BigInteger)
    current_amount = Column(BigInteger, default=0)
    frequency = Column(String(10))          # daily or weekly
    auto_debit_amount = Column(BigInteger)
    goal_description = Column(Text)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    policy_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    product_name = Column(String(100))
    provider = Column(String(100))
    premium_amount = Column(BigInteger)     # in kobo per period
    frequency = Column(String(10))          # monthly
    status = Column(String(20), default="active")   # active, lapsed, claimed
    started_at = Column(DateTime, default=datetime.utcnow)
