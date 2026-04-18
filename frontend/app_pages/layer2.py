"""Layer 2 — BUY score page (auto-refreshed every 5 minutes)."""

import os

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh


API_BASE = os.environ.get("BACKEND_URL", "http://localhost:8000")
REFRESH_INTERVAL = 300

# Tick every second so the countdown circle animates smoothly.
st_autorefresh(interval=1000, key="layer2_tick")


def fetch_latest() -> dict | None:
    try:
        resp = requests.get(f"{API_BASE}/layer2/latest", timeout=10)
    except requests.ConnectionError:
        st.error("Cannot connect to backend. Is the server running?")
        return None
    if not resp.ok:
        st.error(f"API error {resp.status_code}: {resp.text}")
        return None
    return resp.json()


def render_countdown(next_refresh_in: int):
    elapsed = REFRESH_INTERVAL - next_refresh_in
    fraction = max(0.0, min(1.0, elapsed / REFRESH_INTERVAL))
    mins, secs = divmod(next_refresh_in, 60)
    st.progress(fraction, text=f":material/schedule: Next refresh in **{mins}m {secs:02d}s**")


def render_scores(data: dict):
    scores = data.get("scores", [])
    scored_at = data.get("scored_at")

    if not scores:
        st.info(
            "No Layer 2 scores yet. The scheduler refreshes every 5 minutes once Layer 1 has passed symbols.",
            icon=":material/hourglass_empty:",
        )
        return

    with st.container(horizontal=True):
        st.metric("Total scored", len(scores), border=True)

    if scored_at:
        st.caption(f":material/schedule: Scored at `{scored_at[:19]}`")

    rows = [
        {
            "Symbol": s["symbol"],
            "Exchange": s["exchange"],
            "BUY Score": s["buy_score"],
            "Liquidity": s["liquidity_score"],
            "Momentum": s["momentum_score"],
            "Breakout": s["breakout_score"],
        }
        for s in scores
    ]
    df = pd.DataFrame(rows)

    st.subheader(f"Scored stocks ({len(scores)})", anchor=False)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Symbol": st.column_config.TextColumn(pinned=True),
            "BUY Score": st.column_config.ProgressColumn(
                "BUY Score",
                min_value=0,
                max_value=100,
                format="%.1f",
            ),
            "Liquidity": st.column_config.NumberColumn(format="%.1f"),
            "Momentum": st.column_config.NumberColumn(format="%.1f"),
            "Breakout": st.column_config.NumberColumn(format="%.1f"),
        },
    )


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Layer 2 settings", anchor=False)
    st.caption(
        "BUY score = 35% Liquidity + 30% Momentum + 35% Breakout. "
        "Scored automatically every 5 minutes from Layer 1's passed symbols."
    )

# ── Scoring methodology ─────────────────────────────────────────────────────
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

st.divider()

# ── Fetch + render ──────────────────────────────────────────────────────────
latest = fetch_latest()
if latest is None:
    st.stop()

cached = st.session_state.get("layer2_data")
if cached is None or cached.get("scored_at") != latest.get("scored_at"):
    st.session_state["layer2_data"] = latest

data = st.session_state["layer2_data"]

render_countdown(latest.get("next_refresh_in", REFRESH_INTERVAL))

render_scores(data)
