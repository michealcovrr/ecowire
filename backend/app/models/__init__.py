# Import all models so Alembic can detect them for autogenerate
from app.models.user import User, KycRecord, SquadAccount, UserIntent
from app.models.transaction import Transaction
from app.models.profile import WorkProfile, ProofMedia
from app.models.community import CommunityGroup, CommunityMembership, UserConnection, Recommendation
from app.models.job import Job, JobApplication, JobChat, ChatMessage, JobAgreement, EscrowRecord, Dispute, DisputeEvidence
from app.models.financial import FinancialLog, DebtRecord, FinancialIdentity, Loan, SavingsPlan, InsurancePolicy
from app.models.ai import AIInteraction, LearningPrompt
from app.models.agent import Agent, AgentTransaction

__all__ = [
    "User", "KycRecord", "SquadAccount", "UserIntent",
    "Transaction",
    "WorkProfile", "ProofMedia",
    "CommunityGroup", "CommunityMembership", "UserConnection", "Recommendation",
    "Job", "JobApplication", "JobChat", "ChatMessage", "JobAgreement",
    "EscrowRecord", "Dispute", "DisputeEvidence",
    "FinancialLog", "DebtRecord", "FinancialIdentity", "Loan", "SavingsPlan", "InsurancePolicy",
    "AIInteraction", "LearningPrompt",
    "Agent", "AgentTransaction",
]
