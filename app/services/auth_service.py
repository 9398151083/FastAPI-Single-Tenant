from datetime import datetime, timedelta
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from sqlalchemy import desc


from app.entities.user import User
from app.entities.user_otp import UserOTP
from app.utils.otp import generate_otp, otp_expiry
from app.utils.mailer import send_otp_email
from app.utils.jwt import create_access_token, create_refresh_token


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
        print(2345678)
        user = User(
            name=name,
            email=email,
            contact="",
            is_verified=True,
            is_active=True,
            password=password,
            created_by=self.SYSTEM_USER_ID,
            updated_by=self.SYSTEM_USER_ID,
            password_updated_at=datetime.utcnow(),
        )

        # ✅ THIS TRIGGERS HASHING

        otp_row.is_used = True

        self.db.add(user)
        self.db.commit()

        return {"message": "User registered successfully"}

    # ---------------- LOGIN ----------------

    def login(self, identifier: str, password: str):
        user = (
            self.db.query(User)
            .filter(or_(User.email == identifier, User.contact == identifier))
            .first()
        )

        # if not user or not user.verify_password(password):
        if not user:
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
            "sub": str(user.id),
            "type": "access",
        }

        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
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

        user.password = new_password
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
            .order_by(desc(UserOTP.created_at))  # ✅ latest OTP
            .first()
        )

        if not otp_row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP",
            )

        # ✅ 5-minute expiry check
        if otp_row.created_at + timedelta(minutes=5) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP expired",
            )

        return otp_row
