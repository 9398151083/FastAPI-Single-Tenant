from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.connectors.database_connector import Base


class Notification(Base):
    """
    Notification Entity
    """

    __tablename__ = "notifications"

    id: uuid.UUID = sa.Column(UUID(as_uuid=False), primary_key=True, nullable=False)

    user_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)
    group_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)

    type: str = sa.Column(sa.String(100), nullable=False)
    reference_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False)

    is_read: bool = sa.Column(sa.Boolean, nullable=False, default=False)
    created_at: datetime = sa.Column(sa.DateTime, nullable=False, default=sa.func.now())
