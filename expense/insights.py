"""Smart insight algorithms researched from leading budgeting apps.

Every function is pure data-in/data-out so it can be unit tested, called by the
MCP server, and reused by the Streamlit UI.

Feature provenance
------------------
* ``safe_to_spend``      -- PocketGuard / Safe Spend "one number you can trust"
* ``month_forecast``     -- PocketSmith / Simplifi / Paper cash-flow forecast
* ``detect_recurring``   -- Rocket Money / Copilot "Spot subscriptions"
* ``financial_health``   -- Fiscify / Origin explainable health score
* ``monthly_recap``      -- Monarch weekly/monthly recap
* ``debt_payoff``        -- Monarch / YNAB loan payoff simulator
"""

from __future__ import annotations

import calendar
import statistics
from datetime import date, datetime, timedelta
from pathlib import Path

from database.connection import get_connection
from expense.budgets import list_budgets
from expense.goals import goal_summary
from expense.rules import normalize_merchant

DAY_SECONDS = 86400


# ---------------------------------------------------------------------------
# Small date helpers
# ---------------------------------------------------------------------------
def _parse_month(month: str | None, today: date | None = None) -> tuple[date, str]:
    today = today or date.today()
    month = month or today.strftime("%Y-%m")
    try:
        start = datetime.strptime(month, "%Y-%m").date().replace(day=1)
    except ValueError as exc:
        raise ValueError("Month must use YYYY-MM format.") from exc
    return start, month


def _days_in_month(month_start: date) -> int:
    return calendar.monthrange(month_start.year, month_start.month)[1]


def _month_end(month_start: date) -> date:
    return month_start.replace(day=_days_in_month(month_start))


def _previous_month(month_start: date) -> date:
    return (month_start - timedelta(days=1)).replace(day=1)


def _recent_months(month_start: date, count: int) -> list[date]:
    months = []
    cursor = month_start
    for _ in range(count):
        months.append(cursor)
        cursor = _previous_month(cursor)
    return months


def _transactions_between(start: date, end: date, db_path=None) -> list[dict]:
    with get_connection(db_path) as connection:
        return [
            dict(row)
            for row in connection.execute(
                """
                SELECT t.id, t.description, t.amount, c.name AS category,
                       t.transaction_date
                FROM transactions t
                JOIN categories c ON c.id = t.category_id
                WHERE t.transaction_date >= ? AND t.transaction_date <= ?
                ORDER BY t.transaction_date
                """,
                (start.isoformat(), end.isoformat()),
            )
        ]


def _spent_in_month(month_start: date, db_path=None) -> float:
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE substr(transaction_date, 1, 7) = ?",
            (month_start.strftime("%Y-%m"),),
        ).fetchone()
    return round(float(row[0]), 2)


def _budget_for_month(month: str, db_path=None) -> tuple[float, list[dict]]:
    budgets = list_budgets(month, db_path)
    overall = next((b for b in budgets if b["category"] is None), None)
    category_budgets = [b for b in budgets if b["category"]]
    if overall:
        return float(overall["amount"]), category_budgets
    return round(sum(float(b["amount"]) for b in category_budgets), 2), category_budgets


# ---------------------------------------------------------------------------
# Recurring charges / subscriptions
# ---------------------------------------------------------------------------
def _cadence_for_gap(gap: float) -> tuple[str, float, int] | None:
    """Return (label, expected_gap_days, minimum_occurrences)."""
    if 5 <= gap <= 9:
        return "weekly", 7.0, 4
    if 12 <= gap <= 16:
        return "biweekly", 14.0, 3
    if 25 <= gap <= 35:
        return "monthly", 30.44, 3
    if 80 <= gap <= 100:
        return "quarterly", 91.0, 2
    if 340 <= gap <= 390:
        return "yearly", 365.0, 2
    return None


def _monthly_factor(cadence: str, gap: float) -> float:
    return {
        "weekly": 52 / 12,
        "biweekly": 26 / 12,
        "monthly": 1.0,
        "quarterly": 1 / 3,
        "yearly": 1 / 12,
    }.get(cadence, 30.44 / max(gap, 1))


