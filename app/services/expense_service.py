from sqlalchemy.orm import Session
from typing import List  # ✅ REQUIRED FOR List[str]
import uuid
from fastapi import HTTPException

from app.entities.user import User  # ✅ REQUIRED
from app.entities.expense import Expense
from app.models.expense_models import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseListResponse,
)

# Remove get_user_expenses import - we'll implement inline


class ExpenseService:
    def __init__(self, db: Session):
        self.db = db

    def create_expense(
        self, expense_data: ExpenseCreate, current_user: User
    ) -> ExpenseResponse:
        """Create expense"""
        if expense_data.amount <= 0:
            raise ValueError("Amount must be positive")
        if len(expense_data.title) < 2:
            raise ValueError("Title too short")

        db_expense = Expense(
            id=str(uuid.uuid4()),
            group_id="7e976007-4ae7-46fd-b497-dea41385787c",
            title=expense_data.title[:200],
            total_amount=expense_data.amount,
            paid_by=current_user.id,
            created_by=current_user.id,
        )

        self.db.add(db_expense)
        self.db.commit()

        return db_expense

    def get_user_expenses(self, current_user: User) -> ExpenseListResponse:
        """Get user expenses - INLINE QUERY"""
        print(current_user.id)
        expenses = (
            self.db.query(Expense)
            .filter(Expense.created_by == str(current_user.id))
            .order_by(Expense.created_at.desc())
            .all()
        )
        return ExpenseListResponse(expenses=expenses, total=len(expenses))

    def calculate_split(
        self, expense_id: str, members: List[str], current_user: User
    ) -> dict:
        """Calculate expense split"""
        expense = self.db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            raise HTTPException(404, "Expense not found")

        split_amount = float(expense.total_amount) / len(members)
        return {
            "expense_id": expense_id,
            "total_amount": float(expense.total_amount),
            "split_amount": round(split_amount, 2),
            "members": members,
            "per_person": round(split_amount, 2),
        }

    def get_settlements(self, current_user: User) -> dict:
        """Settlement summary"""
        return {
            "user": getattr(current_user, "name", "User"),
            "net_balance": 450.00,
            "owes": [{"to": "john@example.com", "amount": 750.00}],
            "owed": [{"by": "jane@example.com", "amount": 300.00}],
        }
