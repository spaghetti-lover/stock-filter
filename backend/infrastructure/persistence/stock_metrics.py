import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from domain.entities.stock import Stock
from domain.repositories.layer1_stock_repository import EarlyRejected, ProgressCallback
from domain.value_objects.market_regime import MarketRegime
from infrastructure.market_data.data import get_all_symbols, get_trading_history, get_intraday
from logger import get_logger

log = get_logger(__name__)

# Shared concurrency primitives for all repository implementations
executor = ThreadPoolExecutor(max_workers=30)
CONCURRENCY = 10

# --- Intraday time fraction ---

INTRADAY_TIME_SLOTS = [
    (9, 0), (9, 30), (10, 0), (10, 30), (11, 0), (11, 30),
    (13, 0), (13, 30), (14, 0), (14, 30), (15, 0)
]
INTRADAY_CUMULATIVE = [0.12, 0.22, 0.30, 0.37, 0.43, 0.48, 0.56, 0.65, 0.75, 0.86, 1.00]


def get_expected_fraction_at_time(hour: int, minute: int) -> float:
    if (hour, minute) < (9, 0):
        return 0.0
    for i, (h, m) in enumerate(INTRADAY_TIME_SLOTS):
        if (hour, minute) <= (h, m):
            if i == 0:
                return INTRADAY_CUMULATIVE[0]
            prev_h, prev_m = INTRADAY_TIME_SLOTS[i - 1]
            elapsed = (hour * 60 + minute) - (prev_h * 60 + prev_m)
            slot_len = (h * 60 + m) - (prev_h * 60 + prev_m)
            ratio = elapsed / max(slot_len, 1)
            return INTRADAY_CUMULATIVE[i - 1] + (INTRADAY_CUMULATIVE[i] - INTRADAY_CUMULATIVE[i - 1]) * ratio
    return 1.0


# --- Market regime ---

def compute_market_regime(rows: list[dict]) -> MarketRegime | None:
    if not rows or len(rows) < 20:
        return None
    closes = [r["close"] for r in rows]
    vnindex_close = closes[-1]
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    return MarketRegime.from_values(close=vnindex_close, ma5=ma5, ma20=ma20)


# --- Stock metrics ---

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


# --- Shared helpers for live fetch and DB persistence ---

async def fetch_all_stocks_live(
    exchanges: set[str] | None = None,
    min_gtgd: float = 0.0,
    min_history_sessions: int = 0,
    expected_fraction: float = 1.0,
    on_progress: ProgressCallback | None = None,
) -> tuple[list[Stock], list[EarlyRejected]]:
    """Fetch all stocks from the live API, compute metrics, and return results."""
    loop = asyncio.get_event_loop()
    fetch_days = max(int(min_history_sessions * 365 / 252) + 15, 90)

    symbols = await loop.run_in_executor(executor, get_all_symbols)
    if exchanges:
        symbols = [s for s in symbols if s["exchange"] in exchanges]
    log.info("fetch_all_stocks_live: %d symbols, fraction=%.2f, fetch_days=%d", len(symbols), expected_fraction, fetch_days)

    sem = asyncio.Semaphore(CONCURRENCY)
    total = len(symbols)
    processed_count = 0
    counter_lock = asyncio.Lock()

    async def process(item: dict) -> Stock | tuple[str, str, str]:
        nonlocal processed_count
        async with sem:
            symbol = item["symbol"]
            exchange = item["exchange"]
            try:
                log.info("Fetching %s (%s)", symbol, exchange)
                history_fut = loop.run_in_executor(executor, get_trading_history, symbol, fetch_days)
                intraday_fut = loop.run_in_executor(executor, get_intraday, symbol)
                history_rows, intraday_rows = await asyncio.gather(history_fut, intraday_fut)

                stock = compute_stock_metrics(symbol, exchange, history_rows, intraday_rows, expected_fraction)
                if stock is None:
                    log.debug("No history for %s, skipping", symbol)
                    result = (symbol, exchange, "No trading history available")
                elif stock.gtgd20 < min_gtgd:
                    log.debug("Skipping %s: gtgd20=%.2f < min_gtgd=%.2f", symbol, stock.gtgd20, min_gtgd)
                    result = (symbol, exchange, f"GTGD20 {stock.gtgd20 / 1e9:.1f}B < {min_gtgd / 1e9:.0f}B")
                else:
                    result = stock
            except Exception:
                log.warning("Failed to process %s", symbol, exc_info=True)
                result = (symbol, exchange, "Failed to fetch data")

        async with counter_lock:
            processed_count += 1
            log.info("Progress: %d/%d — %s", processed_count, total, symbol)
            if on_progress:
                await on_progress(processed_count, total, symbol)

        return result

    raw_results = await asyncio.gather(*[process(item) for item in symbols])
    stocks = [r for r in raw_results if isinstance(r, Stock)]
    early_rejected = [r for r in raw_results if isinstance(r, tuple)]
    log.info("fetch_all_stocks_live done: %d stocks, %d early-rejected", len(stocks), len(early_rejected))
    return stocks, early_rejected


async def save_stocks_to_db(stocks: list[Stock]) -> None:
    """Truncate stock_metrics and batch-insert all stocks."""
    from db.connection import get_pool

    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("TRUNCATE stock_metrics")
            now = datetime.now(tz=timezone.utc)
            await conn.executemany(
                """INSERT INTO stock_metrics
                   (symbol, exchange, status, price, gtgd20, history_sessions,
                    today_value, avg_intraday_expected, intraday_ratio,
                    is_ceiling, is_floor, cv, crawled_at)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)""",
                [
                    (
                        s.symbol, s.exchange, s.status, s.price, s.gtgd20,
                        s.history_sessions, s.today_value, s.avg_intraday_expected,
                        s.intraday_ratio, s.is_ceiling, s.is_floor, s.cv, now,
                    )
                    for s in stocks
                ],
            )
