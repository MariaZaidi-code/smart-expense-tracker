"""Shared dark-navy design tokens for the Streamlit UI."""

from __future__ import annotations

import streamlit as st

BG_BASE = "#0A0F1E"
SIDEBAR = "#0D1324"
CARD = "#111A2E"
CARD_BORDER = "#1E2A44"
PRIMARY = "#2F6BFF"
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
DANGER = "#EF4444"
TEXT_MAIN = "#E6EAF2"
TEXT_MUTED = "#8A94A8"
MUTED = TEXT_MUTED
OVER_BUDGET = DANGER
PRIMARY_FADE = "rgba(47,107,255,0.16)"
GRID = "rgba(30,42,68,0.7)"

CHART_COLORS = [PRIMARY, "#F59E0B", "#22C55E", "#8A94A8", "#1E2A44", "#0D1324"]


def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {{
            --bg-base: {BG_BASE};
            --sidebar: {SIDEBAR};
            --card: {CARD};
            --border: {CARD_BORDER};
            --primary: {PRIMARY};
            --success: {SUCCESS};
            --warning: {WARNING};
            --danger: {DANGER};
            --text-main: {TEXT_MAIN};
            --text-muted: {TEXT_MUTED};
        }}

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background: var(--bg-base);
            color: var(--text-main);
        }}

        [data-testid="stSidebar"] {{
            background: var(--sidebar);
            border-right: 1px solid var(--border);
        }}

        [data-testid="stSidebarNav"] span,
        [data-testid="stSidebar"] p {{
            color: var(--text-main);
        }}

        [data-testid="stSidebarNavLink"] {{
            border-radius: 999px;
            margin-bottom: .3rem;
            color: var(--text-muted);
        }}

        [data-testid="stSidebarNavLink"][aria-current="page"] {{
            background: rgba(47,107,255,0.18);
            color: var(--text-main);
        }}

        .block-container {{
            max-width: 1280px;
            padding: 1.5rem 2rem 3rem;
        }}

        h1, h2, h3, h4, strong, b {{
            color: var(--text-main) !important;
            letter-spacing: -0.02em;
        }}

        p, label, [data-testid="stCaptionContainer"] {{
            color: var(--text-muted);
        }}

        .page-kicker {{
            color: var(--primary);
            font-size: .72rem;
            font-weight: 700;
            letter-spacing: .16em;
            text-transform: uppercase;
            margin-bottom: .4rem;
        }}

        .page-subtitle {{
            color: var(--text-muted);
            font-size: .92rem;
            margin-top: -.4rem;
            margin-bottom: 1.5rem;
        }}

        .surface-card, [data-testid="stExpander"], [data-testid="stForm"],
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 1rem;
            box-shadow: 0 8px 24px rgba(0,0,0,.18);
        }}

        .kpi-card {{
            min-height: 7.5rem;
            padding: 1.1rem 1.2rem;
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 1rem;
        }}

        .kpi-label {{
            color: var(--text-muted);
            font-size: .75rem;
            font-weight: 600;
        }}

        .kpi-value {{
            color: var(--text-main);
            font-size: clamp(1.35rem, 1.8vw, 1.85rem);
            font-weight: 700;
            font-variant-numeric: tabular-nums;
            margin: .7rem 0 .3rem;
        }}

        .kpi-detail {{
            color: var(--text-muted);
            font-size: .72rem;
        }}

        .hero-card {{
            position: relative;
            min-height: 10rem;
            overflow: hidden;
            padding: 1.5rem;
            border-radius: 1rem;
            background: linear-gradient(135deg, var(--primary), #6D5BFF);
            color: #fff;
            box-shadow: 0 12px 30px rgba(47,107,255,.25);
        }}

        .hero-card h2, .hero-card p, .hero-card strong {{
            color: #fff !important;
        }}

        .hero-label {{
            font-size: .78rem;
            font-weight: 700;
            opacity: .8;
            text-transform: uppercase;
            letter-spacing: .12em;
        }}

        .hero-value {{
            margin-top: .5rem;
            font-size: clamp(2rem, 4vw, 3.2rem);
            line-height: 1;
            font-weight: 800;
            font-variant-numeric: tabular-nums;
            letter-spacing: -.04em;
        }}

        .hero-change {{
            display: inline-flex;
            margin-top: .8rem;
            padding: .35rem .7rem;
            border-radius: 999px;
            background: rgba(239,68,68,.18);
            color: #FCA5A5;
            font-size: .75rem;
            font-weight: 700;
        }}

        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: .35rem;
            padding: .25rem .65rem;
            border-radius: 999px;
            font-size: .7rem;
            font-weight: 700;
            background: rgba(34,197,94,.12);
            color: var(--success);
            border: 1px solid rgba(34,197,94,.35);
        }}

        .status-pill.warning {{
            color: var(--warning);
            background: rgba(245,158,11,.12);
            border-color: rgba(245,158,11,.35);
        }}

        .status-pill.danger {{
            color: var(--danger);
            background: rgba(239,68,68,.12);
            border-color: rgba(239,68,68,.35);
        }}

        .progress-track {{
            height: .55rem;
            overflow: hidden;
            background: var(--border);
            border-radius: 999px;
        }}

        .progress-fill {{
            height: 100%;
            border-radius: 999px;
            background: var(--primary);
        }}

        .progress-fill.over {{
            background: var(--danger);
        }}

        div.stButton > button, div.stFormSubmitButton > button {{
            min-height: 2.5rem;
            border-radius: 999px;
            border: 1px solid var(--primary);
            background: var(--primary);
            color: #fff;
            font-weight: 700;
            padding-inline: 1.1rem;
        }}

        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            background: #1D4ED8;
            border-color: #1D4ED8;
        }}

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-baseweb="select"] > div,
        [data-testid="stDateInput"] input,
        textarea {{
            color: var(--text-main) !important;
            background: #1A233A !important;
            border: 1px solid var(--primary) !important;
            border-radius: .75rem !important;
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid var(--border);
            border-radius: 1rem;
            overflow: hidden;
        }}

        [data-testid="stChatMessage"] {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 1rem;
            margin-bottom: .75rem;
        }}

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
            background: var(--primary);
        }}

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p {{
            color: #fff !important;
        }}

        @media (max-width: 900px) {{
            .block-container {{ padding-inline: 1rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def chart_layout(height: int = 320) -> dict:
    return {
        "height": height,
        "margin": dict(l=10, r=10, t=20, b=10),
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": dict(family="Inter", color=TEXT_MAIN, size=11),
        "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        "hoverlabel": dict(bgcolor=CARD, font_color=TEXT_MAIN),
    }
