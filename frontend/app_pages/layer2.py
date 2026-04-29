"""Layer 2 — BUY score page (auto-refreshed every 5 minutes)."""

import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh


API_BASE = os.environ.get("BACKEND_URL", "http://localhost:8000")
REFRESH_INTERVAL = 300

if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = set()

# Tick every second so the countdown circle animates smoothly.
st_autorefresh(interval=1000, key="layer2_tick")

DEFAULT_WEIGHTS = {
    "liquidity": 0.35, "momentum": 0.30, "breakout": 0.35,
    "liq_gtgd20": 0.55, "liq_intraday": 0.30, "liq_cv": 0.15,
    "mom_volatility": 0.30, "mom_ma": 0.20, "mom_rs": 0.20, "mom_ad": 0.15, "mom_tech": 0.15,
    "brk_price": 0.30, "brk_vol": 0.25, "brk_dryup": 0.20, "brk_base": 0.15, "brk_hold": 0.10,
    "composite_1d": 0.50, "composite_5d": 0.30, "composite_20d": 0.20,
    "ma_ma20": 0.35, "ma_ma50": 0.30, "ma_slope": 0.35,
    "rs_3m": 0.60, "rs_1m": 0.40,
    "tech_rsi": 0.50, "tech_macd": 0.50,
}

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Client-side re-scoring
# ---------------------------------------------------------------------------

def _normalize(weights: dict, keys: list[str]) -> dict:
    """Return a copy with the given keys normalized to sum to 1.0."""
    total = sum(weights[k] for k in keys)
    if total == 0:
        return {k: 0.0 for k in keys}
    return {k: weights[k] / total for k in keys}


def recompute_scores(breakdown: dict, w: dict) -> tuple[float, float, float, float]:
    """Re-compute pillar + buy scores from sub-scores and custom weights."""
    liq = breakdown["liquidity"]
    nw = _normalize(w, ["liq_gtgd20", "liq_intraday", "liq_cv"])
    liq_score = (nw["liq_gtgd20"] * liq["gtgd20"]["score"]
                 + nw["liq_intraday"] * liq["intraday_ratio"]["score"]
                 + nw["liq_cv"] * liq["cv"]["score"])

    mom = breakdown["momentum"]
    nw_m = _normalize(w, ["mom_volatility", "mom_ma", "mom_rs", "mom_ad", "mom_tech"])
    mom_score = (nw_m["mom_volatility"] * mom["composite_return"]["score"]
                 + nw_m["mom_ma"] * mom["ma"]["score"]
                 + nw_m["mom_rs"] * mom["rs"]["score"]
                 + nw_m["mom_ad"] * mom["ad"]["score"]
                 + nw_m["mom_tech"] * mom["technical"]["score"])

    brk = breakdown["breakout"]
    if not brk.get("gate_active", False):
        brk_score = 0.0
    else:
        nw_b = _normalize(w, ["brk_price", "brk_vol", "brk_dryup", "brk_base", "brk_hold"])
        brk_score = (nw_b["brk_price"] * brk["breakout_ratio"]["score"]
                     + nw_b["brk_vol"] * brk["volume_ratio"]["score"]
                     + nw_b["brk_dryup"] * brk["dry_up_ratio"]["score"]
                     + nw_b["brk_base"] * brk["narrowing_ratio"]["score"]
                     + nw_b["brk_hold"] * brk["holding_ratio"]["score"])

    nw_top = _normalize(w, ["liquidity", "momentum", "breakout"])
    buy = (nw_top["liquidity"] * liq_score
           + nw_top["momentum"] * mom_score
           + nw_top["breakout"] * brk_score)

    return round(buy, 2), round(liq_score, 2), round(mom_score, 2), round(brk_score, 2)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_billion(val: float) -> str:
    return f"{val / 1e9:.1f}B"


def _fmt_pct(val: float) -> str:
    return f"{val:.2f}%"


