from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Expense, RecurringExpense, User
from app.schemas import RecurringExpenseCreate, RecurringExpenseOut, RecurringExpenseUpdate

router = APIRouter(tags=["recurring"])


def _advance(dt: datetime, frequency: str) -> datetime:
    if frequency == "daily":
        return dt + timedelta(days=1)
    if frequency == "weekly":
        return dt + timedelta(weeks=1)
    if frequency == "monthly":
        return dt + timedelta(days=30)
    if frequency == "yearly":
        return dt + timedelta(days=365)
    return dt


@router.get("", response_model=list[RecurringExpenseOut])
def list_recurring(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(RecurringExpense).filter(RecurringExpense.user_id == current_user.id).all()


@router.post("", response_model=RecurringExpenseOut, status_code=201)
def create_recurring(payload: RecurringExpenseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = RecurringExpense(
        user_id=current_user.id,
        amount=payload.amount,
        currency=payload.currency,
        description=payload.description,
        category_id=payload.category_id,
        frequency=payload.frequency,
        next_run=payload.next_run or datetime.utcnow(),
        active=payload.active,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=RecurringExpenseOut)
def get_recurring(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(RecurringExpense).filter(RecurringExpense.id == item_id, RecurringExpense.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    return item


@router.put("/{item_id}", response_model=RecurringExpenseOut)
def update_recurring(item_id: int, payload: RecurringExpenseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(RecurringExpense).filter(RecurringExpense.id == item_id, RecurringExpense.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    if payload.amount is not None:
        item.amount = payload.amount
    if payload.currency is not None:
        item.currency = payload.currency
    if payload.description is not None:
        item.description = payload.description
    if payload.category_id is not None:
        item.category_id = payload.category_id
    if payload.frequency is not None:
        item.frequency = payload.frequency
    if payload.next_run is not None:
        item.next_run = payload.next_run
    if payload.active is not None:
        item.active = payload.active
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_recurring(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(RecurringExpense).filter(RecurringExpense.id == item_id, RecurringExpense.user_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    db.delete(item)
    db.commit()
    return None


@router.post("/run-due")
def run_due(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.utcnow()
    due_items = db.query(RecurringExpense).filter(
        RecurringExpense.user_id == current_user.id,
        RecurringExpense.active == True,  # noqa: E712
        RecurringExpense.next_run <= now,
    ).all()
    created_ids = []
    for item in due_items:
        expense = Expense(
            user_id=current_user.id,
            amount=item.amount,
            currency=item.currency,
            description=item.description,
            category_id=item.category_id,
            date=item.next_run,
        )
        db.add(expense)
        db.flush()
        created_ids.append(expense.id)
        item.next_run = _advance(item.next_run, item.frequency)
    db.commit()
    return {"created": len(created_ids), "expense_ids": created_ids}
