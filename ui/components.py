"""Reusable presentation components for the Streamlit pages."""

from __future__ import annotations

import html

import streamlit as st


def format_money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}Rs. {abs(value):,.0f}"


def page_header(title: str, subtitle: str, kicker: str = "PERSONAL FINANCE") -> None:
    st.html(f'<div class="page-kicker">{html.escape(kicker)}</div>')
    st.title(title)
    st.html(f'<div class="page-subtitle">{html.escape(subtitle)}</div>')


def kpi_card(title: str, value: str, detail: str) -> None:
    st.html(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{html.escape(title)}</div>
            <div class="kpi-value">{html.escape(value)}</div>
            <div class="kpi-detail">{html.escape(detail)}</div>
        </div>
        """,
        
    )


def hero_card(value: float, change_percent: float) -> None:
    direction = "higher" if change_percent >= 0 else "lower"
    st.html(
        f"""
        <div class="hero-card">
            <div class="hero-label">REMAINING BUDGET</div>
            <div class="hero-value">{format_money(value)}</div>
            <div class="hero-change">{change_percent:+.1f}% {direction} than last month</div>
            <div class="hero-illustration" aria-hidden="true">
                <div class="hero-coin one"></div>
                <div class="hero-coin two"></div>
                <div class="hero-wallet"></div>
            </div>
        </div>
        """,
        
    )


def safe_to_spend_card(snapshot: dict) -> None:
    """Hero card for the Safe-to-Spend number (PocketGuard / Safe Spend style)."""
    status = snapshot.get("status", "comfortable")
    tone = "tight" if status in {"tight", "critical", "no_budget"} else "comfortable"
    st.html(
        f"""
        <div class="hero-card safe-card {tone}">
            <div class="hero-label">SAFE TO SPEND</div>
            <div class="hero-value">{format_money(snapshot.get('safe_to_spend', 0))}</div>
            <div class="hero-change">{html.escape(snapshot.get('label', ''))} ·
                {format_money(snapshot.get('per_day', 0))}/day for
                {int(snapshot.get('days_left', 0))} days</div>
            <div class="safe-meta">
                <span>{format_money(snapshot.get('remaining', 0))} budget left</span>
                <span>{format_money(snapshot.get('upcoming_commitments', 0))} reserved for bills</span>
            </div>
            <div class="hero-illustration" aria-hidden="true">
                <div class="hero-coin one"></div>
                <div class="hero-coin two"></div>
                <div class="hero-wallet"></div>
            </div>
        </div>
        """,
        
    )


def score_bar(label: str, score: float, detail: str, advice: str = "") -> None:
    """Explainable health-score component row."""
    percent = max(0.0, min(float(score), 100.0))
    tone = "over" if percent < 55 else ""
    st.html(
        f"""
        <div class="budget-block">
            <div class="budget-row">
                <strong>{html.escape(label)}</strong>
                <span class="money">{percent:.0f}/100</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill {tone}" style="width:{percent:.1f}%"></div>
            </div>
            <div class="score-detail">{html.escape(detail)}</div>
            {f'<div class="score-advice">→ {html.escape(advice)}</div>' if advice else ''}
        </div>
        """,
        
    )


def goal_progress(goal: dict) -> None:
    percent = min(float(goal.get("progress_percent", 0)), 100.0)
    status = goal.get("status", "active")
    over = status == "behind"
    label = {
        "achieved": "✓ Achieved",
        "on_track": "✓ On track",
        "active": "◷ In progress",
        "behind": "⚠ Behind schedule",
    }.get(status, status.title())
    monthly = goal.get("required_monthly")
    monthly_text = (
        f"{format_money(monthly)}/month needed" if monthly else "No target date set"
    )
    st.html(
        f"""
        <div class="budget-block">
            <div class="budget-row">
                <strong>{html.escape(goal['name'])}</strong>
                <span class="money">{format_money(goal['saved_amount'])} / {format_money(goal['target_amount'])}</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill {'over' if over else ''}" style="width:{percent:.1f}%"></div>
            </div>
            <div class="budget-row" style="margin-top:.45rem">
                <span class="status-pill {'over' if over else ''}">{label}</span>
                <span>{percent:.0f}% funded · {monthly_text}</span>
            </div>
        </div>
        """,
        
    )


def budget_progress(name: str, spent: float, limit: float) -> None:
    percent = (spent / limit * 100) if limit else 0
    over = spent > limit
    remaining = limit - spent
    label = "Over budget" if over else "On track"
    st.html(
        f"""
        <div class="budget-block">
            <div class="budget-row">
                <strong>{html.escape(name)}</strong>
                <span class="money">{format_money(spent)} / {format_money(limit)}</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill {'over' if over else ''}" style="width:{min(percent, 100):.1f}%"></div>
            </div>
            <div class="budget-row" style="margin-top:.45rem">
                <span class="status-pill {'over' if over else ''}">{"⚠ " if over else "✓ "}{label}</span>
                <span>{format_money(abs(remaining))} {'over' if over else 'remaining'}</span>
            </div>
        </div>
        """,
        
    )


def alert_banner(title: str, reason: str) -> None:
    st.html(
        f"""
        <div class="alert-banner">
            <div class="alert-icon">!</div>
            <div>
                <div class="alert-title">{html.escape(title)}</div>
                <div class="alert-copy">{html.escape(reason)}</div>
            </div>
        </div>
        """,
        
    )


def tool_tag(tool: str) -> None:
    st.html(
        f'<span class="tool-tag">⚙ Used tool: {html.escape(tool)}</span>',
        
    )


def source_citation(source: dict, index: int) -> None:
    title = source.get("title", f"Source {index}")
    excerpt = source.get("excerpt", "No excerpt provided.")
    with st.expander(f"Source {index}: {title}"):
        st.html(
            f'<div class="source-card">{html.escape(excerpt)}</div>',
            
        )


def empty_state(title: str, message: str) -> None:
    st.html(
        f'<div class="empty-state"><strong>{html.escape(title)}</strong><br><br>{html.escape(message)}</div>',
        
    )


def recent_transaction_list(rows: list[dict]) -> None:
    rendered = []
    for row in rows:
        over = row["amount"] >= 2500
        status = "▲ Review" if over else "✓ Within budget"
        rendered.append(
            f"""
            <div class="transaction-row">
                <div>
                    <div class="transaction-name">{html.escape(row['description'])}</div>
                    <div class="transaction-meta">{html.escape(row['category'])} · {html.escape(row['transaction_date'])}</div>
                </div>
                <div class="transaction-meta">{html.escape(row['payment_method'])}</div>
                <div class="money">{format_money(row['amount'])}</div>
                <div style="display:flex;align-items:center;gap:.7rem">
                    <span class="status-pill {'over' if over else ''}">{status}</span>
                    <span class="transaction-more">More</span>
                </div>
            </div>
            """
        )
    st.html(
        f'<div class="transaction-list">{"".join(rendered)}</div>',
        
    )
