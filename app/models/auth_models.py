from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.validators import validate_password


# =========================
# REGISTER (SEND OTP)
# =========================
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    contact: str = Field(..., min_length=6, max_length=20)


# =========================
# VERIFY REGISTER OTP
# =========================
class VerifyRegisterRequest(BaseModel):
    name: str
    email: EmailStr = Field(..., min_length=8, max_length=100)
    otp: str = Field(..., min_length=6, max_length=6)
    password: str = Field(..., min_length=8, max_length=20)

    @field_validator("password")
    def validate_user_creation_password(cls, password: str):
        return validate_password(password)


# =========================
# LOGIN
# =========================
class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Username or Email")
    password: str = Field(..., min_length=8)


# =========================
# FORGOT PASSWORD
# =========================
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


# =========================
# RESET PASSWORD
# =========================
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)
