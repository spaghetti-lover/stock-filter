"""Stock filtering logic."""

ALLOWED_EXCHANGES = {"HOSE", "HNX"}
ALLOWED_STATUSES = {"normal"}
MIN_GTGD20 = 20e9          # 20 billion VND
MIN_HISTORY_SESSIONS = 60
MIN_PRICE = 5_000           # VND
MIN_INTRADAY_RATIO = 0.30   # today's value must be >= 30% of expected
MIN_VOLUME = 5_000_000      # 5 million VND


def apply_filters(
    stocks: list[dict],
    exchanges: set[str] | None = None,
    min_gtgd20: float = MIN_GTGD20,
    allowed_statuses: set[str] = ALLOWED_STATUSES,
    min_history: int = MIN_HISTORY_SESSIONS,
    min_price: float = MIN_PRICE,
    min_intraday_ratio: float = MIN_INTRADAY_RATIO,
    min_volume: float = MIN_VOLUME,
    use_exchange: bool = True,
    use_gtgd20: bool = True,
    use_status: bool = True,
    use_history: bool = True,
    use_price: bool = True,
    use_intraday: bool = True,
    use_volume: bool = True,
) -> tuple[list[dict], list[dict]]:
    """
    Filter stocks and return (passed, rejected) lists.
    Each rejected stock includes a 'reject_reason' field.
    """
    if exchanges is None:
        exchanges = ALLOWED_EXCHANGES

    passed = []
    rejected = []

    for stock in stocks:
        reason = _check(
            stock,
            exchanges, min_gtgd20, allowed_statuses, min_history, min_price, min_intraday_ratio, min_volume,
            use_exchange, use_gtgd20, use_status, use_history, use_price, use_intraday, use_volume,
        )
        if reason:
            stock = {**stock, "reject_reason": reason}
            rejected.append(stock)
        else:
            passed.append(stock)

    return passed, rejected


def _check(
    s: dict,
    exchanges: set[str],
    min_gtgd20: float,
    allowed_statuses: set[str],
    min_history: int,
    min_price: float,
    min_intraday_ratio: float,
    min_volume: float,
    use_exchange: bool,
    use_gtgd20: bool,
    use_status: bool,
    use_history: bool,
    use_price: bool,
    use_intraday: bool,
    use_volume: bool,
) -> str | None:
    """Return rejection reason string, or None if stock passes all filters."""
    if use_exchange and s["exchange"] not in exchanges:
        return f"Exchange {s['exchange']} not in {sorted(exchanges)}"

    if use_status and s["status"] not in allowed_statuses:
        return f"Trading status: {s['status']}"

    if use_gtgd20 and s["gtgd20"] < min_gtgd20:
        return f"GTGD20 {s['gtgd20']/1e9:.1f}B < {min_gtgd20/1e9:.0f}B"

    if use_history and s["history_sessions"] < min_history:
        return f"Only {s['history_sessions']} sessions of history (need {min_history})"

    if use_price and s["current_price"] * 1000 < min_price:
        return f"Price {s['current_price'] * 1000:,.0f} VND < {min_price:,.0f} VND"

    if use_intraday and s["avg_intraday_expected"] > 0:
        ratio = s["today_value"] / s["avg_intraday_expected"]
        if ratio < min_intraday_ratio:
            return (
                f"Intraday activity {ratio*100:.0f}% of expected "
                f"({s['today_value']/1e9:.2f}B / {s['avg_intraday_expected']/1e9:.2f}B expected)"
            )

    if use_volume and s["today_value"] < min_volume:
        return f"Volume {s['today_value']/1e6:.1f}M VND < {min_volume/1e6:.0f}M VND"

    return None
