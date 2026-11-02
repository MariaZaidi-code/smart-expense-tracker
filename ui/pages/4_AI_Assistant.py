"""AI assistant chat with visible tool and source evidence."""

from __future__ import annotations

import uuid

import streamlit as st

from ui.agent_bridge import ask_agent
from ui.components import page_header, source_citation, tool_tag

page_header(
    "AI Assistant",
    "Ask natural-language questions grounded in your expense and budget data.",
    "AGENT WORKSPACE",
)

if "agent_session_id" not in st.session_state:
    st.session_state.agent_session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "answer": (
                "Hi Rameen. I can check spending, compare budgets, and retrieve "
                "general saving guidance. What would you like to know?"
            ),
            "tools_used": [],
            "sources": [],
        }
    ]

st.caption("● Agent ready · Synthetic demo data only · Session memory enabled")

st.markdown("**Try asking**")
prompt_columns = st.columns(3)
suggestions = [
    "How much did I spend on food this month?",
    "How much budget is left?",
    "Give me a tip to save more",
]
selected_prompt = None
for column, suggestion in zip(prompt_columns, suggestions):
    with column:
        if st.button(suggestion, width="stretch"):
            selected_prompt = suggestion

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["answer"])
        for tool in message.get("tools_used", []):
            tool_tag(tool)
        if message.get("sources"):
            st.markdown("##### Sources")
            for index, source in enumerate(message["sources"], start=1):
                source_citation(source, index)

typed_prompt = st.chat_input("Ask about your spending...")
prompt = selected_prompt or typed_prompt
if prompt:
    st.session_state.chat_history.append(
        {"role": "user", "answer": prompt, "tools_used": [], "sources": []}
    )
    try:
        response = ask_agent(prompt, st.session_state.agent_session_id)
    except Exception:
        response = {
            "answer": (
                "I’m sorry, the expense agent is temporarily unavailable. "
                "Your app and data are still safe—please try again in a moment."
            ),
            "tools_used": [],
            "sources": [],
        }
    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "answer": response["answer"],
            "tools_used": response.get("tools_used", []),
            "sources": response.get("sources", []),
        }
    )
    st.rerun()
