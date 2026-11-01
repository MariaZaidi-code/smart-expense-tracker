import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from expense import transactions, budgets, analytics


@pytest.fixture
def db(tmp_path):
    return str(tmp_path / "test.db")


def test_add_and_list_transaction(db):
    tx = transactions.add_transaction("2026-11-01", 500, "Food", "lunch", db_path=db)
    assert tx["id"] >= 1
    rows = transactions.list_transactions(db_path=db)
    assert len(rows) == 1
    assert rows[0]["amount"] == 500.0


def test_invalid_transaction(db):
    with pytest.raises(ValueError):
        transactions.add_transaction("bad", 10, "Food", db_path=db)
    with pytest.raises(ValueError):
        transactions.add_transaction("2026-11-01", -5, "Food", db_path=db)
    with pytest.raises(ValueError):
        transactions.add_transaction("2026-11-01", 10, "Nope", db_path=db)


def test_update_delete(db):
    tx = transactions.add_transaction("2026-11-01", 100, "Food", db_path=db)
    upd = transactions.update_transaction(tx["id"], amount=150, db_path=db)
    assert upd["amount"] == 150.0
    assert transactions.delete_transaction(tx["id"], db_path=db) is True
    with pytest.raises(ValueError):
        transactions.delete_transaction(tx["id"], db_path=db)


def test_budget_and_remaining(db):
    budgets.create_budget("2026-11", "Food", 2000, db_path=db)
    transactions.add_transaction("2026-11-02", 500, "Food", db_path=db)
    status = analytics.remaining_budget("2026-11", "Food", db_path=db)
    assert status["remaining"] == 1500.0


def test_summary_and_comparison(db):
    transactions.add_transaction("2026-11-01", 100, "Food", db_path=db)
    transactions.add_transaction("2026-10-01", 50, "Food", db_path=db)
    s = analytics.total_spending(month="2026-11", db_path=db)
    assert s == 100.0
    cmp = analytics.month_comparison("2026-10", "2026-11", db_path=db)
    assert cmp["difference"] == 50.0


def test_mcp_add_expense_tool(db, monkeypatch):
    # point MCP tools at temp db via env
    import os
    os.environ["EXPENSE_DB_PATH"] = db
    # reload connection default by passing db_path not supported by tool; tool uses default env
    # Re-init schema
    from database.connection import init_db
    init_db(db)
    out = __import__("mcp_server.tools", fromlist=["add_expense"]).add_expense("2026-11-01", 10, "Food", "x")
    assert out["ok"] is True
    out2 = __import__("mcp_server.tools", fromlist=["get_spending_summary"]).get_spending_summary("2026-11")
    assert out2["ok"] is True
    assert out2["total"] == 10.0
