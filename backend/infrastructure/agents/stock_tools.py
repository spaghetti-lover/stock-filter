"""SDK MCP tools for stock data, used by the Claude agent.

Wraps existing crawler functions as claude-agent-sdk tools so the LLM
can fetch live data during a conversation.
"""

import asyncio
import json

from claude_agent_sdk import tool, create_sdk_mcp_server

from infrastructure.market_data.data import get_all_symbols, get_trading_history, get_intraday
from infrastructure.market_data.news import get_stock_news, get_market_news, search_news, get_trending_topics


def _to_text(data) -> dict:
    """Wrap data as MCP text content."""
    text = json.dumps(data, ensure_ascii=False, default=str)
    return {"content": [{"type": "text", "text": text}]}


def _error(msg: str) -> dict:
    return {"content": [{"type": "text", "text": msg}], "is_error": True}


# ── Tools ────────────────────────────────────────────────────────────────────


@tool(
    "list_symbols",
    "List all stock symbols from HOSE and HNX exchanges. Returns symbol and exchange for each stock.",
    {"exchange": str},
)
async def list_symbols_tool(args: dict) -> dict:
    exchange_filter = args.get("exchange", "").upper()
    symbols = await asyncio.to_thread(get_all_symbols)
    if exchange_filter:
        symbols = [s for s in symbols if s["exchange"] == exchange_filter]
    return _to_text({"total": len(symbols), "symbols": symbols})


@tool(
    "trading_history",
    "Get daily OHLCV (open, high, low, close, volume) history for a stock symbol. "
    "Returns the most recent trading sessions.",
    {"symbol": str, "days": int},
)
async def trading_history_tool(args: dict) -> dict:
    symbol = args["symbol"].upper()
    days = args.get("days", 30)
    rows = await asyncio.to_thread(get_trading_history, symbol, days)
    if not rows:
        return _error(f"No trading history found for {symbol}")
    return _to_text({"symbol": symbol, "sessions": len(rows), "history": rows})


@tool(
    "intraday_data",
    "Get today's intraday tick data (time, price, volume) for a stock symbol. "
    "Only available during trading hours (9:00-15:00 Vietnam time).",
    {"symbol": str},
)
async def intraday_data_tool(args: dict) -> dict:
    symbol = args["symbol"].upper()
    rows = await asyncio.to_thread(get_intraday, symbol)
    if not rows:
        return _error(f"No intraday data for {symbol} (market may be closed)")
    return _to_text({"symbol": symbol, "ticks": len(rows), "data": rows})


@tool(
    "stock_price",
    "Get the current (latest closing) price and basic metrics for a stock. "
    "Returns price, recent high/low, average volume, and GTGD20.",
    {"symbol": str},
)
async def stock_price_tool(args: dict) -> dict:
    symbol = args["symbol"].upper()
    rows = await asyncio.to_thread(get_trading_history, symbol, 30)
    if not rows:
        return _error(f"No data found for {symbol}")

    latest = rows[-1]
    last_20 = rows[-20:] if len(rows) >= 20 else rows
    gtgd20 = sum(r["close"] * 1000 * r["volume"] for r in last_20) / len(last_20)
    avg_volume = sum(r["volume"] for r in last_20) / len(last_20)

    result = {
        "symbol": symbol,
        "current_price": latest["close"],
        "price_unit": "thousand VND",
        "latest_date": latest.get("time"),
        "high_30d": max(r["high"] for r in rows),
        "low_30d": min(r["low"] for r in rows),
        "avg_volume_20d": round(avg_volume),
        "gtgd20_billion": round(gtgd20 / 1e9, 2),
    }
    return _to_text(result)