def detect_recurring(
    months: int = 14,
    db_path: str | Path | None = None,
    today: date | None = None,
    min_confidence: float = 60.0,
) -> list[dict]:
    """Detect subscriptions and recurring bills from transaction history.

    Detection is based on timing consistency and amount stability, not on the
    merchant name, so inconsistent statements (``NETFLIX`` vs
    ``Netflix.com``) still group correctly.
    """
    today = today or date.today()
    month_start, _ = _parse_month(None, today)
    start = _previous_month(month_start)
    for _ in range(max(months, 2) - 1):
        start = _previous_month(start)
    rows = _transactions_between(start, today, db_path)

    groups: dict[str, list[dict]] = {}
    for row in rows:
        merchant = normalize_merchant(row["description"])
        if not merchant or float(row["amount"]) <= 0:
            continue
        groups.setdefault(merchant, []).append(row)

    detected: list[dict] = []
    for merchant, items in groups.items():
        if len(items) < 2:
            continue
        items.sort(key=lambda item: item["transaction_date"])
        dates = [date.fromisoformat(item["transaction_date"]) for item in items]
        gaps = [(b - a).days for a, b in zip(dates, dates[1:]) if (b - a).days > 0]
        if not gaps:
            continue
        median_gap = statistics.median(gaps)
        cadence = _cadence_for_gap(median_gap)
        if cadence is None:
            continue
        label, expected_gap, minimum = cadence
        if len(items) < minimum:
            continue

        gap_spread = statistics.pstdev(gaps) if len(gaps) > 1 else 0.0
        timing_consistency = max(0.0, 1 - min(gap_spread / max(expected_gap, 1), 1.0))
        amounts = [float(item["amount"]) for item in items]
        mean_amount = statistics.fmean(amounts)
        amount_spread = statistics.pstdev(amounts) if len(amounts) > 1 else 0.0
        amount_stability = max(0.0, 1 - min(amount_spread / max(mean_amount, 1), 1.0))
        confidence = round(
            100 * (0.45 + 0.35 * timing_consistency + 0.20 * amount_stability), 1
        )
        confidence = min(confidence, 99.0)
        if confidence < min_confidence:
            continue

        last_date = dates[-1]
        last_amount = amounts[-1]
        next_due = last_date + timedelta(days=round(expected_gap))
        while next_due < today:
            next_due += timedelta(days=round(expected_gap))
        # A charge that stopped arriving well past its cadence is likely canceled.
        stale_after = max(expected_gap * 1.6, expected_gap + 10)
        stale = (today - last_date).days > stale_after

        price_change = (
            round((last_amount - mean_amount) / mean_amount * 100, 1)
            if mean_amount
            else 0.0
        )
        monthly_cost = round(last_amount * _monthly_factor(label, expected_gap), 2)
        display = max((item["description"] for item in items), key=len)

        detected.append(
            {
                "merchant": merchant,
                "description": display,
                "category": items[-1]["category"],
                "cadence": label,
                "average_amount": round(mean_amount, 2),
                "last_amount": round(last_amount, 2),
                "monthly_cost": monthly_cost,
                "occurrences": len(items),
                "last_charged": last_date.isoformat(),
                "next_due": next_due.isoformat(),
                "confidence": confidence,
                "price_change_percent": price_change,
                "price_hike": price_change >= 8,
                "stale": stale,
                "status": "canceled?" if stale else "active",
                "kind": "subscription" if amount_stability >= 0.9 and label != "weekly" else "recurring bill",
            }
        )

    detected.sort(key=lambda item: item["monthly_cost"], reverse=True)
    return detected


def subscription_summary(db_path=None, today: date | None = None) -> dict:
    recurring = detect_recurring(db_path=db_path, today=today)
    active = [item for item in recurring if not item["stale"]]
    monthly = round(sum(item["monthly_cost"] for item in active), 2)
    return {
        "count": len(active),
        "monthly_total": monthly,
        "annual_total": round(monthly * 12, 2),
        "subscriptions": [item for item in active if item["kind"] == "subscription"],
        "bills": [item for item in active if item["kind"] != "subscription"],
        "price_hikes": [item for item in active if item["price_hike"]],
        "canceled": [item for item in recurring if item["stale"]],
        "items": recurring,
    }


# ---------------------------------------------------------------------------
# Safe to spend
# ---------------------------------------------------------------------------
def _upcoming_commitments(
    month_start: date,
    db_path=None,
    today: date | None = None,
) -> float:
    """Recurring charges still expected between today and month end."""
    today = today or date.today()
    if month_start.year != today.year or month_start.month != today.month:
        return 0.0
    end = _month_end(month_start)
    total = 0.0
    for item in detect_recurring(db_path=db_path, today=today):
        if item["stale"]:
            continue
        due = date.fromisoformat(item["next_due"])
        if today <= due <= end:
            total += float(item["last_amount"])
    return round(total, 2)


