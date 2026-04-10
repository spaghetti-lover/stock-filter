from pydantic import BaseModel


class GetStockResponse(BaseModel):
    symbol: str
    exchange: str
    status: str
    current_price: float
    gtgd20: float
    history_sessions: int
    today_value: float
    avg_intraday_expected: float
    intraday_ratio: float | None
    is_ceiling: bool = False
    is_floor: bool = False
    reject_reason: str | None = None


class FilteredStocksResponse(BaseModel):
    passed: list[GetStockResponse]
    rejected: list[GetStockResponse]