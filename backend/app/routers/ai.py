from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai import categorize, categorize_detail, insights, detect_anomalies, nl_query
from app.deps import get_current_user, get_db
from app.models import Category, Expense, User

router = APIRouter(prefix="/ai", tags=["ai"])


class CategorizeRequest(BaseModel):
    description: Optional[str] = None
    amount: float


class QueryRequest(BaseModel):
    question: str


@router.post("/categorize")
def categorize_endpoint(payload: CategorizeRequest):
    detail = categorize_detail(payload.description, payload.amount)
    return {"category": detail["category"], "confidence": detail["confidence"], "source": detail["source"]}


def _last_90_expenses(db, user_id):
    since = datetime.utcnow() - timedelta(days=90)
    rows = db.query(Expense).filter(Expense.user_id == user_id, Expense.date >= since).all()
    return rows


def _expense_to_dict(e, db):
    cat_name = None
    if e.category_id:
        c = db.query(Category).filter(Category.id == e.category_id).first()
        if c:
            cat_name = c.name
    return {"id": e.id, "amount": e.amount, "description": e.description, "category": cat_name, "date": e.date}


@router.post("/insights")
def insights_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = _last_90_expenses(db, current_user.id)
    items = [_expense_to_dict(e, db) for e in rows]
    by_cat = {}
    monthly = {}
    for it in items:
        by_cat[it["category"] or "Other"] = by_cat.get(it["category"] or "Other", 0.0) + it["amount"]
        d = it["date"]
        if d:
            key = d.strftime("%Y-%m")
            monthly[key] = monthly.get(key, 0.0) + it["amount"]
    summary = {"expenses": items, "by_category": by_cat, "monthly_totals": monthly}
    return {"insights": insights(summary)}


@router.post("/anomalies")
def anomalies_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = db.query(Expense).filter(Expense.user_id == current_user.id).all()
    # attach category name attribute for detection (avoid clobbering the ORM relationship)
    for e in rows:
        if e.category_id:
            c = db.query(Category).filter(Category.id == e.category_id).first()
            e.category_name = c.name if c else None
        else:
            e.category_name = None
    result = detect_anomalies(rows)
    return {"anomalies": [_expense_to_dict(e, db) for e in result]}


@router.post("/query")
def query_endpoint(payload: QueryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = _last_90_expenses(db, current_user.id)
    items = [_expense_to_dict(e, db) for e in rows]
    by_cat = {}
    total = 0.0
    for it in items:
        by_cat[it["category"] or "Other"] = by_cat.get(it["category"] or "Other", 0.0) + it["amount"]
        total += it["amount"]
    context = {"total": total, "by_category": by_cat, "expenses": items}
    return {"answer": nl_query(payload.question, context)}