def _fmt_ratio(val: float) -> str:
    return f"{val:.3f}"


def _fmt_score(val: float | int) -> str:
    if isinstance(val, int) or val == int(val):
        return str(int(val))
    return f"{val:.1f}"


# ---------------------------------------------------------------------------
# Countdown
# ---------------------------------------------------------------------------

def render_countdown(next_refresh_in: int):
    elapsed = REFRESH_INTERVAL - next_refresh_in
    fraction = max(0.0, min(1.0, elapsed / REFRESH_INTERVAL))
    mins, secs = divmod(next_refresh_in, 60)
    st.progress(fraction, text=f":material/schedule: Next refresh in **{mins}m {secs:02d}s**")


# ---------------------------------------------------------------------------
# Breakdown detail for a single stock
# ---------------------------------------------------------------------------

def render_breakdown(breakdown: dict, w: dict):
    """Render 3-column pillar breakdown for one stock."""
    col_liq, col_mom, col_brk = st.columns(3)

    # ── Liquidity ────────────────────────────────────────────────────────
    with col_liq:
        liq = breakdown["liquidity"]
        nw = _normalize(w, ["liq_gtgd20", "liq_intraday", "liq_cv"])
        liq_score = (nw["liq_gtgd20"] * liq["gtgd20"]["score"]
                     + nw["liq_intraday"] * liq["intraday_ratio"]["score"]
                     + nw["liq_cv"] * liq["cv"]["score"])
        with st.container(border=True):
            st.markdown(f":material/water_drop: **Liquidity** — {_fmt_score(liq_score)}")
            st.caption(f"GTGD20 ({nw['liq_gtgd20']:.0%}) | Intraday ({nw['liq_intraday']:.0%}) | CV ({nw['liq_cv']:.0%})")
            st.divider()
            st.markdown(f"**GTGD20**: {_fmt_billion(liq['gtgd20']['value'])}")
            st.caption(f"Score: {_fmt_score(liq['gtgd20']['score'])}")
            st.markdown(f"**Intraday ratio**: {_fmt_pct(liq['intraday_ratio']['value'] * 100)}")
            st.caption(f"Score: {_fmt_score(liq['intraday_ratio']['score'])}")
            st.markdown(f"**CV stability**: {_fmt_pct(liq['cv']['value'])}")
            st.caption(f"Score: {_fmt_score(liq['cv']['score'])}")

    # ── Momentum ─────────────────────────────────────────────────────────
    with col_mom:
        mom = breakdown["momentum"]
        nw_m = _normalize(w, ["mom_volatility", "mom_ma", "mom_rs", "mom_ad", "mom_tech"])
        mom_score = (nw_m["mom_volatility"] * mom["composite_return"]["score"]
                     + nw_m["mom_ma"] * mom["ma"]["score"]
                     + nw_m["mom_rs"] * mom["rs"]["score"]
                     + nw_m["mom_ad"] * mom["ad"]["score"]
                     + nw_m["mom_tech"] * mom["technical"]["score"])
        with st.container(border=True):
            st.markdown(f":material/speed: **Momentum** — {_fmt_score(mom_score)}")
            st.divider()
            # Composite return
            cr = mom["composite_return"]
            d = cr.get("detail", {})
            st.markdown(f"**Composite return**: {_fmt_pct(cr['value'])}")
            st.caption(f"Score: {_fmt_score(cr['score'])}  |  1D: {_fmt_pct(d.get('return_1d', 0))}  5D: {_fmt_pct(d.get('return_5d', 0))}  20D: {_fmt_pct(d.get('return_20d', 0))}")
            # MA
            ma = mom["ma"]
            md = ma.get("detail", {})
            st.markdown(f"**MA analysis**: score {_fmt_score(ma['score'])}")
            pvm20 = md.get("price_vs_ma20", {})
            pvm50 = md.get("price_vs_ma50", {})
            slope = md.get("slope_pct", {})
            st.caption(
                f"MA20: {_fmt_pct(pvm20.get('value', 0))} -> {_fmt_score(pvm20.get('score', 0))}  |  "
                f"MA50: {_fmt_pct(pvm50.get('value', 0))} -> {_fmt_score(pvm50.get('score', 0))}  |  "
                f"Slope: {_fmt_pct(slope.get('value', 0))} -> {_fmt_score(slope.get('score', 0))}"
            )
            # RS
            rs = mom["rs"]
            rd = rs.get("detail", {})
            st.markdown(f"**RS vs VN-Index**: {_fmt_pct(rs['value'])}")
            st.caption(f"Score: {_fmt_score(rs['score'])}  |  3M: {_fmt_pct(rd.get('rs_3m', 0))}  1M: {_fmt_pct(rd.get('rs_1m', 0))}")
            # A/D
            ad = mom["ad"]
            st.markdown(f"**A/D ratio**: {_fmt_ratio(ad['value'])}")
            st.caption(f"Score: {_fmt_score(ad['score'])}")
            # Technical
            tech = mom["technical"]
            td = tech.get("detail", {})
            rsi = td.get("rsi", {})
            macd = td.get("macd_histogram_pct", {})
            st.markdown(f"**Technical**: score {_fmt_score(tech['score'])}")
            st.caption(f"RSI: {rsi.get('value', 0):.1f} -> {_fmt_score(rsi.get('score', 0))}  |  MACD hist: {_fmt_pct(macd.get('value', 0))} -> {_fmt_score(macd.get('score', 0))}")

    # ── Breakout ─────────────────────────────────────────────────────────
    with col_brk:
        brk = breakdown["breakout"]
        gate = brk.get("gate_active", False)
        if not gate:
            brk_score = 0.0
        else:
            nw_b = _normalize(w, ["brk_price", "brk_vol", "brk_dryup", "brk_base", "brk_hold"])
            brk_score = (nw_b["brk_price"] * brk["breakout_ratio"]["score"]
                         + nw_b["brk_vol"] * brk["volume_ratio"]["score"]
                         + nw_b["brk_dryup"] * brk["dry_up_ratio"]["score"]
                         + nw_b["brk_base"] * brk["narrowing_ratio"]["score"]
                         + nw_b["brk_hold"] * brk["holding_ratio"]["score"])
        with st.container(border=True):
            st.markdown(f":material/rocket_launch: **Breakout** — {_fmt_score(brk_score)}")
            if not gate:
                st.warning("Gate CLOSED — breakout_ratio < 1.0, entire pillar = 0", icon=":material/block:")
            st.divider()
            st.markdown(f"**Breakout ratio**: {_fmt_ratio(brk['breakout_ratio']['value'])}")
            st.caption(f"Score: {_fmt_score(brk['breakout_ratio']['score'])}")
            st.markdown(f"**Volume ratio**: {_fmt_ratio(brk['volume_ratio']['value'])}")
            st.caption(f"Score: {_fmt_score(brk['volume_ratio']['score'])}")
            st.markdown(f"**Dry-up ratio**: {_fmt_ratio(brk['dry_up_ratio']['value'])}")
            st.caption(f"Score: {_fmt_score(brk['dry_up_ratio']['score'])}")
            st.markdown(f"**Base quality (narrowing)**: {_fmt_ratio(brk['narrowing_ratio']['value'])}")
            st.caption(f"Score: {_fmt_score(brk['narrowing_ratio']['score'])}")
            st.markdown(f"**Holding ratio**: {_fmt_pct(brk['holding_ratio']['value'] * 100)}")
            st.caption(f"Score: {_fmt_score(brk['holding_ratio']['score'])}")


