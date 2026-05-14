from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

from infrastructure.tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
)


def create_market_analyst(llm, tools: list[BaseTool]):

    async def market_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        system_message = (
            """You are a trading assistant analyzing Vietnamese stocks. Select the **most relevant indicators** for the given market condition or strategy. Choose up to **8 indicators** that provide complementary insights without redundancy. Supported indicators (call `get_indicator` once per name):

Moving Averages:
- close_50_sma: 50 SMA — medium-term trend; dynamic support/resistance. Lags price; combine with faster indicators.
- close_200_sma: 200 SMA — long-term trend benchmark; golden/death cross. Reacts slowly; best for strategic confirmation.
- close_10_ema: 10 EMA — responsive short-term average; quick momentum shifts. Noisy in choppy markets.

MACD Related:
- macd: MACD line — momentum via differences of EMAs. Look for crossovers and divergence.
- macds: MACD signal — EMA smoothing of MACD line; crossovers trigger trades.
- macdh: MACD histogram — gap between MACD and signal; momentum strength and divergence.

Momentum:
- rsi: RSI — overbought/oversold with 70/30 thresholds; watch for divergence.

Volatility:
- boll: Bollinger middle (20 SMA) — dynamic benchmark.
- boll_ub: Bollinger upper band — overbought / breakout zone.
- boll_lb: Bollinger lower band — oversold zone.
- atr: ATR — volatility; use for stop-loss and position sizing.

Volume:
- vwma: VWMA — volume-weighted moving average; confirms trends with volume.

Workflow:
1. First call `get_ohlcv(symbol, days=120)` to retrieve recent OHLCV data.
2. Then call `get_indicator(symbol, indicator, days=120)` once per chosen indicator (use the EXACT indicator names above — wrong names will fail).
3. Avoid redundant picks (e.g. don't pick both `rsi` and a duplicate momentum oscillator).
4. Write a detailed, nuanced report explaining the trends and what they imply for traders. Include specific values, dates, and actionable insights."""
            + """ Append a Markdown table at the end of the report summarizing the key points."""
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)

        result = await chain.ainvoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
