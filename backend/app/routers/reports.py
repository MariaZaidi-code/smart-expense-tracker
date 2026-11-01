from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Expense, User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
def summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = db.query(func.coalesce(func.sum(Expense.amount), 0.0)).filter(Expense.user_id == current_user.id).scalar() or 0.0
    count = db.query(Expense).filter(Expense.user_id == current_user.id).count()
    return {"total_expenses": total, "count": count}


@router.get("/by-category")
def by_category(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(Expense.category_id, func.coalesce(func.sum(Expense.amount), 0.0).label("total"))
        .filter(Expense.user_id == current_user.id)
        .group_by(Expense.category_id)
        .all()
    )
    return [{"category_id": r[0], "total": r[1]} for r in rows]


@router.get("/trends")
def trends(days: int = Query(default=30, ge=1), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(func.date(Expense.date).label("day"), func.coalesce(func.sum(Expense.amount), 0.0).label("total"))
        .filter(Expense.user_id == current_user.id, Expense.date >= since)
        .group_by(func.date(Expense.date))
        .order_by(func.date(Expense.date))
        .all()
    )
    return [{"date": str(r[0]), "total": r[1]} for r in rows]