# ---------------------------------------------------------------------------
# Sidebar: weight settings
# ---------------------------------------------------------------------------

def _weight_input(label: str, key: str, default: float) -> float:
    return st.number_input(
        label, min_value=0.0, max_value=1.0,
        value=st.session_state.get(key, default),
        step=0.05, format="%.2f", key=key,
    )


def _show_sum_warning(keys: list[str], w: dict):
    total = sum(w[k] for k in keys)
    if abs(total - 1.0) > 0.001:
        st.caption(f":orange[Sum = {total:.2f} (will need to be normalized to 1.0)]")


def build_weights() -> dict:
    """Render sidebar weight controls and return current weights."""
    w = {}

    with st.sidebar:
        st.header("Layer 2 settings", anchor=False)

        if st.button("Reset to defaults", use_container_width=True):
            for k in DEFAULT_WEIGHTS:
                if f"w_{k}" in st.session_state:
                    del st.session_state[f"w_{k}"]
            st.rerun()

        st.subheader("Pillar weights", anchor=False)
        w["liquidity"] = _weight_input("Liquidity", "w_liquidity", DEFAULT_WEIGHTS["liquidity"])
        w["momentum"] = _weight_input("Momentum", "w_momentum", DEFAULT_WEIGHTS["momentum"])
        w["breakout"] = _weight_input("Breakout", "w_breakout", DEFAULT_WEIGHTS["breakout"])
        _show_sum_warning(["liquidity", "momentum", "breakout"], w)

        with st.expander("Liquidity sub-weights"):
            w["liq_gtgd20"] = _weight_input("GTGD20", "w_liq_gtgd20", DEFAULT_WEIGHTS["liq_gtgd20"])
            w["liq_intraday"] = _weight_input("Intraday activity", "w_liq_intraday", DEFAULT_WEIGHTS["liq_intraday"])
            w["liq_cv"] = _weight_input("CV stability", "w_liq_cv", DEFAULT_WEIGHTS["liq_cv"])
            _show_sum_warning(["liq_gtgd20", "liq_intraday", "liq_cv"], w)

        with st.expander("Momentum sub-weights"):
            w["mom_volatility"] = _weight_input("Price volatility", "w_mom_volatility", DEFAULT_WEIGHTS["mom_volatility"])
            w["mom_ma"] = _weight_input("MA analysis", "w_mom_ma", DEFAULT_WEIGHTS["mom_ma"])
            w["mom_rs"] = _weight_input("Relative strength", "w_mom_rs", DEFAULT_WEIGHTS["mom_rs"])
            w["mom_ad"] = _weight_input("A/D ratio", "w_mom_ad", DEFAULT_WEIGHTS["mom_ad"])
            w["mom_tech"] = _weight_input("Technical (RSI+MACD)", "w_mom_tech", DEFAULT_WEIGHTS["mom_tech"])
            _show_sum_warning(["mom_volatility", "mom_ma", "mom_rs", "mom_ad", "mom_tech"], w)

        with st.expander("Breakout sub-weights"):
            w["brk_price"] = _weight_input("Price breakout", "w_brk_price", DEFAULT_WEIGHTS["brk_price"])
            w["brk_vol"] = _weight_input("Volume confirm", "w_brk_vol", DEFAULT_WEIGHTS["brk_vol"])
            w["brk_dryup"] = _weight_input("Volume dry-up", "w_brk_dryup", DEFAULT_WEIGHTS["brk_dryup"])
            w["brk_base"] = _weight_input("Base quality", "w_brk_base", DEFAULT_WEIGHTS["brk_base"])
            w["brk_hold"] = _weight_input("Holding ratio", "w_brk_hold", DEFAULT_WEIGHTS["brk_hold"])
            _show_sum_warning(["brk_price", "brk_vol", "brk_dryup", "brk_base", "brk_hold"], w)

    return w


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

