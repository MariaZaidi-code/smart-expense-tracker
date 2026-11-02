"""Validated transaction CRUD operations."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from database.connection import get_connection


def _validate(description: str, amount: float, category: str, transaction_date: str) -> None:
    if not description or not description.strip():
        raise ValueError("Description is required.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if not category or not category.strip():
        raise ValueError("Category is required.")
    try:
        date.fromisoformat(transaction_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("Enter a valid transaction date.") from exc


def list_categories(db_path: str | Path | None = None) -> list[str]:
    with get_connection(db_path) as connection:
        return [
            row["name"]
            for row in connection.execute("SELECT name FROM categories ORDER BY name")
        ]


def list_transactions(
    db_path: str | Path | None = None,
    search: str = "",
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    sort: str = "newest",
) -> list[dict]:
    clauses, params = [], []
    if search:
        clauses.append("(LOWER(t.description) LIKE ? OR LOWER(c.name) LIKE ?)")
        pattern = f"%{search.lower()}%"
        params.extend([pattern, pattern])
    if category:
        clauses.append("c.name = ?")
        params.append(category)
    if start_date:
        clauses.append("t.transaction_date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("t.transaction_date <= ?")
        params.append(end_date)
    if min_amount is not None:
        clauses.append("t.amount >= ?")
        params.append(min_amount)
    if max_amount is not None:
        clauses.append("t.amount <= ?")
        params.append(max_amount)

    order = {
        "newest": "t.transaction_date DESC, t.id DESC",
        "oldest": "t.transaction_date ASC, t.id ASC",
        "amount_high": "t.amount DESC",
        "amount_low": "t.amount ASC",
    }.get(sort, "t.transaction_date DESC, t.id DESC")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT t.id, t.description, t.amount, c.name AS category,
               t.transaction_date, t.payment_method, t.notes
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
        {where}
        ORDER BY {order}
    """
    with get_connection(db_path) as connection:
        return [dict(row) for row in connection.execute(query, params)]


def add_transaction(
    description: str,
    amount: float,
    category: str,
    transaction_date: str,
    payment_method: str = "Card",
    notes: str = "",
    db_path: str | Path | None = None,
) -> int:
    _validate(description, amount, category, transaction_date)
    with get_connection(db_path) as connection:
        category_row = connection.execute(
            "SELECT id FROM categories WHERE name = ?", (category,)
        ).fetchone()
        if not category_row:
            raise ValueError("Select a valid category.")
        cursor = connection.execute(
            """
            INSERT INTO transactions
                (description, amount, category_id, transaction_date, payment_method, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                description.strip(),
                amount,
                category_row["id"],
                transaction_date,
                payment_method,
                notes.strip(),
            ),
        )
        return int(cursor.lastrowid)


def update_transaction(
    transaction_id: int,
    description: str,
    amount: float,
    category: str,
    transaction_date: str,
    payment_method: str = "Card",
    notes: str = "",
    db_path: str | Path | None = None,
) -> None:
    _validate(description, amount, category, transaction_date)
    with get_connection(db_path) as connection:
        category_row = connection.execute(
            "SELECT id FROM categories WHERE name = ?", (category,)
        ).fetchone()
        if not category_row:
            raise ValueError("Select a valid category.")
        cursor = connection.execute(
            """
            UPDATE transactions
            SET description = ?, amount = ?, category_id = ?,
                transaction_date = ?, payment_method = ?, notes = ?
            WHERE id = ?
            """,
            (
                description.strip(),
                amount,
                category_row["id"],
                transaction_date,
                payment_method,
                notes.strip(),
                transaction_id,
            ),
        )
        if cursor.rowcount == 0:
            raise ValueError("Transaction not found.")


def delete_transaction(
    transaction_id: int, db_path: str | Path | None = None
) -> None:
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM transactions WHERE id = ?", (transaction_id,)
        )
        if cursor.rowcount == 0:
            raise ValueError("Transaction not found.")
