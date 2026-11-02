"""Stable UI bridge for the AI-agent module owned by the agent team."""

from __future__ import annotations

from typing import TypedDict


class AgentResponse(TypedDict):
    answer: str
    tools_used: list[str]
    sources: list[dict]


def ask_agent(message: str, session_id: str) -> AgentResponse:
    """Return a deterministic mock response until the real agent is connected.

    The teammate-owned implementation can replace this function without changing
    the chat page as long as the return contract remains the same.
    """
    if not message.strip():
        raise ValueError("Please enter a question.")

    lowered = message.lower()
    if "food" in lowered:
        return {
            "answer": (
                "You spent **Rs. 5,370** on food and dining this month. "
                "Your food budget is **Rs. 8,000**, so **Rs. 2,630 remains**."
            ),
            "tools_used": ["get_spending_summary", "get_budget_status"],
            "sources": [
                {
                    "title": "November food transactions",
                    "excerpt": "Four synthetic food transactions totalling Rs. 5,370.",
                }
            ],
        }
    if "budget" in lowered or "left" in lowered:
        return {
            "answer": (
                "Your monthly budget is **Rs. 46,000**. Based on recorded "
                "expenses, you still have room available this month. "
                "The Dashboard shows the exact live balance."
            ),
            "tools_used": ["get_budget_status"],
            "sources": [
                {
                    "title": "Monthly budget record",
                    "excerpt": "November 2026 monthly budget and category limits.",
                }
            ],
        }
    return {
        "answer": (
            "A practical saving step is to set a weekly dining cap and move the "
            "difference into savings at the end of each week. Your recent records "
            "show dining is the easiest category to adjust without affecting bills."
        ),
        "tools_used": ["search_financial_guidance"],
        "sources": [
            {
                "title": "50/30/20 budgeting guide",
                "excerpt": "Review flexible wants weekly and redirect unspent funds toward savings goals.",
            },
            {
                "title": "Synthetic transaction summary",
                "excerpt": "Dining is a recurring discretionary category in the demo dataset.",
            },
        ],
    }
