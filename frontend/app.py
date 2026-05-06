"""Vietnam Stock Filter — multi-page Streamlit app."""

import streamlit as st

st.set_page_config(
    page_title="Vietnam Stock Filter",
    page_icon=":material/analytics:",
    layout="wide",
)

page = st.navigation(
    [
        st.Page("app_pages/layer1.py", title="Layer 1 — Hard filters", icon=":material/filter_list:"),
        st.Page("app_pages/layer2.py", title="Layer 2 — BUY score", icon=":material/trending_up:"),
        st.Page("app_pages/chat.py", title="Stock assistant", icon=":material/chat:"),
    ],
    position="top",
)

page.run()
