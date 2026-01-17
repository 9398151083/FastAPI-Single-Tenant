from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.connectors.database_connector import get_db
from app.utils.auth_dependencies import verify_auth_token
from app.entities.user import User
from app.models.expense_models import (
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseResponse,
)

from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


# ✅ NEW: Split request model
class SplitRequest(BaseModel):
    members: List[str]


@router.post("/", response_model=ExpenseResponse, status_code=201)
async def create_expense(
    expense: ExpenseCreate,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """Create new expense"""
    service = ExpenseService(db)
    return service.create_expense(expense, current_user)


@router.get("/", response_model=ExpenseListResponse)  # ✅ Fixed path + response
async def get_user_expenses(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    """Get all expenses created by user"""
    service = ExpenseService(db)
    print(current_user.id)
    return service.get_user_expenses(current_user)  # ✅ Returns ExpenseListResponse


@router.post("/{expense_id}/split", response_model=dict)  # ✅ Fixed signature
async def split_expense(
    expense_id: str,
    split_data: SplitRequest,  # ✅ Pydantic model for members
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """Calculate expense split among members"""
    service = ExpenseService(db)
    result = service.calculate_split(expense_id, split_data.members, current_user)
    return result


@router.get("/settlements", response_model=dict)
async def get_settlements(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    """Get settlement summary (who owes who)"""
    service = ExpenseService(db)
    return service.get_settlements(current_user)
