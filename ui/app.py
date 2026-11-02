"""Expense Tracker AI Agent entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.seed import seed_database
from ui.theme import inject_theme

st.set_page_config(
    page_title="Expense Tracker AI Agent",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

seed_database()
inject_theme()

with st.sidebar:
    st.markdown("## ◉ Expense Tracker")
    st.caption("AI AGENT · AIDE3313")
    st.markdown("---")
    st.markdown("<div style='height:calc(100vh - 19rem)'></div>", unsafe_allow_html=True)
    if st.button("↪ Log out", width="stretch"):
        st.session_state.clear()
        st.toast("Session cleared. You are now logged out.")

navigation = st.navigation(
    [
        st.Page("pages/1_Dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
        st.Page("pages/2_Transactions.py", title="Transactions", icon=":material/receipt_long:"),
        st.Page("pages/3_Budgets.py", title="Budgets", icon=":material/account_balance_wallet:"),
        st.Page("pages/4_AI_Assistant.py", title="AI Assistant", icon=":material/auto_awesome:"),
        st.Page("pages/5_Settings.py", title="Settings", icon=":material/settings:"),
    ]
)
navigation.run()
