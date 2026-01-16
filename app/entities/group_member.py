from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.connectors.database_connector import Base


class GroupMember(Base):
    """
    User membership in groups
    """

    __tablename__ = "group_members"

    id: uuid.UUID = sa.Column(UUID(as_uuid=False), primary_key=True, nullable=False)

    group_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)
    user_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)

    role: str = sa.Column(sa.String(50), nullable=False, default="member")
    joined_at: datetime = sa.Column(sa.DateTime, nullable=False, default=sa.func.now())
