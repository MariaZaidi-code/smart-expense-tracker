import json
from datetime import datetime, timezone

from expense.transactions import (
    add_transaction, list_transactions, update_transaction, delete_transaction, get_transaction,
    VALID_CATEGORIES as TX_CATS,
)
from expense.budgets import create_budget as _create_budget, list_budgets as _list_budgets, get_budget as _get_budget
from expense.analytics import (
    total_spending, category_breakdown, remaining_budget, month_comparison, unusual_spending,
)
from rag.retriever import retrieve

BUDGET_CATS = TX_CATS | {"ALL"}


def search_financial_guidance(query, top_k=5):
    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        top_k = 5
    top_k = max(1, min(top_k, 20))
    try:
        results = retrieve(query, top_k=top_k)
    except Exception as e:
        return {"error": str(e), "results": []}
    out = []
    for r in results:
        out.append({
            "source": r.get("source"),
            "text": r.get("text"),
            "score": None if r.get("distance") is None else round(1 - r["distance"], 4),
        })
    return {"query": query, "count": len(out), "results": out}


def get_budgeting_rules():
    rules = [
        "50/30/20 rule: 50% needs, 30% wants, 20% savings/debt.",
        "Keep 3-6 months of expenses in an emergency fund.",
        "Track every expense and categorize consistently.",
        "Review budget weekly and monthly.",
    ]
    return {"rules": rules}


def add_expense(date, amount, category, description=""):
    try:
        tx = add_transaction(date, amount, category, description)
        return {"ok": True, "transaction": tx}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_expenses(month=None, category=None):
    try:
        txns = list_transactions(month=month, category=category)
        return {"ok": True, "count": len(txns), "transactions": txns}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_expense(transaction_id):
    try:
        tid = int(transaction_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": "transaction_id must be an integer"}
    try:
        delete_transaction(tid)
        return {"ok": True, "deleted": tid}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def update_expense(transaction_id, date=None, amount=None, category=None, description=None):
    try:
        tid = int(transaction_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": "transaction_id must be an integer"}
    try:
        tx = update_transaction(tid, date=date, amount=amount, category=category, description=description)
        return {"ok": True, "transaction": tx}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def create_budget(month, category, amount):
    from expense.budgets import create_budget as cb
    try:
        b = cb(month, category, amount)
        return {"ok": True, "budget": b}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_budgets(month=None):
    try:
        bs = _list_budgets(month=month)
        return {"ok": True, "count": len(bs), "budgets": bs}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_spending_summary(month):
    try:
        total = total_spending(month=month)
        breakdown = category_breakdown(month=month)
        return {"ok": True, "month": month, "total": total, "by_category": breakdown}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_budget_status(month, category=None):
    try:
        status = remaining_budget(month, category=category)
        return {"ok": True, "status": status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def compare_months(month_a, month_b):
    try:
        return {"ok": True, "comparison": month_comparison(month_a, month_b)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_unusual_spending(month):
    try:
        flags = unusual_spending(month)
        return {"ok": True, "month": month, "flags": flags}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def health_check():
    return {"status": "ok", "service": "expense-tracker-mcp", "time": datetime.now(timezone.utc).isoformat()}
