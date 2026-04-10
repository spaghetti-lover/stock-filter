from typing import Literal

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
    cv: float | None = None
    reject_reason: str | None = None


class MarketRegimeResponse(BaseModel):
    state: Literal["uptrend", "choppy", "downtrend", "unknown"]
    vnindex_close: float | None = None
    vnindex_ma5: float | None = None
    vnindex_ma20: float | None = None
    ratio: float | None = None
    message: str | None = None
    gate_applied: bool = False


class FilteredStocksResponse(BaseModel):
    passed: list[GetStockResponse]
    rejected: list[GetStockResponse]
    market_regime: MarketRegimeResponse | None = None