from datetime import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.connectors.database_connector import Base


class UserOTP(Base):
    __tablename__ = "user_otps"

    id = sa.Column(UUID(as_uuid=False), primary_key=True, default=uuid.uuid4)

    user_id = sa.Column(UUID(as_uuid=False), nullable=True)  # logical ref only
    email = sa.Column(sa.String(256), index=True, nullable=False)

    otp = sa.Column(sa.String(6), nullable=False)
    purpose = sa.Column(sa.String(50), nullable=False)

    expires_at = sa.Column(sa.DateTime, nullable=False)
    is_used = sa.Column(sa.Boolean, default=False, nullable=False)

    created_at = sa.Column(sa.DateTime, server_default=sa.func.now(), nullable=False)
