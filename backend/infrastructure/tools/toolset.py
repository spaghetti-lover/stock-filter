"""Per-agent tool selection. Each agent declares the tools it wants by name."""

from dataclasses import dataclass

from fastmcp import FastMCP

from infrastructure.tools.catalog import CATALOG, SERVER_INSTANCES


@dataclass(frozen=True)
class ToolSet:
    names: tuple[str, ...]

    def __post_init__(self) -> None:
        unknown = [n for n in self.names if n not in CATALOG]
        if unknown:
            raise ValueError(f"unknown tool names: {unknown}")

    def categories(self) -> tuple[str, ...]:
        return tuple(sorted({CATALOG[n] for n in self.names}))

    def mcp_servers(self) -> dict[str, FastMCP]:
        """FastMCP server instances grouped by category — for chat agents."""
        return {c: SERVER_INSTANCES[c] for c in self.categories()}

    def mcp_allowed_tool_ids(self) -> list[str]:
        """Tool IDs in the `mcp__<server>__<name>` format Claude SDK expects."""
        return [f"mcp__{CATALOG[n]}__{n}" for n in self.names]


CHAT_ALL = ToolSet(
    names=(
        "list_symbols",
        "trading_history",
        "intraday_data",
        "stock_price",
        "compare_stocks",
        "get_ohlcv",
        "get_indicator",
        "stock_news",
        "market_news",
        "search_news",
        "trending_topics",
        "get_fundamentals",
        "get_balance_sheet",
        "get_cashflow",
        "get_income_statement",
    )
)

MARKET_ANALYST = ToolSet(names=("get_ohlcv", "get_indicator"))

FUNDAMENTALS_ANALYST = ToolSet(
    names=(
        "get_fundamentals",
        "get_balance_sheet",
        "get_cashflow",
        "get_income_statement",
    )
)

NEWS_ANALYST = ToolSet(names=("stock_news", "market_news", "search_news", "trending_topics"))

SOCIAL_ANALYST = ToolSet(names=("stock_news", "search_news"))
