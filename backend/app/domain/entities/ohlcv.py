from dataclasses import dataclass
from datetime import date


@dataclass
class OHLCV:
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
