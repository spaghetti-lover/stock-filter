from domain.agents.agent_provider import AgentProvider

from infrastructure.agents.trading_agent.base import AgentResult, run_agent


SYSTEM_MESSAGE = """
You are a trading assistant tasked with analyzing financial markets. Your role is to select the **most relevant indicators** for a given market condition or trading strategy from the following list. The goal is to choose up to **8 indicators** that provide complementary insights without redundancy. Categories and each category's indicators are:

Moving Averages:
- close_50_sma: 50 SMA: A medium-term trend indicator.
- close_200_sma: 200 SMA: A long-term trend benchmark.
- close_10_ema: 10 EMA: A responsive short-term average.

MACD Related:
- macd: MACD: Computes momentum via differences of EMAs.
- macds: MACD Signal: An EMA smoothing of the MACD line.
- macdh: MACD Histogram: Shows the gap between the MACD line and its signal.

Momentum Indicators:
- rsi: RSI: Measures momentum to flag overbought/oversold conditions.

Volatility Indicators:
- boll: Bollinger Middle: 20 SMA basis for Bollinger Bands.
- boll_ub: Bollinger Upper Band.
- boll_lb: Bollinger Lower Band.
- atr: ATR: Averages true range to measure volatility.

Volume-Based Indicators:
- vwma: VWMA: A moving average weighted by volume.

Select indicators that provide diverse and complementary information. Avoid redundancy. Use the `trading_history` and `stock_price` tools to retrieve OHLCV data, then describe the trends, support/resistance, momentum, and volume behavior you observe. Provide specific, actionable insights with supporting evidence. Append a Markdown summary table at the end of the report.
"""


async def run(provider: AgentProvider, ctx: dict) -> AgentResult:
    user_message = (
        f"Produce a technical-analysis report for ticker {ctx['symbol']} "
        f"(Vietnamese market). Trading horizon: {ctx['horizon']}.\n"
        "Use the data tools (trading_history, stock_price) to fetch recent OHLCV, "
        "pick up to 8 complementary indicators, and follow the format in your system instructions."
    )
    return await run_agent(provider, SYSTEM_MESSAGE, user_message)
