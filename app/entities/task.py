from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
from app.connectors.database_connector import Base
import uuid


class Task(Base):
    __tablename__ = "tasks"

    id = Column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    group_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    title = Column(sa.String(200), nullable=False)
    description = Column(sa.Text)
    assigned_to = Column(UUID(as_uuid=False))  # Optional assignee
    status = Column(sa.String(20), default="pending")  # pending/in-progress/done
    priority = Column(sa.String(20), default="medium")  # low/medium/high
    due_date = Column(sa.DateTime)
    created_by = Column(UUID(as_uuid=False), nullable=False)
    created_at = Column(sa.DateTime, default=sa.func.now())
