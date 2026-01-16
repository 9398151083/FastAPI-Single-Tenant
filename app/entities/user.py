from datetime import datetime
import uuid
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from app.connectors.database_connector import Base
from app.utils.hasher import Hasher


class User(Base):
    __tablename__ = "users"

    id = sa.Column(UUID(as_uuid=False), primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String(50), index=True)
    email = sa.Column(sa.String(256), unique=True, index=True, nullable=False)

    # 🔐 PRIVATE COLUMN (DO NOT ACCESS DIRECTLY)
    password: str = sa.Column(name="password", type_=sa.String(100), index=True)
    contact = sa.Column(sa.String(100), unique=True, index=True)
    designation = sa.Column(sa.String(100))

    invitation_token = sa.Column(UUID(as_uuid=False))
    is_password_reset = sa.Column(sa.Boolean, default=False, nullable=False)
    is_verified = sa.Column(sa.Boolean, default=False, nullable=False)
    has_sap_access = sa.Column(sa.Boolean, default=False, nullable=False)

    profile_image = sa.Column(sa.String(512))
    password_updated_at = sa.Column(sa.DateTime)

    created_at = sa.Column(sa.DateTime, server_default=sa.func.now(), nullable=False)
    updated_at = sa.Column(sa.DateTime, server_default=sa.func.now(), nullable=False)

    created_by = sa.Column(UUID(as_uuid=False))
    updated_by = sa.Column(UUID(as_uuid=False))

    is_active = sa.Column(sa.Boolean, default=True, nullable=False)

    # @property
    # def password(self):
    #     raise AttributeError(
    #         "password is not a readable attribute, use verify_password method for verifying"
    #     )

    # @password.setter
    # def password(self, password: str):
    #     self.__password = Hasher.get_password_hash(password)

    # def verify_password(self, password: str):
    #     return Hasher.verify_password(password, self.__password)
