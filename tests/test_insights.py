"""Tests for the researched standout features: insights, goals, and merchant learning."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

import pytest

from agent.agent import ExpenseAgent
from agent.llm import GrokLLM
from agent.memory import new_session_id
from database.connection import get_connection, initialize_database
from expense.budgets import set_budget
from expense.goals import (
    add_to_goal,
    create_goal,
    delete_goal,
    goal_summary,
    list_goals,
)
from expense.insights import (
    can_i_afford,
    debt_payoff,
    detect_recurring,
    financial_health,
    month_forecast,
    monthly_recap,
    safe_to_spend,
    spending_calendar,
    subscription_summary,
)
from expense.rules import list_rules, normalize_merchant, suggest_category
from expense.transactions import add_transaction

TODAY = date.today()


class NoLLM(GrokLLM):
    """Deterministic stub that forces the grounded rule engine."""

    def __init__(self):
        self.api_key = ""

    @property
    def available(self) -> bool:
        return False

    def status(self) -> dict:
        return {
            "available": False,
            "provider": "Local fallback",
            "model": "rules",
            "base_url": "",
            "key_source": "test",
            "last_error": None,
        }


def _month_start(offset: int) -> date:
    index = TODAY.year * 12 + (TODAY.month - 1) - offset
    return date(index // 12, index % 12 + 1, 1)


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "insights-test.db"
    initialize_database(path)
    with get_connection(path) as connection:
        connection.executemany(
            "INSERT INTO categories(name) VALUES (?)",
            [
                ("Food & dining",),
                ("Bills & utilities",),
                ("Entertainment",),
                ("Transport",),
            ],
        )

    month = TODAY.strftime("%Y-%m")
    set_budget(month, 30000, db_path=path)
    set_budget(month, 10000, "Food & dining", db_path=path)
    set_budget(month, 5000, "Entertainment", db_path=path)
    set_budget(month, 5000, "Bills & utilities", db_path=path)

    # Four months of recurring charges make detection deterministic.
    for offset in range(4):
        netflix_date = _month_start(offset).replace(day=3)
        if netflix_date <= TODAY:
            add_transaction(
                "Netflix subscription",
                1000,
                "Entertainment",
                netflix_date.isoformat(),
                db_path=path,
            )
        ptcl_date = _month_start(offset).replace(day=1)
        add_transaction(
            "PTCL Internet",
            3000,
            "Bills & utilities",
            ptcl_date.isoformat(),
            db_path=path,
        )

    add_transaction(
        "Lahore Kitchen", 1500, "Food & dining", _month_start(0).isoformat(), db_path=path
    )
    add_transaction(
        "Chai Corner", 400, "Food & dining", _month_start(0).isoformat(), db_path=path
    )
    add_transaction(
        "Metro Card", 500, "Transport", _month_start(0).isoformat(), db_path=path
    )

    create_goal(
        "Emergency fund",
        120000,
        30000,
        (TODAY + timedelta(days=180)).isoformat(),
        "safety",
        db_path=path,
    )
    return path


def test_recurring_detection_and_subscription_summary(db):
    recurring = detect_recurring(db_path=db)
    names = {item["merchant"] for item in recurring}
    assert "netflix subscription" in names
    assert "ptcl internet" in names

    netflix = next(item for item in recurring if item["merchant"] == "netflix subscription")
    assert netflix["cadence"] == "monthly"
    assert netflix["confidence"] >= 60
    assert netflix["monthly_cost"] == 1000.0

    summary = subscription_summary(db_path=db)
    assert summary["count"] >= 2
    assert summary["monthly_total"] >= 4000
    assert summary["annual_total"] == round(summary["monthly_total"] * 12, 2)


def test_safe_to_spend_and_affordability(db):
    snapshot = safe_to_spend(db_path=db)
    assert snapshot["budget"] == 30000
    assert snapshot["spent"] > 0
    assert snapshot["safe_to_spend"] <= snapshot["remaining"]
    assert snapshot["safe_to_spend"] >= 0
    assert snapshot["days_left"] > 0

    cheap = can_i_afford(100, db_path=db)
    assert cheap["affordable"] is True
    assert cheap["remaining_after"] == cheap["safe_to_spend"] - 100

    expensive = can_i_afford(snapshot["safe_to_spend"] + 5000, db_path=db)
    assert expensive["affordable"] is False
    assert "beyond" in expensive["message"].lower()


def test_month_forecast(db):
    forecast = month_forecast(db_path=db)
    assert forecast["budget"] == 30000
    assert forecast["projected_total"] >= forecast["spent"]
    assert forecast["risk"] in {"over", "watch", "on_track", "unknown"}
    assert forecast["days_left"] >= 0


def test_financial_health_is_explainable(db):
    health = financial_health(db_path=db)
    assert 0 <= health["score"] <= 100
    assert health["grade"] in {"A", "B", "C", "D", "E"}
    assert len(health["components"]) == 5
    assert sum(component["weight"] for component in health["components"]) == 100
    assert all(component["detail"] for component in health["components"])
    assert health["next_step"]
    assert health["focus_area"]


def test_monthly_recap_and_heatmap(db):
    recap = monthly_recap(db_path=db)
    assert "Rs." in recap["headline"]
    assert recap["total_spent"] > 0
    assert recap["bullets"]

    grid = spending_calendar(db_path=db)
    days = calendar.monthrange(TODAY.year, TODAY.month)[1]
    assert len(grid) == days
    assert round(sum(cell["amount"] for cell in grid), 2) == recap["total_spent"]


def test_goal_crud_and_progress(db):
    created = create_goal(
        "New laptop",
        100000,
        10000,
        (TODAY + timedelta(days=150)).isoformat(),
        "purchase",
        db_path=db,
    )
    assert created
    goals = {goal["name"]: goal for goal in list_goals(db_path=db)}
    assert goals["New laptop"]["progress_percent"] == 10.0
    assert goals["New laptop"]["required_monthly"] is not None

    updated = add_to_goal(created, 5000, db_path=db)
    assert updated["saved_amount"] == 15000

    summary = goal_summary(db_path=db)
    assert summary["count"] == 2
    assert summary["total_saved"] == 45000
    assert 0 < summary["progress_percent"] < 100

    delete_goal(created, db_path=db)
    assert len(list_goals(db_path=db)) == 1


def test_merchant_learning_and_suggestion(db):
    assert normalize_merchant("NETFLIX.COM  ref 9912") == "netflix com"
    suggestion = suggest_category("CHAI CORNER", db_path=db)
    assert suggestion["category"] == "Food & dining"
    assert "learned" in suggestion["source"]
    assert suggestion["confidence"] >= 0.5

    unknown = suggest_category("Totally Unknown Vendor", db_path=db)
    assert unknown["category"] is None

    rules = {rule["merchant"]: rule["category"] for rule in list_rules(db_path=db)}
    assert rules["chai corner"] == "Food & dining"


def test_debt_payoff_compares_strategies():
    debts = [
        {"name": "Card", "balance": 120000, "apr": 24, "min_payment": 6000},
        {"name": "Loan", "balance": 300000, "apr": 12, "min_payment": 12000},
    ]
    plan = debt_payoff(debts, extra_payment=5000)
    assert plan["recommended"] in {"avalanche", "snowball"}
    assert plan["avalanche"]["total_interest"] <= plan["snowball"]["total_interest"]
    assert plan["avalanche"]["months"] > 0
    assert "Rs." in plan["summary"]


def make_agent(db):
    return ExpenseAgent(
        user_id="insight-user",
        session_id=new_session_id(),
        use_mcp=False,
        llm=NoLLM(),
        db_path=db,
    )


@pytest.mark.parametrize(
    "question,tool",
    [
        ("How much can I spend safely?", "get_safe_to_spend"),
        ("Can I afford Rs. 2,500?", "can_i_afford"),
        ("What is my month-end forecast?", "get_month_forecast"),
        ("Show my subscriptions", "list_subscriptions"),
        ("What is my financial health?", "get_financial_health"),
        ("How are my goals?", "list_goals"),
        ("Give me a recap for this month", "get_monthly_recap"),
        ("Which category should Chai Corner go in?", "suggest_transaction_category"),
    ],
)
def test_agent_insight_intents(db, question, tool):
    agent = make_agent(db)
    response = agent.ask(question)
    assert tool in response["tools_used"], response["answer"]
    assert response["transport"] == "local"
    assert "Rs." in response["answer"] or tool == "suggest_transaction_category"


def test_agent_afford_verdict_is_grounded(db):
    agent = make_agent(db)
    response = agent.ask("Can I afford Rs. 2,500?")
    assert "safe to spend" in response["answer"].lower()
    assert "daily allowance" in response["answer"].lower()
