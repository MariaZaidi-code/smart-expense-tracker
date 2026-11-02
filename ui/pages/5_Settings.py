"""Application preferences and demo diagnostics."""

from pathlib import Path

import streamlit as st

from agent.llm import KEY_FILE_CANDIDATES, GrokLLM
from database.connection import get_db_path
from database.seed import seed_database
from rag.retriever import build_index
from ui.components import page_header

page_header(
    "Settings",
    "Manage display, demo data, and the agent's runtime configuration.",
    "PREFERENCES",
)

with st.container(border=True):
    st.markdown("### Display")
    st.selectbox("Currency", ["Pakistani Rupees (Rs.)"], disabled=True)
    st.toggle("Compact transaction rows", value=False)
    st.toggle("Show synthetic-data reminder", value=True)

with st.container(border=True):
    st.markdown("### Agent configuration")
    llm = GrokLLM()
    status = llm.status()
    st.markdown(f"**LLM:** {status['provider']} · `{status['model']}`")
    st.markdown(f"**Key source:** `{status['key_source']}`")
    st.markdown(f"**Key files checked:** " + ", ".join(f"`{path.name}`" for path in KEY_FILE_CANDIDATES))
    if status["available"]:
        st.success("Grok key detected. The agent will use the live LLM.")
    else:
        st.warning(
            "No Grok key detected. Add `grok_api_key.txt` in the project root with your "
            "`xai-...` key, or set `GROK_API_KEY`. The deterministic fallback is active."
        )
    st.caption(f"Expense database: `{get_db_path()}`")
    st.caption("MCP is enabled by default (`MCP_ENABLED=0` disables it).")

with st.container(border=True):
    st.markdown("### Demo data and RAG index")
    st.caption(
        "This assignment uses synthetic transactions only. No bank account or "
        "real financial credential is connected."
    )
    left, right = st.columns(2)
    with left:
        if st.button("Reset demo transactions", width="stretch"):
            seed_database(reset=True)
            st.success("Synthetic demo data reset.")
            st.rerun()
    with right:
        if st.button("Rebuild RAG index", width="stretch"):
            with st.spinner("Indexing knowledge documents..."):
                info = build_index()
            st.success(f"Indexed {info['documents']} documents into {info['chunks']} chunks.")
    st.button("Reset demo preferences")
