"""End-to-end CLI demonstration of the Assignment 2 agent.

Run from the project root:

    python scripts/demo_agent.py

It seeds synthetic data, builds the RAG index on first use, runs a multi-turn
conversation, then starts a brand-new session to prove long-term memory.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent.agent import ExpenseAgent
from agent.memory import MemoryStore
from database.connection import get_connection
from database.seed import seed_database
from rag.retriever import ensure_index


def show(label: str, response: dict) -> None:
    print("\n" + "=" * 78)
    print(label)
    print("-" * 78)
    print(response["answer"])
    print("-" * 78)
    print(f"LLM used     : {response['llm_used']} ({response.get('llm_model') or 'fallback'})")
    if response.get("llm_error"):
        print(f"LLM note     : {response['llm_error']}")
    print(f"Tools used   : {', '.join(response['tools_used']) or '(none)'}")
    print(f"Transport    : {response['transport']}")
    print(f"Sources      : {', '.join(source['title'] for source in response['sources']) or '(none)'}")
    print(f"Memory used  : {len(response.get('memory_used') or [])} durable fact(s)")


def main() -> None:
    print("Seeding synthetic demo data...")
    seed_database()
    print("Building/checking RAG index...")
    print("Index:", ensure_index())

    user_id = "demo_user"
    memory = MemoryStore(user_id=user_id)
    memory.clear_long_term()  # make the demo deterministic

    agent = ExpenseAgent(user_id=user_id)
    print(f"\nSession 1: {agent.session_id}")
    print(f"LLM status: {agent.status()['llm']}")
    print(f"MCP status: {agent.status()['tools']['mcp']}")

    show("TURN 1 — spending question", agent.ask("How much did I spend last month?"))
    show(
        "TURN 2 — elliptical follow-up in the same session",
        agent.ask("What about food?"),
    )
    show(
        "TURN 3 — write a durable memory",
        agent.ask("My monthly food budget is Rs. 8,000 — remember that."),
    )

    old_session = agent.session_id
    new_session = agent.new_session()
    print("\n" + "#" * 78)
    print(f"NEW SESSION: {old_session}  ->  {new_session}")
    print("Short-term history is empty; long-term memory must still be available.")
    print("#" * 78)

    show(
        "TURN 4 — recall in a brand-new session",
        agent.ask("What do you remember about me?"),
    )
    show("TURN 5 — RAG guidance", agent.ask("Give me a tip to save more."))
    show("TURN 6 — month comparison", agent.ask("How much did I spend last month?"))

    print("\n" + "=" * 78)
    print("LONG-TERM MEMORY ROWS")
    for fact in memory.all_facts():
        print(f"  - {fact['memory_key']}: {fact['memory_value']} ({fact['category']})")

    with get_connection() as connection:
        audit = connection.execute(
            "SELECT tool_name, transport, created_at FROM agent_tool_calls ORDER BY id DESC LIMIT 12"
        ).fetchall()
    print("\nTOOL AUDIT (latest 12)")
    for row in audit:
        print(f"  - {row['tool_name']:<28} {row['transport']:<6} {row['created_at']}")
    print("\nDone. Open the Streamlit app for the same flow with a UI.")


if __name__ == "__main__":
    main()
