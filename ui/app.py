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
    st.markdown(
        """
        <div style='min-height:70vh;display:flex;align-items:center;justify-content:center;'>
        <div style='max-width:420px;width:100%;background:#111A2E;border:1px solid #1E2A44;border-radius:1rem;padding:2rem;box-shadow:0 12px 30px rgba(0,0,0,.25);'>
        <div style='text-align:center;margin-bottom:1.5rem;'>
            <div style='width:44px;height:44px;margin:0 auto .75rem;border-radius:12px;background:#2F6BFF;display:grid;place-items:center;color:#fff;font-weight:800;'>E</div>
            <h2 style='margin:0;color:#E6EAF2;'>Expense Tracker</h2>
            <p style='margin:.25rem 0 0;color:#8A94A8;font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;'>AI AGENT · AIDE3313</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        st.text_input("Email", key="login_email")
        st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Sign in", width="stretch")
        if submitted:
            username = st.session_state.get("login_email", "")
            password = st.session_state.get("login_password", "")
            user = authenticate(username, password)
            if user:
                st.session_state.user_id = user["id"]
                st.session_state.username = user["username"]
                st.session_state.display_name = user["display_name"]
                st.rerun()
            else:
                st.error("Invalid username or password.")
    with st.expander("Create account"):
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
    st.markdown(
        "<p style='text-align:center;color:#8A94A8;font-size:.75rem;margin-top:1rem;'>This is synthetic demo data only.</p></div></div>",
        unsafe_allow_html=True,
    )
    st.stop()
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
