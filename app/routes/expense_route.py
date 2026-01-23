"""✅ Complete Expense Routes + Splitwise Split with Caching"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.connectors.database_connector import get_db
from app.utils.auth_dependencies import verify_auth_token
from app.entities.user import User
from app.services.expense_service import ExpenseService
from app.models.expense_models import CreateExpenseRequest, SplitExpenseRequest
from app.core.cache import get_cache, set_cache, invalidate_cache
import json

CACHE_TTL = 60  # seconds

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


# ------------------ POST ROUTES ------------------
@router.post("/", response_model=dict, status_code=201)
async def create_expense(
    expense: CreateExpenseRequest,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    result = service.create_expense(expense, current_user)

    # Invalidate relevant caches after creating expense
    await invalidate_cache(f"user_expenses:{current_user.id}")
    await invalidate_cache(f"group_expenses:*")  # optional wildcard for group caches
    return result


@router.post("/{expense_id}/split", response_model=dict)
async def split_expense(
    expense_id: str,
    split_data: SplitExpenseRequest,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    service = ExpenseService(db)
    result = service.split_expense_with_payers(expense_id, split_data, current_user)

    # Invalidate caches related to debts and group expenses
    await invalidate_cache(f"user_debts:{current_user.id}")
    await invalidate_cache(f"group_expenses:*")
    return result


# ------------------ GET ROUTES WITH CACHE ------------------
@router.get("/", response_model=dict)
async def get_user_expenses(
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"user_expenses:{current_user.id}"
    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    service = ExpenseService(db)
    result = service.get_user_expenses(current_user)
    await set_cache(cache_key, json.dumps(result), CACHE_TTL)
    return result


@router.get("/group/{group_id}", response_model=dict)
async def get_group_expenses(
    group_id: str,
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"group_expenses:{group_id}"
    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    service = ExpenseService(db)
    result = service.get_group_expenses(group_id, current_user)
    await set_cache(cache_key, json.dumps(result), CACHE_TTL)
    return result


@router.get("/my-debts", response_model=dict)
async def get_user_debts(
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"user_debts:{current_user.id}"
    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    service = ExpenseService(db)
    result = service.get_user_debts(current_user)
    await set_cache(cache_key, json.dumps(result), CACHE_TTL)
    return result


@router.get("/settlements", response_model=dict)
async def get_settlements(
    current_user: User = Depends(verify_auth_token),
    db: Session = Depends(get_db),
):
    cache_key = f"user_settlements:{current_user.id}"
    cached = await get_cache(cache_key)
    if cached:
        return json.loads(cached)

    service = ExpenseService(db)
    result = service.get_settlements(current_user)
    await set_cache(cache_key, json.dumps(result), CACHE_TTL)
    return result
