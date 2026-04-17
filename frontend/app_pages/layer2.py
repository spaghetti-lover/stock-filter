"""Layer 2 — BUY score page."""

import json
import requests
import sseclient
import streamlit as st
import pandas as pd


API_BASE = "http://localhost:8000"

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Layer 2 settings", anchor=False)
    st.caption(
        "BUY score = 35% Liquidity + 30% Momentum + 35% Breakout. "
        "Scores stocks that passed Layer 1 on breakout quality."
    )
    refresh = st.button(
        "Refresh scores",
        type="secondary",
        use_container_width=True,
        icon=":material/refresh:",
        help="Re-fetch live market data and recompute all BUY scores.",
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


# ── Helpers ──────────────────────────────────────────────────────────────────

def render_scores(data: dict):
    scores = data.get("scores", [])
    from_cache = data.get("from_cache", False)
    scored_at = data.get("scored_at")

    if not scores:
        st.warning("No stocks could be scored. Check Layer 1 results.", icon=":material/warning:")
        return

    with st.container(horizontal=True):
        st.metric("Total scored", len(scores), border=True)

    meta_parts = []
    if scored_at:
        meta_parts.append(f"Scored at: `{scored_at[:19]}`")
    if from_cache:
        meta_parts.append(":material/cached: Served from cache")
    else:
        meta_parts.append(":material/cloud_download: Freshly computed")
    st.caption(" · ".join(meta_parts))

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


def stream_layer2(use_refresh: bool) -> dict | None:
    """Call /layer2/stream via SSE, show progress, return final result dict."""
    progress_bar = st.progress(0, text="Starting scoring...")
    status_text = st.empty()

    try:
        resp = requests.get(
            f"{API_BASE}/layer2/stream",
            params={"refresh": "true" if use_refresh else "false"},
            stream=True,
            headers={"Accept": "text/event-stream"},
        )
        if not resp.ok:
            st.error(f"API error {resp.status_code}: {resp.text}")
            return None

        client = sseclient.SSEClient(resp.iter_content(chunk_size=None))
        result = None

        for event in client.events():
            payload = json.loads(event.data)
            event_type = payload.get("type")

            if event_type == "progress":
                processed = payload["processed"]
                total = payload["total"]
                symbol = payload["symbol"]
                pct = processed / total if total > 0 else 0
                progress_bar.progress(pct, text=f"Scoring {symbol} ({processed}/{total})")

            elif event_type == "result":
                result = payload["data"]

            elif event_type == "error":
                progress_bar.empty()
                status_text.empty()
                code = payload.get("code", 500)
                detail = payload.get("detail", "Unknown error")
                if code == 422:
                    st.warning(
                        f"{detail}\n\nPlease go to **Layer 1** and run the filter first.",
                        icon=":material/filter_alt:",
                    )
                else:
                    st.error(f"Error: {detail}")
                return None

        progress_bar.empty()
        status_text.empty()
        return result

    except requests.ConnectionError:
        st.error("Cannot connect to backend. Is the server running?")
        return None


# ── Main content ─────────────────────────────────────────────────────────────

data = stream_layer2(use_refresh=refresh)

if data is None:
    st.stop()

render_scores(data)
