import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import Expense, Income, User

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/csv")
def export_csv(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["type", "id", "amount", "currency", "description", "source", "category_id", "date"])
    for e in db.query(Expense).filter(Expense.user_id == current_user.id).all():
        writer.writerow(["expense", e.id, e.amount, e.currency, e.description, "", e.category_id, e.date])
    for i in db.query(Income).filter(Income.user_id == current_user.id).all():
        writer.writerow(["income", i.id, i.amount, i.currency, "", i.source, "", i.date])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=export.csv"})


@router.get("/json")
def export_json(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = {
        "expenses": [
            {"id": e.id, "amount": e.amount, "currency": e.currency, "description": e.description, "category_id": e.category_id, "date": e.date.isoformat() if e.date else None}
            for e in db.query(Expense).filter(Expense.user_id == current_user.id).all()
        ],
        "incomes": [
            {"id": i.id, "amount": i.amount, "currency": i.currency, "source": i.source, "date": i.date.isoformat() if i.date else None}
            for i in db.query(Income).filter(Income.user_id == current_user.id).all()
        ],
    }
    content = json.dumps(data, default=str)
    return StreamingResponse(iter([content]), media_type="application/json", headers={"Content-Disposition": "attachment; filename=export.json"})
