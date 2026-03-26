"""Vietnam Stock Filter — Streamlit app."""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime

from filters import (
    apply_filters,
    MIN_HISTORY_SESSIONS,
    MIN_PRICE,
    MIN_INTRADAY_RATIO,
    MIN_VOLUME,
)

st.set_page_config(page_title="Vietnam Stock Filter", page_icon="📈", layout="wide")

st.title("📈 Vietnam Stock Filter")
st.caption(f"Data as of: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (simulated)")

# ── Sidebar: filter options ───────────────────────────────────────────────────
with st.sidebar:
    st.header("Filter Options")

    use_exchange = st.toggle("Exchange", value=True)
    exchanges = st.multiselect(
        "Exchange",
        options=["HOSE", "HNX", "UPCOM"],
        default=["HOSE", "HNX"],
        help="Only include stocks listed on the selected exchanges.",
        disabled=not use_exchange,
        label_visibility="collapsed",
    )

    use_gtgd20 = st.toggle("Min GTGD (billion VND)", value=True)
    min_gtgd20 = st.number_input(
        "Min GTGD (billion VND)",
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
        min_value=1,
        max_value=500,
        value=MIN_HISTORY_SESSIONS,
        step=5,
        help="Stock must have at least this many trading sessions of historical data.",
        disabled=not use_history,
        label_visibility="collapsed",
    )

    use_price = st.toggle("Min price (VND)", value=True)
    min_price = st.number_input(
        "Min price (VND)",
        min_value=100,
        max_value=1_000_000,
        value=int(MIN_PRICE),
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
        value=MIN_VOLUME / 1e6,
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
        value=int(MIN_INTRADAY_RATIO * 100),
        step=5,
        help=(
            "Today's trading value up to now must be >= X% of the expected value "
            "at this time of day (based on 20-session average)."
        ),
        disabled=not use_intraday,
        label_visibility="collapsed",
    )

    st.divider()
    run = st.button("🔍 Filter Stocks", type="primary", use_container_width=True)

# ── Main area ─────────────────────────────────────────────────────────────────
if not run:
    st.info("Configure filters in the sidebar and click **Filter Stocks** to run.")
    st.stop()

with st.spinner("Fetching data from API…"):
    raw_stocks = requests.get("http://localhost:8000/stocks").json()

passed, rejected = apply_filters(
    raw_stocks,
    exchanges=set(exchanges),
    min_gtgd20=min_gtgd20 * 1e9,
    allowed_statuses=set(allowed_statuses_labels),
    min_history=min_history,
    min_price=min_price,
    min_intraday_ratio=min_intraday_pct / 100,
    min_volume=min_volume_m * 1e6,
    use_exchange=use_exchange,
    use_gtgd20=use_gtgd20,
    use_status=use_status,
    use_history=use_history,
    use_price=use_price,
    use_intraday=use_intraday,
    use_volume=use_volume,
)

# ── Summary metrics ───────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Total stocks scanned", len(raw_stocks))
col2.metric("✅ Passed", len(passed))
col3.metric("❌ Filtered out", len(rejected))

st.divider()


def build_df(stocks: list[dict], include_reason: bool = False) -> pd.DataFrame:
    rows = []
    for s in stocks:
        intraday_ratio = s.get("intraday_ratio")
        row = {
            "Symbol": s["symbol"],
            "Exchange": s["exchange"],
            "Status": s["status"],
            "Price (VND)": f"{s['current_price'] * 1000:,.0f}",
            "GTGD (B)": f"{s['gtgd20']/1e9:.1f}",
            "History (sessions)": s["history_sessions"],
            "Today value (B)": f"{s['today_value']/1e9:.2f}",
            "Expected by now (B)": f"{s['avg_intraday_expected']/1e9:.2f}",
            "Intraday ratio": f"{intraday_ratio*100:.0f}%" if intraday_ratio is not None else "N/A",
        }
        if include_reason:
            row["Reject reason"] = s.get("reject_reason", "")
        rows.append(row)
    return pd.DataFrame(rows)


# ── Passed stocks ─────────────────────────────────────────────────────────────
st.subheader(f"✅ Passed stocks ({len(passed)})")
if passed:
    st.dataframe(build_df(passed), use_container_width=True, hide_index=True)
else:
    st.warning("No stocks passed all filters.")

# ── Rejected stocks ───────────────────────────────────────────────────────────
with st.expander(f"❌ Filtered-out stocks ({len(rejected)})", expanded=False):
    if rejected:
        st.dataframe(build_df(rejected, include_reason=True), use_container_width=True, hide_index=True)
    else:
        st.success("All stocks passed the filters.")
