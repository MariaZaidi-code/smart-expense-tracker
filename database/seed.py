"""Seed the local database with synthetic demonstration data."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

from database.connection import get_connection, initialize_database

CATEGORIES = [
    ("Food & dining", "utensils"),
    ("Bills & utilities", "receipt"),
    ("Transport", "car"),
    ("Groceries", "basket"),
    ("Shopping", "bag"),
    ("Entertainment", "ticket"),
]

TRANSACTIONS = [
    ("Lahore Kitchen", 1450, "Food & dining", 0, "Card"),
    ("PTCL Internet", 3200, "Bills & utilities", 1, "Bank transfer"),
    ("Metro Card", 500, "Transport", 2, "Cash"),
    ("Fresh Basket", 2740, "Groceries", 3, "Card"),
    ("Stationery Hub", 890, "Shopping", 4, "Card"),
    ("Cinepax", 1800, "Entertainment", 5, "Card"),
    ("Chai Corner", 650, "Food & dining", 6, "Cash"),
    ("Careem ride", 1180, "Transport", 7, "Card"),
    ("Grocery Mart", 3650, "Groceries", 8, "Card"),
    ("Campus Cafe", 920, "Food & dining", 9, "Cash"),
    ("Electricity bill", 5800, "Bills & utilities", 11, "Bank transfer"),
    ("Sunday brunch", 2350, "Food & dining", 13, "Card"),
]

BUDGETS = [
    ("Food & dining", 8000),
    ("Bills & utilities", 12000),
    ("Transport", 7000),
    ("Groceries", 9000),
    ("Shopping", 6000),
    ("Entertainment", 4000),
]


def seed_database(db_path: str | Path | None = None, reset: bool = False) -> None:
    initialize_database(db_path)
    today = date.today()
    month = today.strftime("%Y-%m")
    previous_month_day = today.replace(day=1) - timedelta(days=1)

    with get_connection(db_path) as connection:
        if reset:
            connection.execute("DELETE FROM transactions")
            connection.execute("DELETE FROM budgets")
            connection.execute("DELETE FROM categories")

        connection.executemany(
            "INSERT OR IGNORE INTO categories(name, icon) VALUES (?, ?)", CATEGORIES
        )
        count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if not count:
            category_ids = {
                row["name"]: row["id"]
                for row in connection.execute("SELECT id, name FROM categories")
            }
            connection.executemany(
                """
                INSERT INTO transactions
                    (description, amount, category_id, transaction_date, payment_method)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        description,
                        amount,
                        category_ids[category],
                        (today - timedelta(days=days_ago)).isoformat(),
                        method,
                    )
                    for description, amount, category, days_ago, method in TRANSACTIONS
                ],
            )
            # Previous-month records make the month-over-month KPI meaningful.
            connection.executemany(
                """
                INSERT INTO transactions
                    (description, amount, category_id, transaction_date, payment_method)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        f"Previous month {category}",
                        amount,
                        category_ids[category],
                        previous_month_day.replace(day=min(index * 3 + 2, 25)).isoformat(),
                        "Card",
                    )
                    for index, (category, amount) in enumerate(
                        [
                            ("Food & dining", 9200),
                            ("Bills & utilities", 8800),
                            ("Transport", 5200),
                            ("Groceries", 7300),
                        ]
                    )
                ],
            )

        category_ids = {
            row["name"]: row["id"]
            for row in connection.execute("SELECT id, name FROM categories")
        }
        connection.execute(
            "INSERT OR IGNORE INTO budgets(month, category_id, amount) VALUES (?, NULL, ?)",
            (month, 46000),
        )
        connection.executemany(
            "INSERT OR IGNORE INTO budgets(month, category_id, amount) VALUES (?, ?, ?)",
            [(month, category_ids[name], amount) for name, amount in BUDGETS],
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--db", type=Path)
    args = parser.parse_args()
    seed_database(args.db, args.reset)
    print("Synthetic expense data seeded successfully.")
