"""Watchlist — symbols starred during the current session."""

import pandas as pd
import streamlit as st

if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = set()

watchlist: set[str] = st.session_state["watchlist"]

st.header(f"★ Watchlist ({len(watchlist)})", anchor=False)
st.caption("Session-only — symbols clear when the app reloads.")

if not watchlist:
    st.info(
        "No starred symbols yet. Star rows on Layer 1 or Layer 2 to track them here.",
        icon=":material/star_border:",
    )
    st.stop()

col_clear, _ = st.columns([1, 5])
with col_clear:
    if st.button("Clear watchlist", icon=":material/delete:"):
        st.session_state["watchlist"] = set()
        st.rerun()

# Layer 1 metrics for watchlisted symbols
st.subheader("Layer 1 metrics", anchor=False)
passed = st.session_state.get("passed_stocks") or []
last = st.session_state.get("last_stocks") or []
pool = {s["symbol"]: s for s in (passed + last)}
matched = [pool[sym] for sym in watchlist if sym in pool]

if matched:
    rows = []
    for s in matched:
        rows.append({
            "Symbol": s["symbol"],
            "Exchange": s["exchange"],
            "Status": s["status"],
            "Price (VND)": f"{s['current_price'] * 1000:,.0f}",
            "GTGD20 (B)": f"{s['gtgd20']/1e9:.1f}",
            "Today val (B)": f"{s['today_value']/1e9:.2f}",
            "CV %": f"{s['cv']:.0f}" if s.get("cv") is not None else "—",
            "Passed": "✅" if s.get("passed", False) else "❌",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.caption("No Layer 1 data cached for watchlisted symbols. Run Layer 1 first.")

# Layer 2 scores for watchlisted symbols
st.subheader("Layer 2 scores", anchor=False)
layer2_data = st.session_state.get("layer2_data") or {}
scores = layer2_data.get("scores", []) if isinstance(layer2_data, dict) else []
score_pool = {s["symbol"]: s for s in scores}
score_rows = []
for sym in watchlist:
    s = score_pool.get(sym)
    if not s:
        continue
    score_rows.append({
        "Symbol": s["symbol"],
        "Exchange": s["exchange"],
        "BUY Score": s.get("_buy_score", s["buy_score"]),
        "Liquidity": s.get("_liquidity_score", s["liquidity_score"]),
        "Momentum": s.get("_momentum_score", s["momentum_score"]),
        "Breakout": s.get("_breakout_score", s["breakout_score"]),
    })

if score_rows:
    st.dataframe(
        pd.DataFrame(score_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "BUY Score": st.column_config.ProgressColumn(
                "BUY Score", min_value=0, max_value=100, format="%.1f",
            ),
            "Liquidity": st.column_config.NumberColumn(format="%.1f"),
            "Momentum": st.column_config.NumberColumn(format="%.1f"),
            "Breakout": st.column_config.NumberColumn(format="%.1f"),
        },
    )
else:
    st.caption("No Layer 2 data cached for watchlisted symbols. Open Layer 2 first.")

# Symbols with no cached data
unmatched = sorted(watchlist - set(pool.keys()) - set(score_pool.keys()))
if unmatched:
    st.caption(f"No cached data for: {', '.join(unmatched)}")
