from dataclasses import dataclass


@dataclass
class McpConfig:
    servers: list[str]
    allowed_tools: list[str]


ALL_TOOLS = McpConfig(
    servers=["data", "news", "fundamentals"],
    allowed_tools=[
        "mcp__data__list_symbols",
        "mcp__data__trading_history",
        "mcp__data__intraday_data",
        "mcp__data__stock_price",
        "mcp__data__compare_stocks",
        "mcp__news__stock_news",
        "mcp__news__market_news",
        "mcp__news__search_news",
        "mcp__news__trending_topics",
        "mcp__fundamentals__get_fundamentals",
        "mcp__fundamentals__get_balance_sheet",
        "mcp__fundamentals__get_cashflow",
        "mcp__fundamentals__get_income_statement",
    ],
)

DATA_ONLY = McpConfig(
    servers=["data"],
    allowed_tools=[
        "mcp__data__list_symbols",
        "mcp__data__trading_history",
        "mcp__data__intraday_data",
        "mcp__data__stock_price",
        "mcp__data__compare_stocks",
    ],
)

NEWS_ONLY = McpConfig(
    servers=["news"],
    allowed_tools=[
        "mcp__news__stock_news",
        "mcp__news__market_news",
        "mcp__news__search_news",
        "mcp__news__trending_topics",
    ],
)

FUNDAMENTALS_ONLY = McpConfig(
    servers=["fundamentals"],
    allowed_tools=[
        "mcp__fundamentals__get_fundamentals",
        "mcp__fundamentals__get_balance_sheet",
        "mcp__fundamentals__get_cashflow",
        "mcp__fundamentals__get_income_statement",
    ],
)
