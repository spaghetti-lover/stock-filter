"""Live market scan — fans out per-symbol vnstock fetches, runs the pure
metric calc, and emits a typed signal (Stock or EarlyRejected) per symbol.

Owns the asyncio orchestration; delegates all computation to
``domain.services.stock_metrics``. The scanner intentionally does NOT
format user-facing rejection strings — it emits ``EarlyRejectKind`` so
the application layer (``Layer1UseCase``) can render messages using the
same rule formatters the regular filter uses.
"""

import asyncio

from domain.entities.stock import Stock
from domain.repositories.layer1_stock_repository import (
    EarlyRejected,
    EarlyRejectKind,
    ProgressCallback,
)
from domain.services.stock_metrics import compute_stock_metrics
from infrastructure.concurrency import CONCURRENCY, executor
from infrastructure.market_data.data import (
    get_all_symbols,
    get_intraday,
    get_trading_history,
)
from logger import get_logger

log = get_logger(__name__)


async def scan_market(
    exchanges: set[str] | None = None,
    min_gtgd: float = 0.0,
    min_history_sessions: int = 0,
    expected_fraction: float = 1.0,
    on_progress: ProgressCallback | None = None,
) -> tuple[list[Stock], list[EarlyRejected]]:
    loop = asyncio.get_event_loop()
    fetch_days = max(int(min_history_sessions * 365 / 252) + 15, 90)

    symbols = await loop.run_in_executor(executor, get_all_symbols)
    if exchanges:
        symbols = [s for s in symbols if s["exchange"] in exchanges]
    log.info(
        "scan_market: %d symbols, fraction=%.2f, fetch_days=%d",
        len(symbols), expected_fraction, fetch_days,
    )

    sem = asyncio.Semaphore(CONCURRENCY)
    total = len(symbols)
    processed_count = 0
    counter_lock = asyncio.Lock()

    async def process(item: dict) -> Stock | EarlyRejected:
        nonlocal processed_count
        async with sem:
            symbol = item["symbol"]
            exchange = item["exchange"]
            try:
                log.info("Fetching %s (%s)", symbol, exchange)
                history_fut = loop.run_in_executor(executor, get_trading_history, symbol, fetch_days)
                intraday_fut = loop.run_in_executor(executor, get_intraday, symbol)
                history_rows, intraday_rows = await asyncio.gather(history_fut, intraday_fut)

                stock = compute_stock_metrics(
                    symbol, exchange, history_rows, intraday_rows,
                    expected_fraction, item.get("status", "normal"),
                )
                if stock is None:
                    log.debug("No history for %s, skipping", symbol)
                    result: Stock | EarlyRejected = (symbol, exchange, EarlyRejectKind.NO_HISTORY, None)
                elif stock.gtgd20 < min_gtgd:
                    log.debug("Skipping %s: gtgd20=%.2f < min_gtgd=%.2f", symbol, stock.gtgd20, min_gtgd)
                    result = (symbol, exchange, EarlyRejectKind.BELOW_MIN_GTGD, stock.gtgd20)
                else:
                    result = stock
            except Exception:
                log.warning("Failed to process %s", symbol, exc_info=True)
                result = (symbol, exchange, EarlyRejectKind.FETCH_FAILED, None)

        async with counter_lock:
            processed_count += 1
            log.info("Progress: %d/%d — %s", processed_count, total, symbol)
            if on_progress:
                await on_progress(processed_count, total, symbol)

        return result

    raw_results = await asyncio.gather(*[process(item) for item in symbols])
    stocks = [r for r in raw_results if isinstance(r, Stock)]
    early_rejected: list[EarlyRejected] = [r for r in raw_results if isinstance(r, tuple)]
    log.info("scan_market done: %d stocks, %d early-rejected", len(stocks), len(early_rejected))
    return stocks, early_rejected
