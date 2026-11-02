# Reproducible Demo Script

## 0. One-time setup

```powershell
cd C:\Users\Go\smart-expense-tracker
python -m pip install -r requirements.txt
notepad grok_api_key.txt       # paste xai-... and save
python database\seed.py --reset
python build_index.py
```

Expected: `Indexed: {'documents': 6, 'chunks': ...}`.

## 1. CLI demo (fastest evidence)

```powershell
python scripts\demo_agent.py
```

The script prints:

1. **Turn 1** — spending for last month, with `get_spending_summary`
   and its transport (`mcp` or `local`).
2. **Turn 2** — an elliptical follow-up (“What about food?”) that inherits the
   month from the previous turn, proving short-term memory even in the offline
   fallback.
3. **Turn 3** — “My monthly food budget is Rs. 8,000 — remember that.” writes a
   long-term memory via `remember_fact`.
4. **New session** — a brand-new `session_id`.
5. **Turn 4** — “What do you remember about me?” returns the saved budget from
   the new session.
6. **Turn 5** — “Give me a tip to save more” returns RAG passages with sources.
7. **Turn 6** — “How much did I spend last month?” compares months.

The follow-up can also be tried in the Streamlit chat:

```text
How much did I spend last month?
What about food?
```

Look for lines like:

```
transport : mcp
tools     : get_spending_summary
sources   : Expense database
```

## 1b. Smart insights CLI

```powershell
python scripts\demo_insights.py
```

Expected output includes:

- Safe to Spend with reserved upcoming bills and a daily allowance.
- A month-end forecast labelled **On track**.
- Four detected subscriptions (PTCL, gym, Netflix, Spotify) and their annual cost.
- A financial health score with five explainable components.
- A monthly recap, goal progress, affordability verdicts, merchant suggestions,
  and an avalanche-vs-snowball debt comparison.

## 2. Streamlit demo

```powershell
streamlit run ui/app.py
```

1. Open **AI Assistant**.
2. Confirm the green banner: `Grok connected · grok-... · key from grok_api_key.txt`.
3. Ask: **“How much did I spend this month?”**
   - Expect real totals and `⚙ Used tool: get_spending_summary`.
   - Expect `🔌 Executed through the MCP client → MCP server`.
4. Ask a follow-up: **“What about food?”**
   - This proves short-term memory: the month is inherited from the previous
     turn without being repeated.
5. Ask: **“My monthly food budget is Rs. 8,000 — remember that.”**
   - Expect “I've saved that to long-term memory…”.
6. Click **＋ New session**.
7. Ask: **“What do you remember about me?”**
   - Expect the Rs. 8,000 budget from the previous session.
8. Ask: **“Give me a tip to save more.”**
   - Expect grounded passages and source expanders.
9. Open **Agent Memory**:
   - Long-term tab shows the saved fact.
   - Session transcripts tab shows both conversations.
10. Open a SQLite client (or run the query below) to show tool audit evidence:

```powershell
python -c "import sqlite3; c=sqlite3.connect('data/expenses.db'); print(c.execute('select tool_name, transport, created_at from agent_tool_calls order by id desc limit 10').fetchall())"
```

11. Open **Smart Insights**:
    - Safe to Spend hero shows the reserved-bill breakdown and daily allowance.
    - Forecast gauge is **On track**; health score shows five components.
    - Subscription hunter lists PTCL, gym, Netflix, and Spotify.
    - Heatmap, recap, “Can I afford this?”, and the debt planner are on the same page.
12. Open **Goals**:
    - Emergency fund and laptop progress bars, required monthly amounts, and status.
    - Click **Add money** to update a goal; click **＋ New goal** to create one.
13. Open **Transactions → ＋ Add expense**:
    - Type `Netflix.com`; the category is suggested as **Entertainment** from the
      keyword heuristic. Saving the transaction teaches the merchant for next time.

## 3. MCP evidence

```powershell
python mcp_client\client_demo.py
```

Expected: a list of 26 tools, then JSON results for `health_check`,
`search_financial_guidance`, `add_expense`, `get_spending_summary`,
`get_budget_status`, `get_safe_to_spend`, `list_subscriptions`,
`get_financial_health`, `get_monthly_recap`, `list_goals`, and
`suggest_transaction_category`.

## 4. Tests

```powershell
python -m pytest
```

Expected: data-layer, RAG/MCP, memory, prompt, and agent tests pass. Live LLM
tests are skipped when no key is configured.

## 5. Failure-path demo (optional)

- Rename `grok_api_key.txt` and unset `GROK_API_KEY`.
- Restart Streamlit.
- The AI Assistant shows the amber “No Grok API key found” banner and still
  answers using the deterministic fallback.
- Ask about a month with no data: the agent says it has no transactions rather
  than inventing a number.
- Set `MCP_ENABLED=0` to show the local tool fallback; tool badges switch from
  `mcp` to `local`.

## Assignment talking points

- **Short-term vs long-term memory:** the transcript is per `session_id`; durable
  facts are per `user_id` and survive a new session.
- **RAG vs memory:** RAG documents are shared guidance; memory is user context.
- **MCP vs HTTP:** the client performs the MCP handshake and `call_tool` over
  stdio; it is not a plain REST call.
- **Human oversight:** `add_expense` is blocked unless the UI toggle and an
  explicit confirmation are present.
- **Grounding:** every numeric answer comes from a tool result; general advice
  comes from retrieved passages with source names.
- **Competitive research:** Safe to Spend (PocketGuard), subscription hunter
  (Rocket Money), forecasting (PocketSmith), explainable health (Fiscify),
  goals (YNAB), merchant learning (Copilot), and recap (Monarch) are implemented
  in `expense/insights.py`, `expense/goals.py`, and `expense/rules.py`. See
  `docs/FEATURE_RESEARCH.md` for the full mapping.
- **MCP native-import fix:** the MCP server preloads NumPy/SciPy/scikit-learn on
  its main thread before `mcp.run()`. On Windows, first-time native imports from
  FastMCP's worker thread deadlock, which previously stalled the RAG tool.
