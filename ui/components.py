"""Reusable presentation components for the Streamlit pages."""

from __future__ import annotations

import html

import streamlit as st


def format_money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}Rs. {abs(value):,.0f}"


def page_header(title: str, subtitle: str, kicker: str = "PERSONAL FINANCE") -> None:
    st.markdown(f'<div class="page-kicker">{html.escape(kicker)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-subtitle">{html.escape(subtitle)}</div>', unsafe_allow_html=True)


def kpi_card(title: str, value: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{html.escape(title)}</div>
            <div class="kpi-value">{html.escape(value)}</div>
            <div class="kpi-detail">{html.escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_card(value: float, change_percent: float) -> None:
    direction = "higher" if change_percent >= 0 else "lower"
    st.markdown(
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
        unsafe_allow_html=True,
    )


def budget_progress(name: str, spent: float, limit: float) -> None:
    percent = (spent / limit * 100) if limit else 0
    over = spent > limit
    remaining = limit - spent
    label = "Over budget" if over else "On track"
    st.markdown(
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
        unsafe_allow_html=True,
    )


def alert_banner(title: str, reason: str) -> None:
    st.markdown(
        f"""
        <div class="alert-banner">
            <div class="alert-icon">!</div>
            <div>
                <div class="alert-title">{html.escape(title)}</div>
                <div class="alert-copy">{html.escape(reason)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tool_tag(tool: str) -> None:
    st.markdown(
        f'<span class="tool-tag">⚙ Used tool: {html.escape(tool)}</span>',
        unsafe_allow_html=True,
    )


def source_citation(source: dict, index: int) -> None:
    title = source.get("title", f"Source {index}")
    excerpt = source.get("excerpt", "No excerpt provided.")
    with st.expander(f"Source {index}: {title}"):
        st.markdown(
            f'<div class="source-card">{html.escape(excerpt)}</div>',
            unsafe_allow_html=True,
        )


def empty_state(title: str, message: str) -> None:
    st.markdown(
        f'<div class="empty-state"><strong>{html.escape(title)}</strong><br><br>{html.escape(message)}</div>',
        unsafe_allow_html=True,
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
    st.markdown(
        f'<div class="transaction-list">{"".join(rendered)}</div>',
        unsafe_allow_html=True,
    )
