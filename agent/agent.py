"""Personal Expense Management Agent.

Flow for every user turn:

1. Load the session transcript (short-term memory) and durable facts
   (long-term memory) from SQLite.
2. Build the engineered system prompt.
3. Ask Grok.  Grok chooses tools; tool calls go through the MCP client/server.
4. If Grok is unavailable, run a deterministic grounded rule engine that uses
   the exact same tools.
5. Save the turn, the tool audit trail, and any new durable facts.

The public ``ask()`` return value is the contract used by the Streamlit UI.
"""

from __future__ import annotations

import json
import re
from datetime import date

from agent.llm import GrokLLM, LLMUnavailable
from agent.mcp_client import MCPToolClient
from agent.memory import MemoryStore, current_month, new_session_id
from agent.prompts import build_system_prompt
from agent.tools import ToolRunner
from expense.transactions import list_categories

MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

CATEGORY_SYNONYMS = {    "food": ["Food & dining", "Food"],
    "dining": ["Food & dining", "Food"],
    "restaurant": ["Food & dining", "Food"],
    "eat": ["Food & dining", "Food"],
    "groceries": ["Groceries", "Food & dining", "Food"],
    "grocery": ["Groceries", "Food & dining", "Food"],
    "transport": ["Transport"],
    "travel": ["Transport"],
    "ride": ["Transport"],
    "careem": ["Transport"],
    "uber": ["Transport"],
    "bills": ["Bills & utilities", "Utilities"],
    "utilities": ["Bills & utilities", "Utilities"],
    "electricity": ["Bills & utilities", "Utilities"],
    "internet": ["Bills & utilities", "Utilities"],
    "shopping": ["Shopping"],
    "clothes": ["Shopping"],
    "entertainment": ["Entertainment"],
    "movie": ["Entertainment"],
    "health": ["Health"],
}

# Elliptical follow-ups ("what about food?") inherit month/category from the
# previous turn.  This is the deterministic stand-in for the LLM path's
# short-term-memory resolution.
FOLLOWUP_MARKERS = (
    "what about",
    "how about",
    "same for",
    "and what",
    "that month",
    "that category",
    "those",
)


def _money(value: float) -> str:
    return f"Rs. {float(value):,.0f}"


def _previous_month(month: str) -> str:
    year, number = (int(part) for part in month.split("-"))
    if number == 1:
        return f"{year - 1}-12"
    return f"{year}-{number - 1:02d}"


