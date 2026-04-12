from domain.entities.stock import Stock

_BAND = {"HOSE": 0.07, "HNX": 0.10, "UPCOM": 0.15}
_CEILING_FLOOR_TOLERANCE = 0.005


def _detect_ceiling_floor(exchange: str, history_rows: list[dict]) -> tuple[bool, bool]:
    """Return (is_ceiling, is_floor) for the latest session."""
    if len(history_rows) < 2:
        return False, False
    ref = history_rows[-2]["close"]
    if not ref:
        return False, False
    band = _BAND.get(exchange, 0.07)
    close = history_rows[-1]["close"]
    ceiling = ref * (1 + band)
    floor = ref * (1 - band)
    is_ceiling = abs(close - ceiling) / ceiling <= _CEILING_FLOOR_TOLERANCE
    is_floor = abs(close - floor) / floor <= _CEILING_FLOOR_TOLERANCE
    return is_ceiling, is_floor


def compute_stock_metrics(
    symbol: str,
    exchange: str,
    history_rows: list[dict],
    intraday_rows: list[dict],
    expected_fraction: float,
) -> Stock | None:
    """Compute all stock metrics from raw OHLCV + intraday data.

    Returns a Stock entity, or None if history is empty.
    """
    if not history_rows:
        return None

    current_price = history_rows[-1]["close"]
    history_sessions = len(history_rows)
    last20_values = [r["close"] * 1000 * r["volume"] for r in history_rows[-20:]]
    gtgd20 = sum(last20_values) / len(last20_values)

    if len(last20_values) >= 20 and gtgd20 > 0:
        variance = sum((x - gtgd20) ** 2 for x in last20_values) / len(last20_values)
        cv = (variance ** 0.5 / gtgd20) * 100.0
    else:
        cv = None

    today_value = sum(r["price"] * 1000 * r["volume"] for r in intraday_rows) if intraday_rows else 0.0
    avg_intraday_expected = gtgd20 * expected_fraction

    is_ceiling, is_floor = _detect_ceiling_floor(exchange, history_rows)

    return Stock(
        symbol=symbol,
        exchange=exchange,
        status="normal",
        price=current_price,
        gtgd20=gtgd20,
        history_sessions=history_sessions,
        today_value=today_value,
        avg_intraday_expected=avg_intraday_expected,
        intraday_ratio=today_value / avg_intraday_expected if avg_intraday_expected > 0 else None,
        is_ceiling=is_ceiling,
        is_floor=is_floor,
        cv=cv,
    )
