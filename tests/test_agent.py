from datetime import date, timedelta

import pytest

from agent.agent import ExpenseAgent
from agent.llm import GrokLLM
from agent.memory import MemoryStore, new_session_id
from agent.prompts import build_system_prompt
from agent.tools import ToolRunner, current_month
from database.connection import get_connection, initialize_database
from expense.budgets import set_budget
from expense.transactions import add_transaction


class NoLLM(GrokLLM):
    """Deterministic LLM stub: forces the grounded fallback path."""

    def __init__(self):
        super().__init__(api_key="not-a-real-key")
        self.api_key = ""

    @property
    def available(self) -> bool:
        return False

    def status(self) -> dict:
        return {
            "available": False,
            "provider": "Local fallback",
            "model": "rules",
            "base_url": "",
            "key_source": "test",
            "last_error": None,
        }


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "agent-test.db"
    initialize_database(path)
    with get_connection(path) as connection:
        connection.executemany(
            "INSERT INTO categories(name) VALUES (?)",
            [("Food & dining",), ("Transport",)],
        )
    add_transaction(
        "Lunch", 1500, "Food & dining", date.today().replace(day=2).isoformat(), db_path=path
    )
    add_transaction(
        "Bus", 300, "Transport", date.today().replace(day=3).isoformat(), db_path=path
    )
    previous_month = date.today().replace(day=1) - timedelta(days=1)
    add_transaction(
        "October dinner", 900, "Food & dining", previous_month.isoformat(), db_path=path
    )
    set_budget(current_month(), 5000, db_path=path)
    set_budget(current_month(), 2000, "Food & dining", db_path=path)
    return path


def make_agent(db, user_id="test_user", session_id=None):
    return ExpenseAgent(
        user_id=user_id,
        session_id=session_id or new_session_id(),
        use_mcp=False,
        llm=NoLLM(),
        db_path=db,
    )


def test_prompt_contains_required_sections():
    prompt = build_system_prompt(
        current_month="2026-11",
        user_id="demo",
        memory_context="- budget_food: 8000",
        tool_names=["get_spending_summary", "search_financial_guidance"],
    )
    for phrase in (
        "Tool-selection rules",
        "Short-term memory",
        "long-term memory",
        "Sources",
        "uncertain",
        "add_expense",
    ):
        assert phrase.lower() in prompt.lower()


def test_short_term_memory_is_persisted(db):
    memory = MemoryStore(user_id="u1", db_path=db)
    session = "sess_test"
    memory.add_message(session, "user", "How much did I spend?")
    memory.add_message(session, "assistant", "You spent Rs. 1,800.")
    history = MemoryStore(user_id="u1", db_path=db).history_for_llm(session)
    assert [item["role"] for item in history] == ["user", "assistant"]
    assert "1,800" in history[1]["content"]


def test_long_term_memory_survives_new_session(db):
    first = MemoryStore(user_id="u2", db_path=db)
    first.remember("budget_food", "8000", category="budget", importance=5)
    second = MemoryStore(user_id="u2", db_path=db)
    facts = second.recall("budget")
    assert facts
    assert facts[0]["memory_value"] == "8000"
    assert "budget_food" in second.format_for_prompt()


def test_rule_extraction(db):
    memory = MemoryStore(user_id="u3", db_path=db)
    facts = memory.extract_facts("My name is Maria and my monthly food budget is Rs. 8,000.")
    keys = {fact["key"] for fact in facts}
    assert "name" in keys
    assert "budget_food" in keys
    memory.save_extracted_facts("Remember that I hate subscriptions.")
    assert memory.recall("subscriptions")


def test_agent_fallback_spending_and_followup(db):
    agent = make_agent(db)
    first = agent.ask("How much did I spend this month?")
    assert "Rs." in first["answer"]
    assert "get_spending_summary" in first["tools_used"]
    assert first["llm_used"] is False
    assert first["transport"] == "local"

    second = agent.ask("How much budget is left for food?")
    assert "remaining" in second["answer"].lower() or "budget" in second["answer"].lower()
    assert "get_budget_status" in second["tools_used"]
    # The follow-up ran in the same session, so short-term history has both turns.
    assert len(agent.memory.history(agent.session_id)) == 4


def test_fallback_elliptical_followup_uses_short_term_memory(db):
    agent = make_agent(db)
    previous_month = (date.today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    first = agent.ask(f"How much did I spend in {previous_month}?")
    assert previous_month in first["answer"]
    assert "900" in first["answer"]

    followup = agent.ask("What about food?")
    assert previous_month in followup["answer"]
    assert "Food & dining" in followup["answer"]
    assert followup["tools_used"] == ["get_spending_summary"]


def test_agent_remembers_across_sessions(db):
    first_session = make_agent(db, user_id="maria")
    response = first_session.ask("My monthly food budget is Rs. 8,000 — remember that.")
    assert "saved" in response["answer"].lower()
    assert "remember_fact" in response["tools_used"]

    # Brand-new agent + brand-new session, same user id.
    second_session = make_agent(db, user_id="maria")
    recall = second_session.ask("What do you remember about me?")
    assert "8,000" in recall["answer"]
    assert "recall_facts" in recall["tools_used"]


def test_agent_no_data_month_is_honest(db):
    agent = make_agent(db)
    response = agent.ask("How much did I spend in 2020-01?")
    assert "don't see any transactions" in response["answer"].lower()


def test_tool_runner_local(db):
    runner = ToolRunner(session_id="tool-test", memory=MemoryStore(user_id="u4", db_path=db), prefer_mcp=False)
    result = runner.run("get_spending_summary", {"month": current_month()})
    assert result["ok"] is True
    assert result["transport"] == "local"
    assert result["result"]["total"] == 1800.0

    memory_result = runner.run("remember_fact", {"key": "goal", "value": "save 50000"})
    assert memory_result["ok"] is True
    recalled = runner.run("recall_facts", {"query": "goal"})
    assert recalled["result"]["count"] >= 1


def test_mcp_client_round_trip():
    pytest.importorskip("mcp")
    from agent.mcp_client import MCPToolClient

    client = MCPToolClient()
    if not client.enabled:
        pytest.skip("MCP server dependency unavailable")
    tools = client.list_tools()
    assert "health_check" in tools
    result = client.call_tool("health_check", {})
    assert result["ok"] is True
    assert result["result"]["status"] == "ok"
