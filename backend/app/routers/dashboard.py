from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Budget, Expense, Income, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _month_range(month: str):
    y, m = month.split("-")
    start = datetime(int(y), int(m), 1)
    if int(m) == 12:
        end = datetime(int(y) + 1, 1, 1)
    else:
        end = datetime(int(y), int(m) + 1, 1)
    return start, end


@router.get("/summary")
def summary(month: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    start, end = _month_range(month)
    income_total = db.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.user_id == current_user.id, Income.date >= start, Income.date < end
    ).scalar()
    expense_total = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == current_user.id, Expense.date >= start, Expense.date < end
    ).scalar()
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    return {
        "month": month,
        "income": round(float(income_total), 2),
        "expenses": round(float(expense_total), 2),
        "net": round(float(income_total) - float(expense_total), 2),
        "budgets": [{"id": b.id, "category_id": b.category_id, "amount": b.amount} for b in budgets],
    }