def safe_to_spend(
    month: str | None = None,
    db_path=None,
    today: date | None = None,
) -> dict:
    """One trustworthy number: what can still be spent, and per day.

    Reserves money for recurring bills that have not posted yet, so the number
    does not overstate what is actually available.
    """
    today = today or date.today()
    month_start, month_key = _parse_month(month, today)
    budget, _ = _budget_for_month(month_key, db_path)
    spent = _spent_in_month(month_start, db_path)
    remaining = round(budget - spent, 2)
    committed = _upcoming_commitments(month_start, db_path, today)
    flexible = round(max(remaining - committed, 0.0), 2)
    days_in_month = _days_in_month(month_start)
    is_current = (month_start.year, month_start.month) == (today.year, today.month)
    days_left = days_in_month - today.day + 1 if is_current else days_in_month
    per_day = round(flexible / days_left, 2) if days_left else flexible

    if budget <= 0:
        status, label = "no_budget", "No budget set"
    elif flexible <= 0:
        status, label = "critical", "Reserved for bills"
    elif per_day < 300:
        status, label = "critical", "Very tight"
    elif per_day < 1000:
        status, label = "tight", "Spend carefully"
    else:
        status, label = "comfortable", "Comfortable"

    return {
        "month": month_key,
        "budget": budget,
        "spent": spent,
        "remaining": remaining,
        "upcoming_commitments": committed,
        "safe_to_spend": flexible,
        "days_left": days_left,
        "per_day": per_day,
        "status": status,
        "label": label,
    }


def can_i_afford(amount: float, month: str | None = None, db_path=None) -> dict:
    """Answer the Safe Spend style question: "can I afford this?"."""
    amount = float(amount)
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    snapshot = safe_to_spend(month=month, db_path=db_path)
    after = round(snapshot["safe_to_spend"] - amount, 2)
    affordable = after >= 0
    if affordable:
        message = (
            f"Yes — {_money(amount)} still leaves {_money(after)} of flexible money "
            f"this month ({_money(snapshot['per_day'])}/day)."
        )
    else:
        message = (
            f"Not comfortably. That purchase is {_money(abs(after))} beyond your "
            f"flexible money after reserving {_money(snapshot['upcoming_commitments'])} "
            "for upcoming bills."
        )
    return {
        "amount": round(amount, 2),
        "affordable": affordable,
        "safe_to_spend": snapshot["safe_to_spend"],
        "remaining_after": after,
        "per_day": snapshot["per_day"],
        "message": message,
        "snapshot": snapshot,
    }


def _money(value: float) -> str:
    return f"Rs. {float(value):,.0f}"


# ---------------------------------------------------------------------------
# Month-end forecast
# ---------------------------------------------------------------------------
def month_forecast(
    month: str | None = None,
    db_path=None,
    today: date | None = None,
) -> dict:
    today = today or date.today()
    month_start, month_key = _parse_month(month, today)
    days_in_month = _days_in_month(month_start)
    is_current = (month_start.year, month_start.month) == (today.year, today.month)
    days_elapsed = today.day if is_current else days_in_month
    days_left = max(days_in_month - days_elapsed, 0)

    budget, _ = _budget_for_month(month_key, db_path)
    spent = _spent_in_month(month_start, db_path)

    recurring = detect_recurring(db_path=db_path, today=today)
    recurring_names = {item["merchant"] for item in recurring}
    month_rows = _transactions_between(month_start, _month_end(month_start), db_path)
    recurring_actual = round(
        sum(
            float(row["amount"])
            for row in month_rows
            if normalize_merchant(row["description"]) in recurring_names
        ),
        2,
    )
    discretionary = max(spent - recurring_actual, 0.0)
    daily_run_rate = round(discretionary / days_elapsed, 2) if days_elapsed else 0.0
    committed = _upcoming_commitments(month_start, db_path, today)
    projected = round(recurring_actual + committed + daily_run_rate * days_left, 2)
    projected = max(projected, spent)
    projected_over = round(projected - budget, 2) if budget else 0.0

    if not budget:
        risk, label = "unknown", "No budget to compare"
    elif projected > budget * 1.05:
        risk, label = "over", "Trending over budget"
    elif projected > budget * 0.95:
        risk, label = "watch", "Close to the limit"
    else:
        risk, label = "on_track", "On track"

    return {
        "month": month_key,
        "budget": budget,
        "spent": spent,
        "projected_total": projected,
        "projected_over": projected_over,
        "daily_run_rate": daily_run_rate,
        "recurring_actual": recurring_actual,
        "upcoming_commitments": committed,
        "days_elapsed": days_elapsed,
        "days_left": days_left,
        "risk": risk,
        "label": label,
    }


