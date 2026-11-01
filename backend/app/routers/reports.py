from calendar import monthrange
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Budget, Currency, Expense, Income, User

router = APIRouter(prefix="/reports", tags=["reports"])


def rate_for(db: Session, code: Optional[str]) -> float:
    if not code or code == "USD":
        return 1.0
    c = db.query(Currency).filter(Currency.code == code).first()
    return c.rate if c else 1.0


def to_base(db: Session, amount: float, currency: Optional[str]) -> float:
    return amount * rate_for(db, currency)


def expenses_base(db: Session, user_id: int):
    rows = db.query(Expense).filter(Expense.user_id == user_id).all()
    return [(e, to_base(db, e.amount, e.currency)) for e in rows]


def incomes_base(db: Session, user_id: int):
    rows = db.query(Income).filter(Income.user_id == user_id).all()
    return [(i, to_base(db, i.amount, i.currency)) for i in rows]


@router.get("/summary")
def summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_expense = sum(v for _, v in expenses_base(db, current_user.id))
    total_income = sum(v for _, v in incomes_base(db, current_user.id))
    balance = total_income - total_expense
    savings_rate = (balance / total_income) if total_income else 0.0
    return {
        "income": total_income,
        "expense": total_expense,
        "balance": balance,
        "savings_rate": savings_rate,
        "total_income": total_income,
        "total_expenses": total_expense,
    }


@router.get("/by-category")
def by_category(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    spent_map = {}
    for e, val in expenses_base(db, current_user.id):
        spent_map[e.category_id] = spent_map.get(e.category_id, 0.0) + val
    budget_map = {}
    for b in db.query(Budget).filter(Budget.user_id == current_user.id).all():
        budget_map[b.category_id] = budget_map.get(b.category_id, 0.0) + b.amount
    ids = set(spent_map) | set(budget_map)
    result = []
    for cid in ids:
        result.append({
            "category_id": cid,
            "spent": spent_map.get(cid, 0.0),
            "budget": budget_map.get(cid, 0.0),
        })
    return result


@router.get("/trends")
def trends(period: str = Query(default="day", pattern="^(day|week|month|year)$"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agg = {}
    for e, val in expenses_base(db, current_user.id):
        d = e.date or datetime.utcnow()
        if period == "day":
            key = d.strftime("%Y-%m-%d")
        elif period == "week":
            iso = d.isocalendar()
            key = f"{iso[0]}-W{iso[1]:02d}"
        elif period == "month":
            key = d.strftime("%Y-%m")
        else:
            key = d.strftime("%Y")
        agg[key] = agg.get(key, 0.0) + val
    return [{"date": k, "total": v} for k, v in sorted(agg.items())]


@router.get("/top-expenses")
def top_expenses(limit: int = Query(default=10, ge=1), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = []
    for e, val in expenses_base(db, current_user.id):
        items.append((e, val))
    items.sort(key=lambda x: x[1], reverse=True)
    out = []
    for e, val in items[:limit]:
        out.append({
            "id": e.id,
            "amount": e.amount,
            "currency": e.currency,
            "converted_amount": val,
            "description": e.description,
            "category_id": e.category_id,
            "date": e.date,
        })
    return out


@router.get("/velocity")
def velocity(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    since = now - timedelta(days=30)
    recent = 0.0
    for e, val in expenses_base(db, current_user.id):
        if e.date and e.date >= since:
            recent += val
    avg_daily = recent / 30.0
    days_in_month = monthrange(now.year, now.month)[1]
    projected = avg_daily * days_in_month
    return {"avg_daily_spend": avg_daily, "projected_month_total": projected}
