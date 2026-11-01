import sys
from pathlib import Path

# ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from mcp_server import tools

mcp = FastMCP("expense-tracker-mcp")


@mcp.tool()
def search_financial_guidance(query: str, top_k: int = 5):
    """Search the financial knowledge base for relevant guidance passages."""
    return tools.search_financial_guidance(query, top_k)


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
    """Add an expense transaction."""
    return tools.add_expense(date, amount, category, description)


@mcp.tool()
def list_expenses(month: str = None, category: str = None):
    """List expense transactions, optionally filtered by month (YYYY-MM) or category."""
    return tools.list_expenses(month, category)


@mcp.tool()
def update_expense(transaction_id: int, date: str = None, amount: float = None,
                  category: str = None, description: str = None):
    """Update an existing expense transaction."""
    return tools.update_expense(transaction_id, date, amount, category, description)


@mcp.tool()
def delete_expense(transaction_id: int):
    """Delete an expense transaction by id."""
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


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
