"""Seed the local database with synthetic demonstration data."""

from __future__ import annotations

import argparse
import calendar
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.connection import get_connection, initialize_database

CATEGORIES = [
    ("Food & dining", "utensils"),
    ("Bills & utilities", "receipt"),
    ("Transport", "car"),
    ("Groceries", "basket"),
    ("Shopping", "bag"),
    ("Entertainment", "ticket"),
    ("Health", "heart"),
]

TRANSACTIONS = [
    ("Lahore Kitchen", 1450, "Food & dining", 0, "Card"),
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

# (description, amount, category, charge day, months of history)
RECURRING = [
    ("Netflix subscription", 1200, "Entertainment", 3, 6),
    ("Spotify Premium", 450, "Entertainment", 8, 6),
    ("PTCL Internet", 3200, "Bills & utilities", 1, 6),
    ("Pulse Fitness gym", 2500, "Health", 5, 6),
]

BUDGETS = [
    ("Food & dining", 8000),
    ("Bills & utilities", 12000),
    ("Transport", 7000),
    ("Groceries", 9000),
    ("Shopping", 6000),
    ("Entertainment", 4000),
    ("Health", 4000),
]

GOALS = [
    ("Emergency fund", 300000, 85000, 9, "safety"),
    ("New laptop", 250000, 40000, 6, "purchase"),
]

# Demonstrated merchant -> category learning (normally created as the user saves).
MERCHANT_RULES = [("chai corner", "Food & dining", 4), ("careem ride", "Transport", 3)]


def _month_start(offset: int, today: date) -> date:
    index = today.year * 12 + (today.month - 1) - offset
    return date(index // 12, index % 12 + 1, 1)


def _on_day(month_start: date, day: int) -> date:
    return month_start.replace(day=min(day, calendar.monthrange(month_start.year, month_start.month)[1]))


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
            connection.execute("DELETE FROM goals")
            connection.execute("DELETE FROM merchant_rules")

        connection.executemany(
            "INSERT OR IGNORE INTO categories(name, icon) VALUES (?, ?)", CATEGORIES
        )
        count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if not count:
            category_ids = {
                row["name"]: row["id"]
                for row in connection.execute("SELECT id, name FROM categories")
            }
            rows = []
            for description, amount, category, days_ago, method in TRANSACTIONS:
                rows.append(
                    (
                        description,
                        amount,
                        category_ids[category],
                        (today - timedelta(days=days_ago)).isoformat(),
                        method,
                    )
                )

            # Prior-month discretionary spending so month-over-month is meaningful.
            for index, (category, amount) in enumerate(
                [
                    ("Food & dining", 9200),
                    ("Bills & utilities", 8800),
                    ("Transport", 5200),
                    ("Groceries", 7300),
                    ("Shopping", 4200),
                ]
            ):
                rows.append(
                    (
                        f"Previous month {category}",
                        amount,
                        category_ids[category],
                        previous_month_day.replace(day=min(index * 4 + 2, 25)).isoformat(),
                        "Card",
                    )
                )

            # Recurring charges across six months enable subscription detection and
            # next-due forecasting.  Future-dated occurrences are skipped.
            for description, amount, category, day, months in RECURRING:
                for offset in range(months):
                    charge_date = _on_day(_month_start(offset, today), day)
                    if charge_date > today:
                        continue
                    rows.append(
                        (
                            description,
                            amount,
                            category_ids[category],
                            charge_date.isoformat(),
                            "Card",
                        )
                    )

            connection.executemany(
                """
                INSERT INTO transactions
                    (description, amount, category_id, transaction_date, payment_method)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
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

        if connection.execute("SELECT COUNT(*) FROM goals").fetchone()[0] == 0:
            for name, target, saved, months_ahead, category in GOALS:
                target_date = _month_start(-months_ahead, today).replace(day=28)
                connection.execute(
                    """
                    INSERT INTO goals(name, target_amount, saved_amount, target_date, category)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, target, saved, target_date.isoformat(), category),
                )

        if connection.execute("SELECT COUNT(*) FROM merchant_rules").fetchone()[0] == 0:
            connection.executemany(
                """
                INSERT INTO merchant_rules(merchant, category, times_used, confidence)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (merchant, category, times, min(0.99, 0.5 + 0.08 * times))
                    for merchant, category, times in MERCHANT_RULES
                ],
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--db", type=Path)
    args = parser.parse_args()
    seed_database(args.db, args.reset)
    print("Synthetic expense data seeded successfully.")
