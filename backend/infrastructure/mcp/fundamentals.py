import asyncio
import json

from fastmcp import FastMCP

from infrastructure.market_data.fundamentals import (
    get_fundamentals as _get_fundamentals,
    get_balance_sheet as _get_balance_sheet,
    get_cashflow as _get_cashflow,
    get_income_statement as _get_income_statement,
)

mcp = FastMCP(name="fundamentals")


def _df_to_records(df) -> list:
    return json.loads(df.to_json(orient="records", force_ascii=False, date_format="iso", default_handler=str))


@mcp.tool
async def get_fundamentals(symbol: str, period: str = "year") -> dict:
    """Get financial ratios and company profile for a stock.

    Args:
        symbol: Stock symbol, e.g. VCB
        period: 'year' or 'quarter' (default 'year')
    """
    ratios, profile = await asyncio.to_thread(_get_fundamentals, symbol, period)
    return {
        "ratios": _df_to_records(ratios),
        "profile": _df_to_records(profile) if profile is not None else None,
    }


@mcp.tool
async def get_balance_sheet(symbol: str, period: str = "quarter", limit: int = 10) -> list:
    """Get balance sheet data for a stock.

    Args:
        symbol: Stock symbol, e.g. VCB
        period: 'year' or 'quarter' (default 'quarter')
        limit: Number of periods to return (default 10)
    """
    df = await asyncio.to_thread(_get_balance_sheet, symbol, period, limit)
    return _df_to_records(df)


@mcp.tool
async def get_cashflow(symbol: str, period: str = "quarter", limit: int = 10) -> list:
    """Get cash flow statement for a stock.

    Args:
        symbol: Stock symbol, e.g. VCB
        period: 'year' or 'quarter' (default 'quarter')
        limit: Number of periods to return (default 10)
    """
    df = await asyncio.to_thread(_get_cashflow, symbol, period, limit)
    return _df_to_records(df)


@mcp.tool
async def get_income_statement(symbol: str, period: str = "quarter", limit: int = 10) -> list:
    """Get income statement for a stock.

    Args:
        symbol: Stock symbol, e.g. VCB
        period: 'year' or 'quarter' (default 'quarter')
        limit: Number of periods to return (default 10)
    """
    df = await asyncio.to_thread(_get_income_statement, symbol, period, limit)
    return _df_to_records(df)


if __name__ == "__main__":
    mcp.run(transport="stdio")
