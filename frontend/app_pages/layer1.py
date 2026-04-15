"""Layer 1 — Hard filters page."""

import requests
import streamlit as st
import pandas as pd

from config import BACKEND_URL


# ── Sidebar: Layer 1 filter controls ─────────────────────────────────────────
with st.sidebar:
    st.header("Layer 1 filters", anchor=False)

    use_exchange = st.toggle("Exchange", value=True)
    exchanges = st.multiselect(
        "Exchange",
        options=["HOSE", "HNX", "UPCOM"],
        default=["HOSE", "HNX"],
        help="Only include stocks listed on the selected exchanges.",
        disabled=not use_exchange,
        label_visibility="collapsed",
    )

    use_gtgd20 = st.toggle("Min GTGD20 (billion VND)", value=True)
    min_gtgd20 = st.number_input(
        "Min GTGD20 (billion VND)",
        min_value=1.0,
        max_value=500.0,
        value=20.0,
        step=1.0,
        help="Average trading value of the last 20 sessions must be >= this value.",
        disabled=not use_gtgd20,
        label_visibility="collapsed",
    )

    use_status = st.toggle("Allowed trading statuses", value=True)
    allowed_statuses_labels = st.multiselect(
        "Allowed trading statuses",
        options=["normal", "warning", "control", "restriction"],
        default=["normal"],
        help="Exclude stocks not in the selected statuses.",
        disabled=not use_status,
        label_visibility="collapsed",
    )

    use_history = st.toggle("Min history (sessions)", value=True)
    min_history = st.number_input(
        "Min history (sessions)",
        min_value=20,
        max_value=500,
        value=60,
        step=5,
        help="Trading sessions only (excludes weekends & holidays).",
        disabled=not use_history,
        label_visibility="collapsed",
    )

    use_price = st.toggle("Min price (VND)", value=True)
    min_price = st.number_input(
        "Min price (VND)",
        min_value=100,
        max_value=1_000_000,
        value=5_000,
        step=500,
        help="Current price must be >= this value.",
        disabled=not use_price,
        label_visibility="collapsed",
    )

    use_volume = st.toggle("Min volume (million VND)", value=True)
    min_volume_m = st.number_input(
        "Min volume (million VND)",
        min_value=0.0,
        max_value=10_000.0,
        value=5.0,
        step=1.0,
        help="Today's trading volume (value) must be >= this amount.",
        disabled=not use_volume,
        label_visibility="collapsed",
    )

    use_intraday = st.toggle("Min intraday activity (%)", value=True)
    min_intraday_pct = st.slider(
        "Min intraday activity (%)",
        min_value=0,
        max_value=100,
        value=30,
        step=5,
        help=(
            "Today's trading value up to now must be >= X% of the expected value "
            "at this time of day (based on 20-session average)."
        ),
        disabled=not use_intraday,
        label_visibility="collapsed",
    )

    exclude_ceiling_floor = st.toggle("Exclude ceiling/floor stocks", value=True)

    use_cv = st.toggle("CV cap (%)", value=True)
    cv_cap = st.slider(
        "Coefficient of Variation",
        min_value=0,
        max_value=500,
        value=200,
        step=10,
        help=(
            "Filter out symbols with unstable trading value over the last 20 sessions. "
            "CV = std / mean x 100. High CV indicates irregular liquidity."
        ),
        disabled=not use_cv,
        label_visibility="collapsed",
    )

    market_regime_gate = st.toggle("Apply market regime gate", value=True)

    run = st.button("Filter stocks", type="primary", use_container_width=True, icon=":material/search:")


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_df(stocks: list[dict], include_reason: bool = False) -> pd.DataFrame:
    rows = []
    for s in stocks:
        intraday_ratio = s.get("intraday_ratio")
        row = {
            "Symbol": s["symbol"],
            "Exchange": s["exchange"],
            "Status": s["status"],
            "Price (VND)": f"{s['current_price'] * 1000:,.0f}",
            "GTGD20 (B)": f"{s['gtgd20']/1e9:.1f}",
            "History": s["history_sessions"],
            "Today val (B)": f"{s['today_value']/1e9:.2f}",
            "Expected (B)": f"{s['avg_intraday_expected']/1e9:.2f}",
            "Intraday %": f"{intraday_ratio*100:.0f}%" if intraday_ratio is not None else "—",
            "CV %": f"{s['cv']:.0f}" if s.get("cv") is not None else "—",
        }
        if include_reason:
            row["Reject reason"] = s.get("reject_reason", "")
        rows.append(row)
    return pd.DataFrame(rows)


def render_market_regime(regime: dict | None):
    if not regime:
        return
    state = regime["state"]
    msg = regime.get("message", "")
    if state == "downtrend":
        st.error(msg or "Market in downtrend — screener suspended", icon=":material/trending_down:")
    elif state == "choppy":
        st.warning(msg or "Market caution — VN-Index in choppy range", icon=":material/swap_vert:")
    elif state == "unknown" and msg:
        st.info(msg, icon=":material/help:")


# ── Main content ──────────────────────────────────────────────────────────────

if not run:
    st.info(
        "Configure filters in the sidebar and click **Filter stocks** to run.",
        icon=":material/tune:",
    )
else:
    params = {
        "exchanges": exchanges,
        "min_gtgd": min_gtgd20,
        "statuses": allowed_statuses_labels if allowed_statuses_labels else None,
        "min_history": min_history,
        "min_price": min_price,
        "min_intraday_ratio": min_intraday_pct / 100,
        "min_volume": min_volume_m * 1e6,
        "use_exchange": use_exchange,
        "use_gtgd20": use_gtgd20,
        "use_status": use_status,
        "use_history": use_history,
        "use_price": use_price,
        "use_intraday": use_intraday,
        "use_volume": use_volume,
        "exclude_ceiling_floor": exclude_ceiling_floor,
        "cv_cap": cv_cap,
        "use_cv": use_cv,
        "market_regime_gate": market_regime_gate,
    }

    data = None
    with st.spinner("Fetching data…"):
        resp = requests.get(f"{BACKEND_URL}/stocks", params=params)
        if not resp.ok:
            st.error(f"API error {resp.status_code}: {resp.text}")
            st.stop()
        data = resp.json()

    if data is None:
        st.error("No result received from API.")
        st.stop()

    render_market_regime(data.get("market_regime"))

    passed = data["passed"]
    rejected = data["rejected"]
    st.session_state["last_stocks"] = passed + rejected
    st.session_state["passed_stocks"] = passed

    # KPI row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total scanned", len(passed) + len(rejected))
    col2.metric("Passed", len(passed))
    col3.metric("Filtered out", len(rejected))

    # Passed stocks
    st.subheader(f"Passed stocks ({len(passed)})", anchor=False)
    if passed:
        st.dataframe(
            build_df(passed),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Symbol": st.column_config.TextColumn(pinned=True),
            },
        )
    else:
        st.warning("No stocks passed all filters.", icon=":material/filter_alt_off:")

    # Rejected stocks
    with st.expander(f"Filtered-out stocks ({len(rejected)})", expanded=False, icon=":material/block:"):
        if rejected:
            st.dataframe(
                build_df(rejected, include_reason=True),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("All stocks passed the filters.", icon=":material/check_circle:")
