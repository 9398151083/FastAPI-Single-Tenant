from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.connectors.database_connector import Base


class Settlement(Base):
    """
    Settlement / Payment record
    """

    __tablename__ = "settlements"

    id: uuid.UUID = sa.Column(UUID(as_uuid=False), primary_key=True, nullable=False)

    expense_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)
    from_user: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False)
    to_user: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False)

    amount = sa.Column(sa.Numeric(10, 2), nullable=False)
    paid_at: datetime = sa.Column(sa.DateTime, nullable=False, default=sa.func.now())
