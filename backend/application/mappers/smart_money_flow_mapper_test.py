"""
Tests for smart_money_flow_mapper.py.

Run from backend/:
    uv run python3 -B -m pytest backend/application/mappers/smart_money_flow_mapper_test.py -v
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from domain.entities.smart_money_flow_day import SmartMoneyFlowDay
from domain.entities.smart_money_flow_series import SmartMoneyFlowSeries
from application.mappers.smart_money_flow_mapper import SmartMoneyFlowMapper


def _day(
    date: str = "2026-01-01",
    f_buy: float = 0.0, f_sell: float = 0.0,
    p_buy: float = 0.0, p_sell: float = 0.0,
    gtgd: float = 1_000_000_000.0,
    close: float = 100.0,
) -> SmartMoneyFlowDay:
    return SmartMoneyFlowDay(
        date=date,
        foreign_buy_value=f_buy, foreign_sell_value=f_sell,
        prop_buy_value=p_buy, prop_sell_value=p_sell,
        total_gtgd=gtgd, close_price=close,
    )


def _series(rows: list[SmartMoneyFlowDay]) -> SmartMoneyFlowSeries:
    return SmartMoneyFlowSeries(symbol="TEST", days_requested=len(rows), rows=rows)


def _map(rows: list[SmartMoneyFlowDay]):
    return SmartMoneyFlowMapper.to_response(_series(rows)).rows


# --- §2.1 four cases ---

def test_consensus_accumulation_all_positive():
    # Both foreign and prop buy heavily → both net% positive, sm = sum.
    row = _map([_day(f_buy=100, f_sell=20, p_buy=80, p_sell=30, gtgd=1000)])[0]
    assert row.foreign_net_pct == 8.0       # (100-20)/1000 * 100
    assert row.prop_net_pct == 5.0          # (80-30)/1000 * 100
    assert row.sm_net_pct == 13.0
    assert row.sm_net_pct_uncapped == 13.0


def test_consensus_distribution_all_negative():
    row = _map([_day(f_buy=20, f_sell=100, p_buy=30, p_sell=80, gtgd=1000)])[0]
    assert row.foreign_net_pct == -8.0
    assert row.prop_net_pct == -5.0
    assert row.sm_net_pct == -13.0


def test_divergence_foreign_up_prop_down():
    # F net = +5%, P net = -2% → divergence "prop_taking_profit"
    # foreign > 3% and prop < -1%
    row = _map([_day(f_buy=70, f_sell=20, p_buy=10, p_sell=30, gtgd=1000)])[0]
    assert row.foreign_net_pct == 5.0
    assert row.prop_net_pct == -2.0
    assert row.divergence_type == "prop_taking_profit"
    assert row.sm_net_pct == 3.0   # sum of mixed signs


def test_divergence_foreign_down_prop_up():
    # F net = -5%, P net = +2% → divergence "prop_supporting"
    row = _map([_day(f_buy=20, f_sell=70, p_buy=30, p_sell=10, gtgd=1000)])[0]
    assert row.foreign_net_pct == -5.0
    assert row.prop_net_pct == 2.0
    assert row.divergence_type == "prop_supporting"


# --- §10 capping ---

def test_cap_at_plus_25_preserves_uncapped():
    # Construct so foreign net% = +30 and prop net% = +30 → sum 60.
    row = _map([_day(f_buy=400, f_sell=100, p_buy=400, p_sell=100, gtgd=1000)])[0]
    assert row.sm_net_pct == 25.0
    assert row.sm_net_pct_uncapped == 60.0


def test_cap_at_minus_25_preserves_uncapped():
    row = _map([_day(f_buy=100, f_sell=400, p_buy=100, p_sell=400, gtgd=1000)])[0]
    assert row.sm_net_pct == -25.0
    assert row.sm_net_pct_uncapped == -60.0


def test_no_cap_within_bounds():
    row = _map([_day(f_buy=120, f_sell=20, p_buy=70, p_sell=30, gtgd=1000)])[0]
    # foreign 10, prop 4, sum 14 → within bounds
    assert row.sm_net_pct == 14.0
    assert row.sm_net_pct_uncapped == 14.0


# --- §4.5 rolling 5d ---

def test_rolling_5d_returns_null_for_first_4_rows():
    # 4 sessions only → all sm_net_5d should be None
    rows = _map([
        _day(date=f"2026-01-0{i+1}", f_buy=100, f_sell=50, gtgd=1000) for i in range(4)
    ])
    for r in rows:
        assert r.sm_net_5d is None


def test_rolling_5d_correct_after_5_rows():
    # 5 sessions, each with sm_net = 10% → rolling = 10%
    rows = _map([
        _day(date=f"2026-01-0{i+1}", f_buy=150, f_sell=50, gtgd=1000) for i in range(5)
    ])
    # First 4 rows: None; 5th row: avg of all 5 = 10.0
    assert rows[0].sm_net_5d is None
    assert rows[3].sm_net_5d is None
    assert rows[4].sm_net_5d == 10.0


# --- §4.4 dominance from gross ---

def test_dominance_pct_uses_gross_not_net():
    # Divergence case keeps dominance high (both sides trading heavily).
    # F: buy 200, sell 200 (net 0); P: buy 100, sell 100 (net 0). Gross = 600.
    row = _map([_day(f_buy=200, f_sell=200, p_buy=100, p_sell=100, gtgd=1000)])[0]
    assert row.dominance_pct == 60.0
    assert row.sm_net_pct == 0.0


# --- §10 block deal ---

def test_block_deal_flag_when_dominance_above_35():
    # Gross 400, GTGD 1000 → dominance 40% > 35
    row = _map([_day(f_buy=200, f_sell=100, p_buy=50, p_sell=50, gtgd=1000)])[0]
    assert row.dominance_pct == 40.0
    assert row.block_deal is True


def test_block_deal_flag_off_when_below_35():
    row = _map([_day(f_buy=100, f_sell=100, p_buy=50, p_sell=50, gtgd=1000)])[0]
    assert row.dominance_pct == 30.0
    assert row.block_deal is False


# --- §7 signal label tiers (based on sm_net_5d) ---

def _build_5d(sm_pct_target: float) -> list[SmartMoneyFlowDay]:
    # Build 5 sessions each with sm_net_pct == target (uncapped). foreign-only.
    # net% = (f_buy - 0)/gtgd * 100 = target → f_buy = target/100 * gtgd
    gtgd = 1000.0
    f_buy = (sm_pct_target / 100.0) * gtgd
    if sm_pct_target >= 0:
        return [_day(date=f"2026-01-0{i+1}", f_buy=f_buy, gtgd=gtgd) for i in range(5)]
    else:
        return [_day(date=f"2026-01-0{i+1}", f_sell=-f_buy, gtgd=gtgd) for i in range(5)]


def test_signal_strong_accumulation_above_5pct():
    rows = _map(_build_5d(10.0))
    assert "Tích lũy mạnh" in rows[-1].signal_label


def test_signal_accumulation_2_to_5pct():
    rows = _map(_build_5d(3.0))
    assert rows[-1].signal_label == "↑ Tích lũy"


def test_signal_neutral_in_pm_2pct_band():
    rows = _map(_build_5d(1.0))
    assert "Trung tính" in rows[-1].signal_label


def test_signal_distribution_neg_5_to_neg_2():
    rows = _map(_build_5d(-3.0))
    assert rows[-1].signal_label == "↓ Phân phối"


def test_signal_strong_distribution_below_neg_5():
    rows = _map(_build_5d(-10.0))
    assert "Phân phối mạnh" in rows[-1].signal_label


# --- Ordering / general ---

def test_rows_preserve_order_oldest_first():
    rows = _map([
        _day(date="2026-01-01", f_buy=100, gtgd=1000),
        _day(date="2026-01-02", f_buy=200, gtgd=1000),
        _day(date="2026-01-03", f_buy=300, gtgd=1000),
    ])
    assert [r.date for r in rows] == ["2026-01-01", "2026-01-02", "2026-01-03"]
