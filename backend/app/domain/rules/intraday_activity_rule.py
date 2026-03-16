from typing import List
from app.domain.entities.ohlcv import OHLCV


def passes_intraday_activity_rule(ohlcv_list: List[OHLCV], min_range_pct: float = 0.5) -> bool:
    if not ohlcv_list:
        return False
    latest = ohlcv_list[-1]
    if latest.open == 0:
        return False
    intraday_range_pct = (latest.high - latest.low) / latest.open * 100
    return intraday_range_pct >= min_range_pct