class ExpenseAgent:
    def __init__(
        self,
        user_id: str = "demo_user",
        session_id: str | None = None,
        use_mcp: bool = True,
        llm: GrokLLM | None = None,
        db_path=None,
    ):
        self.user_id = user_id
        self.session_id = session_id or new_session_id()
        self.db_path = db_path
        self.memory = MemoryStore(user_id=user_id, db_path=db_path)
        self.llm = llm or GrokLLM()
        self.runner = ToolRunner(
            session_id=self.session_id,
            memory=self.memory,
            mcp_client=MCPToolClient(enabled=use_mcp),
            prefer_mcp=use_mcp,
            db_path=db_path,
        )
        self.last_error: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def new_session(self) -> str:
        self.session_id = new_session_id()
        self.runner.session_id = self.session_id
        return self.session_id

    def status(self) -> dict:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "llm": self.llm.status(),
            "tools": self.runner.status(),
            "long_term_memories": len(self.memory.all_facts(limit=100)),
            "session_messages": len(self.memory.history(self.session_id, limit=100)),
        }

    def ask(
        self,
        message: str,
        confirm_write: bool = False,
        extract_memory: bool = True,
    ) -> dict:
        message = (message or "").strip()
        if not message:
            raise ValueError("Please enter a question.")

        # Short-term memory: store the user turn before building the history.
        self.memory.add_message(self.session_id, "user", message)
        history = self.memory.history_for_llm(self.session_id, limit=14)
        facts = self.memory.all_facts(limit=20)
        memory_context = self.memory.format_for_prompt(limit=20)
        system_prompt = build_system_prompt(
            current_month=current_month(),
            user_id=self.user_id,
            memory_context=memory_context,
            tool_names=self.runner.tool_names,
        )

        executions: list[dict] = []
        llm_used = False
        answer = ""
        self.last_error = None

        if self.llm.available:
            try:
                messages = [{"role": "system", "content": system_prompt}, *history]
                answer, executions = self._llm_turn(messages, confirm_write=confirm_write)
                llm_used = bool(answer)
            except LLMUnavailable as exc:
                self.last_error = str(exc)
            except Exception as exc:  # network, parsing, provider outage
                self.last_error = f"{type(exc).__name__}: {exc}"

        if not answer:
            answer, executions = self._rule_based(message, confirm_write=confirm_write)
            llm_used = False

        sources = self._sources_from_executions(executions)
        tools_used = [execution["tool"] for execution in executions if execution.get("tool")]

        self.memory.add_message(
            self.session_id,
            "assistant",
            answer,
            tools_used=tools_used,
            sources=sources,
        )

        if extract_memory:
            self.memory.save_extracted_facts(message)

        transports = {execution.get("transport") for execution in executions}
        if "mcp" in transports and "local" in transports:
            transport = "mixed"
        elif "mcp" in transports:
            transport = "mcp"
        elif "local" in transports:
            transport = "local"
        else:
            transport = "none"

        return {
            "answer": answer,
            "tools_used": tools_used,
            "sources": sources,
            "memory_used": facts,
            "llm_used": llm_used,
            "llm_model": self.llm.last_model if llm_used else None,
            "llm_error": self.last_error,
            "transport": transport,
            "session_id": self.session_id,
        }

    # ------------------------------------------------------------------
    # LLM path
    # ------------------------------------------------------------------
    def _llm_turn(
        self, messages: list[dict], confirm_write: bool = False
    ) -> tuple[str, list[dict]]:
        executions: list[dict] = []
        for _ in range(5):
            result = self.llm.chat(messages, tools=self.runner.tool_specs)
            if result.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": result.content or "",
                        "tool_calls": result.tool_calls,
                    }
                )
                for call in result.tool_calls:
                    function = call.get("function") or {}
                    name = function.get("name") or ""
                    raw_arguments = function.get("arguments") or "{}"
                    if isinstance(raw_arguments, dict):
                        arguments = raw_arguments
                    else:
                        try:
                            arguments = json.loads(raw_arguments)
                        except json.JSONDecodeError:
                            arguments = {}

                    if name == "add_expense" and not confirm_write:
                        execution = {
                            "ok": False,
                            "tool": name,
                            "arguments": arguments,
                            "error": "write blocked: explicit user confirmation is required",
                            "transport": "none",
                        }
                    else:
                        execution = self.runner.run(name, arguments)
                    executions.append(execution)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.get("id", ""),
                            "name": name,
                            "content": self.runner.tool_message(execution),
                        }
                    )
                continue

            content = (result.content or "").strip()
            if content:
                return content, executions
            messages.append(
                {
                    "role": "user",
                    "content": "Please answer using the tool results above, or state exactly what data is missing.",
                }
            )
        raise LLMUnavailable("Grok returned no final answer after tool calls")

    # ------------------------------------------------------------------
    # Deterministic fallback path (also used for tests without a key)
    # ------------------------------------------------------------------
    def _rule_based(
        self, message: str, confirm_write: bool = False
    ) -> tuple[str, list[dict]]:
        text = message.strip()
        lowered = text.lower()
        month = self._detect_month(lowered)
        category = self._detect_category(text)
        is_followup = any(marker in lowered for marker in FOLLOWUP_MARKERS)
        if is_followup:
            previous = self._previous_user_message()
            if previous:
                if self._explicit_month(lowered) is None:
                    month = self._explicit_month(previous.lower()) or month
                if category is None:
                    category = self._detect_category(previous)
        executions: list[dict] = []

        def call(name: str, arguments: dict) -> dict:
            execution = self.runner.run(name, arguments)
            executions.append(execution)
            return execution

        # 1. Explicit memory statements
        is_memory_question = any(
            phrase in lowered
            for phrase in (
                "what do you remember",
                "what do you know about me",
                "my preferences",
                "who am i",
                "recall",
            )
        )
        memory_facts = self.memory.extract_facts(text)
        if memory_facts and not is_memory_question and any(
            phrase in lowered
            for phrase in (
                "remember",
                "don't forget",
                "dont forget",
                "my name is",
                "my budget",
                "i prefer",
                "i like",
                "i hate",
                "i am saving",
                "i'm saving",
                "my income",
                "my salary",
                "i live",
                "favorite category",
            )
        ):
            saved = []
            for fact in memory_facts:
                execution = call(
                    "remember_fact",
                    {
                        "key": fact["key"],
                        "value": fact["value"],
                        "category": fact["category"],
                    },
                )
                saved.append(fact)
            lines = [
                f"- **{fact['key'].replace('_', ' ')}**: {self._display_value(fact['value'])}"
                for fact in saved
            ]
            return (
                "I've saved that to long-term memory so it is available in future sessions:\n\n"
                + "\n".join(lines),
                executions,
            )

        # 2. Memory questions
        if any(
            phrase in lowered
            for phrase in (
                "what do you remember",
                "what do you know about me",
                "my preferences",
                "who am i",
                "recall",
            )
        ):
            execution = call("recall_facts", {"query": ""})
            facts = (execution.get("result") or {}).get("facts") or []
            if not facts:
                return (
                    "I don't have any saved long-term memories about you yet. "
                    "Tell me something durable, for example: \"Remember that my monthly food budget is Rs. 8,000.\"",
                    executions,
                )
            lines = [
                f"- **{fact['memory_key'].replace('_', ' ')}**: {self._display_value(fact['memory_value'])}"
                for fact in facts
            ]
            return ("Here is what I remember from earlier sessions:\n\n" + "\n".join(lines), executions)

        # 3. Add expense (write action requires confirmation)
        if "add expense" in lowered or "record expense" in lowered or "log expense" in lowered:
            amount_match = re.search(r"(?:rs\.?|pkr|₨)?\s*([\d,]+(?:\.\d+)?)", text, re.I)
            if not amount_match:
                return (
                    "Sure. What amount, category, date, and description should I record?",
                    executions,
                )
            amount = float(amount_match.group(1).replace(",", ""))
            if not confirm_write:
                return (
                    f"I can add that expense, but it is a write action. Please confirm: "
                    f"**{_money(amount)}** in **{category or 'Other'}** on **{month}-01**"
                    f" (description: \"{text}\"). Reply with \"confirm add expense\" to save it.",
                    executions,
                )
            execution = call(
                "add_expense",
                {
                    "date": f"{month}-01",
                    "amount": amount,
                    "category": category or "Other",
                    "description": text[:120],
                },
            )
            result = execution.get("result") or {}
            if result.get("ok"):
                transaction = result.get("transaction") or {}
                return (
                    f"Added your expense: {_money(transaction.get('amount', amount))} in "
                    f"{transaction.get('category', category or 'Other')} "
                    f"on {transaction.get('transaction_date', f'{month}-01')}.",
                    executions,
                )
            return (f"I couldn't add that expense: {execution.get('error') or result.get('error')}", executions)

        # 4. Comparison
        if "compare" in lowered or ("last month" in lowered and "spend" in lowered):
            explicit_months = re.findall(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", text)
            if len(explicit_months) >= 2:
                month_a = f"{explicit_months[0][0]}-{int(explicit_months[0][1]):02d}"
                month_b = f"{explicit_months[1][0]}-{int(explicit_months[1][1]):02d}"
            elif "last month" in lowered and not explicit_months:
                month_b = current_month()
                month_a = _previous_month(month_b)
            else:
                month_a = _previous_month(month)
                month_b = month
            execution = call(
                "compare_months", {"month_a": month_a, "month_b": month_b}
            )
            comparison = (execution.get("result") or {}).get("comparison") or {}
            difference = comparison.get("difference", 0)
            direction = "more" if difference >= 0 else "less"
            return (
                f"**{comparison.get('month_b')}** vs **{comparison.get('month_a')}**\n\n"
                f"- {comparison.get('month_b')}: {_money(comparison.get('total_b', 0))}\n"
                f"- {comparison.get('month_a')}: {_money(comparison.get('total_a', 0))}\n"
                f"- Difference: {_money(abs(difference))} {direction} in {comparison.get('month_b')}",
                executions,
            )

        # 5. Smart insights (Safe to Spend, forecast, subscriptions, health, goals)
        if any(
            phrase in lowered
            for phrase in ("can i afford", "afford this", "should i buy", "is it affordable")
        ):
            amount_match = re.search(r"(?:rs\.?|pkr|₨)?\s*([\d,]+(?:\.\d+)?)", text, re.I)
            if not amount_match:
                return (
                    "Tell me the purchase amount (for example \"Can I afford Rs. 4,500?\") "
                    "and I'll check it against your Safe-to-Spend amount.",
                    executions,
                )
            amount = float(amount_match.group(1).replace(",", ""))
            execution = call("can_i_afford", {"amount": amount, "month": month})
            verdict = (execution.get("result") or {}).get("verdict") or {}
            snapshot = verdict.get("snapshot") or {}
            return (
                f"{verdict.get('message', 'I could not check that purchase.')}\n\n"
                f"- Safe to spend: {_money(verdict.get('safe_to_spend', 0))}\n"
                f"- Daily allowance: {_money(snapshot.get('per_day', 0))} for "
                f"{int(snapshot.get('days_left', 0))} days\n"
                f"- Reserved for bills: {_money(snapshot.get('upcoming_commitments', 0))}",
                executions,
            )

        if any(
            phrase in lowered
            for phrase in (
                "safe to spend",
                "how much can i spend",
                "how much do i have left",
                "spending money",
                "spare money",
            )
        ):
            execution = call("get_safe_to_spend", {"month": month})
            snapshot = (execution.get("result") or {}).get("snapshot") or {}
            if not snapshot:
                return ("I could not calculate a Safe-to-Spend amount for that month.", executions)
            return (
                f"**Safe to spend in {snapshot.get('month')}: {_money(snapshot.get('safe_to_spend', 0))}** "
                f"({snapshot.get('label', '').lower()}).\n\n"
                f"- Budget: {_money(snapshot.get('budget', 0))}\n"
                f"- Spent: {_money(snapshot.get('spent', 0))}\n"
                f"- Reserved for upcoming bills: {_money(snapshot.get('upcoming_commitments', 0))}\n"
                f"- Daily allowance: {_money(snapshot.get('per_day', 0))} for "
                f"{int(snapshot.get('days_left', 0))} days",
                executions,
            )

        if any(
            phrase in lowered
            for phrase in (
                "forecast",
                "projected",
                "end of month",
                "will i overspend",
                "on track to",
            )
        ):
            execution = call("get_month_forecast", {"month": month})
            forecast = (execution.get("result") or {}).get("forecast") or {}
            if not forecast:
                return ("I could not build a forecast for that month.", executions)
            gap = forecast.get("projected_over", 0)
            position = "over" if gap > 0 else "under"
            return (
                f"**Month-end forecast: {_money(forecast.get('projected_total', 0))}** "
                f"against a {_money(forecast.get('budget', 0))} budget.\n\n"
                f"- Status: {forecast.get('label')}\n"
                f"- Current spend: {_money(forecast.get('spent', 0))}\n"
                f"- Discretionary run rate: {_money(forecast.get('daily_run_rate', 0))}/day\n"
                f"- Trend is {_money(abs(gap))} {position} budget with "
                f"{int(forecast.get('days_left', 0))} days left",
                executions,
            )

        if any(
            phrase in lowered
            for phrase in (
                "subscription",
                "recurring",
                "netflix",
                "spotify",
                "cancel",
                "monthly bills",
            )
        ):
            execution = call("list_subscriptions", {})
            summary = (execution.get("result") or {}).get("summary") or {}
            items = [item for item in summary.get("items", []) if not item.get("stale")]
            if not items:
                return (
                    "I could not detect any recurring subscriptions yet. I need at least "
                    "three months of charges with a consistent amount and cadence.",
                    executions,
                )
            lines = [
                f"- **{item['description']}** · {_money(item['monthly_cost'])}/month · "
                f"{item['cadence']} · next {item['next_due']}"
                + (" · **price hike**" if item.get("price_hike") else "")
                for item in items
            ]
            stale = summary.get("canceled") or []
            tail = (
                f"\n\nPossibly cancelled: {', '.join(item['description'] for item in stale)}."
                if stale
                else ""
            )
            return (
                f"You have **{summary.get('count', 0)} active recurring charges** costing "
                f"**{_money(summary.get('monthly_total', 0))}/month** "
                f"({_money(summary.get('annual_total', 0))}/year):\n\n"
                + "\n".join(lines)
                + tail,
                executions,
            )

        if any(
            phrase in lowered
            for phrase in (
                "financial health",
                "health score",
                "how am i doing",
                "score my finances",
                "financial wellness",
            )
        ):
            execution = call("get_financial_health", {"month": month})
            health = (execution.get("result") or {}).get("health") or {}
            if not health:
                return ("I could not calculate a financial health score.", executions)
            components = "\n".join(
                f"- {component['label']}: {component['score']:.0f}/100 — {component['detail']}"
                for component in health.get("components", [])
            )
            return (
                f"**Financial health: {health.get('score')}/100 (grade {health.get('grade')})**\n\n"
                f"{components}\n\n"
                f"**Next step:** {health.get('next_step')}",
                executions,
            )

        if any(
            phrase in lowered
            for phrase in (
                "goal",
                "saving for",
                "emergency fund",
                "savings target",
            )
        ):
            execution = call("list_goals", {})
            summary = (execution.get("result") or {}).get("summary") or {}
            goals = summary.get("goals") or []
            if not goals:
                return (
                    "You do not have any savings goals yet. A good first goal is an "
                    "emergency fund covering three to six months of essential expenses. "
                    "You can create one on the Goals page.",
                    executions,
                )
            lines = [
                f"- **{goal['name']}**: {_money(goal['saved_amount'])} of "
                f"{_money(goal['target_amount'])} ({goal['progress_percent']:.0f}%, "
                f"{goal['status'].replace('_', ' ')})"
                + (
                    f" · save {_money(goal['required_monthly'])}/month to hit the date"
                    if goal.get("required_monthly")
                    else ""
                )
                for goal in goals
            ]
            return (
                f"You have **{summary.get('count')} goals**, "
                f"{summary.get('progress_percent')}% funded overall:\n\n" + "\n".join(lines),
                executions,
            )

        if any(
            phrase in lowered
            for phrase in (
                "recap",
                "month in review",
                "how did i do",
                "summarise my month",
                "summarize my month",
            )
        ):
            execution = call("get_monthly_recap", {"month": month})
            recap = (execution.get("result") or {}).get("recap") or {}
            if not recap:
                return ("I could not build a recap for that month.", executions)
            return (
                f"**{recap.get('headline')}**\n\n"
                + "\n".join(f"- {bullet}" for bullet in recap.get("bullets", [])),
                executions,
            )

        if any(
            phrase in lowered
            for phrase in (
                "what category",
                "which category",
                "categorise",
                "categorize",
                "suggest category",
                "auto categor",
            )
        ):
            execution = call("suggest_transaction_category", {"description": text})
            suggestion = (execution.get("result") or {}).get("suggestion") or {}
            if not suggestion.get("category"):
                return (
                    "I could not match that merchant to a category yet. Save one transaction "
                    "with the right category and I will learn it for next time.",
                    executions,
                )
            return (
                f"I would file that under **{suggestion['category']}** "
                f"({float(suggestion.get('confidence', 0)) * 100:.0f}% confidence). "
                f"Reason: {suggestion.get('source')}.",
                executions,
            )

        # 6. Unusual spending
        if any(word in lowered for word in ("unusual", "anomaly", "spike", "overspend")):
            execution = call("detect_unusual_spending", {"month": month})
            flags = (execution.get("result") or {}).get("flags") or []
            if not flags:
                return (
                    f"I don't see any unusual category spending for **{month}** based on the "
                    "3-month comparison rule.",
                    executions,
                )
            lines = [f"- **{flag['category']}**: {flag['reason']}" for flag in flags]
            return (f"Unusual spending for **{month}**:\n\n" + "\n".join(lines), executions)

        # 7. Budget questions
        if any(word in lowered for word in ("budget", "remaining", "left", "on track")):
            arguments = {"month": month}
            if category:
                arguments["category"] = category
            execution = call("get_budget_status", arguments)
            status = (execution.get("result") or {}).get("status") or {}
            if category:
                if status.get("budget") is None:
                    return (
                        f"I don't have a budget set for **{category}** in **{month}**. "
                        "You can set one on the Budgets page.",
                        executions,
                    )
                return (
                    f"For **{category}** in **{month}**: budget {_money(status['budget'])}, "
                    f"spent {_money(status['spent'])}, remaining {_money(status['remaining'])}.",
                    executions,
                )
            monthly_budget = status.get("monthly_budget")
            if monthly_budget is None:
                return (
                    f"I don't see a monthly budget for **{month}**. Set one on the Budgets page "
                    "and I can track it for you.",
                    executions,
                )
            return (
                f"Your **{month}** monthly budget is {_money(monthly_budget)}. "
                f"You have spent {_money(status.get('monthly_spent', 0))} and have "
                f"{_money(status.get('monthly_remaining', 0))} remaining.",
                executions,
            )

        # 8. List transactions
        if any(word in lowered for word in ("show", "list", "recent", "transactions", "ledger")):
            arguments = {"month": month, "limit": 10}
            if category:
                arguments["category"] = category
            execution = call("list_transactions", arguments)
            rows = (execution.get("result") or {}).get("transactions") or []
            if not rows:
                return (f"I couldn't find any transactions for **{month}**" + (f" in **{category}**" if category else "") + ".", executions)
            lines = [
                f"- {row['transaction_date']} · {row['description']} · {row['category']} · {_money(row['amount'])}"
                for row in rows
            ]
            return (f"Recent transactions for **{month}**:\n\n" + "\n".join(lines), executions)

        # 9. Spending totals / category questions
        if any(word in lowered for word in ("spend", "spent", "total", "how much", "cost")) or (
            is_followup and (category or self._explicit_month(lowered))
        ):
            execution = call("get_spending_summary", {"month": month})
            summary = execution.get("result") or {}
            breakdown = summary.get("by_category") or {}
            if category:
                amount = breakdown.get(category, 0)
                return (
                    f"You spent {_money(amount)} on **{category}** in **{month}**.",
                    executions,
                )
            if not breakdown:
                return (f"I don't see any transactions for **{month}** yet.", executions)
            top = sorted(breakdown.items(), key=lambda pair: pair[1], reverse=True)
            lines = [f"- {name}: {_money(amount)}" for name, amount in top[:5]]
            return (
                f"You spent **{_money(summary.get('total', 0))}** in **{month}** across "
                f"{len(breakdown)} categories.\n\nTop categories:\n" + "\n".join(lines),
                executions,
            )

        # 10. General guidance (RAG)
        if any(
            word in lowered
            for word in (
                "save",
                "saving",
                "tip",
                "advice",
                "emergency",
                "debt",
                "50/30/20",
                "rule",
                "how should",
                "how can i",
            )
        ):
            execution = call("search_financial_guidance", {"query": text, "top_k": 3})
            results = (execution.get("result") or {}).get("results") or []
            if results:
                lines = [
                    f"- {result['text']} _(source: {result['source']})_"
                    for result in results
                ]
                return ("Here is grounded guidance from the knowledge base:\n\n" + "\n".join(lines), executions)
            execution = call("get_budgeting_rules", {})
            rules = (execution.get("result") or {}).get("rules") or []
            return ("Here are the built-in budgeting rules:\n\n" + "\n".join(f"- {rule}" for rule in rules), executions)

        # 11. Greetings and everything else
        if any(greeting in lowered for greeting in ("hello", "hi", "hey", "salam", "assalam")):
            return (
                "Hi! I'm Paisa, your expense agent. I can check spending, compare months, "
                "track budgets, flag unusual activity, and retrieve saving guidance. "
                "Try: \"How much did I spend on food this month?\"",
                executions,
            )

        execution = call("search_financial_guidance", {"query": text, "top_k": 3})
        results = (execution.get("result") or {}).get("results") or []
        if results:
            lines = [f"- {result['text']} _(source: {result['source']})_" for result in results]
            return (
                "I couldn't map that to a specific expense question, but here is relevant "
                "guidance from the knowledge base:\n\n" + "\n".join(lines),
                executions,
            )
        return (
            "I can help with spending totals, budgets, transaction lists, month comparisons, "
            "unusual activity, and general saving guidance. Which would you like?",
            executions,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _display_value(value: str) -> str:
        text = str(value or "")
        if re.fullmatch(r"\d+(?:\.\d+)?", text):
            number = float(text)
            return f"{number:,.0f}" if number.is_integer() else f"{number:,.2f}"
        return text

    def _previous_user_message(self) -> str:
        history = self.memory.history(self.session_id, limit=10)
        user_messages = [
            message["content"] for message in history if message.get("role") == "user"
        ]
        # The current turn is already persisted, so the previous turn is [-2].
        return user_messages[-2] if len(user_messages) >= 2 else ""

    def _explicit_month(self, text: str) -> str | None:
        if "last month" in text or "previous month" in text:
            return _previous_month(current_month())
        match = re.search(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", text)
        if match:
            return f"{match.group(1)}-{int(match.group(2)):02d}"
        for name, number in MONTH_NAMES.items():
            if re.search(rf"\b{name}\b", text):
                year_match = re.search(r"\b(20\d{2})\b", text)
                year = int(year_match.group(1)) if year_match else date.today().year
                return f"{year}-{number:02d}"
        return None

    def _detect_month(self, text: str) -> str:
        return self._explicit_month(text) or current_month()

    def _detect_category(self, text: str) -> str | None:
        known = {name.lower(): name for name in list_categories(self.db_path)}
        lowered = text.lower()
        for name, original in known.items():
            if name in lowered:
                return original
        for synonym, candidates in CATEGORY_SYNONYMS.items():
            if re.search(rf"\b{re.escape(synonym)}\b", lowered):
                for candidate in candidates:
                    if candidate.lower() in known:
                        return known[candidate.lower()]
                return candidates[0]
        return None

    def _sources_from_executions(self, executions: list[dict]) -> list[dict]:
        sources: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for execution in executions:
            result = execution.get("result")
            if not isinstance(result, dict):
                continue
            for passage in result.get("results") or []:
                title = passage.get("source") or "Knowledge base"
                excerpt = (passage.get("text") or "")[:500]
                key = (title, excerpt)
                if key not in seen:
                    seen.add(key)
                    sources.append(
                        {
                            "title": title,
                            "excerpt": excerpt,
                            "score": passage.get("score"),
                            "tool": execution.get("tool"),
                        }
                    )
            if execution.get("tool") == "recall_facts":
                sources.append(
                    {
                        "title": "Long-term memory",
                        "excerpt": "Facts saved in the agent_memory table and retrieved for this session.",
                        "tool": "recall_facts",
                    }
                )
            if execution.get("tool") in {
                "get_spending_summary",
                "get_budget_status",
                "list_transactions",
                "compare_months",
                "detect_unusual_spending",
                "get_safe_to_spend",
                "can_i_afford",
                "get_month_forecast",
                "list_subscriptions",
                "get_financial_health",
                "get_monthly_recap",
                "list_goals",
                "suggest_transaction_category",
            }:
                sources.append(
                    {
                        "title": "Expense database",
                        "excerpt": f"Query result from {execution['tool']} over the SQLite expense database.",
                        "tool": execution.get("tool"),
                    }
                )
        return sources[:8]
