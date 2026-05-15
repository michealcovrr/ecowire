import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey
from app.database import Base


def _uuid():
    return str(uuid.uuid4())


class CommunityGroup(Base):
    __tablename__ = "community_groups"

    group_id = Column(String(36), primary_key=True, default=_uuid)
    group_name = Column(String(100))
    lga = Column(String(100))
    geo_lat = Column(Numeric(10, 8))
    geo_lng = Column(Numeric(11, 8))
    radius_km = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)


class CommunityMembership(Base):
    __tablename__ = "community_memberships"

    membership_id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    group_id = Column(String(36), ForeignKey("community_groups.group_id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)


class UserConnection(Base):
    __tablename__ = "user_connections"

    connection_id = Column(String(36), primary_key=True, default=_uuid)
    user_a_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    user_b_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    connection_type = Column(String(30))    # contact, recommendation, job_history
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(String(36), primary_key=True, default=_uuid)
    recommender_user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    worker_user_id = Column(String(20), ForeignKey("users.user_id"), nullable=False)
    recommendation_text = Column(Text)
    job_id = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
