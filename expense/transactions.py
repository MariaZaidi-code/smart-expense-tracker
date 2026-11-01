import re
from datetime import datetime

from database.connection import get_connection, init_db

VALID_CATEGORIES = {
    "Food", "Transport", "Utilities", "Entertainment",
    "Shopping", "Health", "Other",
}

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_date(value):
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise ValueError("date must be YYYY-MM-DD")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValueError("invalid date")


def _validate_amount(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise ValueError("amount must be a number")
    if amount <= 0:
        raise ValueError("amount must be positive")
    return amount


def _validate_category(value):
    if value not in VALID_CATEGORIES:
        raise ValueError(f"unknown category: {value}")


def _conn(db_path):
    conn = init_db(db_path)
    return conn


def add_transaction(date, amount, category, description="", db_path=None):
    _validate_date(date)
    amount = _validate_amount(amount)
    _validate_category(category)
    conn = _conn(db_path)
    cur = conn.execute(
        "INSERT INTO transactions (date, amount, category, description) VALUES (?,?,?,?)",
        (date, amount, category, description or ""),
    )
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return {"id": tid, "date": date, "amount": amount, "category": category,
            "description": description or ""}


def list_transactions(month=None, category=None, db_path=None):
    conn = _conn(db_path)
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if month:
        query += " AND substr(date,1,7)=?"
        params.append(month)
    if category:
        query += " AND category=?"
        params.append(category)
    query += " ORDER BY date DESC, id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_transaction(tid, db_path=None):
    conn = _conn(db_path)
    row = conn.execute("SELECT * FROM transactions WHERE id=?", (tid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_transaction(tid, date=None, amount=None, category=None, description=None, db_path=None):
    existing = get_transaction(tid, db_path)
    if existing is None:
        raise ValueError(f"transaction {tid} not found")
    new_date = date if date is not None else existing["date"]
    new_amount = amount if amount is not None else existing["amount"]
    new_category = category if category is not None else existing["category"]
    new_desc = description if description is not None else existing["description"]
    _validate_date(new_date)
    new_amount = _validate_amount(new_amount)
    _validate_category(new_category)
    conn = _conn(db_path)
    conn.execute(
        "UPDATE transactions SET date=?, amount=?, category=?, description=? WHERE id=?",
        (new_date, new_amount, new_category, new_desc, tid),
    )
    conn.commit()
    conn.close()
    return {"id": tid, "date": new_date, "amount": new_amount, "category": new_category,
            "description": new_desc}


def delete_transaction(tid, db_path=None):
    conn = _conn(db_path)
    cur = conn.execute("DELETE FROM transactions WHERE id=?", (tid,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    if not deleted:
        raise ValueError(f"transaction {tid} not found")
    return True
