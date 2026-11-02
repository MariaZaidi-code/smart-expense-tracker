"""Monthly and category budget data access."""

from __future__ import annotations

from pathlib import Path

from database.connection import get_connection


def set_budget(
    month: str,
    amount: float,
    category: str | None = None,
    db_path: str | Path | None = None,
) -> int:
    if len(month) != 7 or month[4] != "-":
        raise ValueError("Month must use YYYY-MM format.")
    if amount <= 0:
        raise ValueError("Budget amount must be greater than zero.")
    with get_connection(db_path) as connection:
        category_id = None
        if category:
            row = connection.execute(
                "SELECT id FROM categories WHERE name = ?", (category,)
            ).fetchone()
            if not row:
                raise ValueError("Select a valid category.")
            category_id = row["id"]
        existing = connection.execute(
            "SELECT id FROM budgets WHERE month = ? AND category_id IS ?",
            (month, category_id),
        ).fetchone()
        if existing:
            connection.execute(
                "UPDATE budgets SET amount = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (amount, existing["id"]),
            )
            return int(existing["id"])
        cursor = connection.execute(
            "INSERT INTO budgets(month, category_id, amount) VALUES (?, ?, ?)",
            (month, category_id, amount),
        )
        return int(cursor.lastrowid)


def list_budgets(
    month: str, db_path: str | Path | None = None
) -> list[dict]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT b.id, b.month, b.amount,
                   c.name AS category,
                   COALESCE((
                       SELECT SUM(t.amount)
                       FROM transactions t
                       WHERE substr(t.transaction_date, 1, 7) = b.month
                         AND (b.category_id IS NULL OR t.category_id = b.category_id)
                   ), 0) AS spent
            FROM budgets b
            LEFT JOIN categories c ON c.id = b.category_id
            WHERE b.month = ?
            ORDER BY b.category_id IS NULL DESC, c.name
            """,
            (month,),
        ).fetchall()
        return [
            {
                **dict(row),
                "remaining": row["amount"] - row["spent"],
                "percent": (row["spent"] / row["amount"] * 100)
                if row["amount"]
                else 0,
            }
            for row in rows
        ]
