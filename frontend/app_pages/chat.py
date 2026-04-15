"""Stock assistant — chat page."""

import requests
import streamlit as st


# ── Sidebar: chat settings ────────────────────────────────────────────────────
with st.sidebar:
    provider = st.selectbox(
        "LLM provider",
        options=["claude", "gemini", "openai"],
        index=0,
        key="chat_provider",
    )


# ── Main content ──────────────────────────────────────────────────────────────

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

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
