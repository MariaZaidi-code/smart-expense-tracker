"""Shared design tokens for a clean, premium light SaaS look.

White canvas, slate surfaces, single blue accent. No dark theme, no indigo.
"""

from __future__ import annotations

import streamlit as st

BG_BASE = "#f8fafc"
BG_DEEP = "#f1f5f9"
SURFACE = "#ffffff"
PILL = "#e2e8f0"
MUTED = "#cbd5e1"
PRIMARY = "#2563eb"
PRIMARY_HOVER = "#1d4ed8"
OVER_BUDGET = "#dc2626"
TEXT_MAIN = "#0f172a"
TEXT_MUTED = "#64748b"
INK = "#ffffff"
PRIMARY_FADE = "rgba(37,99,235,0.08)"
GRID = "rgba(203,213,225,0.6)"

CHART_COLORS = [PRIMARY, "#06b6d4", "#10b981", "#f59e0b", OVER_BUDGET, TEXT_MUTED]


def inject_theme() -> None:
    st.html(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {{
            --bg-base: {BG_BASE};
            --bg-deep: {BG_DEEP};
            --surface: {SURFACE};
            --pill: {PILL};
            --muted: {MUTED};
            --primary: {PRIMARY};
            --primary-hover: {PRIMARY_HOVER};
            --text-main: {TEXT_MAIN};
            --text-muted: {TEXT_MUTED};
            --over-budget: {OVER_BUDGET};
            --ink: {INK};
        }}

        html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            -webkit-font-smoothing: antialiased;
        }}

        .stApp {{
            background: var(--bg-base);
            color: var(--text-main);
        }}

        [data-testid="stSidebar"] {{
            background: #ffffff;
            border-right: 1px solid var(--pill);
        }}

        [data-testid="stSidebarNav"] span,
        [data-testid="stSidebar"] p {{
            color: var(--text-main);
        }}

        [data-testid="stSidebarNavLink"] {{
            border-radius: 6px;
            margin-bottom: 2px;
            color: var(--text-muted);
            font-weight: 500;
            font-size: 0.9rem;
            padding: 0.45rem 0.75rem;
        }}

        [data-testid="stSidebarNavLink"][aria-current="page"] {{
            background: var(--pill);
            color: var(--text-main);
        }}

        [data-testid="stHeader"] {{
            background: rgba(248,250,252,0.92);
            border-bottom: 1px solid var(--pill);
            backdrop-filter: blur(8px);
        }}

        .block-container {{
            max-width: 1280px;
            padding-top: 2rem;
            padding-bottom: 3rem;
            padding-inline: 2rem;
        }}

        h1, h2, h3, h4 {{
            color: var(--text-main) !important;
            letter-spacing: -0.025em;
            font-weight: 600;
        }}

        p, label, [data-testid="stCaptionContainer"] {{
            color: var(--text-muted);
        }}

        strong, b {{
            color: var(--text-main);
            font-weight: 600;
        }}

        .page-kicker {{
            color: var(--primary);
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }}

        .page-subtitle {{
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-top: -0.25rem;
            margin-bottom: 1.75rem;
            font-weight: 400;
        }}

        .surface-card, [data-testid="stExpander"], [data-testid="stForm"],
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--surface);
            border: 1px solid var(--pill);
            border-radius: 10px;
            box-shadow: 0 1px 2px rgba(15,23,42,0.04);
        }}

        [data-testid="stMetric"] {{
            padding: 1rem;
            border-radius: 8px;
            background: var(--surface);
            border: 1px solid var(--pill);
        }}

        .kpi-card {{
            min-height: 7.5rem;
            padding: 1.1rem 1.25rem;
            background: var(--surface);
            border: 1px solid var(--pill);
            border-radius: 10px;
            box-shadow: 0 1px 2px rgba(15,23,42,0.04);
        }}

        .kpi-label {{
            color: var(--text-muted);
            font-size: 0.72rem;
            font-weight: 500;
        }}

        .kpi-value {{
            color: var(--text-main);
            font-size: 1.6rem;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
            margin: 0.5rem 0 0.3rem;
            letter-spacing: -0.02em;
        }}

        .kpi-detail {{
            color: var(--text-muted);
            font-size: 0.72rem;
            line-height: 1.4;
        }}

        .budget-block {{
            margin: 0.6rem 0 1rem;
        }}

        .budget-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.4rem;
            font-size: 0.8rem;
        }}

        .money {{
            font-variant-numeric: tabular-nums;
            font-weight: 500;
            color: var(--text-main);
        }}

        .progress-track {{
            height: 6px;
            overflow: hidden;
            background: var(--pill);
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
            gap: 0.3rem;
            width: fit-content;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-size: 0.68rem;
            font-weight: 500;
            background: var(--pill);
            color: var(--text-muted);
            border: 1px solid var(--muted);
        }}

        .tool-tag {{
            color: var(--primary);
            border-color: color-mix(in srgb, var(--primary) 30%, var(--muted));
        }}

        .status-pill.over {{
            color: var(--over-budget);
            border-color: color-mix(in srgb, var(--over-budget) 40%, var(--muted));
        }}

        .alert-banner {{
            display: flex;
            gap: 0.75rem;
            align-items: flex-start;
            padding: 0.85rem 1rem;
            margin-bottom: 0.6rem;
            background: var(--surface);
            border: 1px solid color-mix(in srgb, var(--over-budget) 30%, var(--pill));
            border-radius: 10px;
        }}

        .alert-icon {{
            display: grid;
            place-items: center;
            min-width: 1.6rem;
            height: 1.6rem;
            border-radius: 6px;
            background: var(--over-budget);
            color: #ffffff;
            font-weight: 700;
            font-size: 0.8rem;
        }}

        .alert-title {{
            color: var(--text-main);
            font-size: 0.82rem;
            font-weight: 600;
        }}

        .alert-copy {{
            color: var(--text-muted);
            font-size: 0.75rem;
            line-height: 1.5;
            margin-top: 0.15rem;
        }}

        .empty-state {{
            padding: 2rem 1.5rem;
            text-align: center;
            border: 1px dashed var(--muted);
            border-radius: 10px;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        .source-card {{
            padding: 0.7rem 0.9rem;
            margin: 0.4rem 0;
            border-radius: 8px;
            background: var(--pill);
            border-left: 2px solid var(--primary);
            font-size: 0.78rem;
            line-height: 1.5;
        }}

        div.stButton > button, div.stFormSubmitButton > button {{
            min-height: 2.4rem;
            border-radius: 6px;
            border: 1px solid var(--primary);
            background: var(--primary);
            color: #ffffff;
            font-weight: 500;
            padding-inline: 1rem;
            font-size: 0.85rem;
            box-shadow: 0 1px 2px rgba(37,99,235,0.2);
        }}

        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            color: #ffffff;
            border-color: var(--primary-hover);
            background: var(--primary-hover);
        }}

        div.stButton > button:focus-visible {{
            box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary) 35%, transparent);
        }}

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-baseweb="select"] > div,
        [data-testid="stDateInput"] input,
        textarea {{
            color: var(--text-main) !important;
            background: #ffffff !important;
            border: 1px solid var(--muted) !important;
            border-radius: 6px !important;
            font-size: 0.85rem;
        }}

        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        textarea:focus {{
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 1px var(--primary) !important;
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid var(--pill);
            border-radius: 10px;
            overflow: hidden;
        }}

        [data-testid="stChatMessage"] {{
            background: var(--surface);
            border: 1px solid var(--pill);
            border-radius: 10px;
            margin-bottom: 0.75rem;
        }}

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {{
            background: var(--primary);
            border-color: var(--primary);
        }}

        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p {{
            color: #ffffff !important;
        }}

        [data-testid="stChatInput"] {{
            border-radius: 8px;
            border: 1px solid var(--pill);
            background: #ffffff;
        }}

        hr {{
            border-color: var(--pill);
        }}

        .hero-card {{
            position: relative;
            min-height: 11rem;
            overflow: hidden;
            padding: 1.75rem;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary) 0%, #1d4ed8 100%);
            color: #ffffff;
            box-shadow: 0 1px 2px rgba(37,99,235,0.15), 0 8px 24px rgba(37,99,235,0.12);
        }}

        .hero-card h2, .hero-card p, .hero-card strong {{
            color: #ffffff !important;
        }}

        .hero-label {{
            font-size: 0.7rem;
            font-weight: 600;
            opacity: 0.85;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}

        .hero-value {{
            margin-top: 0.5rem;
            font-size: 2.25rem;
            line-height: 1;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.04em;
        }}

        .hero-change {{
            display: inline-flex;
            margin-top: 0.75rem;
            padding: 0.3rem 0.65rem;
            border-radius: 6px;
            background: rgba(255,255,255,0.18);
            font-size: 0.75rem;
            font-weight: 500;
        }}

        .hero-illustration {{ display: none; }}

        .safe-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem 1.25rem;
            margin-top: 0.75rem;
            font-size: 0.72rem;
            font-weight: 500;
            opacity: 0.9;
        }}

        .score-detail {{
            margin-top: 0.35rem;
            color: var(--text-muted);
            font-size: 0.75rem;
            line-height: 1.45;
        }}

        .score-advice {{
            margin-top: 0.2rem;
            color: var(--primary);
            font-size: 0.72rem;
            font-weight: 500;
        }}

        .transaction-list {{
            overflow: hidden;
            border-radius: 10px;
            border: 1px solid var(--pill);
            background: var(--surface);
        }}

        .transaction-row {{
            display: grid;
            grid-template-columns: minmax(13rem, 2fr) 1fr 1fr auto;
            align-items: center;
            gap: 1rem;
            padding: 0.85rem 1.1rem;
            border-bottom: 1px solid var(--pill);
            font-size: 0.85rem;
        }}

        .transaction-row:last-child {{ border-bottom: 0; }}
        .transaction-name {{ font-weight: 500; color: var(--text-main); }}
        .transaction-meta {{ color: var(--text-muted); font-size: 0.72rem; }}
        .transaction-more {{ color: var(--primary); font-size: 0.75rem; font-weight: 500; }}

        @media (max-width: 900px) {{
            .block-container {{ padding-inline: 1.25rem; padding-top: 1.5rem; }}
            .kpi-card {{ min-height: 7rem; }}
        }}

        @media (max-width: 480px) {{
            .block-container {{ padding: 1rem 1rem 4rem; }}
            h1 {{ font-size: 1.5rem !important; }}
            .hero-card {{ min-height: 9rem; padding: 1.25rem; border-radius: 10px; }}
            .hero-value {{ font-size: 1.85rem; }}
            .kpi-card {{ min-height: 6.5rem; border-radius: 8px; }}
            .kpi-value {{ font-size: 1.3rem; margin-top: 0.4rem; }}
            .transaction-row {{ grid-template-columns: 1fr auto; }}
            .transaction-row > :nth-child(2), .transaction-row > :nth-child(3) {{ display: none; }}
            [data-testid="stHorizontalBlock"] {{ gap: 0.6rem; }}
        }}
        </style>
        """,
    )


def chart_layout(height: int = 340) -> dict:
    return {
        "height": height,
        "margin": dict(l=8, r=8, t=24, b=8),
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": dict(family="Inter", color=TEXT_MAIN, size=11),
        "legend": dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        "hoverlabel": dict(bgcolor=SURFACE, font_color=TEXT_MAIN, bordercolor=MUTED),
    }
