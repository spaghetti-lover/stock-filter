from langchain_core.messages import HumanMessage, RemoveMessage


def get_trading_style_hint() -> str:
    """Return a one-line hint nudging the Market Analyst toward the right
    time horizon. Day Trading → intraday/hour; Swing Trading → daily."""
    from infrastructure.tradingagents.runtime_config import get_config
    style = (get_config().get("trading_style") or "swing").lower()
    if style == "day":
        return (
            "Trading style: DAY TRADING. Default time unit is HOUR — pull "
            "shorter OHLCV windows (e.g. days=20), favor intraday momentum, "
            "and frame entry/exit on the hourly horizon."
        )
    return (
        "Trading style: SWING TRADING. Default time unit is DAY — pull "
        "multi-month OHLCV windows (e.g. days=120), favor multi-day "
        "trend structure, and frame entry/exit on the daily horizon."
    )


def get_language_instruction() -> str:
    """Return a prompt instruction for the configured output language.

    Returns empty string when English (default), so no extra tokens are used.
    Only applied to user-facing agents (analysts, portfolio manager).
    Internal debate agents stay in English for reasoning quality.
    """
    from infrastructure.tradingagents.runtime_config import get_config
    lang = get_config().get("output_language", "English")
    if lang.strip().lower() == "english":
        return ""
    return f" Write your entire response in {lang}."


def build_instrument_context(ticker: str) -> str:
    """Describe the exact instrument so agents preserve the symbol verbatim."""
    return (
        f"The instrument to analyze is `{ticker}` on Vietnamese exchanges (HOSE/HNX/UPCOM). "
        "Use this exact ticker in every tool call, report, and recommendation. "
        "Prices are in thousands of VND."
    )


_SPEAKER_PREFIXES = (
    "Bull Analyst:",
    "Bear Analyst:",
    "Aggressive Analyst:",
    "Conservative Analyst:",
    "Neutral Analyst:",
)


def tail_history(history: str, n_turns: int = 3) -> str:
    """Return only the last `n_turns` speaker blocks of a debate transcript.

    Caps unbounded growth of `history + "\\n" + argument` so re-injected
    debate context stays small. With current `max_*_rounds=1` this is a
    no-op (history always <= n_turns blocks); it becomes load-bearing
    once rounds are bumped.
    """
    if not history or n_turns <= 0:
        return history or ""
    text = history
    indices = []
    for prefix in _SPEAKER_PREFIXES:
        start = 0
        while True:
            idx = text.find(prefix, start)
            if idx == -1:
                break
            indices.append(idx)
            start = idx + len(prefix)
    if len(indices) <= n_turns:
        return text
    indices.sort()
    cut = indices[-n_turns]
    return text[cut:]


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        placeholder = HumanMessage(content="Continue")
        return {"messages": removal_operations + [placeholder]}

    return delete_messages
