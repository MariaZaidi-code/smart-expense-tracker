import sys
from pathlib import Path

# ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import functools
import os

import anyio
from mcp.server.fastmcp import FastMCP

from mcp_server import tools

mcp = FastMCP("expense-tracker-mcp")


def _warmup_embeddings() -> None:
    """Preload native embedding libraries on the main thread.

    FastMCP runs synchronous tools in a worker thread.  On Windows, importing
    NumPy/SciPy/scikit-learn for the *first* time from that worker deadlocks the
    process while the import lock is held.  Importing them here, before the
    event loop starts, makes later RAG calls cheap and reliable.
    """
    try:
        import numpy  # noqa: F401
        import scipy.special  # noqa: F401
        from sklearn.feature_extraction.text import HashingVectorizer

        HashingVectorizer(n_features=8).transform(["warmup"]).toarray()
    except Exception:
        pass

    try:
        from rag.embeddings import _model_is_cached

        if os.environ.get("EMBEDDING_BACKEND") == "sentence-transformers" or _model_is_cached():
            import sentence_transformers  # noqa: F401
    except Exception:
        pass


@mcp.tool()
async def search_financial_guidance(query: str, top_k: int = 5):
    """Search the financial knowledge base for relevant guidance passages."""
    # Retrieval may load an embedding model on first use.  Run it off the event
    # loop so the stdio transport keeps flowing, and so a slow cold start does
    # not block the JSON-RPC session.
    return await anyio.to_thread.run_sync(
        functools.partial(tools.search_financial_guidance, query, top_k)
    )


@mcp.tool()
def get_budgeting_rules():
    """Return general budgeting rules."""
    return tools.get_budgeting_rules()


@mcp.tool()
def health_check():
    """Health check for the MCP server."""
    return tools.health_check()


@mcp.tool()
def add_expense(date: str, amount: float, category: str, description: str = ""):
    """Add an expense transaction (write action; confirm with the user first)."""
    return tools.add_expense(date, amount, category, description)


@mcp.tool()
def list_expenses(month: str = None, category: str = None, limit: int = 50):
    """List expense transactions, optionally filtered by month (YYYY-MM) or category."""
    return tools.list_expenses(month, category, limit)


@mcp.tool()
def update_expense(transaction_id: int, date: str = None, amount: float = None,
                  category: str = None, description: str = None):
    """Update an existing expense transaction (write action)."""
    return tools.update_expense(transaction_id, date, amount, category, description)


@mcp.tool()
def delete_expense(transaction_id: int):
    """Delete an expense transaction by id (write action)."""
    return tools.delete_expense(transaction_id)


@mcp.tool()
def create_budget(month: str, category: str, amount: float):
    """Create or update a monthly/category budget."""
    return tools.create_budget(month, category, amount)


@mcp.tool()
def list_budgets(month: str = None):
    """List budgets, optionally filtered by month."""
    return tools.list_budgets(month)


@mcp.tool()
def get_spending_summary(month: str):
    """Total spending and category breakdown for a month."""
    return tools.get_spending_summary(month)


@mcp.tool()
def get_budget_status(month: str, category: str = None):
    """Remaining budget for a month/category."""
    return tools.get_budget_status(month, category)


@mcp.tool()
def compare_months(month_a: str, month_b: str):
    """Compare spending between two months."""
    return tools.compare_months(month_a, month_b)


@mcp.tool()
def get_unusual_spending(month: str):
    """Detect unusual spending for a month."""
    return tools.get_unusual_spending(month)


@mcp.tool()
def remember_fact(key: str, value: str, category: str = "fact", importance: int = 3):
    """Persist a durable user fact for future sessions (long-term memory)."""
    return tools.remember_fact(key, value, category, importance)


@mcp.tool()
def recall_facts(query: str = "", limit: int = 10):
    """Retrieve durable user facts saved in earlier sessions."""
    return tools.recall_facts(query, limit)


@mcp.tool()
def get_safe_to_spend(month: str = None):
    """One number the user can safely spend after reserving upcoming bills."""
    return tools.get_safe_to_spend(month)


@mcp.tool()
def can_i_afford(amount: float, month: str = None):
    """Check whether a purchase fits inside the Safe-to-Spend amount."""
    return tools.can_i_afford(amount, month)


@mcp.tool()
def get_month_forecast(month: str = None):
    """Project month-end spending from the current run rate and upcoming bills."""
    return tools.get_month_forecast(month)


@mcp.tool()
def list_subscriptions():
    """Detect recurring subscriptions and bills, including price hikes and stale charges."""
    return tools.list_subscriptions()


@mcp.tool()
def get_financial_health(month: str = None):
    """Explainable financial health score with component scores and next steps."""
    return tools.get_financial_health(month)


@mcp.tool()
def get_monthly_recap(month: str = None):
    """Generate a short monthly recap with top categories, forecast, and goals."""
    return tools.get_monthly_recap(month)


@mcp.tool()
def list_goals():
    """List savings goals with progress, status, and required monthly contribution."""
    return tools.list_goals()


@mcp.tool()
def add_to_goal(goal: str, amount: float):
    """Add a contribution to a savings goal (write action; confirm with the user first)."""
    return tools.add_to_goal(goal, amount)


@mcp.tool()
def create_savings_goal(
    name: str,
    target_amount: float,
    saved_amount: float = 0.0,
    target_date: str = None,
    category: str = "general",
):
    """Create a savings goal (write action; confirm with the user first)."""
    return tools.create_savings_goal(name, target_amount, saved_amount, target_date, category)


@mcp.tool()
def suggest_transaction_category(description: str):
    """Suggest a category for a merchant description using learned merchant rules."""
    return tools.suggest_transaction_category(description)


@mcp.tool()
def get_debt_payoff_plan(debts: list, extra_payment: float = 0.0, strategy: str = "avalanche"):
    """Compare snowball and avalanche debt payoff plans for a list of debts."""
    return tools.get_debt_payoff_plan(debts, extra_payment, strategy)


def main():
    _warmup_embeddings()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
