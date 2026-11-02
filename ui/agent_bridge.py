"""Stable UI bridge for the Personal Expense Management Agent.

The Streamlit page only knows this contract.  The real agent (Grok + memory +
RAG + MCP) lives in the ``agent`` package.
"""

from __future__ import annotations

from typing import TypedDict

from agent.agent import ExpenseAgent
from agent.memory import new_session_id

DEFAULT_USER_ID = "demo_user"
_AGENTS: dict[tuple[str, str], ExpenseAgent] = {}


class AgentResponse(TypedDict):
    answer: str
    tools_used: list[str]
    sources: list[dict]


def get_agent(
    session_id: str | None = None,
    user_id: str = DEFAULT_USER_ID,
) -> ExpenseAgent:
    session_id = session_id or new_session_id()
    key = (user_id, session_id)
    if key not in _AGENTS:
        _AGENTS[key] = ExpenseAgent(user_id=user_id, session_id=session_id)
    return _AGENTS[key]


def reset_agent_cache() -> None:
    _AGENTS.clear()


def ask_agent(
    message: str,
    session_id: str,
    user_id: str = DEFAULT_USER_ID,
    confirm_write: bool = False,
) -> dict:
    """Ask the agent and return a UI-friendly response.

    Never raises for expected agent/tool failures; the page always gets a
    message it can render.
    """
    if not (message or "").strip():
        raise ValueError("Please enter a question.")
    try:
        agent = get_agent(session_id=session_id, user_id=user_id)
        response = agent.ask(message, confirm_write=confirm_write)
        return {
            **response,
            "tools_used": response.get("tools_used", []),
            "sources": response.get("sources", []),
        }
    except Exception as exc:  # defensive: keep the chat usable
        return {
            "answer": (
                "I’m sorry, the expense agent hit an unexpected error. "
                f"Details: `{type(exc).__name__}: {exc}`. Your data is safe — please try again."
            ),
            "tools_used": [],
            "sources": [],
            "memory_used": [],
            "llm_used": False,
            "llm_error": str(exc),
            "transport": "none",
            "session_id": session_id,
        }
