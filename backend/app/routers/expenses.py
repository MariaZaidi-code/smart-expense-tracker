from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai import categorize
from app.deps import get_current_user, get_db
from app.models import Category, Expense, User
from app.schemas import ExpenseCreate, ExpenseOut, ExpenseUpdate

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    category_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Expense).filter(Expense.user_id == current_user.id)
    if category_id is not None:
        q = q.filter(Expense.category_id == category_id)
    if date_from is not None:
        q = q.filter(Expense.date >= date_from)
    if date_to is not None:
        q = q.filter(Expense.date <= date_to)
    if min_amount is not None:
        q = q.filter(Expense.amount >= min_amount)
    if max_amount is not None:
        q = q.filter(Expense.amount <= max_amount)
    if search:
        q = q.filter(Expense.description.ilike(f"%{search}%"))
    return q.order_by(Expense.date.desc()).all()


@router.post("", response_model=ExpenseOut, status_code=201)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    category_id = payload.category_id
    if category_id is None:
        cat_name = categorize(payload.description, payload.amount)
        cat = db.query(Category).filter(
            Category.name == cat_name,
            (Category.user_id == current_user.id) | (Category.is_default == True),  # noqa: E712
        ).first()
        if cat is None:
            cat = Category(name=cat_name, type="expense", user_id=current_user.id)
            db.add(cat)
            db.commit()
            db.refresh(cat)
        category_id = cat.id
    expense = Expense(
        user_id=current_user.id,
        amount=payload.amount,
        currency=payload.currency or "USD",
        description=payload.description,
        category_id=category_id,
        date=payload.date or datetime.utcnow(),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, payload: ExpenseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if payload.amount is not None:
        expense.amount = payload.amount
    if payload.currency is not None:
        expense.currency = payload.currency
    if payload.description is not None:
        expense.description = payload.description
    if payload.category_id is not None:
        expense.category_id = payload.category_id
    if payload.date is not None:
        expense.date = payload.date
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return None
