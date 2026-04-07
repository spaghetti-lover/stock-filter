"""Vietnam Stock Filter — Streamlit app."""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Vietnam Stock Filter", page_icon="📈", layout="wide")

st.title("📈 Vietnam Stock Filter")
st.caption(f"Data as of: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (simulated)")

tab_filter, tab_chat = st.tabs(["Stock Filter", "Stock Assistant"])

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
        min_value=1,
        max_value=500,
        value=60,
        step=5,
        help="Trading sessions only (excludes weekends & holidays). The lookup window is calendar days, so holidays reduce the actual session count.",
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

    st.divider()
    run = st.button("🔍 Filter Stocks", type="primary", use_container_width=True)

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
            "History (sessions)": s["history_sessions"],
            "Today value (B)": f"{s['today_value']/1e9:.2f}",
            "Expected by now (B)": f"{s['avg_intraday_expected']/1e9:.2f}",
            "Intraday ratio": f"{intraday_ratio*100:.0f}%" if intraday_ratio is not None else "N/A",
        }
        if include_reason:
            row["Reject reason"] = s.get("reject_reason", "")
        rows.append(row)
    return pd.DataFrame(rows)


# ── Tab: Stock Filter ─────────────────────────────────────────────────────────
with tab_filter:
    if not run:
        st.info("Configure filters in the sidebar and click **Filter Stocks** to run.")
    else:
        with st.spinner("Fetching data from API…"):
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
            }
            resp = requests.get("http://localhost:8000/stocks", params=params)
            if not resp.ok:
                st.error(f"API error {resp.status_code}: {resp.text}")
                st.stop()
            data = resp.json()

        passed = data["passed"]
        rejected = data["rejected"]
        st.session_state["last_stocks"] = passed + rejected

        col1, col2, col3 = st.columns(3)
        col1.metric("Total stocks scanned", len(passed) + len(rejected))
        col2.metric("✅ Passed", len(passed))
        col3.metric("❌ Filtered out", len(rejected))

        st.divider()

        st.subheader(f"✅ Passed stocks ({len(passed)})")
        if passed:
            st.dataframe(build_df(passed), use_container_width=True, hide_index=True)
        else:
            st.warning("No stocks passed all filters.")

        with st.expander(f"❌ Filtered-out stocks ({len(rejected)})", expanded=False):
            if rejected:
                st.dataframe(build_df(rejected, include_reason=True), use_container_width=True, hide_index=True)
            else:
                st.success("All stocks passed the filters.")


# ── Tab: Stock Assistant ──────────────────────────────────────────────────────
with tab_chat:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    provider = st.selectbox(
        "LLM provider",
        options=["claude", "gemini", "openai"],
        index=0,
        key="chat_provider",
    )

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask about stocks…"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        stocks_context = st.session_state.get("last_stocks")
        payload = {
            "messages": st.session_state.chat_messages,
            "stocks_context": stocks_context,
            "provider": provider,
        }
        with st.spinner("Thinking…"):
            resp = requests.post("http://localhost:8000/chat", json=payload)

        if not resp.ok:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            st.error(f"**{resp.status_code}** — {detail}")
            st.stop()

        answer = resp.json()["response"]
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        st.rerun()
