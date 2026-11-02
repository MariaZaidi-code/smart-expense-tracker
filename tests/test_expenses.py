from datetime import date

import pytest

from database.connection import get_connection, initialize_database
from expense.analytics import (
    category_breakdown,
    month_comparison,
    month_summary,
    remaining_budget,
    total_spending,
    unusual_spending,
)
from expense.budgets import create_budget, get_budget, list_budgets, set_budget
from expense.transactions import (
    add_transaction,
    delete_transaction,
    ensure_category,
    get_transaction,
    list_categories,
    list_transactions,
    update_transaction,
)


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "test.db"
    initialize_database(path)
    with get_connection(path) as connection:
        connection.executemany(
            "INSERT INTO categories(name) VALUES (?)",
            [("Food",), ("Transport",)],
        )
    return path


def test_transaction_crud(db):
    transaction_id = add_transaction(
        "Lunch", 500, "Food", "2026-11-05", "Cash", db_path=db
    )
    rows = list_transactions(db)
    assert rows[0]["description"] == "Lunch"
    assert rows[0]["amount"] == 500

    update_transaction(
        transaction_id, "Team lunch", 750, "Food", "2026-11-06", db_path=db
    )
    assert list_transactions(db)[0]["amount"] == 750
    delete_transaction(transaction_id, db)
    assert list_transactions(db) == []


def test_partial_update_and_get_transaction(db):
    transaction_id = add_transaction("Bus", 200, "Transport", "2026-11-03", db_path=db)
    update_transaction(transaction_id, amount=250, db_path=db)
    transaction = get_transaction(transaction_id, db)
    assert transaction["amount"] == 250
    assert transaction["description"] == "Bus"


@pytest.mark.parametrize(
    "description,amount,category,transaction_date",
    [
        ("", 500, "Food", "2026-11-05"),
        ("Lunch", 0, "Food", "2026-11-05"),
        ("Lunch", -10, "Food", "2026-11-05"),
        ("Lunch", 500, "", "2026-11-05"),
        ("Lunch", 500, "Food", "not-a-date"),
    ],
)
def test_bad_transaction_input_is_rejected(
    db, description, amount, category, transaction_date
):
    with pytest.raises(ValueError):
        add_transaction(
            description, amount, category, transaction_date, db_path=db
        )


def test_filters_and_sorting(db):
    add_transaction("Bus", 200, "Transport", "2026-11-03", db_path=db)
    add_transaction("Dinner", 1200, "Food", "2026-11-04", db_path=db)
    assert len(list_transactions(db, category="Food")) == 1
    assert list_transactions(db, sort="amount_high")[0]["amount"] == 1200
    assert len(list_transactions(db, min_amount=500)) == 1
    assert len(list_transactions(db, month="2026-11")) == 2
    assert len(list_transactions(db, month="2026-10")) == 0


def test_ensure_category_is_idempotent(db):
    first = ensure_category("Health", db_path=db)
    second = ensure_category("Health", db_path=db)
    assert first == second
    assert "Health" in list_categories(db)


def test_budget_and_summary_calculations(db):
    add_transaction("Lunch", 500, "Food", "2026-11-05", db_path=db)
    add_transaction("Dinner", 1000, "Food", "2026-11-06", db_path=db)
    add_transaction("October food", 2000, "Food", "2026-10-05", db_path=db)
    set_budget("2026-11", 5000, db_path=db)
    set_budget("2026-11", 2000, "Food", db_path=db)

    summary = month_summary("2026-11", db)
    assert summary["total_spent"] == 1500
    assert summary["remaining"] == 3500
    assert summary["month_change_percent"] == -25
    breakdown = category_breakdown("2026-11", db)
    assert breakdown == [{"category": "Food", "amount": 1500}]
    category_budget = [b for b in list_budgets("2026-11", db) if b["category"]][0]
    assert category_budget["remaining"] == 500
    assert category_budget["percent"] == 75

    status = remaining_budget("2026-11", "Food", db)
    assert status["budget"] == 2000
    assert status["remaining"] == 500
    assert total_spending("2026-11", db_path=db) == 1500

    comparison = month_comparison("2026-10", "2026-11", db)
    assert comparison["difference"] == -500


def test_budget_compatibility_wrappers(db):
    created = create_budget("2026-11", "ALL", 5000, db)
    assert created["category"] == "ALL"
    assert get_budget("2026-11", None, db)["amount"] == 5000
    create_budget("2026-11", "Food", 2000, db)
    assert get_budget("2026-11", "Food", db)["amount"] == 2000


def test_unusual_spending_rule_is_explainable(db):
    for month in ("2026-08", "2026-09", "2026-10"):
        add_transaction("Food", 1000, "Food", f"{month}-05", db_path=db)
    add_transaction("Food spike", 1500, "Food", "2026-11-05", db_path=db)
    alerts = unusual_spending("2026-11", db)
    assert alerts[0]["percent"] == 50
    assert "3-month average" in alerts[0]["reason"]


def test_mcp_add_expense_tool(db, monkeypatch):
    monkeypatch.setenv("EXPENSE_DB_PATH", str(db))
    initialize_database(db)
    from mcp_server import tools

    out = tools.add_expense("2026-11-01", 10, "Food", "x")
    assert out["ok"] is True
    summary = tools.get_spending_summary("2026-11")
    assert summary["ok"] is True
    assert summary["total"] == 10.0
    assert tools.list_expenses(month="2026-11")["count"] == 1
    assert tools.health_check()["status"] == "ok"
