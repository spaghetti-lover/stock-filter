from dataclasses import dataclass
from typing import Literal

MarketRegimeState = Literal["uptrend", "choppy", "downtrend"]


@dataclass(frozen=True)
class MarketRegime:
    state: MarketRegimeState
    vnindex_close: float
    vnindex_ma5: float
    vnindex_ma20: float
    ratio: float  # vnindex_close / vnindex_ma20

    @classmethod
    def from_values(cls, close: float, ma5: float, ma20: float) -> "MarketRegime":
        ratio = close / ma20 if ma20 > 0 else 0.0
        if ratio < 0.97 and ma5 < ma20:
            state: MarketRegimeState = "downtrend"
        elif ratio < 1.00:
            state = "choppy"
        else:
            state = "uptrend"
        return cls(state=state, vnindex_close=close, vnindex_ma5=ma5, vnindex_ma20=ma20, ratio=ratio)
