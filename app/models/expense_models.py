from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str = "other"
    group_id: str = "7e976007-4ae7-46fd-b497-dea41385787c"


class ExpenseResponse(BaseModel):
    id: str
    group_id: str
    title: str
    total_amount: float
    paid_by: str
    created_by: str


class ExpenseListResponse(BaseModel):
    expenses: List[ExpenseResponse]
    total: int
