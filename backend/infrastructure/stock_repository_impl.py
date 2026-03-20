import random
from datetime import datetime
from domain.entities.stock import Stock
from domain.repositories.stock_repository import StockRepository

# Intraday cumulative fraction at each half-hour mark (Vietnam market 9:00–15:00, break 11:30–13:00)
INTRADAY_TIME_SLOTS = [
    (9, 0), (9, 30), (10, 0), (10, 30), (11, 0), (11, 30),
    (13, 0), (13, 30), (14, 0), (14, 30), (15, 0)
]
INTRADAY_CUMULATIVE = [0.12, 0.22, 0.30, 0.37, 0.43, 0.48, 0.56, 0.65, 0.75, 0.86, 1.00]


def _get_expected_fraction_at_time(hour: int, minute: int) -> float:
    """Return the expected cumulative fraction of daily trading value by a given time."""
    for i, (h, m) in enumerate(INTRADAY_TIME_SLOTS):
        if (hour, minute) <= (h, m):
            if i == 0:
                slot_start = (9, 0)
                elapsed = (hour * 60 + minute) - (slot_start[0] * 60 + slot_start[1])
                slot_len = (h * 60 + m) - (slot_start[0] * 60 + slot_start[1])
                frac = INTRADAY_CUMULATIVE[0] * (elapsed / max(slot_len, 1))
                return max(0.0, frac)
            prev_h, prev_m = INTRADAY_TIME_SLOTS[i - 1]
            prev_frac = INTRADAY_CUMULATIVE[i - 1]
            cur_frac = INTRADAY_CUMULATIVE[i]
            elapsed = (hour * 60 + minute) - (prev_h * 60 + prev_m)
            slot_len = (h * 60 + m) - (prev_h * 60 + prev_m)
            ratio = elapsed / max(slot_len, 1)
            return prev_frac + (cur_frac - prev_frac) * ratio
    return 1.0  # after market close


# (symbol, exchange, status, current_price, avg_gtgd20_billion, history_sessions)
STOCKS = [
    ("VCB",  "HOSE", "normal",       90000, 150.0, 200),
    ("BID",  "HOSE", "normal",       45000,  80.0, 200),
    ("VIC",  "HOSE", "normal",       55000,  60.0, 200),
    ("HPG",  "HOSE", "normal",       28000,  90.0, 200),
    ("VHM",  "HOSE", "normal",       42000,  45.0, 200),
    ("TCB",  "HOSE", "normal",       32000,  55.0, 200),
    ("MBB",  "HOSE", "normal",       22000,  70.0, 200),
    ("VNM",  "HOSE", "normal",       70000,  30.0, 200),
    ("MSN",  "HOSE", "normal",       65000,  25.0, 200),
    ("GAS",  "HOSE", "normal",       85000,  18.0, 200),
    ("FPT",  "HOSE", "normal",       95000,  35.0, 200),
    ("STB",  "HOSE", "normal",       18000,  40.0, 200),
    ("ACB",  "HOSE", "normal",       25000,  65.0, 200),
    ("EIB",  "HOSE", "warning",      17000,  22.0, 200),
    ("HAG",  "HOSE", "control",       8000,  15.0, 200),
    ("KBC",  "HOSE", "normal",       14000,  21.0, 200),
    ("DXG",  "HOSE", "restriction",  12000,  19.0, 200),
    ("NVL",  "HOSE", "normal",        3000,  20.0, 200),
    ("PDR",  "HOSE", "normal",        6000,   8.0, 200),
    ("HDB",  "HOSE", "normal",       26000,  42.0, 200),
    ("LPB",  "HOSE", "normal",       20000,  33.0, 200),
    ("VIB",  "HOSE", "normal",       18000,  28.0, 200),
    ("OCB",  "HOSE", "normal",       13000,  16.0, 200),
    ("SHB",  "HNX",  "normal",       12000,  25.0, 200),
    ("PVS",  "HNX",  "normal",       22000,  20.0, 200),
    ("IDC",  "HNX",  "normal",       38000,  22.0, 200),
    ("VCS",  "HNX",  "normal",       72000,  12.0, 200),
    ("CEO",  "HNX",  "warning",       9000,  10.0,  45),
    ("NTP",  "HNX",  "normal",       40000,  20.5,  55),
    ("HUT",  "HNX",  "normal",       15000,  21.0, 200),
    ("NEW",  "HOSE", "normal",       25000,  30.0,  30),
    ("TIN",  "HOSE", "normal",        4500,  25.0, 200),
]


def fetch_stock_list() -> list[Stock]:
    now = datetime.now()
    expected_fraction = _get_expected_fraction_at_time(now.hour, now.minute)

    result = []
    for symbol, exchange, status, price, gtgd20, history in STOCKS:
        daily_factor = random.uniform(0.6, 1.4)
        expected_today_full = gtgd20 * daily_factor
        intraday_factor = random.uniform(0.2, 1.1)
        today_value_so_far = expected_today_full * expected_fraction * intraday_factor
        avg_intraday_at_this_time = gtgd20 * expected_fraction

        stock = Stock(
            symbol=symbol,
            exchange=exchange,
            status=status,
            price=price,
            gtgd20=gtgd20 * 1e9,
            history_sessions=history,
            today_value=today_value_so_far * 1e9,
            avg_intraday_expected=avg_intraday_at_this_time * 1e9
        )
        result.append(stock)

    return result

class StockRepositoryImpl(StockRepository):
  def list_stocks(self):
      return fetch_stock_list()