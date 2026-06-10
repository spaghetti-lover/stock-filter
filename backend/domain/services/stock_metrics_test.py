"""
Tests for the pure Layer 1 metric functions (domain/services/stock_metrics.py).

These functions used to live inside infrastructure/persistence/ with a
ThreadPoolExecutor module-global, which made them effectively untestable.
After the split they're pure — they take dicts and return entities/primitives.

Run from backend/:
    uv run python3 -B -m pytest backend/domain/services/stock_metrics_test.py -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from domain.services.stock_metrics import (
    compute_market_regime,
    compute_stock_metrics,
    detect_ceiling_floor,
    get_expected_fraction_at_time,
)


# ---------- get_expected_fraction_at_time ----------

def test_fraction_before_open_is_zero():
    assert get_expected_fraction_at_time(8, 30) == 0.0


def test_fraction_after_close_is_one():
    assert get_expected_fraction_at_time(15, 30) == 1.0


def test_fraction_at_slot_anchor_matches_table():
    # The 9:30 slot is index 1 in INTRADAY_CUMULATIVE.
    assert get_expected_fraction_at_time(9, 30) == 0.22


def test_fraction_interpolates_between_anchors():
    # Halfway between (9, 30) → 0.22 and (10, 0) → 0.30 should be 0.26.
    assert get_expected_fraction_at_time(9, 45) == 0.26


# ---------- compute_market_regime ----------

def _vnindex(closes: list[float]) -> list[dict]:
    return [{"close": c} for c in closes]


def test_regime_returns_none_when_under_20_rows():
    assert compute_market_regime(_vnindex([1000.0] * 19)) is None


def test_regime_returns_none_when_empty():
    assert compute_market_regime([]) is None


def test_regime_uses_last_20_for_ma20():
    # 20 closes at 1000 → ma20 = 1000, ma5 = 1000, close = 1000, ratio = 1.0.
    rows = _vnindex([1000.0] * 20)
    regime = compute_market_regime(rows)
    assert regime is not None
    assert regime.vnindex_close == 1000.0
    assert regime.vnindex_ma20 == 1000.0
    assert regime.vnindex_ma5 == 1000.0


def test_regime_detects_downtrend():
    # Last 20 closes drop steeply: ma5 << ma20 and close < ma20 by > 3%.
    closes = [1100.0] * 15 + [950.0, 940.0, 930.0, 920.0, 900.0]
    regime = compute_market_regime(_vnindex(closes))
    assert regime is not None
    assert regime.state == "downtrend"


# ---------- detect_ceiling_floor ----------

def test_no_ceiling_or_floor_when_under_two_rows():
    assert detect_ceiling_floor("HOSE", [{"close": 100.0}]) == (False, False)


def test_hose_ceiling_at_7_percent_band():
    # HOSE band is 7%. Reference close = 100, ceiling = 107.
    rows = [{"close": 100.0}, {"close": 107.0}]
    is_ceiling, is_floor = detect_ceiling_floor("HOSE", rows)
    assert is_ceiling is True
    assert is_floor is False


def test_hnx_ceiling_uses_10_percent_band():
    # HNX band is 10%. 107 would NOT be a ceiling on HNX.
    rows = [{"close": 100.0}, {"close": 107.0}]
    assert detect_ceiling_floor("HNX", rows) == (False, False)
    rows = [{"close": 100.0}, {"close": 110.0}]
    assert detect_ceiling_floor("HNX", rows) == (True, False)


def test_floor_detection():
    rows = [{"close": 100.0}, {"close": 93.0}]
    assert detect_ceiling_floor("HOSE", rows) == (False, True)


def test_unknown_exchange_defaults_to_hose_band():
    rows = [{"close": 100.0}, {"close": 107.0}]
    assert detect_ceiling_floor("FOREIGN", rows) == (True, False)


# ---------- compute_stock_metrics ----------

def _history(closes_volumes: list[tuple[float, int]]) -> list[dict]:
    return [{"close": c, "volume": v} for c, v in closes_volumes]


def test_compute_returns_none_for_empty_history():
    assert compute_stock_metrics("VCB", "HOSE", [], [], 0.5) is None


def test_gtgd20_averages_last_20_sessions_in_vnd():
    # close=100 (thousands) × volume=1_000_000 × 1000 = 100B VND per session.
    rows = _history([(100.0, 1_000_000)] * 20)
    stock = compute_stock_metrics("VCB", "HOSE", rows, [], expected_fraction=1.0)
    assert stock is not None
    assert stock.gtgd20 == 100_000_000_000.0


def test_cv_requires_full_20_session_window():
    # Only 10 sessions → CV is None.
    rows = _history([(100.0, 1_000_000)] * 10)
    stock = compute_stock_metrics("VCB", "HOSE", rows, [], expected_fraction=1.0)
    assert stock is not None
    assert stock.cv is None


def test_cv_is_zero_when_volume_perfectly_stable():
    rows = _history([(100.0, 1_000_000)] * 20)
    stock = compute_stock_metrics("VCB", "HOSE", rows, [], expected_fraction=1.0)
    assert stock is not None
    assert stock.cv == 0.0


def test_intraday_ratio_is_none_when_expected_is_zero():
    # expected_fraction=0 (pre-open) → avg_intraday_expected=0 → ratio is None.
    rows = _history([(100.0, 1_000_000)] * 20)
    stock = compute_stock_metrics("VCB", "HOSE", rows, [], expected_fraction=0.0)
    assert stock is not None
    assert stock.intraday_ratio is None


def test_history_sessions_counts_all_rows():
    rows = _history([(100.0, 1_000_000)] * 45)
    stock = compute_stock_metrics("VCB", "HOSE", rows, [], expected_fraction=1.0)
    assert stock is not None
    assert stock.history_sessions == 45
