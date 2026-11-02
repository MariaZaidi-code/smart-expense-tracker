"""Tool registry and execution for the expense agent.

Every tool has two implementations:

* **MCP** (preferred) - ``MCPToolClient`` launches the MCP server and invokes
  the tool over stdio.
* **Local fallback** - the same Python functions, used if the MCP server is
  unavailable so the demo never dies.

Both paths write an audit row to ``agent_tool_calls`` with the transport used.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from agent.memory import MemoryStore
from agent.mcp_client import MCPToolClient
from database.connection import get_connection
from expense.analytics import (
    category_totals,
    month_comparison,
    remaining_budget,
    total_spending,
    unusual_spending,
)
from expense.budgets import create_budget
from expense.goals import goal_summary
from expense.insights import (
    can_i_afford as afford_check,
    financial_health,
    month_forecast,
    monthly_recap,
    safe_to_spend,
    subscription_summary,
)
from expense.rules import suggest_category
from expense.transactions import (
    add_transaction,
    ensure_category,
    get_transaction,
    list_transactions,
)
from rag.retriever import ensure_index, retrieve

MCP_TOOL_NAMES = {
    "search_financial_guidance",
    "get_budgeting_rules",
    "add_expense",
    "list_expenses",
    "create_budget",
    "list_budgets",
    "get_spending_summary",
    "get_budget_status",
    "compare_months",
    "get_unusual_spending",
    "remember_fact",
    "recall_facts",
    "get_safe_to_spend",
    "can_i_afford",
    "get_month_forecast",
    "list_subscriptions",
    "get_financial_health",
    "get_monthly_recap",
    "list_goals",
    "suggest_transaction_category",
}

TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "get_spending_summary",
            "description": "Total spending and category breakdown for one month (YYYY-MM).",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string", "description": "Month in YYYY-MM format"}
                },
                "required": ["month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_budget_status",
            "description": "Budget, spending, and remaining amount for a month, optionally one category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_transactions",
            "description": "List or search the user's transactions for a month/category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "month": {"type": "string"},
                    "category": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_months",
            "description": "Compare total and category spending between two months.",
            "parameters": {
                "type": "object",
                "properties": {
                    "month_a": {"type": "string"},
                    "month_b": {"type": "string"},
                },
                "required": ["month_a", "month_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_unusual_spending",
            "description": "Flag categories well above their recent three-month average.",
            "parameters": {
                "type": "object",
                "properties": {"month": {"type": "string"}},
                "required": ["month"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_safe_to_spend",
            "description": "One trustworthy amount the user can still spend this month after reserving upcoming recurring bills, plus a per-day allowance.",
            "parameters": {
                "type": "object",
                "properties": {"month": {"type": "string", "description": "Month in YYYY-MM format"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "can_i_afford",
            "description": "Check whether a specific purchase amount fits inside the Safe-to-Spend amount for the month.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Purchase amount in Rs."},
                    "month": {"type": "string"},
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_month_forecast",
            "description": "Project month-end spending from the current run rate, recurring charges, and upcoming bills.",
            "parameters": {
                "type": "object",
                "properties": {"month": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_subscriptions",
            "description": "Detect recurring subscriptions and bills, with monthly cost, next due date, price hikes, and stale/cancelled charges.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_financial_health",
            "description": "Explainable financial health score (0-100) with component scores and the single best next step.",
            "parameters": {
                "type": "object",
                "properties": {"month": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_monthly_recap",
            "description": "Short monthly recap: headline comparison, top categories, biggest expense, subscriptions, forecast, and goals.",
            "parameters": {
                "type": "object",
                "properties": {"month": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_goals",
            "description": "List savings goals with progress, status, and the required monthly contribution.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_transaction_category",
            "description": "Suggest a category for a merchant description using learned merchant rules and keyword heuristics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Merchant or transaction description"}
                },
                "required": ["description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_financial_guidance",
            "description": "Retrieve grounded personal-finance guidance passages with source names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Persist a durable user preference or fact for future sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_facts",
            "description": "Retrieve durable facts saved in this or earlier sessions.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_expense",
            "description": "Add a transaction. Only call after the user explicitly confirms the exact date, amount, category, and description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "amount": {"type": "number"},
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["date", "amount", "category", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_month",
            "description": "Return the current month in YYYY-MM format.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_budgeting_rules",
            "description": "Return short, general budgeting rules (for example the 50/30/20 rule).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def current_month() -> str:
    return date.today().strftime("%Y-%m")


def _source_list(results: list[dict]) -> list[dict]:
    sources = []
    for index, result in enumerate(results, start=1):
        sources.append(
            {
                "title": result.get("source") or f"Passage {index}",
                "excerpt": (result.get("text") or "")[:500],
                "score": None
                if result.get("distance") is None
                else round(1 - result["distance"], 4),
            }
        )
    return sources


class ToolRunner:
    def __init__(
        self,
        session_id: str = "",
        memory: MemoryStore | None = None,
        mcp_client: MCPToolClient | None = None,
        prefer_mcp: bool = True,
        db_path=None,
    ):
        self.session_id = session_id
        self.memory = memory or MemoryStore(db_path=db_path)
        self.db_path = db_path if db_path is not None else self.memory.db_path
        self.mcp = mcp_client if mcp_client is not None else MCPToolClient()
        self.prefer_mcp = prefer_mcp and self.mcp.enabled
        self.mcp_tools = self.mcp.list_tools() if self.prefer_mcp else []
        self.executions: list[dict] = []

    @property
    def tool_specs(self) -> list[dict]:
        return TOOL_SPECS

    @property
    def tool_names(self) -> list[str]:
        return [spec["function"]["name"] for spec in TOOL_SPECS]

    def status(self) -> dict:
        return {
            "prefer_mcp": self.prefer_mcp,
            "mcp": self.mcp.status(),
            "mcp_tools": self.mcp_tools,
            "available_tools": self.tool_names,
        }

    def _log(
        self,
        name: str,
        arguments: dict,
        result: dict,
        transport: str,
    ) -> None:
        try:
            with get_connection(self.memory.db_path) as connection:
                connection.execute(
                    """
                    INSERT INTO agent_tool_calls(session_id, tool_name, arguments, result, transport)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        self.session_id,
                        name,
                        json.dumps(arguments, default=str),
                        json.dumps(result, default=str)[:8000],
                        transport,
                    ),
                )
        except Exception:
            # Audit logging must never break a user-facing answer.
            pass

    def run(self, name: str, arguments: dict | None = None) -> dict:
        arguments = dict(arguments or {})
        if name not in self.tool_names:
            return {
                "ok": False,
                "tool": name,
                "arguments": arguments,
                "error": f"Unknown tool: {name}",
                "transport": "none",
            }

        if self.prefer_mcp and name in MCP_TOOL_NAMES and name in self.mcp_tools:
            mcp_result = self.mcp.call_tool(name, arguments)
            if mcp_result.get("ok"):
                execution = {
                    **mcp_result,
                    "tool": name,
                    "arguments": arguments,
                }
                self.executions.append(execution)
                self._log(name, arguments, mcp_result.get("result", {}), "mcp")
                return execution
            # Record the MCP failure and try the local implementation.
            self._log(name, arguments, {"mcp_error": mcp_result.get("error")}, "mcp")

        try:
            result = self._local(name, arguments)
            execution = {
                "ok": True,
                "tool": name,
                "arguments": arguments,
                "result": result,
                "transport": "local",
            }
        except Exception as exc:
            execution = {
                "ok": False,
                "tool": name,
                "arguments": arguments,
                "error": str(exc),
                "transport": "local",
            }
        self.executions.append(execution)
        self._log(
            name,
            arguments,
            execution.get("result", {"error": execution.get("error")}),
            execution["transport"],
        )
        return execution

    def _local(self, name: str, arguments: dict) -> dict:
        if name == "get_spending_summary":
            month = arguments.get("month") or current_month()
            return {
                "ok": True,
                "month": month,
                "total": total_spending(month=month, db_path=self.db_path),
                "by_category": category_totals(month, db_path=self.db_path),
            }
        if name == "get_budget_status":
            month = arguments.get("month") or current_month()
            return {
                "ok": True,
                "status": remaining_budget(
                    month, category=arguments.get("category"), db_path=self.db_path
                ),
            }
        if name == "list_transactions":
            rows = list_transactions(
                month=arguments.get("month"),
                category=arguments.get("category"),
                limit=arguments.get("limit", 20),
                db_path=self.db_path,
            )
            return {"ok": True, "count": len(rows), "transactions": rows}
        if name == "compare_months":
            return {
                "ok": True,
                "comparison": month_comparison(
                    arguments.get("month_a") or current_month(),
                    arguments.get("month_b") or current_month(),
                    db_path=self.db_path,
                ),
            }
        if name == "detect_unusual_spending":
            month = arguments.get("month") or current_month()
            return {
                "ok": True,
                "month": month,
                "flags": unusual_spending(month, db_path=self.db_path),
            }
        if name == "get_safe_to_spend":
            return {
                "ok": True,
                "snapshot": safe_to_spend(arguments.get("month"), db_path=self.db_path),
            }
        if name == "can_i_afford":
            return {
                "ok": True,
                "verdict": afford_check(
                    float(arguments.get("amount", 0)),
                    arguments.get("month"),
                    db_path=self.db_path,
                ),
            }
        if name == "get_month_forecast":
            return {
                "ok": True,
                "forecast": month_forecast(
                    arguments.get("month"), db_path=self.db_path
                ),
            }
        if name == "list_subscriptions":
            return {"ok": True, "summary": subscription_summary(db_path=self.db_path)}
        if name == "get_financial_health":
            return {
                "ok": True,
                "health": financial_health(
                    arguments.get("month"), db_path=self.db_path
                ),
            }
        if name == "get_monthly_recap":
            return {
                "ok": True,
                "recap": monthly_recap(
                    arguments.get("month"), db_path=self.db_path
                ),
            }
        if name == "list_goals":
            return {"ok": True, "summary": goal_summary(db_path=self.db_path)}
        if name == "suggest_transaction_category":
            return {
                "ok": True,
                "suggestion": suggest_category(
                    arguments.get("description", ""), db_path=self.db_path
                ),
            }
        if name == "search_financial_guidance":
            query = (arguments.get("query") or "").strip()
            if not query:
                return {"ok": True, "query": "", "count": 0, "results": []}
            ensure_index()
            results = retrieve(query, top_k=int(arguments.get("top_k", 5) or 5))
            formatted = [
                {
                    "source": result.get("source"),
                    "text": result.get("text"),
                    "score": None
                    if result.get("distance") is None
                    else round(1 - result["distance"], 4),
                }
                for result in results
            ]
            return {"ok": True, "query": query, "count": len(formatted), "results": formatted}
        if name == "remember_fact":
            fact = self.memory.remember(
                arguments.get("key", "note"),
                arguments.get("value", ""),
                category=arguments.get("category", "fact"),
            )
            return {"ok": True, "remembered": fact}
        if name == "recall_facts":
            facts = self.memory.recall(arguments.get("query", ""), limit=20)
            return {"ok": True, "count": len(facts), "facts": facts}
        if name == "add_expense":
            category = arguments.get("category") or "Other"
            ensure_category(category, db_path=self.db_path)
            transaction_id = add_transaction(
                arguments.get("description") or "Agent-added expense",
                float(arguments.get("amount", 0)),
                category,
                arguments.get("date") or date.today().isoformat(),
                db_path=self.db_path,
            )
            return {
                "ok": True,
                "transaction": get_transaction(transaction_id, self.db_path),
            }
        if name == "get_current_month":
            return {"ok": True, "month": current_month()}
        if name == "get_budgeting_rules":
            return {
                "ok": True,
                "rules": [
                    "50/30/20 rule: 50% needs, 30% wants, 20% savings/debt.",
                    "Keep 3-6 months of essential expenses in an emergency fund.",
                    "Track every expense and categorize consistently.",
                    "Review the budget weekly and do a deeper review monthly.",
                ],
            }
        raise ValueError(f"Local implementation missing for {name}")

    def tool_message(self, execution: dict) -> str:
        payload = execution.get("result") if execution.get("ok") else {
            "error": execution.get("error", "tool failed")
        }
        return json.dumps(payload, default=str)[:8000]
