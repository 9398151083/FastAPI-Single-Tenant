from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.connectors.database_connector import Base


class Task(Base):
    """
    Task / Subtask Entity
    """

    __tablename__ = "tasks"

    id: uuid.UUID = sa.Column(UUID(as_uuid=False), primary_key=True, nullable=False)

    group_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)

    title: str = sa.Column(sa.String(200), nullable=False)
    description: str = sa.Column(sa.Text)

    assigned_to: uuid.UUID = sa.Column(
        UUID(as_uuid=False)
    )  # logical reference to users.id

    parent_id: uuid.UUID = sa.Column(UUID(as_uuid=False))  # self-reference for subtasks

    priority: str = sa.Column(sa.String(50), nullable=False, default="medium")
    status: str = sa.Column(sa.String(50), nullable=False, default="open")

    due_date = sa.Column(sa.Date)
