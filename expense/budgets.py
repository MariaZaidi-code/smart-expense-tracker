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
    month: str | None = None, db_path: str | Path | None = None
) -> list[dict]:
    with get_connection(db_path) as connection:
        if month:
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
        else:
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
                ORDER BY b.month, b.category_id IS NULL DESC, c.name
                """
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


def get_budget(
    month: str,
    category: str | None = None,
    db_path: str | Path | None = None,
) -> dict | None:
    """Return one budget row.  ``category=None`` is the monthly total."""
    for budget in list_budgets(month, db_path):
        if budget["category"] == category:
            return budget
    return None


def create_budget(
    month: str,
    category: str | None,
    amount: float,
    db_path: str | Path | None = None,
) -> dict:
    """Qaim/MCP-compatible wrapper.

    ``category='ALL'`` (or ``None``) creates the monthly overall budget;
    every other value creates a category budget.
    """
    from expense.transactions import ensure_category

    clean_category = None if category in (None, "", "ALL") else category
    if clean_category:
        ensure_category(clean_category, db_path=db_path)
    budget_id = set_budget(month, amount, clean_category, db_path)
    return {
        "id": budget_id,
        "month": month,
        "category": clean_category or "ALL",
        "amount": float(amount),
    }


def delete_budget(budget_id: int, db_path: str | Path | None = None) -> bool:
    with get_connection(db_path) as connection:
        cursor = connection.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        if cursor.rowcount == 0:
            raise ValueError("Budget not found.")
        return True
