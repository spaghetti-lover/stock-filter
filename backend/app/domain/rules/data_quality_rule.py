from typing import List
from app.domain.entities.ohlcv import OHLCV


def passes_data_quality_rule(ohlcv_list: List[OHLCV], min_days: int = 5) -> bool:
    return len(ohlcv_list) >= min_days
