from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Currency, User
from app.schemas import CurrencyCreate, CurrencyOut, CurrencyUpdate

router = APIRouter(prefix="/currencies", tags=["currencies"])


def _get_or_create(db, code):
    c = db.query(Currency).filter(Currency.code == code).first()
    if not c:
        c = Currency(code=code, rate=1.0, updated_at=datetime.utcnow())
        db.add(c)
        db.commit()
        db.refresh(c)
    return c


@router.get("", response_model=list[CurrencyOut])
def list_currencies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Currency).order_by(Currency.code).all()


@router.get("/{code}", response_model=CurrencyOut)
def get_currency(code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(Currency).filter(Currency.code == code).first()
    if not c:
        raise HTTPException(status_code=404, detail="Currency not found")
    return c


@router.post("", response_model=CurrencyOut, status_code=201)
def create_currency(payload: CurrencyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Currency).filter(Currency.code == payload.code).first()
    if existing:
        existing.rate = payload.rate
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    c = Currency(code=payload.code, rate=payload.rate, updated_at=datetime.utcnow())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.put("/{code}", response_model=CurrencyOut)
def update_currency(code: str, payload: CurrencyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = _get_or_create(db, code)
    c.rate = payload.rate
    c.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(c)
    return c


@router.patch("/{code}", response_model=CurrencyOut)
def patch_currency(code: str, payload: CurrencyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return update_currency(code, payload, db, current_user)


@router.post("/{code}", response_model=CurrencyOut)
def post_update_currency(code: str, payload: CurrencyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return update_currency(code, payload, db, current_user)
