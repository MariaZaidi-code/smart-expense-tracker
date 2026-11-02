"""End-to-end MCP client demo.

Run with ``python mcp_client\\client_demo.py``.  This launches the real MCP
server over stdio, performs the initialize handshake, and invokes tools through
the MCP protocol (not by importing the functions directly).
"""

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MONTH = date.today().strftime("%Y-%m")


def _show(label: str, result) -> None:
    text = result.content[0].text if result.content else str(result)
    try:
        parsed = json.loads(text)
        text = json.dumps(parsed, indent=2, default=str)
    except (json.JSONDecodeError, TypeError):
        pass
    print(f"\n{label}:\n{text}")


async def demo():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / "mcp_server" / "server.py")],
        cwd=str(ROOT),
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(" -", tool.name)

            _show("health_check", await session.call_tool("health_check", {}))

            # RAG over MCP (the embedding libraries are preloaded by the server).
            _show(
                "search_financial_guidance",
                await session.call_tool(
                    "search_financial_guidance",
                    {"query": "emergency fund", "top_k": 3},
                ),
            )
            _show(
                "get_budgeting_rules",
                await session.call_tool("get_budgeting_rules", {}),
            )

            # Write tools.
            _show(
                "add_expense",
                await session.call_tool(
                    "add_expense",
                    {
                        "date": f"{MONTH}-01",
                        "amount": 500,
                        "category": "Food & dining",
                        "description": "lunch",
                    },
                ),
            )
            _show(
                "create_budget",
                await session.call_tool(
                    "create_budget",
                    {"month": MONTH, "category": "Food & dining", "amount": 2000},
                ),
            )

            # Read and analytics tools.
            _show(
                "get_spending_summary",
                await session.call_tool("get_spending_summary", {"month": MONTH}),
            )
            _show(
                "get_budget_status",
                await session.call_tool(
                    "get_budget_status", {"month": MONTH, "category": "Food & dining"}
                ),
            )

            # Researched standout features.
            _show(
                "get_safe_to_spend",
                await session.call_tool("get_safe_to_spend", {"month": MONTH}),
            )
            _show(
                "can_i_afford",
                await session.call_tool(
                    "can_i_afford", {"amount": 2500, "month": MONTH}
                ),
            )
            _show(
                "get_month_forecast",
                await session.call_tool("get_month_forecast", {"month": MONTH}),
            )
            _show(
                "list_subscriptions",
                await session.call_tool("list_subscriptions", {}),
            )
            _show(
                "get_financial_health",
                await session.call_tool("get_financial_health", {"month": MONTH}),
            )
            _show(
                "get_monthly_recap",
                await session.call_tool("get_monthly_recap", {"month": MONTH}),
            )
            _show("list_goals", await session.call_tool("list_goals", {}))
            _show(
                "suggest_transaction_category",
                await session.call_tool(
                    "suggest_transaction_category",
                    {"description": "Netflix.com"},
                ),
            )


if __name__ == "__main__":
    asyncio.run(demo())