# ---------------------------------------------------------------------------
# Explainable financial health score
# ---------------------------------------------------------------------------
def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def financial_health(
    month: str | None = None,
    db_path=None,
    today: date | None = None,
) -> dict:
    today = today or date.today()
    month_start, month_key = _parse_month(month, today)
    days_in_month = _days_in_month(month_start)
    day_fraction = min(today.day / days_in_month, 1.0)
    budget, category_budgets = _budget_for_month(month_key, db_path)
    spent = _spent_in_month(month_start, db_path)
    subscriptions = subscription_summary(db_path=db_path, today=today)

    components: list[dict] = []

    # 1. Budget pace -------------------------------------------------------
    if budget <= 0:
        pace_score, pace_detail = 40.0, "No monthly budget set, so pace cannot be judged."
    else:
        # Fixed recurring bills land early in the month; judge the pace of the
        # money the user actually controls.
        fixed = min(subscriptions["monthly_total"], spent)
        discretionary = max(spent - fixed, 0.0)
        flexible_budget = max(budget - fixed, budget * 0.1)
        expected = flexible_budget * max(day_fraction, 0.05)
        pace_ratio = discretionary / max(expected, 1.0)
        pace_score = 100.0 if pace_ratio <= 1 else _clamp(100 - (pace_ratio - 1) * 45)
        pace_detail = (
            f"Discretionary spending is at {pace_ratio * 100:.0f}% of the expected pace "
            f"({day_fraction * 100:.0f}% of the month gone)."
        )
    components.append(
        {
            "key": "budget_pace",
            "label": "Budget pace",
            "score": round(pace_score, 1),
            "weight": 35,
            "detail": pace_detail,
            "advice": "Slow discretionary spending for the rest of the month."
            if pace_score < 70
            else "Keep the current pace.",
        }
    )

    # 2. Category control --------------------------------------------------
    if category_budgets:
        good = sum(1 for b in category_budgets if b["spent"] <= b["amount"])
        over = [
            b["category"] for b in category_budgets if b["spent"] > b["amount"]
        ]
        category_score = 100 * good / len(category_budgets)
        category_detail = (
            f"{good}/{len(category_budgets)} category budgets are within their limit."
            + (f" Over: {', '.join(over)}." if over else "")
        )
        category_advice = (
            f"Rebalance spending away from {', '.join(over)}." if over else "No category is over budget."
        )
    else:
        category_score, category_detail = 70.0, "No category budgets configured."
        category_advice = "Add category budgets to get sharper guidance."
    components.append(
        {
            "key": "category_control",
            "label": "Category control",
            "score": round(category_score, 1),
            "weight": 20,
            "detail": category_detail,
            "advice": category_advice,
        }
    )

    # 3. Recurring load ----------------------------------------------------
    monthly_recurring = subscriptions["monthly_total"]
    if budget > 0:
        load_ratio = monthly_recurring / budget
        load_score = 100 if load_ratio <= 0.08 else _clamp(100 - (load_ratio - 0.08) / 0.27 * 100)
        load_detail = (
            f"{_money(monthly_recurring)}/month in recurring charges "
            f"({load_ratio * 100:.0f}% of the budget)."
        )
    else:
        load_score, load_detail = 60.0, f"{_money(monthly_recurring)}/month in recurring charges."
    components.append(
        {
            "key": "recurring_load",
            "label": "Recurring load",
            "score": round(load_score, 1),
            "weight": 15,
            "detail": load_detail,
            "advice": "Review the subscription list and cancel anything unused."
            if load_score < 70
            else "Recurring costs are well controlled.",
        }
    )

    # 4. Spending stability ------------------------------------------------
    previous = [
        _spent_in_month(month_start_, db_path)
        for month_start_ in _recent_months(month_start, 4)[1:]
    ]
    previous = [value for value in previous if value > 0]
    if previous:
        average = statistics.fmean(previous)
        deviation = (spent - average) / average
        stability_score = 100.0 if deviation <= 0 else _clamp(100 - deviation * 150)
        stability_detail = (
            f"This month is {abs(deviation) * 100:.0f}% "
            f"{'below' if deviation <= 0 else 'above'} your 3-month average."
        )
    else:
        stability_score, stability_detail = 75.0, "Not enough history to compare months yet."
    components.append(
        {
            "key": "stability",
            "label": "Spending stability",
            "score": round(stability_score, 1),
            "weight": 15,
            "detail": stability_detail,
            "advice": "Spending is above your usual pattern; check the top categories."
            if stability_score < 70
            else "Spending is consistent with your history.",
        }
    )

    # 5. Goals -------------------------------------------------------------
    goals = goal_summary(db_path)
    if not goals["count"]:
        goal_score, goal_detail = 65.0, "No savings goals yet."
        goal_advice = "Create a goal (emergency fund is a good first one)."
    elif any(goal["status"] == "behind" for goal in goals["goals"]):
        goal_score = 40.0
        goal_detail = "At least one goal is behind schedule."
        goal_advice = "Top up the goal that is behind, or move its target date."
    elif all(goal["status"] in {"achieved", "on_track"} for goal in goals["goals"]):
        goal_score = 100.0
        goal_detail = f"{goals['count']} goal(s) on track, {goals['progress_percent']}% funded."
        goal_advice = "Goals are on track."
    else:
        goal_score = 80.0
        goal_detail = f"{goals['count']} goal(s) in progress."
        goal_advice = "Keep contributing to your goals."
    components.append(
        {
            "key": "goals",
            "label": "Goal progress",
            "score": round(goal_score, 1),
            "weight": 15,
            "detail": goal_detail,
            "advice": goal_advice,
        }
    )

    total_weight = sum(component["weight"] for component in components)
    score = round(
        sum(component["score"] * component["weight"] for component in components) / total_weight
    )
    grade = (
        "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "E"
    )
    weakest = min(components, key=lambda component: component["score"] / component["weight"])

    return {
        "month": month_key,
        "score": score,
        "grade": grade,
        "components": components,
        "next_step": weakest["advice"],
        "focus_area": weakest["label"],
        "subscriptions_monthly": monthly_recurring,
    }


