from typing import List
from app.domain.entities.ohlcv import OHLCV


def passes_liquidity_rule(ohlcv_list: List[OHLCV], min_avg_volume: float = 100_000) -> bool:
    if not ohlcv_list:
        return False
    avg_volume = sum(o.volume for o in ohlcv_list) / len(ohlcv_list)
    return avg_volume >= min_avg_volume
