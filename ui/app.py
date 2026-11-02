"""Expense Tracker AI Agent entry point."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auth import authenticate, create_user, ensure_default_user
from database.connection import get_connection, initialize_database
from database.seed import seed_database
from ui.theme import inject_theme

st.set_page_config(
    page_title="Expense Tracker AI Agent",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None

seed_database()
ensure_default_user()

# ---------------------------------------------------------------------------
# Login gate
# ---------------------------------------------------------------------------
if st.session_state.user_id is None:
    st.title("Sign in to Expense Tracker")
    st.caption("Track your expenses, budgets, and goals per account.")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Log in")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", width="stretch")
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state.user_id = user["id"]
                    st.session_state.username = user["username"]
                    st.session_state.display_name = user["display_name"]
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    with col2:
        st.subheader("Create account")
        with st.form("register_form"):
            new_username = st.text_input("New username")
            new_password = st.text_input("New password", type="password")
            new_display = st.text_input("Display name (optional)")
            registered = st.form_submit_button("Create account", width="stretch")
            if registered:
                try:
                    uid = create_user(new_username, new_password, new_display)
                    st.session_state.user_id = uid
                    st.session_state.username = new_username.strip().lower()
                    st.session_state.display_name = new_display.strip() or new_username
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    st.caption("Demo account: username `demo`, password `demo`.")
    st.stop()

# ---------------------------------------------------------------------------
# Authenticated app
# ---------------------------------------------------------------------------
display_name = st.session_state.get("display_name") or st.session_state.username

with st.sidebar:
    st.markdown("## ◉ Expense Tracker")
    st.caption(f"{display_name} · AI AGENT")
    st.markdown("---")
    st.html("<div style='height:calc(100vh - 19rem)'></div>")
    if st.button("↪ Log out", width="stretch"):
        st.session_state.clear()
        st.rerun()

navigation = st.navigation(
    [
        st.Page("pages/1_Dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
        st.Page("pages/2_Transactions.py", title="Transactions", icon=":material/receipt_long:"),
        st.Page("pages/3_Budgets.py", title="Budgets", icon=":material/account_balance_wallet:"),
        st.Page("pages/7_Insights.py", title="Smart Insights", icon=":material/insights:"),
        st.Page("pages/8_Goals.py", title="Goals", icon=":material/flag:"),
        st.Page("pages/4_AI_Assistant.py", title="AI Assistant", icon=":material/auto_awesome:"),
        st.Page("pages/6_Memory.py", title="Agent Memory", icon=":material/psychology:"),
        st.Page("pages/5_Settings.py", title="Settings", icon=":material/settings:"),
    ]
)
navigation.run()
