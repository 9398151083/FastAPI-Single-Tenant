from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
from app.connectors.database_connector import Base
import uuid


class Invite(Base):
    __tablename__ = "invites"

    id = Column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    group_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    email = Column(sa.String(255), nullable=False, index=True)
    invited_by = Column(UUID(as_uuid=False), nullable=False)
    token = Column(sa.String(64), nullable=False, unique=True, index=True)
    status = Column(sa.String(20), default="pending")  # pending/accepted/expired
    created_at = Column(sa.DateTime, nullable=False, default=sa.func.now())
