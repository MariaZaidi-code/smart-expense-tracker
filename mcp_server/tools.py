"""Business logic exposed by the MCP server.

The MCP server is the *only* surface the AI agent uses for expense tools by
default.  Keeping calculations here (rather than in the agent) makes tool
execution independently testable and keeps the agent grounded.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from expense.transactions import (
    add_transaction,
    delete_transaction,
    ensure_category,
    get_transaction,
    list_transactions,
    update_transaction,
)
from expense.budgets import create_budget as _create_budget
from expense.budgets import list_budgets as _list_budgets
from expense.analytics import (
    category_totals,
    month_comparison,
    remaining_budget,
    total_spending,
    unusual_spending,
)
from rag.retriever import retrieve


def _json(value) -> str:
    return json.dumps(value, default=str)


def search_financial_guidance(query: str, top_k: int = 5) -> dict:
    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        top_k = 5
    top_k = max(1, min(top_k, 20))
    try:
        results = retrieve(query, top_k=top_k)
    except Exception as exc:  # pragma: no cover - defensive
        return {"error": str(exc), "results": []}
    out = []
    for result in results:
        score = None
        if result.get("distance") is not None:
            score = round(1 - result["distance"], 4)
        out.append(
            {
                "source": result.get("source"),
                "text": result.get("text"),
                "score": score,
            }
        )
    return {"query": query, "count": len(out), "results": out}


def get_budgeting_rules() -> dict:
    return {
        "rules": [
            "50/30/20 rule: 50% needs, 30% wants, 20% savings/debt.",
            "Keep 3-6 months of essential expenses in an emergency fund.",
            "Track every expense and categorize consistently.",
            "Review the budget weekly and do a deeper review monthly.",
        ]
    }


def add_expense(date: str, amount: float, category: str, description: str = "") -> dict:
    try:
        ensure_category(category)
        transaction_id = add_transaction(
            description or "Expense",
            amount,
            category,
            date,
        )
        return {"ok": True, "transaction": get_transaction(transaction_id)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def list_expenses(month: str | None = None, category: str | None = None, limit: int = 50) -> dict:
    try:
        transactions = list_transactions(
            month=month,
            category=category,
            limit=max(1, int(limit)),
        )
        return {"ok": True, "count": len(transactions), "transactions": transactions}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def update_expense(
    transaction_id: int,
    date: str | None = None,
    amount: float | None = None,
    category: str | None = None,
    description: str | None = None,
) -> dict:
    try:
        transaction_id = int(transaction_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": "transaction_id must be an integer"}
    try:
        update_transaction(
            transaction_id,
            description=description,
            amount=amount,
            category=category,
            transaction_date=date,
        )
        return {"ok": True, "transaction": get_transaction(transaction_id)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def delete_expense(transaction_id: int) -> dict:
    try:
        transaction_id = int(transaction_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": "transaction_id must be an integer"}
    try:
        delete_transaction(transaction_id)
        return {"ok": True, "deleted": transaction_id}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def create_budget(month: str, category: str, amount: float) -> dict:
    try:
        budget = _create_budget(month, category, amount)
        return {"ok": True, "budget": budget}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def list_budgets(month: str | None = None) -> dict:
    try:
        budgets = _list_budgets(month=month)
        return {"ok": True, "count": len(budgets), "budgets": budgets}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_spending_summary(month: str) -> dict:
    try:
        total = total_spending(month=month)
        breakdown = category_totals(month)
        return {"ok": True, "month": month, "total": total, "by_category": breakdown}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_budget_status(month: str, category: str | None = None) -> dict:
    try:
        return {"ok": True, "status": remaining_budget(month, category=category)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def compare_months(month_a: str, month_b: str) -> dict:
    try:
        return {"ok": True, "comparison": month_comparison(month_a, month_b)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_unusual_spending(month: str) -> dict:
    try:
        return {"ok": True, "month": month, "flags": unusual_spending(month)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def remember_fact(key: str, value: str, category: str = "fact", importance: int = 3) -> dict:
    """Persist a long-term user fact through the MCP server."""
    try:
        from agent.memory import LongTermMemory

        memory = LongTermMemory()
        memory.remember(key, value, category=category, importance=importance)
        return {"ok": True, "remembered": {"key": key, "value": value}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def recall_facts(query: str = "", limit: int = 10) -> dict:
    try:
        from agent.memory import LongTermMemory

        memory = LongTermMemory()
        facts = memory.recall(query=query, limit=limit)
        return {"ok": True, "count": len(facts), "facts": facts}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def health_check() -> dict:
    return {
        "status": "ok",
        "service": "expense-tracker-mcp",
        "time": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Smart insight tools (researched from leading budgeting apps)
# ---------------------------------------------------------------------------
def get_safe_to_spend(month: str | None = None) -> dict:
    try:
        from expense.insights import safe_to_spend

        return {"ok": True, "snapshot": safe_to_spend(month)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def can_i_afford(amount: float, month: str | None = None) -> dict:
    try:
        from expense.insights import can_i_afford as _can_i_afford

        return {"ok": True, "verdict": _can_i_afford(amount, month)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_month_forecast(month: str | None = None) -> dict:
    try:
        from expense.insights import month_forecast

        return {"ok": True, "forecast": month_forecast(month)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def list_subscriptions() -> dict:
    try:
        from expense.insights import subscription_summary

        return {"ok": True, "summary": subscription_summary()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_financial_health(month: str | None = None) -> dict:
    try:
        from expense.insights import financial_health

        return {"ok": True, "health": financial_health(month)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_monthly_recap(month: str | None = None) -> dict:
    try:
        from expense.insights import monthly_recap

        return {"ok": True, "recap": monthly_recap(month)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def list_goals() -> dict:
    try:
        from expense.goals import goal_summary

        return {"ok": True, "summary": goal_summary()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def add_to_goal(goal: str, amount: float) -> dict:
    try:
        from expense.goals import add_to_goal as _add_to_goal
        from expense.goals import list_goals as _list_goals

        goals = _list_goals()
        match = next(
            (
                item
                for item in goals
                if str(item["id"]) == str(goal)
                or item["name"].lower() == str(goal).strip().lower()
            ),
            None,
        )
        if match is None:
            return {"ok": False, "error": f"Goal not found: {goal}"}
        return {"ok": True, "goal": _add_to_goal(match["id"], amount)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def create_savings_goal(
    name: str,
    target_amount: float,
    saved_amount: float = 0.0,
    target_date: str | None = None,
    category: str = "general",
) -> dict:
    try:
        from expense.goals import create_goal as _create_goal
        from expense.goals import get_goal as _get_goal

        goal_id = _create_goal(name, target_amount, saved_amount, target_date, category)
        return {"ok": True, "goal": _get_goal(goal_id)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def suggest_transaction_category(description: str) -> dict:
    try:
        from expense.rules import suggest_category

        return {"ok": True, "suggestion": suggest_category(description)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_debt_payoff_plan(
    debts: list[dict],
    extra_payment: float = 0.0,
    strategy: str = "avalanche",
) -> dict:
    try:
        from expense.insights import debt_payoff

        return {"ok": True, "plan": debt_payoff(debts, extra_payment, strategy)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
