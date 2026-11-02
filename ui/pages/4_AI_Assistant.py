"""AI assistant chat with visible tool, source, memory, and MCP evidence."""

from __future__ import annotations

import uuid

import streamlit as st

from ui.agent_bridge import ask_agent, get_agent
from ui.components import page_header, source_citation, tool_tag

page_header(
    "AI Assistant",
    "Ask natural-language questions grounded in your expense data, budgets, and knowledge base.",
    "AGENT WORKSPACE",
)

if "agent_session_id" not in st.session_state:
    st.session_state.agent_session_id = f"sess_{uuid.uuid4().hex[:12]}"

session_id = st.session_state.agent_session_id
agent = get_agent(session_id=session_id)
status = agent.status()
llm_status = status["llm"]
tool_status = status["tools"]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "answer": (
                "Hi! I’m **Paisa**, your expense agent. I can check spending, compare months, "
                "track budgets, flag unusual activity, retrieve saving guidance, and remember "
                "durable preferences across sessions."
            ),
            "tools_used": [],
            "sources": [],
            "memory_used": [],
            "transport": "none",
        }
    ]

# ---------------------------------------------------------------------------
# Session + status controls
# ---------------------------------------------------------------------------
control_left, control_mid, control_right = st.columns([1.2, 2.2, 1])
with control_left:
    if st.button("＋ New session", width="stretch"):
        st.session_state.agent_session_id = f"sess_{uuid.uuid4().hex[:12]}"
        st.session_state.chat_history = []
        st.rerun()
with control_mid:
    if llm_status["available"]:
        st.success(
            f"Grok connected · {llm_status['model']} · key from `{llm_status['key_source']}`",
            icon="✅",
        )
    else:
        st.warning(
            "No Grok API key found. The deterministic grounded fallback is active. "
            "Add `grok_api_key.txt` in the project root (or set `GROK_API_KEY`) to enable Grok.",
            icon="🔑",
        )
with control_right:
    st.caption(f"Session `{session_id}`")
    st.caption(f"Long-term memories: {status['long_term_memories']}")

with st.expander("Agent architecture and tool status", expanded=False):
    st.markdown(
        f"""
- **LLM:** {llm_status['provider']} · `{llm_status['model']}` · available: `{llm_status['available']}`
- **Short-term memory:** SQLite transcript for this session (`agent_messages`)
- **Long-term memory:** SQLite facts (`agent_memory`) · {status['long_term_memories']} saved
- **RAG:** vector index over 6 financial-guidance documents
- **MCP:** {"enabled" if tool_status["mcp"]["enabled"] else "disabled"} · server `{tool_status["mcp"]["server"]}`
- **Tools:** {", ".join(tool_status["available_tools"])}
        """
    )
    if llm_status.get("last_error"):
        st.caption(f"Last LLM error: {llm_status['last_error']}")

with st.expander("Long-term memory (persists across sessions)", expanded=False):
    facts = agent.memory.all_facts(limit=50)
    if facts:
        st.dataframe(
            [
                {
                    "Key": fact["memory_key"],
                    "Value": fact["memory_value"],
                    "Category": fact["category"],
                    "Updated": fact["updated_at"],
                }
                for fact in facts
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.caption("No durable facts yet. Try: “Remember that my monthly food budget is Rs. 8,000.”")
    if facts and st.button("Clear long-term memory", type="secondary"):
        agent.memory.clear_long_term()
        st.success("Long-term memory cleared.")
        st.rerun()

allow_writes = st.toggle(
    "Allow confirmed write actions (add an expense)",
    value=False,
    help="Read-only by default. The agent only writes after you enable this and explicitly confirm the details.",
)

st.caption("● Agent ready · Synthetic demo data only · Short-term + long-term memory enabled")

# ---------------------------------------------------------------------------
# Starter prompts
# ---------------------------------------------------------------------------
st.markdown("**Try asking**")
suggestions = [
    "How much did I spend this month?",
    "How much budget is left for food?",
    "My monthly food budget is Rs. 8,000 — remember that.",
    "What do you remember about me?",
]
prompt_columns = st.columns(4)
selected_prompt = None
for column, suggestion in zip(prompt_columns, suggestions):
    with column:
        if st.button(suggestion, width="stretch"):
            selected_prompt = suggestion

# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------
for message in st.session_state.chat_history:
    role = message.get("role", "assistant")
    with st.chat_message(role):
        st.markdown(message.get("answer", ""))
        tools = message.get("tools_used", [])
        if tools:
            for tool in tools:
                tool_tag(tool)
            transport = message.get("transport", "none")
            if transport in {"mcp", "mixed"}:
                st.caption("🔌 Executed through the MCP client → MCP server")
            elif transport == "local":
                st.caption("🧩 Executed through the local fallback (MCP unavailable)")
        if message.get("memory_used"):
            with st.expander(f"Long-term memory used ({len(message['memory_used'])})"):
                for fact in message["memory_used"]:
                    st.markdown(f"- **{fact['memory_key']}**: {fact['memory_value']}")
        if message.get("sources"):
            st.markdown("##### Sources")
            for index, source in enumerate(message["sources"], start=1):
                source_citation(source, index)
        if message.get("llm_error"):
            st.caption(f"LLM note: {message['llm_error']}")

typed_prompt = st.chat_input("Ask about your spending, budgets, or saving goals...")
prompt = selected_prompt or typed_prompt
if prompt:
    st.session_state.chat_history.append(
        {
            "role": "user",
            "answer": prompt,
            "tools_used": [],
            "sources": [],
        }
    )
    response = ask_agent(
        prompt,
        session_id=st.session_state.agent_session_id,
        confirm_write=allow_writes,
    )
    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "answer": response.get("answer", ""),
            "tools_used": response.get("tools_used", []),
            "sources": response.get("sources", []),
            "memory_used": response.get("memory_used", []),
            "transport": response.get("transport", "none"),
            "llm_used": response.get("llm_used", False),
            "llm_error": response.get("llm_error"),
        }
    )
    st.rerun()
