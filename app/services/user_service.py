from fastapi import Depends, HTTPException, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.connectors.database_connector import get_db
from app.entities.user import User
from app.models.user_models import (
    UserCreationRequest,
    UserCreationResponse,
    GetUserDetailsResponse,
)
from app.utils.constants import THE_USER_DETAILS_DOES_NOT_EXIST_FOR_THIS_ID


class UserService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # -------------------- VALIDATIONS --------------------

    def validate_user_details(self, user: User | None, user_id: int) -> User:
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{THE_USER_DETAILS_DOES_NOT_EXIST_FOR_THIS_ID} '{user_id}'",
            )
        return user

    # -------------------- CREATE USER --------------------

    def create_user(self, request: UserCreationRequest) -> UserCreationResponse:
        user = User(
            name=request.name,
            username=request.username,
            password=request.password,  # ⚠️ Hash in production
            role=request.role,
            contact=request.contact,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return UserCreationResponse.model_validate(user)

    # -------------------- GET USER BY ID --------------------

    def get_user_by_id(self, user_id: int) -> GetUserDetailsResponse:
        user = self.db.get(User, user_id)
        user = self.validate_user_details(user, user_id)
        return GetUserDetailsResponse.model_validate(user)

    # -------------------- GET ALL USERS --------------------

    def get_all_users(self) -> list[GetUserDetailsResponse]:
        users = self.db.query(User).all()
        return [GetUserDetailsResponse.model_validate(user) for user in users]

    # -------------------- AUTH VALIDATION --------------------

    def validate_user(self, username: EmailStr, password: str) -> User | None:
        user = self.db.query(User).filter(User.username == username).first()

        if user and user.verify_password(password):
            return user

        return None
