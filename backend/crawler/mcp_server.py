"""MCP server exposing crawler functions as tools."""

import sys
import asyncio
from pathlib import Path

# Ensure backend/ is on the path so crawler imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from crawler.crawler import get_all_symbols, get_trading_history, get_intraday, run_full_crawl

mcp = FastMCP("stock-crawler")


@mcp.tool()
def list_symbols() -> list[dict]:
    """Return all stock symbols from HOSE and HNX exchanges.

    Each item has keys: symbol, exchange.
    """
    return get_all_symbols()


@mcp.tool()
def trading_history(symbol: str, days: int = 90) -> list[dict]:
    """Return daily OHLCV history for a stock symbol.

    Args:
        symbol: Stock ticker, e.g. "VCB".
        days: Number of calendar days to look back (default 90).

    Each row has keys: time, open, high, low, close, volume.
    """
    return get_trading_history(symbol, days)


@mcp.tool()
def intraday_data(symbol: str) -> list[dict]:
    """Return today's intraday tick data for a stock symbol.

    Args:
        symbol: Stock ticker, e.g. "VCB".

    Each row has keys: time, price, volume.
    """
    return get_intraday(symbol)


@mcp.tool()
def full_crawl(history_days: int = 90) -> str:
    """Run a full crawl of all symbols and persist data to the database.

    Args:
        history_days: Number of calendar days of OHLCV history to fetch (default 90).

    Returns a status message when complete.
    """
    asyncio.run(run_full_crawl(history_days=history_days))
    return "Crawl completed successfully."


if __name__ == "__main__":
    mcp.run()
