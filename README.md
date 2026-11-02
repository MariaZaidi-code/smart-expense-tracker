# Smart Expense Tracker — Personal Expense Management Agent

A full-stack personal-finance demo with a **Grok-powered AI agent**, persistent
short-term and long-term memory, a **RAG** knowledge base, and a real **MCP**
client/server tool connection.

This repository combines the work from the `rameen` branch (Streamlit UI, data
layer, seed data, tests) and the `qaim` branch (RAG pipeline, MCP server/client,
retrieval tools) on the `maria` integration branch, then implements the missing
**Agent Based Modeling — Assignment 2** requirements.

## Assignment 2 requirements → implementation

| Requirement | Where it lives |
|---|---|
| One Python AI agent + LLM | `agent/agent.py`, `agent/llm.py` (Grok / xAI) |
| Tool selection and decisions | `agent/tools.py`, tool schemas + Grok function calling |
| Short-term memory | `agent/memory.py` (`agent_messages` table) |
| Long-term memory (new session) | `agent/memory.py` (`agent_memory` table) |
| RAG (≥5 docs, chunk, embed, vector store) | `rag/` + `rag/documents/` (6 docs), ChromaDB |
| MCP client + server + real invocation | `mcp_server/`, `agent/mcp_client.py`, `mcp_client/client_demo.py` |
| Prompt engineering | `agent/prompts.py`, `docs/PROMPTS.md` |
| Architecture diagram | `docs/ARCHITECTURE.md` |
| Tests and error handling | `tests/`, graceful fallbacks in every layer |
| Reproducible demo | `docs/DEMO_SCRIPT.md`, `scripts/demo_agent.py` |
| Standout features from leading apps | `expense/insights.py`, `expense/goals.py`, `expense/rules.py`, Smart Insights + Goals pages |

See `docs/ASSIGNMENT_2_CHECKLIST.md` for the full mapping and
`docs/FEATURE_RESEARCH.md` for the competitor → feature research.

## Features

- Streamlit app with Dashboard, Transactions, Budgets, **Smart Insights**, **Goals**, AI Assistant, Agent Memory, and Settings
- **Safe to Spend** — one trusted number after reserving upcoming bills, plus a daily allowance
- **Can I afford this?** — instant verdict grounded in the same Safe-to-Spend calculation
- **Subscription hunter** — detects recurring charges, next due dates, price hikes, and stale subscriptions
- **Month-end forecast** — projects spending from the current run rate and unbilled recurring charges
- **Financial health score** — explainable 0–100 score with five weighted components and one next step
- **Savings goals** — sinking funds with progress, on-track/behind status, and required monthly contribution
- **Merchant learning** — auto-categorisation improves every time a transaction is saved or corrected
- **Monthly recap + spending heatmap** — Monarch/Copilot-style review of the month
- **Debt payoff planner** — compares avalanche and snowball strategies with total interest
- Natural-language agent grounded in real SQLite data
- Grok tool calling with MCP execution and a deterministic offline fallback
- RAG over budgeting, saving, debt, and emergency-fund guidance
- Persistent long-term memory that survives a brand-new session
- Transaction CRUD, search/filter/sort, monthly and category budgets
- Spending trends, month-over-month comparison, unusual-spending detection
- Legacy FastAPI backend under `backend/` (kept for completeness)

## Quick start

```powershell
cd C:\Users\Go\smart-expense-tracker
python -m pip install -r requirements.txt

# 1) Add your Grok key (or set GROK_API_KEY)
notepad grok_api_key.txt      # paste: xai-...
# get a key at https://console.x.ai

# 2) Seed synthetic demo data (safe to re-run)
python database/seed.py --reset

# 3) Build the RAG index (optional: the app auto-builds it on first use)
python build_index.py

# 4) Run the Streamlit app
streamlit run ui/app.py
```

If the key file is missing or the LLM is unreachable, the app still works with a
deterministic rule-based agent and clearly labels the mode in the AI Assistant.

### Key configuration

`agent/llm.py` reads the key from the first available source:

1. `GROK_API_KEY` / `XAI_API_KEY` environment variable
2. `grok_api_key.txt` in the project root
3. `api_key.txt` or `config/grok_api_key.txt`

This project is **Grok (xAI) only**. A Groq key (`gsk_...`) is rejected with a
clear message instead of being routed to a different provider. Create a Grok key
at <https://console.x.ai>.

Optional settings:

```powershell
$env:GROK_MODEL = "grok-4-fast"          # or grok-3-mini, grok-4
$env:GROK_BASE_URL = "https://api.x.ai/v1"
$env:MCP_ENABLED = "1"                   # 0 disables MCP and uses local tools
$env:EMBEDDING_BACKEND = "hashing"       # offline embeddings
$env:EXPENSE_DB_PATH = "data/expenses.db"
```

## Run the agent without the UI

```powershell
python scripts\demo_agent.py
```

The script runs a multi-turn conversation, prints tool/source/MCP evidence, then
starts a **new session** to prove that long-term memory persists.

To see the researched standout features without the UI:

```powershell
python scripts\demo_insights.py
```

That prints Safe to Spend, the forecast, detected subscriptions, the financial
health breakdown, the monthly recap, goal progress, affordability verdicts,
merchant suggestions, and the debt payoff comparison.

## MCP evidence

```powershell
# Inspect the MCP server tools (stdio handshake + tool calls)
python mcp_client\client_demo.py
```

The agent uses the same server through `agent/mcp_client.py`. Every tool call is
audited in the `agent_tool_calls` table with `transport = mcp` or `local`.

## Tests

```powershell
python -m pytest
```

Optional live checks:

```powershell
$env:RUN_UI_TESTS = "1"      # Flask + Playwright retrieval demo
python -m pytest tests/test_llm_optional.py -v
```

Tests that need a real key are skipped automatically when no key is configured.

## Competitive research

The Smart Insights and Goals pages are the result of a review of YNAB, Monarch,
Copilot, PocketGuard, Rocket Money, PocketSmith, Simplifi, Safe Spend, Fiscify,
Origin, and Cleo. The mapping from each app's signature feature to the code that
implements it is in [`docs/FEATURE_RESEARCH.md`](docs/FEATURE_RESEARCH.md).

## Project structure

```
agent/              Grok LLM client, prompts, memory, tool runner, agent loop
rag/                loader, chunker, embeddings, Chroma/JSON vector store, retriever
rag/documents/      6 financial-guidance documents
mcp_server/         FastMCP server (26 tools) and tool business logic
mcp_client/         standalone MCP client demo
ui/                 Streamlit app and pages (Rameen's UI + Smart Insights/Goals)
database/           SQLite schema, connection helpers, six-month seed data
expense/            transactions, budgets, analytics, insights, goals, merchant rules
tests/              data-layer, insights/goals, RAG/MCP, memory, agent, optional LLM tests
docs/               architecture, checklist, prompt rationale, demo, feature research
backend/            FastAPI backend (legacy, optional)
```

## Branch history

- `rameen` — Streamlit UI, normalized expense data layer, seed data, tests
- `qaim` — RAG pipeline, MCP server/client, retrieval tools
- `maria` — integration branch: both merged, data layers unified, Assignment 2 agent added

## Safety

The demo uses synthetic data only. The agent is read-only by default; write tools
require explicit confirmation in the UI. No real bank credentials are used.
