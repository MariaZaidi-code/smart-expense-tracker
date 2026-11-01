from database.connection import init_db

VALID_CATEGORIES = {
    "Food", "Transport", "Utilities", "Entertainment",
    "Shopping", "Health", "Other", "ALL",
}


def _conn(db_path):
    return init_db(db_path)


def create_budget(month, category, amount, db_path=None):
    if not isinstance(month, str) or len(month) != 7 or month[4] != "-":
        raise ValueError("month must be YYYY-MM")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"unknown category: {category}")
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        raise ValueError("amount must be a number")
    if amt < 0:
        raise ValueError("amount must be non-negative")
    conn = _conn(db_path)
    conn.execute(
        "INSERT INTO budgets (month, category, amount) VALUES (?,?,?) "
        "ON CONFLICT(month, category) DO UPDATE SET amount=excluded.amount",
        (month, category, amt),
    )
    conn.commit()
    conn.close()
    return {"month": month, "category": category, "amount": amt}


def list_budgets(month=None, db_path=None):
    conn = _conn(db_path)
    if month:
        rows = conn.execute("SELECT * FROM budgets WHERE month=?", (month,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM budgets ORDER BY month, category").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_budget(month, category=None, db_path=None):
    conn = _conn(db_path)
    if category:
        row = conn.execute(
            "SELECT * FROM budgets WHERE month=? AND category=?", (month, category)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    rows = conn.execute("SELECT * FROM budgets WHERE month=?", (month,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
