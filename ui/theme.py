"""Shared charcoal, lavender, and peach design tokens."""

from __future__ import annotations

import streamlit as st

BG_BASE = "#242529"
BG_DEEP = "#242529"
SURFACE = "#373841"
PILL = "#373841"
MUTED = "#5F6067"
PRIMARY = "#A3A7F6"
OVER_BUDGET = "#DCD9DB"
TEXT_MAIN = "#DCD9DB"
TEXT_MUTED = "#858C95"
INK = "#242529"
PRIMARY_FADE = "rgba(163,167,246,0.16)"
GRID = "rgba(95,96,103,0.55)"

CHART_COLORS = [PRIMARY, OVER_BUDGET, TEXT_MAIN, MUTED, SURFACE, PILL]


def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {{
            --bg-base: {BG_BASE};
            --bg-deep: {BG_DEEP};
            --surface: {SURFACE};
            --pill: {PILL};
            --muted: {MUTED};
            --primary: {PRIMARY};
            --text-main: {TEXT_MAIN};
            --text-muted: {TEXT_MUTED};
            --over-budget: {OVER_BUDGET};
            --ink: {INK};
        }}

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background: var(--bg-base);
            color: var(--text-main);
        }}

        [data-testid="stSidebar"] {{
            background: var(--bg-base);
            border-right: 1px solid var(--surface);
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
            background: var(--surface);
            color: var(--text-main);
        }}

        [data-testid="stHeader"] {{
            background: color-mix(in srgb, var(--bg-base) 92%, transparent);
            border-bottom: 1px solid var(--surface);
            backdrop-filter: blur(14px);
        }}

        .block-container {{
            max-width: 1440px;
            padding-top: 2.25rem;
            padding-bottom: 4rem;
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
            background: var(--surface);
            border: 1px solid var(--muted);
            border-radius: 1.875rem;
            box-shadow: 0 16px 36px rgba(36,37,41,.22);
        }}

        [data-testid="stMetric"] {{
            padding: 1rem;
            border-radius: 1.5rem;
            background: var(--pill);
        }}

        .kpi-card {{
            min-height: 9.5rem;
            padding: 1.25rem;
            background: var(--surface);
            border: 1px solid var(--muted);
            border-radius: 1.875rem;
            box-shadow: 0 16px 36px rgba(36,37,41,.22);
        }}

        .kpi-label {{
            color: var(--text-muted);
            font-size: .75rem;
            font-weight: 600;
        }}

        .kpi-value {{
            color: var(--text-main);
            font-size: clamp(1.45rem, 2vw, 2rem);
            font-weight: 700;
            font-variant-numeric: tabular-nums;
            margin: .85rem 0 .4rem;
        }}

        .kpi-detail {{
            color: var(--text-muted);
            font-size: .72rem;
        }}

        .budget-block {{
            margin: .75rem 0 1.2rem;
        }}

        .budget-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: .5rem;
            font-size: .78rem;
        }}

        .money {{
            font-variant-numeric: tabular-nums;
            font-weight: 650;
        }}

        .progress-track {{
            height: .62rem;
            overflow: hidden;
            background: var(--muted);
            border-radius: 999px;
        }}

        .progress-fill {{
            height: 100%;
            border-radius: 999px;
            background: var(--primary);
        }}

        .progress-fill.over {{
            background: var(--over-budget);
        }}

        .status-pill, .tool-tag {{
            display: inline-flex;
            align-items: center;
            gap: .35rem;
            width: fit-content;
            padding: .28rem .68rem;
            border-radius: 999px;
            font-size: .68rem;
            font-weight: 700;
            letter-spacing: .02em;
            background: color-mix(in srgb, var(--primary) 14%, transparent);
            color: var(--text-main);
            border: 1px solid var(--muted);
            background: var(--pill);
        }}

        .tool-tag {{ color: var(--primary); }}

        .status-pill.over {{
            color: var(--over-budget);
            border-color: color-mix(in srgb, var(--over-budget) 48%, transparent);
            background: var(--pill);
        }}

        .alert-banner {{
            display: flex;
            gap: .8rem;
            align-items: flex-start;
            padding: 1rem;
            margin-bottom: .7rem;
            background: var(--surface);
            border: 1px solid var(--over-budget);
            border-radius: 1.75rem;
        }}

        .alert-icon {{
            display: grid;
            place-items: center;
            min-width: 2rem;
            height: 2rem;
            border-radius: 999px;
            background: var(--over-budget);
            color: var(--ink);
            font-weight: 800;
        }}

        .alert-title {{
            color: var(--text-main);
            font-size: .82rem;
            font-weight: 700;
        }}

        .alert-copy {{
            color: var(--text-muted);
            font-size: .75rem;
            line-height: 1.5;
            margin-top: .18rem;
        }}

        .empty-state {{
            padding: 2.5rem 1.5rem;
            text-align: center;
            border: 1px dashed var(--muted);
            border-radius: 1.875rem;
            color: var(--text-muted);
        }}

        .source-card {{
            padding: .8rem 1rem;
            margin: .45rem 0;
            border-radius: 1.25rem;
            background: var(--pill);
            border-left: 3px solid var(--primary);
            font-size: .76rem;
        }}

        div.stButton > button, div.stFormSubmitButton > button {{
            min-height: 2.65rem;
            border-radius: 999px;
            border: 1px solid var(--primary);
            background: var(--primary);
            color: var(--ink);
            font-weight: 700;
            padding-inline: 1.15rem;
        }}

        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            color: var(--ink);
            border-color: var(--text-main);
            background: var(--text-main);
        }}

        div.stButton > button:focus-visible {{
            box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 35%, transparent);
        }}

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-baseweb="select"] > div,
        [data-testid="stDateInput"] input,
        textarea {{
            color: var(--text-main) !important;
            background: color-mix(in srgb, var(--surface) 72%, var(--bg-base)) !important;
            border-color: var(--muted) !important;
            border-radius: 999px !important;
            background: var(--pill) !important;
        }}

        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        textarea:focus {{
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary) 24%, transparent) !important;
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid var(--muted);
            border-radius: 1.75rem;
            overflow: hidden;
        }}

        [data-testid="stChatMessage"] {{
            background: var(--surface);
            border: 1px solid var(--muted);
            border-radius: 1.75rem;
            margin-bottom: .8rem;
        }}

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
            background: var(--primary);
        }}

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p {{
            color: var(--ink) !important;
        }}

        [data-testid="stChatInput"] {{
            border-radius: 999px;
            border: 1px solid var(--muted);
            background: var(--pill);
        }}

        hr {{
            border-color: var(--surface);
        }}

        .hero-card {{
            position: relative;
            min-height: 16rem;
            overflow: hidden;
            padding: 2rem;
            border-radius: 2rem;
            background: var(--primary);
            color: var(--ink);
            box-shadow: 0 18px 42px rgba(36,37,41,.28);
        }}

        .hero-card h2, .hero-card p, .hero-card strong {{
            color: var(--ink) !important;
        }}

        .hero-label {{
            font-size: .78rem;
            font-weight: 700;
            opacity: .72;
        }}

        .hero-value {{
            margin-top: .65rem;
            font-size: clamp(2.25rem, 5vw, 4.25rem);
            line-height: 1;
            font-weight: 800;
            font-variant-numeric: tabular-nums;
            letter-spacing: -.06em;
        }}

        .hero-change {{
            display: inline-flex;
            margin-top: 1.1rem;
            padding: .45rem .8rem;
            border-radius: 999px;
            background: rgba(36,37,41,.12);
            font-size: .75rem;
            font-weight: 700;
        }}

        .hero-illustration {{
            position: absolute;
            right: 2.2rem;
            bottom: 1.5rem;
            width: 10rem;
            height: 8rem;
        }}

        .hero-wallet {{
            position: absolute;
            right: 0;
            bottom: 0;
            width: 8.5rem;
            height: 5.2rem;
            border-radius: 1.5rem;
            background: var(--ink);
            transform: rotate(-4deg);
        }}

        .hero-wallet::after {{
            content: "";
            position: absolute;
            right: -.25rem;
            top: 1.1rem;
            width: 3.2rem;
            height: 2.1rem;
            border-radius: 999px 0 0 999px;
            background: var(--over-budget);
        }}

        .hero-coin {{
            position: absolute;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            background: var(--over-budget);
            border: .4rem solid rgba(36,37,41,.16);
        }}

        .hero-coin.one {{ right: 1rem; top: .2rem; }}
        .hero-coin.two {{ right: 4.1rem; top: 1.1rem; width: 1.8rem; height: 1.8rem; }}

        .transaction-list {{
            overflow: hidden;
            border-radius: 1.875rem;
            border: 1px solid var(--muted);
            background: var(--surface);
        }}

        .transaction-row {{
            display: grid;
            grid-template-columns: minmax(13rem, 2fr) 1fr 1fr auto;
            align-items: center;
            gap: 1rem;
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--muted);
        }}

        .transaction-row:last-child {{ border-bottom: 0; }}
        .transaction-name {{ font-weight: 700; color: var(--text-main); }}
        .transaction-meta {{ color: var(--text-muted); font-size: .72rem; }}
        .transaction-more {{ color: var(--primary); font-size: .75rem; font-weight: 700; }}

        @media (max-width: 900px) {{
            .block-container {{ padding-inline: 1.1rem; padding-top: 1.5rem; }}
            .kpi-card {{ min-height: 8.5rem; }}
        }}

        @media (max-width: 480px) {{
            .block-container {{ padding: 1rem .85rem 5rem; }}
            h1 {{ font-size: 1.65rem !important; }}
            .hero-card {{ min-height: 19rem; padding: 1.5rem; border-radius: 1.75rem; }}
            .hero-value {{ font-size: 2.65rem; }}
            .hero-illustration {{ right: 1.25rem; bottom: 1.2rem; transform: scale(.82); transform-origin: bottom right; }}
            .kpi-card {{ min-height: 7.75rem; border-radius: 1.6rem; }}
            .kpi-value {{ font-size: 1.45rem; margin-top: .55rem; }}
            .transaction-row {{ grid-template-columns: 1fr auto; }}
            .transaction-row > :nth-child(2), .transaction-row > :nth-child(3) {{ display: none; }}
            [data-testid="stHorizontalBlock"] {{ gap: .75rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def chart_layout(height: int = 340) -> dict:
    return {
        "height": height,
        "margin": dict(l=10, r=10, t=30, b=10),
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": dict(family="Inter", color=TEXT_MAIN, size=11),
        "legend": dict(orientation="h", yanchor="bottom", y=1.03, x=0),
        "hoverlabel": dict(bgcolor=SURFACE, font_color=TEXT_MAIN),
    }
