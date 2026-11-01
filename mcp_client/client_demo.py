import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


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
            for t in tools.tools:
                print(" -", t.name)

            # health check
            r = await session.call_tool("health_check", {})
            print("\nhealth_check:", r.content[0].text if r.content else r)

            # search guidance
            r = await session.call_tool("search_financial_guidance", {"query": "emergency fund", "top_k": 3})
            print("\nsearch_financial_guidance:", r.content[0].text if r.content else r)

            # budgeting rules
            r = await session.call_tool("get_budgeting_rules", {})
            print("\nget_budgeting_rules:", r.content[0].text if r.content else r)

            # add expense
            r = await session.call_tool("add_expense", {"date": "2026-11-01", "amount": 500, "category": "Food", "description": "lunch"})
            print("\nadd_expense:", r.content[0].text if r.content else r)

            # spending summary
            r = await session.call_tool("get_spending_summary", {"month": "2026-11"})
            print("\nget_spending_summary:", r.content[0].text if r.content else r)

            # budget status
            await session.call_tool("create_budget", {"month": "2026-11", "category": "Food", "amount": 2000})
            r = await session.call_tool("get_budget_status", {"month": "2026-11", "category": "Food"})
            print("\nget_budget_status:", r.content[0].text if r.content else r)


if __name__ == "__main__":
    asyncio.run(demo())
