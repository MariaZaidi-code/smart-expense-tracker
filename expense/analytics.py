"""Testable expense calculations used by the dashboard and agent tools."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from database.connection import get_connection
from expense.budgets import list_budgets


def month_summary(month: str, db_path: str | Path | None = None) -> dict:
    with get_connection(db_path) as connection:
        total = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE substr(transaction_date, 1, 7) = ?",
            (month,),
        ).fetchone()[0]
        budget = connection.execute(
            "SELECT COALESCE(amount, 0) FROM budgets WHERE month = ? AND category_id IS NULL",
            (month,),
        ).fetchone()
        total_budget = budget[0] if budget else 0

    current = datetime.strptime(month, "%Y-%m")
    previous_month = (
        f"{current.year - 1}-12"
        if current.month == 1
        else f"{current.year}-{current.month - 1:02d}"
    )
    with get_connection(db_path) as connection:
        previous_total = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE substr(transaction_date, 1, 7) = ?",
            (previous_month,),
        ).fetchone()[0]
    change = ((total - previous_total) / previous_total * 100) if previous_total else 0
    return {
        "total_spent": total,
        "total_budget": total_budget,
        "remaining": total_budget - total,
        "previous_total": previous_total,
        "month_change_percent": change,
    }


def category_breakdown(month: str, db_path: str | Path | None = None) -> list[dict]:
    with get_connection(db_path) as connection:
        return [
            dict(row)
            for row in connection.execute(
                """
                SELECT c.name AS category, COALESCE(SUM(t.amount), 0) AS amount
                FROM transactions t
                JOIN categories c ON c.id = t.category_id
                WHERE substr(t.transaction_date, 1, 7) = ?
                GROUP BY c.id
                ORDER BY amount DESC
                """,
                (month,),
            )
        ]


def spending_trend(month: str, db_path: str | Path | None = None) -> list[dict]:
    with get_connection(db_path) as connection:
        return [
            dict(row)
            for row in connection.execute(
                """
                SELECT transaction_date AS date, SUM(amount) AS amount
                FROM transactions
                WHERE substr(transaction_date, 1, 7) = ?
                GROUP BY transaction_date
                ORDER BY transaction_date
                """,
                (month,),
            )
        ]


def unusual_spending(month: str, db_path: str | Path | None = None) -> list[dict]:
    """Flag categories 25% above their average across the prior three months."""
    current = {row["category"]: row["amount"] for row in category_breakdown(month, db_path)}
    with get_connection(db_path) as connection:
        history = connection.execute(
            """
            SELECT c.name AS category,
                   SUM(t.amount) / COUNT(DISTINCT substr(t.transaction_date, 1, 7)) AS average
            FROM transactions t
            JOIN categories c ON c.id = t.category_id
            WHERE substr(t.transaction_date, 1, 7) < ?
              AND substr(t.transaction_date, 1, 7) >= strftime('%Y-%m', date(?, '-3 months'))
            GROUP BY c.id
            """,
            (month, f"{month}-01"),
        ).fetchall()
    alerts = []
    for row in history:
        amount, average = current.get(row["category"], 0), row["average"]
        if average and amount > average * 1.25:
            percent = round((amount - average) / average * 100)
            alerts.append(
                {
                    "category": row["category"],
                    "percent": percent,
                    "reason": f"{row['category']} is {percent}% above your 3-month average.",
                }
            )
    return alerts


def budget_status(month: str, db_path: str | Path | None = None) -> list[dict]:
    return [budget for budget in list_budgets(month, db_path) if budget["category"]]
