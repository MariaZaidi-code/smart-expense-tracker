"""Savings goals and sinking funds (YNAB / Monarch style).

A goal is a name, a target amount, what has been saved so far, and an optional
target date.  The UI and the agent both read the same rows, so progress is
consistent everywhere.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from database.connection import get_connection


def _months_until(target_date: str | None, today: date | None = None) -> int:
    if not target_date:
        return 0
    today = today or date.today()
    target = date.fromisoformat(target_date)
    months = (target.year - today.year) * 12 + (target.month - today.month)
    if target.day > today.day:
        months += 1
    return max(months, 0)


def _decorate(row: dict, today: date | None = None) -> dict:
    today = today or date.today()
    target = float(row["target_amount"])
    saved = float(row["saved_amount"])
    remaining = max(target - saved, 0.0)
    progress = (saved / target * 100) if target else 0.0
    months = _months_until(row.get("target_date"), today)
    required_monthly = round(remaining / months, 2) if months else None

    status = "achieved" if remaining <= 0 else "active"
    if status == "active" and row.get("target_date"):
        created = (row.get("created_at") or today.isoformat())[:10]
        try:
            start = date.fromisoformat(created)
            end = date.fromisoformat(row["target_date"])
            total_days = max((end - start).days, 1)
            elapsed_days = max((today - start).days, 0)
            if elapsed_days < 1:
                # A goal created today has no track record yet.
                status = "active"
            else:
                expected_progress = min(elapsed_days / total_days, 1.0) * target
                status = "on_track" if saved + 0.5 >= expected_progress else "behind"
        except ValueError:
            status = "active"

    return {
        **row,
        "target_amount": target,
        "saved_amount": saved,
        "remaining": round(remaining, 2),
        "progress_percent": round(progress, 1),
        "months_left": months,
        "required_monthly": required_monthly,
        "status": status,
    }


def list_goals(db_path: str | Path | None = None) -> list[dict]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM goals ORDER BY target_date IS NULL, target_date, id"
        ).fetchall()
    return [_decorate(dict(row)) for row in rows]


def get_goal(goal_id: int, db_path: str | Path | None = None) -> dict | None:
    with get_connection(db_path) as connection:
        row = connection.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    return _decorate(dict(row)) if row else None


def create_goal(
    name: str,
    target_amount: float,
    saved_amount: float = 0.0,
    target_date: str | None = None,
    category: str = "general",
    db_path: str | Path | None = None,
) -> int:
    name = (name or "").strip()
    if not name:
        raise ValueError("Goal name is required.")
    if float(target_amount) <= 0:
        raise ValueError("Target amount must be greater than zero.")
    if float(saved_amount) < 0:
        raise ValueError("Saved amount cannot be negative.")
    if target_date:
        try:
            date.fromisoformat(target_date)
        except ValueError as exc:
            raise ValueError("Target date must be YYYY-MM-DD.") from exc
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO goals(name, target_amount, saved_amount, target_date, category)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                target_amount = excluded.target_amount,
                saved_amount = excluded.saved_amount,
                target_date = excluded.target_date,
                category = excluded.category,
                updated_at = CURRENT_TIMESTAMP
            """,
            (name, float(target_amount), float(saved_amount), target_date, category),
        )
        row = connection.execute(
            "SELECT id FROM goals WHERE name = ?", (name,)
        ).fetchone()
    return int(row["id"]) if row else int(cursor.lastrowid or 0)


def add_to_goal(goal_id: int, amount: float, db_path: str | Path | None = None) -> dict:
    if float(amount) <= 0:
        raise ValueError("Contribution must be greater than zero.")
    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE goals
            SET saved_amount = saved_amount + ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (float(amount), goal_id),
        )
        row = connection.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    if row is None:
        raise ValueError("Goal not found.")
    return _decorate(dict(row))


def delete_goal(goal_id: int, db_path: str | Path | None = None) -> bool:
    with get_connection(db_path) as connection:
        cursor = connection.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        if cursor.rowcount == 0:
            raise ValueError("Goal not found.")
    return True


def goal_summary(db_path: str | Path | None = None) -> dict:
    goals = list_goals(db_path)
    total_target = sum(goal["target_amount"] for goal in goals)
    total_saved = sum(goal["saved_amount"] for goal in goals)
    return {
        "count": len(goals),
        "total_target": round(total_target, 2),
        "total_saved": round(total_saved, 2),
        "progress_percent": round(total_saved / total_target * 100, 1) if total_target else 0.0,
        "behind": [goal["name"] for goal in goals if goal["status"] == "behind"],
        "goals": goals,
    }
