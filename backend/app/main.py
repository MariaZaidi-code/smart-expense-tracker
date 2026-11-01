from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine, init_db
from app.models import Category, Currency
from app.routers import ai, auth, budgets, categories, currencies, expenses, export, income, incomes, recurring, reports

DEFAULT_CATEGORIES = [
    ("Food", "expense"),
    ("Transport", "expense"),
    ("Housing", "expense"),
    ("Entertainment", "expense"),
    ("Health", "expense"),
    ("Education", "expense"),
    ("Shopping", "expense"),
    ("Utilities", "expense"),
    ("Other", "expense"),
    ("Salary", "income"),
    ("Freelance", "income"),
    ("Investment", "income"),
    ("Other", "income"),
]


def seed_categories():
    from sqlalchemy.orm import Session

    from app.db import SessionLocal

    db = SessionLocal()
    try:
        if db.query(Category).filter(Category.is_default == True).count() == 0:  # noqa: E712
            for name, ctype in DEFAULT_CATEGORIES:
                db.add(Category(name=name, type=ctype, is_default=True, user_id=None))
            db.commit()
        if db.query(Currency).filter(Currency.code == "USD").first() is None:
            db.add(Currency(code="USD", rate=1.0))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_categories()
    yield


app = FastAPI(title="Smart Expense Tracker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(incomes.router)
app.include_router(income.router, prefix="/income")
app.include_router(budgets.router)
app.include_router(recurring.router, prefix="/recurring")
app.include_router(recurring.router, prefix="/recurring-expenses")
app.include_router(reports.router)
app.include_router(currencies.router)
app.include_router(export.router)


@app.get("/health")
def health():
    return {"status": "ok"}