@tool(
    "compare_stocks",
    "Compare key metrics (price, GTGD20, volume, 30-day high/low) for multiple stock symbols side by side. "
    "Provide 2-5 symbols separated by commas.",
    {"symbols": str},
)
async def compare_stocks_tool(args: dict) -> dict:
    raw = args["symbols"]
    symbol_list = [s.strip().upper() for s in raw.split(",") if s.strip()]
    if len(symbol_list) < 2:
        return _error("Provide at least 2 symbols separated by commas")
    if len(symbol_list) > 5:
        return _error("Maximum 5 symbols for comparison")

    results = []
    for sym in symbol_list:
        rows = await asyncio.to_thread(get_trading_history, sym, 30)
        if not rows:
            results.append({"symbol": sym, "error": "no data"})
            continue
        latest = rows[-1]
        last_20 = rows[-20:] if len(rows) >= 20 else rows
        gtgd20 = sum(r["close"] * 1000 * r["volume"] for r in last_20) / len(last_20)
        results.append({
            "symbol": sym,
            "current_price": latest["close"],
            "high_30d": max(r["high"] for r in rows),
            "low_30d": min(r["low"] for r in rows),
            "gtgd20_billion": round(gtgd20 / 1e9, 2),
            "sessions": len(rows),
        })
    return _to_text(results)


@tool(
    "stock_news",
    "Fetch recent news articles mentioning a specific stock symbol from CafeF RSS feed.",
    {"symbol": str, "limit": int},
)
async def stock_news_tool(args: dict) -> dict:
    symbol = args["symbol"].upper()
    limit = args.get("limit", 10)
    articles = await asyncio.to_thread(get_stock_news, symbol, limit)
    if not articles:
        return _error(f"No recent news found for {symbol}")
    return _to_text({"symbol": symbol, "count": len(articles), "articles": articles})


@tool(
    "market_news",
    "Fetch the latest general market and financial news from CafeF RSS feed.",
    {"limit": int},
)
async def market_news_tool(args: dict) -> dict:
    limit = args.get("limit", 10)
    articles = await asyncio.to_thread(get_market_news, limit)
    if not articles:
        return _error("No market news available")
    return _to_text({"count": len(articles), "articles": articles})


@tool(
    "search_news",
    "Search recent news by keyword across CafeF and VietStock RSS feeds. "
    "Useful for sector queries (e.g. 'ngân hàng', 'bất động sản'), company full names, or any topic.",
    {"keyword": str, "limit": int},
)
async def search_news_tool(args: dict) -> dict:
    keyword = args["keyword"]
    limit = args.get("limit", 10)
    articles = await asyncio.to_thread(search_news, keyword, limit)
    if not articles:
        return _error(f"No news found for keyword: {keyword}")
    return _to_text({"keyword": keyword, "count": len(articles), "articles": articles})


@tool(
    "trending_topics",
    "Get the most frequently appearing phrases in today's financial news headlines from CafeF. "
    "Returns trending n-gram phrases and their frequency counts.",
    {"top_n": int},
)
async def trending_topics_tool(args: dict) -> dict:
    top_n = args.get("top_n", 20)
    trends = await asyncio.to_thread(get_trending_topics, top_n)
    if not trends:
        return _error("No trending topics found")
    return _to_text({"top_n": top_n, "trends": trends})


# ── Server factory ───────────────────────────────────────────────────────────


_SERVER_NAME = "stock-data"

TOOL_NAMES = [
    f"mcp__{_SERVER_NAME}__list_symbols",
    f"mcp__{_SERVER_NAME}__trading_history",
    f"mcp__{_SERVER_NAME}__intraday_data",
    f"mcp__{_SERVER_NAME}__stock_price",
    f"mcp__{_SERVER_NAME}__compare_stocks",
    f"mcp__{_SERVER_NAME}__stock_news",
    f"mcp__{_SERVER_NAME}__market_news",
    f"mcp__{_SERVER_NAME}__search_news",
    f"mcp__{_SERVER_NAME}__trending_topics",
]


def create_stock_mcp_server():
    """Create an in-process SDK MCP server with all stock tools."""
    return create_sdk_mcp_server(
        name="stock-data",
        version="1.0.0",
        tools=[
            list_symbols_tool,
            trading_history_tool,
            intraday_data_tool,
            stock_price_tool,
            compare_stocks_tool,
            stock_news_tool,
            market_news_tool,
            search_news_tool,
            trending_topics_tool,
        ],
    )
