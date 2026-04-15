"""Layer 2 — BUY score page."""

import streamlit as st
import pandas as pd


# ── Sidebar: Layer 2 controls ────────────────────────────────────────────────
with st.sidebar:
    st.header("Layer 2 settings", anchor=False)

    min_buy_score = st.slider(
        "Min BUY score",
        min_value=0,
        max_value=100,
        value=50,
        step=5,
        help="Only show stocks with BUY score >= this threshold.",
    )
    st.caption(
        "BUY score = 35% Liquidity + 30% Momentum + 35% Breakout. "
        "Scores stocks that passed Layer 1 on breakout quality."
    )


# ── Scoring methodology ──────────────────────────────────────────────────────

col_a, col_b, col_c = st.columns(3)
with col_a:
    with st.container(border=True):
        st.markdown(":material/water_drop: **Liquidity** (35%)")
        st.caption("GTGD20 · Intraday activity · CV stability")
with col_b:
    with st.container(border=True):
        st.markdown(":material/speed: **Momentum** (30%)")
        st.caption("Price volatility · MA analysis · RS vs VN-Index · A/D ratio · RSI+MACD")
with col_c:
    with st.container(border=True):
        st.markdown(":material/rocket_launch: **Breakout** (35%)")
        st.caption("Price breakout · Volume confirm · Dry-up · Base quality · Holding ratio")


# ── Main content ──────────────────────────────────────────────────────────────

passed_stocks = st.session_state.get("passed_stocks")

if not passed_stocks:
    st.info(
        "Run **Layer 1** filters first. Layer 2 scores the stocks that pass the hard filters.",
        icon=":material/layers:",
    )
else:
    st.caption(
        f"{len(passed_stocks)} stocks passed Layer 1. "
        f"Showing BUY score breakdown (min score: {min_buy_score})."
    )

    # Placeholder: Layer 2 API not yet wired
    st.warning(
        "Layer 2 scoring endpoint is not yet available. "
        "The BUY score computation (`cal_buy_score`) is implemented but not exposed via the API. "
        "Once connected, this page will show scored and ranked results.",
        icon=":material/construction:",
    )

    # Preview table with passed stocks (no scores yet)
    st.subheader("Layer 1 passed stocks (scores pending)", anchor=False)
    preview_rows = []
    for s in passed_stocks:
        preview_rows.append({
            "Symbol": s["symbol"],
            "Exchange": s["exchange"],
            "Liquidity": "—",
            "Momentum": "—",
            "Breakout": "—",
            "BUY score": "—",
        })
    st.dataframe(
        pd.DataFrame(preview_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Symbol": st.column_config.TextColumn(pinned=True),
        },
    )
