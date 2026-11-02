# Assignment 2 Checklist — Personal Expense Management Agent

Scenario 14: **Personal Expense Management Agent** — categorize transactions,
remember budgets, and analyze spending patterns.

| # | Requirement | Status | Implementation | Evidence |
|---|---|---|---|---|
| 1 | One primary Python AI agent connected to an LLM | ✅ | `agent/agent.py`, `agent/llm.py` | `python scripts/demo_agent.py`; AI Assistant page |
| 2 | Agent interprets requests and chooses a tool or retrieval path | ✅ | Grok function calling + `agent/tools.py` schemas | Tool tags in the UI; `agent_tool_calls` table |
| 3 | Stored context used in a grounded response | ✅ | `expense/` + RAG + memory injected into prompt | Answers contain real totals and sources |
| 4 | Short-term memory: session conversation history | ✅ | `agent_messages`, `MemoryStore.history()` | Follow-up “How much budget is left for food?” after a spending question |
| 5 | Short-term memory demonstrated with a follow-up | ✅ | Demo turns 1–2; test `test_agent_fallback_spending_and_followup` | `pytest tests/test_agent.py` |
| 6 | Long-term memory: persistent store | ✅ | `agent_memory` SQLite table | Agent Memory page; `MemoryStore.remember()` |
| 7 | Long-term memory retrieved in a NEW session | ✅ | `user_id` scoped recall; demo turn 3 → new session → turn 4 | `scripts/demo_agent.py` output |
| 8 | RAG: at least 5 documents | ✅ | 6 markdown files in `rag/documents/` | `python build_index.py` reports 6 documents |
| 9 | RAG: chunk, embed, store in a vector database, retrieve | ✅ | `rag/chunker.py`, `rag/embeddings.py`, `rag/vector_store.py` (ChromaDB), `rag/retriever.py` | `pytest tests/test_rag_mcp.py`; sources shown in chat |
| 10 | Ground answers in sources | ✅ | Prompt rule + `sources` in `ask()` response | Source expanders under each answer |
| 11 | MCP: at least one functioning MCP server/tool | ✅ | `mcp_server/server.py` (FastMCP, 26 tools incl. RAG, insights, goals) | `python mcp_client\client_demo.py` |
| 12 | MCP: real tool invocation through a Python integration | ✅ | `agent/mcp_client.py` stdio client; agent uses it by default | `test_mcp_client_round_trip`; transport badge “MCP” |
| 13 | Prompt engineering: role, scope, tool rules, evidence, memory, failure | ✅ | `agent/prompts.py` | `docs/PROMPTS.md` |
| 14 | Architecture diagram | ✅ | `docs/ARCHITECTURE.md` | Mermaid diagram |
| 15 | Test cases | ✅ | `tests/test_expenses.py`, `test_insights.py`, `test_rag_mcp.py`, `test_agent.py`, `test_llm_optional.py` | `python -m pytest` |
| 16 | Error handling | ✅ | Tool errors returned as structured dicts; LLM/RAG/MCP fallbacks; UI never crashes | Ask about a month with no data |
| 17 | Evidence of tool execution | ✅ | `agent_tool_calls` table + UI tags + audit | Query `SELECT * FROM agent_tool_calls` |
| 18 | Reproducible demonstration | ✅ | README quick start, `scripts/demo_agent.py`, `docs/DEMO_SCRIPT.md` | Fresh clone walkthrough |
| 19 | Synthetic / authorized data only | ✅ | `database/seed.py` | Seed script and Settings page disclaimer |
| 20 | Human oversight for consequential actions | ✅ | Write tools blocked unless `confirm_write=True`; UI toggle | Ask “add expense” without confirmation |

## Standout features (competitive research)

Researched from YNAB, Monarch, Copilot, PocketGuard, Rocket Money, PocketSmith,
Simplifi, Safe Spend, Fiscify, Origin, and Cleo. Full mapping and algorithms:
`docs/FEATURE_RESEARCH.md`.

| Feature | Inspired by | Implementation | UI | Agent intent |
|---|---|---|---|---|
| Safe to Spend | PocketGuard / Safe Spend | `expense/insights.py::safe_to_spend` | Smart Insights hero, Dashboard KPI | `get_safe_to_spend` |
| Can I afford this? | Safe Spend | `expense/insights.py::can_i_afford` | Smart Insights form | `can_i_afford` |
| Subscription hunter | Rocket Money | `expense/insights.py::detect_recurring` | Subscription table + alerts | `list_subscriptions` |
| Month-end forecast | PocketSmith / Simplifi | `expense/insights.py::month_forecast` | Forecast gauge | `get_month_forecast` |
| Financial health score | Fiscify / Origin | `expense/insights.py::financial_health` | Component score bars | `get_financial_health` |
| Savings goals | YNAB / Monarch | `expense/goals.py` | Goals page | `list_goals` |
| Merchant learning | Copilot Money | `expense/rules.py` | Transactions add dialog | `suggest_transaction_category` |
| Monthly recap | Monarch | `expense/insights.py::monthly_recap` | Recap card | `get_monthly_recap` |
| Spending heatmap | Copilot | `expense/insights.py::spending_calendar` | Month grid | — |
| Debt payoff planner | YNAB / Monarch | `expense/insights.py::debt_payoff` | Avalanche vs snowball | MCP only |

## Quick verification commands

```powershell
python -m pytest
python scripts\demo_agent.py
python mcp_client\client_demo.py
streamlit run ui/app.py
```

## Notes on the integrated branches

- `rameen` supplied the Streamlit UI, normalized SQLite schema, seed data, and
  the original data-layer tests.
- `qaim` supplied the RAG pipeline and MCP server/client.
- The integration branch (`maria`) unified the two competing `expense/` and
  `database/` implementations into one data layer, then added the agent,
  memory, Grok client, prompts, and documentation.
