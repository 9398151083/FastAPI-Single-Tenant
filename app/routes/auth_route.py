from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.connectors.database_connector import get_db
from app.models.auth_models import (
    OAuth2PasswordRequestFormWithInvite,
    RegisterRequest,
    VerifyRegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import AuthService
from app.models.token_models import TokenResponse
from app.utils.db_queries import get_invite_by_token

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------- REGISTER (SEND OTP) ----------------


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    AuthService(db).register(
        name=req.name,
        email=req.email,
        contact=req.contact,
    )
    return {"message": "OTP sent to email"}


# ---------------- VERIFY REGISTER ----------------


@router.post("/verify-register")
def verify_register(req: VerifyRegisterRequest, db: Session = Depends(get_db)):
    AuthService(db).verify_register(
        name=req.name,
        email=req.email,
        password=req.password,
        otp=req.otp,
    )
    return {"message": "Registration successful"}


# ---------------- LOGIN ----------------


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(
        identifier=req.identifier,
        password=req.password,
    )


# ---------------- FORGOT PASSWORD ----------------


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).forgot_password(req.email)
    return {"message": "OTP sent to email"}


# ---------------- RESET PASSWORD ----------------


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).reset_password(
        email=req.email,
        otp=req.otp,
        new_password=req.new_password,
    )
    return {"message": "Password reset successful"}
