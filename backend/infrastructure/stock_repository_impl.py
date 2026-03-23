from datetime import datetime

from domain.entities.stock import Stock
from domain.repositories.stock_repository import StockRepository
from crawler.crawler import get_all_symbols, get_trading_history, get_intraday

INTRADAY_TIME_SLOTS = [
    (9, 0), (9, 30), (10, 0), (10, 30), (11, 0), (11, 30),
    (13, 0), (13, 30), (14, 0), (14, 30), (15, 0)
]
INTRADAY_CUMULATIVE = [0.12, 0.22, 0.30, 0.37, 0.43, 0.48, 0.56, 0.65, 0.75, 0.86, 1.00]

def _get_expected_fraction_at_time(hour: int, minute: int) -> float:
    for i, (h, m) in enumerate(INTRADAY_TIME_SLOTS):
        if (hour, minute) <= (h, m):
            if i == 0:
                slot_start = (9, 0)
                elapsed = (hour * 60 + minute) - (slot_start[0] * 60 + slot_start[1])
                slot_len = (h * 60 + m) - (slot_start[0] * 60 + slot_start[1])
                return max(0.0, INTRADAY_CUMULATIVE[0] * (elapsed / max(slot_len, 1)))
            prev_h, prev_m = INTRADAY_TIME_SLOTS[i - 1]
            elapsed = (hour * 60 + minute) - (prev_h * 60 + prev_m)
            slot_len = (h * 60 + m) - (prev_h * 60 + prev_m)
            ratio = elapsed / max(slot_len, 1)
            return INTRADAY_CUMULATIVE[i - 1] + (INTRADAY_CUMULATIVE[i] - INTRADAY_CUMULATIVE[i - 1]) * ratio
    return 1.0


class StockRepositoryImpl(StockRepository):
    def list_stocks(self, exchanges: set[str] | None = None, min_gtgd: float = 0.0):
        now = datetime.now()
        expected_fraction = _get_expected_fraction_at_time(now.hour, now.minute)

        symbols = get_all_symbols()  # [{"symbol": ..., "exchange": ...}]
        if exchanges:
            symbols = [s for s in symbols if s["exchange"] in exchanges]

        result = []
        for item in symbols:
            symbol = item["symbol"]
            exchange = item["exchange"]

            # --- trading history: current_price, gtgd20, history_sessions ---
            history_rows = get_trading_history(symbol, days=60)
            if not history_rows:
                continue

            current_price = history_rows[-1]["close"]
            history_sessions = len(history_rows)
            last20_values = [r["close"] * r["volume"] for r in history_rows[-20:]]
            gtgd20 = sum(last20_values) / len(last20_values) # Gia tri giao dich 20 ngay gan nhat

            if gtgd20 < min_gtgd:
                continue

            # --- intraday: today_value ---
            intraday_rows = get_intraday(symbol)
            today_value = sum(r["price"] * r["volume"] for r in intraday_rows) if intraday_rows else 0.0

            # --- avg_intraday_expected: gtgd20 scaled by current time fraction ---
            avg_intraday_expected = gtgd20 * expected_fraction

            result.append(Stock(
                symbol=symbol,
                exchange=exchange,
                status="normal",
                price=current_price,
                gtgd20=gtgd20,
                history_sessions=history_sessions,
                today_value=today_value,
                avg_intraday_expected=avg_intraday_expected,
            ))

        return result