weights = build_weights()

latest = fetch_latest()
if latest is None:
    st.stop()

cached = st.session_state.get("layer2_data")
if cached is None or cached.get("scored_at") != latest.get("scored_at"):
    st.session_state["layer2_data"] = latest

data = st.session_state["layer2_data"]

render_countdown(latest.get("next_refresh_in", REFRESH_INTERVAL))

scores = data.get("scores", [])
scored_at = data.get("scored_at")

if not scores:
    st.info(
        "No Layer 2 scores yet. The scheduler refreshes every 5 minutes once Layer 1 has passed symbols.",
        icon=":material/hourglass_empty:",
    )
    st.stop()

# Check if breakdowns are available
has_breakdown = scores[0].get("breakdown") is not None

# Recompute scores with custom weights (if breakdowns exist)
if has_breakdown:
    for s in scores:
        buy, liq, mom, brk = recompute_scores(s["breakdown"], weights)
        s["_buy_score"] = buy
        s["_liquidity_score"] = liq
        s["_momentum_score"] = mom
        s["_breakout_score"] = brk
    scores.sort(key=lambda s: s["_buy_score"], reverse=True)

with st.container(horizontal=True):
    st.metric("Total scored", len(scores), border=True)

if scored_at:
    st.caption(f":material/schedule: Scored at `{scored_at[:19]}`")

