"""
Tests for FilterCriteria, individual rules, and apply_filters (Layer 1 Hard Filter).

Run from backend/:
    uv run python3 -B -m pytest backend/application/layer1/layer1_test.py -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from application.dto.stock_dto import GetStockResponse
from application.layer1 import FilterCriteria
from application.layer1.rules import (
    CvCapRule,
    ExchangeAllowlistRule,
    MinGtgdRule,
    MinIntradayRatioRule,
    MinPriceRule,
)
from application.services.stock_filter import apply_filters


def _stock(
    symbol: str = "VCB",
    exchange: str = "HOSE",
    status: str = "normal",
    current_price: float = 100.0,
    gtgd20: float = 50e9,
    history_sessions: int = 100,
    today_value: float = 5e9,
    avg_intraday_expected: float = 5e9,
    cv: float | None = 30.0,
    is_ceiling: bool = False,
    is_floor: bool = False,
) -> GetStockResponse:
    return GetStockResponse(
        symbol=symbol,
        exchange=exchange,
        status=status,
        current_price=current_price,
        gtgd20=gtgd20,
        history_sessions=history_sessions,
        today_value=today_value,
        avg_intraday_expected=avg_intraday_expected,
        intraday_ratio=today_value / avg_intraday_expected if avg_intraday_expected else None,
        is_ceiling=is_ceiling,
        is_floor=is_floor,
        cv=cv,
    )


# ---------- Individual rule checks ----------

def test_min_gtgd_passes_when_above_threshold():
    rule = MinGtgdRule(threshold_vnd=20e9)
    assert rule.check(_stock(gtgd20=30e9)) is None


def test_min_gtgd_rejects_with_billions_message():
    rule = MinGtgdRule(threshold_vnd=20e9)
    reason = rule.check(_stock(gtgd20=10e9))
    assert reason == "GTGD20 10.0B < 20B"


def test_min_price_compares_in_vnd_not_thousands():
    # current_price is in thousands; threshold is raw VND.
    rule = MinPriceRule(threshold_vnd=10_000)
    assert rule.check(_stock(current_price=9.5)) == "Price 9,500 VND < 10,000 VND"
    assert rule.check(_stock(current_price=10.0)) is None


def test_min_intraday_ratio_auto_passes_when_no_expected():
    rule = MinIntradayRatioRule(ratio=0.5)
    assert rule.check(_stock(avg_intraday_expected=0)) is None


def test_cv_cap_ignores_none_cv():
    rule = CvCapRule(cap_pct=200.0)
    assert rule.check(_stock(cv=None)) is None
    assert rule.check(_stock(cv=210.0)) is not None


# ---------- FilterCriteria assembly ----------

def test_active_rules_skips_none_thresholds():
    criteria = FilterCriteria(
        exchanges=frozenset({"HOSE"}),
        min_gtgd_vnd=20e9,
        exclude_ceiling_floor=False,
    )
    rules = criteria.active_rules()
    assert len(rules) == 2  # exchange + gtgd
    assert isinstance(rules[0], ExchangeAllowlistRule)
    assert isinstance(rules[1], MinGtgdRule)


def test_wave_trader_default_has_expected_rules():
    rules = FilterCriteria.wave_trader_default().active_rules()
    assert len(rules) == 6  # exchanges, gtgd, history, price, cv_cap, ceiling/floor


# ---------- apply_filters: first-rejection-wins ----------

def test_apply_filters_passes_clean_stock():
    criteria = FilterCriteria(
        exchanges=frozenset({"HOSE"}),
        min_gtgd_vnd=20e9,
        exclude_ceiling_floor=True,
    )
    passed, rejected = apply_filters([_stock()], criteria)
    assert len(passed) == 1
    assert rejected == []


def test_apply_filters_first_rejection_wins():
    # Stock fails BOTH exchange (UPCOM not in allowed) and gtgd20 (below 20B).
    # Order in active_rules() is exchange-then-gtgd, so exchange reason must win.
    criteria = FilterCriteria(
        exchanges=frozenset({"HOSE"}),
        min_gtgd_vnd=20e9,
    )
    stock = _stock(exchange="UPCOM", gtgd20=5e9)
    passed, rejected = apply_filters([stock], criteria)
    assert passed == []
    assert len(rejected) == 1
    assert rejected[0].reject_reason is not None
    assert "Exchange UPCOM" in rejected[0].reject_reason
    assert "GTGD20" not in rejected[0].reject_reason


def test_apply_filters_no_rules_passes_everything():
    criteria = FilterCriteria(exclude_ceiling_floor=False)
    passed, rejected = apply_filters([_stock(), _stock(symbol="HPG")], criteria)
    assert len(passed) == 2
    assert rejected == []
