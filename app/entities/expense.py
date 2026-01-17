from datetime import datetime
import uuid
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from app.connectors.database_connector import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: uuid.UUID = sa.Column(UUID(as_uuid=False), primary_key=True, nullable=False)
    group_id: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)
    paid_by: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False)

    title: str = sa.Column(sa.String(200), nullable=False)
    total_amount = sa.Column(sa.Numeric(10, 2), nullable=False)  # ✅ Your field

    created_at: datetime = sa.Column(sa.DateTime, nullable=False, default=sa.func.now())

    # ✅ ADD these for full functionality:
    created_by: uuid.UUID = sa.Column(UUID(as_uuid=False), nullable=False, index=True)
    category: str = sa.Column(sa.String(50), default="other")
