"""Inspect the agent's short-term and long-term memory stores."""

from __future__ import annotations

import streamlit as st

from agent.memory import DEFAULT_USER_ID, MemoryStore
from ui.components import empty_state, page_header

page_header(
    "Agent Memory",
    "See exactly what the assistant remembers and how long each memory lives.",
    "ASSIGNMENT EVIDENCE",
)

memory = MemoryStore(user_id=DEFAULT_USER_ID)

st.markdown(
    """
**Short-term memory** is the transcript of one chat session (`agent_messages`).
It lets the agent resolve follow-ups such as “what about last month?”.

**Long-term memory** is a durable key/value store (`agent_memory`) that is
retrieved by user id in a brand-new session. It is intentionally separate from
the RAG knowledge base: RAG documents are shared financial guidance, while
long-term memory is user-specific context.
"""
)

long_term_tab, short_term_tab = st.tabs(["Long-term memory", "Session transcripts"])

with long_term_tab:
    facts = memory.all_facts(limit=100)
    if facts:
        st.dataframe(
            [
                {
                    "Key": fact["memory_key"],
                    "Value": fact["memory_value"],
                    "Category": fact["category"],
                    "Importance": fact["importance"],
                    "Updated": fact["updated_at"],
                }
                for fact in facts
            ],
            width="stretch",
            hide_index=True,
        )
        selected = st.selectbox(
            "Delete a memory",
            [fact["memory_key"] for fact in facts],
            format_func=lambda key: next(
                f"{fact['memory_key']} — {fact['memory_value']}" for fact in facts if fact["memory_key"] == key
            ),
        )
        if st.button("Delete selected memory"):
            memory.forget(selected)
            st.success(f"Deleted `{selected}`.")
            st.rerun()
    else:
        empty_state("No long-term memories", "Add one below or tell the AI Assistant to remember a fact.")

    with st.form("add_memory_form", border=True):
        st.markdown("#### Add a durable fact")
        key = st.text_input("Key", placeholder="monthly_food_budget")
        value = st.text_input("Value", placeholder="8000")
        category = st.selectbox("Category", ["preference", "goal", "profile", "budget", "note", "fact"])
        if st.form_submit_button("Save memory", width="stretch"):
            try:
                memory.remember(key, value, category=category)
                st.success("Memory saved. Start a new chat session to prove it persists.")
                st.rerun()
            except ValueError as error:
                st.error(str(error), icon="⚠️")

with short_term_tab:
    sessions = memory.sessions()
    if not sessions:
        empty_state("No sessions yet", "Open the AI Assistant and ask a question to create a transcript.")
    else:
        st.dataframe(
            [
                {
                    "Session": session["session_id"],
                    "Messages": session["messages"],
                    "Started": session["started"],
                    "Last message": session["last_message"],
                }
                for session in sessions
            ],
            width="stretch",
            hide_index=True,
        )
        selected_session = st.selectbox(
            "View transcript",
            [session["session_id"] for session in sessions],
        )
        transcript = memory.history(selected_session, limit=100)
        for message in transcript:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("tools_used"):
                    st.caption("Tools: " + ", ".join(message["tools_used"]))
