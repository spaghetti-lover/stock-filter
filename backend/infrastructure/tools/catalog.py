"""Single source of truth: tool name -> FastMCP server category.

Each tool is defined exactly once as @mcp.tool on a FastMCP instance in
infrastructure/mcp/. This module just wires the names together and exposes the
four server instances under one dict so adapters and toolsets can resolve them.
"""

from fastmcp import FastMCP

from infrastructure.mcp.data import mcp as _data_mcp
from infrastructure.mcp.discussions import mcp as _discussions_mcp
from infrastructure.mcp.news import mcp as _news_mcp
from infrastructure.mcp.fundamentals import mcp as _fundamentals_mcp
from infrastructure.mcp.indicators import mcp as _indicators_mcp
from infrastructure.mcp.youtube import mcp as _youtube_mcp


SERVER_INSTANCES: dict[str, FastMCP] = {
    "data": _data_mcp,
    "news": _news_mcp,
    "fundamentals": _fundamentals_mcp,
    "indicators": _indicators_mcp,
    "youtube": _youtube_mcp,
    "discussions": _discussions_mcp,
}


CATALOG: dict[str, str] = {
    # data
    "list_symbols": "data",
    "trading_history": "data",
    "intraday_data": "data",
    "stock_price": "data",
    "compare_stocks": "data",
    # indicators
    "get_ohlcv": "indicators",
    "get_indicator": "indicators",
    "make_chart": "indicators",
    # news
    "stock_news": "news",
    "market_news": "news",
    "search_news": "news",
    "trending_topics": "news",
    # fundamentals
    "get_fundamentals": "fundamentals",
    "get_balance_sheet": "fundamentals",
    "get_cashflow": "fundamentals",
    "get_income_statement": "fundamentals",
    # youtube
    "get_youtube_transcript": "youtube",
    # discussions
    "discussion_by_ticker": "discussions",
    "discussion_search": "discussions",
}
