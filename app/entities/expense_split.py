from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.connectors.database_connector import Base


class ExpenseSplit(Base):
    """
    Expense split per user
    """

    __tablename__ = "expense_splits"

    id: uuid.UUID = sa.Column(UUID(as_uuid=False), primary_key=True, nullable=False)

    expense_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)
    user_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)

    amount = sa.Column(sa.Numeric(10, 2), nullable=False)
    is_settled: bool = sa.Column(sa.Boolean, nullable=False, default=False)
