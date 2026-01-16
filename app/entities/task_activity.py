from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.connectors.database_connector import Base


class TaskActivity(Base):
    """
    Task activity / audit log
    """

    __tablename__ = "task_activities"

    id: uuid.UUID = sa.Column(UUID(as_uuid=False), primary_key=True, nullable=False)

    task_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)
    action: str = sa.Column(sa.String(100), nullable=False)

    performed_by: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False)

    created_at: datetime = sa.Column(sa.DateTime, nullable=False, default=sa.func.now())
