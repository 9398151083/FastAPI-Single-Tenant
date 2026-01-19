"""✅ Complete Expense Routes + Splitwise Split"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel, Field
from app.connectors.database_connector import get_db
from app.models.expense_models import CreateExpenseRequest, SplitExpenseRequest
from app.utils.auth_dependencies import verify_auth_token
from app.entities.user import User
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


@router.post("/", response_model=dict, status_code=201)
async def create_expense(
    expense: CreateExpenseRequest,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    return service.create_expense(expense, current_user)


@router.get("/", response_model=dict)
async def get_user_expenses(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    service = ExpenseService(db)
    return service.get_user_expenses(current_user)


@router.get("/group/{group_id}", response_model=dict)
async def get_group_expenses(
    group_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    return service.get_group_expenses(group_id, current_user)


@router.post("/{expense_id}/split", response_model=dict)
async def split_expense(
    expense_id: str,
    split_data: SplitExpenseRequest,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    """✅ SPLITWISE: Create debts + send push notifications"""
    service = ExpenseService(db)
    return service.split_expense_with_payers(expense_id, split_data, current_user)


@router.get("/my-debts", response_model=dict)
async def get_user_debts(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    service = ExpenseService(db)
    return service.get_user_debts(current_user)


@router.get("/settlements", response_model=dict)
async def get_settlements(
    current_user: User = Depends(verify_auth_token), db: Session = Depends(get_db)
):
    service = ExpenseService(db)
    return service.get_settlements(current_user)
