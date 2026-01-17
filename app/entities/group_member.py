from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
from app.connectors.database_connector import Base
import uuid


class GroupMembership(Base):
    """
    Many-to-Many: User <-> Group relationship (NO FK - connect via code)
    """

    __tablename__ = "group_memberships"

    id = Column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    group_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    role = Column(sa.String(20), nullable=False, default="member")  # owner/member
    joined_at = Column(sa.DateTime, nullable=False, default=sa.func.now())
