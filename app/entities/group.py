from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
from app.connectors.database_connector import Base
import uuid


class Group(Base):
    """
    Group Entity - Teams/Family for shared expenses/tasks
    """

    __tablename__ = "groups"

    id = Column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name = Column(sa.String(100), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=False), nullable=False, index=True)
    created_at = Column(sa.DateTime, nullable=False, default=sa.func.now())
