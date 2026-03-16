from typing import List
from app.domain.entities.ohlcv import OHLCV


def passes_price_rule(ohlcv_list: List[OHLCV], min_price: float = 5.0, max_price: float = 10_000.0) -> bool:
    if not ohlcv_list:
        return False
    latest_close = ohlcv_list[-1].close
    return min_price <= latest_close <= max_price