# ---------------------------------------------------------------------------
# Monthly recap
# ---------------------------------------------------------------------------
def monthly_recap(
    month: str | None = None,
    db_path=None,
    today: date | None = None,
) -> dict:
    today = today or date.today()
    month_start, month_key = _parse_month(month, today)
    previous_start = _previous_month(month_start)
    spent = _spent_in_month(month_start, db_path)
    previous = _spent_in_month(previous_start, db_path)
    change = round((spent - previous) / previous * 100, 1) if previous else 0.0

    rows = _transactions_between(month_start, _month_end(month_start), db_path)
    by_category: dict[str, float] = {}
    for row in rows:
        by_category[row["category"]] = by_category.get(row["category"], 0.0) + float(row["amount"])
    top = sorted(by_category.items(), key=lambda pair: pair[1], reverse=True)[:3]
    biggest = max(rows, key=lambda row: float(row["amount"])) if rows else None
    subscriptions = subscription_summary(db_path=db_path, today=today)
    forecast = month_forecast(month_key, db_path, today)
    goals = goal_summary(db_path)

    direction = "less" if change <= 0 else "more"
    headline = (
        f"You spent {_money(spent)} in {month_key}, "
        f"{abs(change):.0f}% {direction} than the previous month."
        if previous
        else f"You spent {_money(spent)} in {month_key}."
    )
    bullets = []
    if top:
        bullets.append(
            "Top categories: "
            + ", ".join(f"{name} ({_money(amount)})" for name, amount in top)
            + "."
        )
    if biggest:
        bullets.append(
            f"Largest single expense: {biggest['description']} ({_money(float(biggest['amount']))})."
        )
    bullets.append(
        f"Recurring charges: {subscriptions['count']} active, "
        f"{_money(subscriptions['monthly_total'])}/month."
    )
    if forecast["budget"]:
        bullets.append(
            f"Projected month-end spend is {_money(forecast['projected_total'])} "
            f"against a {_money(forecast['budget'])} budget ({forecast['label'].lower()})."
        )
    if goals["count"]:
        bullets.append(
            f"Goals: {goals['progress_percent']}% funded overall."
            + (f" Behind: {', '.join(goals['behind'])}." if goals["behind"] else "")
        )

    return {
        "month": month_key,
        "headline": headline,
        "bullets": bullets,
        "total_spent": spent,
        "previous_total": previous,
        "change_percent": change,
        "top_categories": [{"category": name, "amount": round(amount, 2)} for name, amount in top],
        "biggest_expense": biggest,
        "subscriptions_monthly": subscriptions["monthly_total"],
        "forecast": forecast,
    }


