from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.connectors.database_connector import Base


class Group(Base):
    """
    Group / Workspace Entity
    """

    __tablename__ = "groups"

    id: uuid.UUID = sa.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    name: str = sa.Column(sa.String(150), nullable=False)

    created_by: uuid.UUID = sa.Column(
        UUID(as_uuid=False), nullable=False
    )  # logical reference to users.id

    created_at: datetime = sa.Column(sa.DateTime, nullable=False, default=sa.func.now())