watchlist = st.session_state.get("watchlist", set())

# Summary table
rows = [
    {
        "★": s["symbol"] in watchlist,
        "Symbol": s["symbol"],
        "Exchange": s["exchange"],
        "BUY Score": s.get("_buy_score", s["buy_score"]),
        "Liquidity": s.get("_liquidity_score", s["liquidity_score"]),
        "Momentum": s.get("_momentum_score", s["momentum_score"]),
        "Breakout": s.get("_breakout_score", s["breakout_score"]),
    }
    for s in scores
]
df = pd.DataFrame(rows)

st.subheader(f"Scored stocks ({len(scores)})", anchor=False)

ctrl_search, ctrl_watch, ctrl_dl = st.columns([2, 1, 1])
with ctrl_search:
    query = st.text_input(
        "Search symbol",
        key="layer2_search",
        placeholder="e.g. VC",
        label_visibility="collapsed",
    )
with ctrl_watch:
    watchlist_only = st.toggle("★ only", key="layer2_watch_only")

today_str = datetime.now().strftime("%Y%m%d")
with ctrl_dl:
    st.download_button(
        "Download CSV",
        data=df.drop(columns=["★"]).to_csv(index=False).encode("utf-8"),
        file_name=f"layer2_scores_{today_str}.csv",
        mime="text/csv",
        use_container_width=True,
        icon=":material/download:",
    )

view_df = df.copy()
if query.strip():
    q = query.strip().upper()
    view_df = view_df[view_df["Symbol"].str.upper().str.startswith(q)]
if watchlist_only:
    view_df = view_df[view_df["Symbol"].isin(watchlist)]

edited = st.data_editor(
    view_df,
    use_container_width=True,
    hide_index=True,
    disabled=[c for c in view_df.columns if c != "★"],
    column_config={
        "★": st.column_config.CheckboxColumn("★", help="Add to watchlist", pinned=True),
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
    key="layer2_editor",
)

# Sync watchlist from edited star column (only for visible rows)
if not edited.empty:
    visible_symbols = set(view_df["Symbol"].tolist())
    starred = set(edited.loc[edited["★"] == True, "Symbol"].tolist())  # noqa: E712
    new_watchlist = (watchlist - visible_symbols) | starred
    if new_watchlist != watchlist:
        st.session_state["watchlist"] = new_watchlist
        st.rerun()

# Per-stock breakdown
if has_breakdown:
    st.divider()
    st.subheader("Score breakdown", anchor=False)

    symbol_list = [s["symbol"] for s in scores]
    selected = st.selectbox(
        "Select stock to inspect",
        options=symbol_list,
        index=0,
    )

    stock = next(s for s in scores if s["symbol"] == selected)
    buy_s = stock.get("_buy_score", stock["buy_score"])
    st.markdown(f"**{selected}** ({stock['exchange']}) — BUY Score: **{buy_s}**")
    render_breakdown(stock["breakdown"], weights)
