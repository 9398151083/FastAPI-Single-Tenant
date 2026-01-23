from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import Optional

from app.entities.user import User
from app.entities.user_otp import UserOTP
from app.utils.db_queries import (
    accept_invite,
    create_membership,
    create_user,
    get_invite_by_token,
    get_user_by_email,
)
from app.utils.otp import generate_otp, otp_expiry
from app.utils.mailer import send_otp_email
from app.utils.jwt import create_access_token, create_refresh_token  # ✅ FIXED


class AuthService:
    SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

    def __init__(self, db: Session):
        self.db = db

    # ---------------- REGISTER (SEND OTP) ----------------
    def register(self, name: str, email: str, contact: str):
        existing_user = (
            self.db.query(User)
            .filter(or_(User.email == email, User.contact == contact))
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            )

        otp = generate_otp()

        self.db.add(
            UserOTP(
                email=email,
                otp=otp,
                purpose="REGISTER",
                expires_at=otp_expiry(),
                is_used=False,
            )
        )
        self.db.commit()

        send_otp_email(email, otp)

        return {"message": "OTP sent to email"}

    # ---------------- VERIFY REGISTER ----------------
    def verify_register(self, name: str, email: str, password: str, otp: str):
        otp_row = self._validate_otp(email, otp, "REGISTER")

        if self.db.query(User).filter(User.email == email).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists",
            )

        user = User(
            name=name,
            email=email,
            contact="0989878765",
            is_verified=True,
            is_active=True,
            password=password,  # ✅ Plain text (no hashing yet)
            created_by=self.SYSTEM_USER_ID,
            updated_by=self.SYSTEM_USER_ID,
            password_updated_at=datetime.utcnow(),
        )

        otp_row.is_used = True
        self.db.add(user)
        self.db.commit()

        return {"message": "User registered successfully"}

    # ---------------- LOGIN (PLAIN TEXT PASSWORD) ----------------
    def login(self, identifier: str, password: str):
        user = (
            self.db.query(User)
            .filter(or_(User.email == identifier, User.contact == identifier))
            .first()
        )

        # ✅ FIXED: Plain text password comparison
        if not user or user.password != password:  # ← PLAIN TEXT MATCH
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not verified",
            )

        payload = {
            "sub": str(user.id),  # ✅ UUID string
        }

        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {"id": str(user.id), "name": user.name, "email": user.email},
        }

    # ---------------- FORGOT PASSWORD ----------------
    def forgot_password(self, email: str):
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        otp = generate_otp()

        self.db.add(
            UserOTP(
                user_id=user.id,
                email=email,
                otp=otp,
                purpose="FORGOT_PASSWORD",
                expires_at=otp_expiry(),
                is_used=False,
            )
        )
        self.db.commit()

        send_otp_email(email, otp)

        return {"message": "OTP sent to email"}

    # ---------------- RESET PASSWORD ----------------
    def reset_password(self, email: str, otp: str, new_password: str):
        otp_row = self._validate_otp(email, otp, "FORGOT_PASSWORD")

        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

        user.password = new_password  # ✅ Plain text
        user.password_updated_at = datetime.utcnow()

        otp_row.is_used = True
        self.db.commit()

        return {"message": "Password reset successful"}

    # ---------------- OTP VALIDATION (INTERNAL) ----------------
    def _validate_otp(self, email: str, otp: str, purpose: str) -> UserOTP:
        otp_row = (
            self.db.query(UserOTP)
            .filter(
                UserOTP.email == email,
                UserOTP.otp == otp,
                UserOTP.purpose == purpose,
                UserOTP.is_used.is_(False),
            )
            .order_by(desc(UserOTP.created_at))
            .first()
        )

        if not otp_row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP",
            )

        if otp_row.created_at + timedelta(minutes=5) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired",
            )

        return otp_row

    def register_with_invite(
        self, email: str, password: str, token: str, group_id: str, name: str = None
    ):
        """Register new user with invite token + auto-join group"""

        # 1. Validate invite token
        invite = get_invite_by_token(self.db, token)
        if not invite or invite.email != email or invite.status != "pending":
            raise ValueError("Invalid invite token or email mismatch")

        # 2. Check user doesn't exist
        existing_user = get_user_by_email(self.db, email)
        if existing_user:
            raise ValueError("Email already registered")

        # 3. Create user
        user_id = str(uuid.uuid4())
        user_name = name or email.split("@")[0]

        create_user(self.db, user_id, email, password, user_name)

        # 4. Auto-join group via invite
        membership_id = str(uuid.uuid4())
        create_membership(self.db, membership_id, group_id, user_id, "member")

        # 5. Mark invite as accepted
        accept_invite(self.db, invite.id)

        self.db.commit()

        # 6. Generate JWT token
        access_token = create_access_token(data={"sub": user_id})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "group_joined": group_id,
            "user_id": user_id,
        }
