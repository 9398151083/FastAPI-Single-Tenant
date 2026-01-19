"""✅ COMPLETE Splitwise Service - Uses YOUR ExpenseSplit"""

import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.entities.user import User
from app.models.expense_models import CreateExpenseRequest, SplitExpenseRequest
from app.services.notification_service import NotificationService

# Local imports (assume these exist from previous fixes)
from app.utils.db_queries import get_user_expenses_in_group
from app.utils.db_queries import (
    get_user_groups,
    get_expense_by_id,
    get_group_expenses,
    create_expense,
)
from app.utils.db_queries import (
    create_expense_splits,
    get_user_debts,
    get_owed_to_user,
)
from app.utils.db_queries import is_user_member


class ExpenseService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def create_expense(
        self, expense_data: CreateExpenseRequest, current_user: User
    ) -> Dict[str, Any]:
        """Create expense in group"""
        if not is_user_member(self.db, expense_data.group_id, str(current_user.id)):
            raise HTTPException(403, "Not a group member")

        expense_dict = {
            "id": str(uuid.uuid4()),
            "group_id": expense_data.group_id,
            "title": expense_data.title[:200],
            "total_amount": expense_data.amount,
            "paid_by": str(current_user.id),
            "created_by": str(current_user.id),
        }

        db_expense = create_expense(self.db, expense_dict)
        return {
            "id": str(db_expense.id),
            "group_id": str(db_expense.group_id),
            "title": db_expense.title,
            "amount": float(db_expense.total_amount),
            "paid_by": str(db_expense.paid_by),
            "created_at": db_expense.created_at.isoformat(),
        }

    def split_expense_with_payers(
        self, expense_id: str, split_data: SplitExpenseRequest, current_user: User
    ) -> dict:
        """✅ SPLITWISE: Multiple payers → ExpenseSplit records + Notifications"""
        expense = get_expense_by_id(self.db, expense_id)
        if not expense:
            raise HTTPException(404, "Expense not found")

        total_amount = float(expense.total_amount)
        members = split_data.members
        payers = split_data.payers

        per_person_share = total_amount / len(members)

        # Step 2: Create ExpenseSplit records
        splits_to_create = []

        for payer in payers:
            payer_id = payer["user_id"]
            payer_amount = float(payer["amount"])
            payer_portion = payer_amount / total_amount

            for member_id in members:
                if payer_id != member_id:  # No self-debt
                    split_amount = per_person_share * payer_portion

                    splits_to_create.append(
                        {
                            "id": str(uuid.uuid4()),
                            "expense_id": expense_id,
                            "group_id": str(expense.group_id),
                            "owes_user_id": member_id,
                            "owed_user_id": payer_id,
                            "amount": split_amount,
                            "is_settled": False,
                        }
                    )

                    # ✅ PUSH NOTIFICATION
                    message = f"💰 You owe {payer_id[:8]}... ₹{round(split_amount, 2)} for '{expense.title}'"
                    self.notification_service.queue_push_notification(
                        user_id=member_id,
                        message=message,
                        group_id=str(expense.group_id),
                        data={
                            "split_id": splits_to_create[-1]["id"],
                            "action": "settle_expense",
                        },
                        type="expense_split",
                    )

        # Step 3: Bulk create
        created_splits = create_expense_splits(self.db, splits_to_create)
        self.db.commit()

        return {
            "expense_id": expense_id,
            "total_amount": total_amount,
            "per_person_share": round(per_person_share, 2),
            "payers": [{k: v for k, v in p.items()} for p in payers],
            "splits_created": len(created_splits),
            "notifications_sent": len(splits_to_create),
        }

    def get_user_debts(self, current_user: User) -> dict:
        """✅ What user owes + what others owe them"""
        user_id = str(current_user.id)

        # What user owes
        owes = get_user_debts(self.db, user_id)
        total_owes = sum(float(d.amount) for d in owes)

        # What others owe user
        owed = get_owed_to_user(self.db, user_id)
        total_owed = sum(float(d.amount) for d in owed)

        return {
            "user_id": user_id,
            "total_owes": round(total_owes, 2),
            "total_owed": round(total_owed, 2),
            "net_balance": round(total_owed - total_owes, 2),
            "owes": [
                {"to": str(d.owed_user_id), "amount": float(d.amount)} for d in owes[:5]
            ],
            "owed": [
                {"by": str(d.owes_user_id), "amount": float(d.amount)} for d in owed[:5]
            ],
        }

    def get_user_expenses(self, current_user: User) -> Dict[str, Any]:
        """All user expenses across groups"""
        user_groups = get_user_groups(self.db, str(current_user.id))
        all_expenses = []

        for group in user_groups:
            group_expenses = get_user_expenses_in_group(
                self.db, str(current_user.id), str(group.id)
            )
            all_expenses.extend(
                [
                    {
                        "id": str(e.id),
                        "group_id": str(e.group_id),
                        "group_name": group.name,
                        "title": e.title,
                        "amount": float(e.total_amount),
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in group_expenses
                ]
            )

        return {"expenses": all_expenses, "total": len(all_expenses)}

    def get_group_expenses(self, group_id: str, current_user: User) -> Dict[str, Any]:
        """Group expenses (if member)"""
        if not is_user_member(self.db, group_id, str(current_user.id)):
            raise HTTPException(403, "Not a group member")
        expenses = get_group_expenses(self.db, group_id)
        return {
            "group_id": group_id,
            "expenses": [
                {
                    "id": str(e.id),
                    "title": e.title,
                    "amount": float(e.total_amount),
                    "paid_by": str(e.paid_by),
                }
                for e in expenses
            ],
            "total": len(expenses),
        }

    def get_settlements(self, current_user: User) -> dict:
        """Net settlement summary"""
        debts = self.get_user_debts(current_user)
        return {
            "user": getattr(current_user, "name", "User"),
            **debts,
            "ready_to_settle": abs(debts["net_balance"]) > 0.01,
        }
