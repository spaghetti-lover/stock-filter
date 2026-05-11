from vnstock_data import Fundamental, Company


def get_fundamentals(symbol: str, period: str = "year") -> tuple:
    """Get financial ratios and company profile."""
    fun = Fundamental()
    ratios = fun.equity(symbol).ratio(period=period)
    profile = Company(source="KBS", symbol=symbol).overview()
    return ratios, profile


def get_balance_sheet(symbol: str, period: str = "quarter", limit: int = 10):
    """Get balance sheet data."""
    return Fundamental().equity(symbol).balance_sheet(period=period, limit=limit)


def get_cashflow(symbol: str, period: str = "quarter", limit: int = 10):
    """Get cash flow statement data."""
    return Fundamental().equity(symbol).cash_flow(period=period, limit=limit)


def get_income_statement(symbol: str, period: str = "quarter", limit: int = 10):
    """Get income statement data."""
    return Fundamental().equity(symbol).income_statement(period=period, limit=limit)
