from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Income, User
from app.schemas import IncomeCreate, IncomeOut, IncomeUpdate

router = APIRouter(prefix="/incomes", tags=["incomes"])


@router.get("", response_model=list[IncomeOut])
def list_incomes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Income).filter(Income.user_id == current_user.id).order_by(Income.date.desc()).all()


@router.post("", response_model=IncomeOut, status_code=201)
def create_income(payload: IncomeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    income = Income(
        user_id=current_user.id,
        amount=payload.amount,
        currency=payload.currency or "USD",
        source=payload.source,
        date=payload.date or datetime.utcnow(),
        notes=payload.notes,
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


@router.get("/{income_id}", response_model=IncomeOut)
def get_income(income_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    income = db.query(Income).filter(Income.id == income_id, Income.user_id == current_user.id).first()
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
    return income


@router.put("/{income_id}", response_model=IncomeOut)
def update_income(income_id: int, payload: IncomeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    income = db.query(Income).filter(Income.id == income_id, Income.user_id == current_user.id).first()
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
    if payload.amount is not None:
        income.amount = payload.amount
    if payload.currency is not None:
        income.currency = payload.currency
    if payload.source is not None:
        income.source = payload.source
    if payload.date is not None:
        income.date = payload.date
    if payload.notes is not None:
        income.notes = payload.notes
    db.commit()
    db.refresh(income)
    return income


@router.delete("/{income_id}", status_code=204)
def delete_income(income_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    income = db.query(Income).filter(Income.id == income_id, Income.user_id == current_user.id).first()
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
    db.delete(income)
    db.commit()
    return None