# ---------------------------------------------------------------------------
# Calendar grid (spending heatmap)
# ---------------------------------------------------------------------------
def spending_calendar(
    month: str | None = None,
    db_path=None,
    today: date | None = None,
) -> list[dict]:
    today = today or date.today()
    month_start, month_key = _parse_month(month, today)
    days = _days_in_month(month_start)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT transaction_date AS date, SUM(amount) AS amount
            FROM transactions
            WHERE substr(transaction_date, 1, 7) = ?
            GROUP BY transaction_date
            """,
            (month_key,),
        ).fetchall()
    totals = {row["date"]: float(row["amount"]) for row in rows}
    # Monday-first weekday index for a tidy grid.
    offset = month_start.weekday()
    grid = []
    for day in range(1, days + 1):
        current = month_start.replace(day=day)
        index = offset + day - 1
        grid.append(
            {
                "date": current.isoformat(),
                "day": day,
                "week": index // 7,
                "weekday": index % 7,
                "amount": round(totals.get(current.isoformat(), 0.0), 2),
            }
        )
    return grid


# ---------------------------------------------------------------------------
# Debt payoff planner (snowball vs avalanche)
# ---------------------------------------------------------------------------
def _simulate_payoff(
    debts: list[dict],
    extra_payment: float,
    strategy: str,
    max_months: int = 600,
) -> dict:
    balances = [
        {
            "name": debt.get("name") or f"Debt {index + 1}",
            "balance": float(debt.get("balance", 0)),
            "apr": float(debt.get("apr", 0)),
            "min_payment": float(debt.get("min_payment", 0)),
        }
        for index, debt in enumerate(debts)
        if float(debt.get("balance", 0)) > 0
    ]
    if not balances:
        raise ValueError("At least one debt with a positive balance is required.")
    if any(debt["min_payment"] <= 0 for debt in balances):
        raise ValueError("Every debt needs a positive minimum payment.")
    extra_payment = max(float(extra_payment), 0.0)

    total_interest = 0.0
    months = 0
    payoff_month: dict[str, int] = {}
    while any(debt["balance"] > 0.005 for debt in balances) and months < max_months:
        months += 1
        for debt in balances:
            if debt["balance"] <= 0:
                continue
            interest = debt["balance"] * debt["apr"] / 100 / 12
            debt["balance"] += interest
            total_interest += interest

        if strategy == "snowball":
            order = sorted([d for d in balances if d["balance"] > 0], key=lambda d: d["balance"])
        else:
            order = sorted([d for d in balances if d["balance"] > 0], key=lambda d: d["apr"], reverse=True)

        for debt in balances:
            if debt["balance"] <= 0:
                continue
            payment = min(debt["min_payment"], debt["balance"])
            debt["balance"] -= payment

        remaining_extra = extra_payment
        for debt in order:
            if remaining_extra <= 0:
                break
            if debt["balance"] <= 0:
                continue
            payment = min(remaining_extra, debt["balance"])
            debt["balance"] -= payment
            remaining_extra -= payment

        for debt in balances:
            if debt["balance"] <= 0.005 and debt["name"] not in payoff_month:
                payoff_month[debt["name"]] = months

        if months >= max_months:
            break

    return {
        "strategy": strategy,
        "months": months,
        "years": round(months / 12, 1),
        "total_interest": round(total_interest, 2),
        "feasible": months < max_months,
        "payoff_order": list(payoff_month.keys()),
        "payoff_months": payoff_month,
    }


def debt_payoff(
    debts: list[dict],
    extra_payment: float = 0.0,
    strategy: str = "avalanche",
) -> dict:
    """Compare snowball and avalanche payoff plans.

    ``debts`` items: ``{"name", "balance", "apr", "min_payment"}``.
    """
    if not debts:
        raise ValueError("Provide at least one debt.")
    snowball = _simulate_payoff(debts, extra_payment, "snowball")
    avalanche = _simulate_payoff(debts, extra_payment, "avalanche")
    recommended = "avalanche" if avalanche["total_interest"] <= snowball["total_interest"] else "snowball"
    chosen = avalanche if recommended == "avalanche" else snowball
    savings = abs(round(snowball["total_interest"] - avalanche["total_interest"], 2))
    return {
        "snowball": snowball,
        "avalanche": avalanche,
        "recommended": recommended,
        "interest_saved": savings,
        "summary": (
            f"{recommended.title()} clears the debt in {chosen['months']} months "
            f"with {_money(chosen['total_interest'])} interest"
            + (f", saving {_money(savings)} versus the other method." if savings else ".")
        ),
    }
