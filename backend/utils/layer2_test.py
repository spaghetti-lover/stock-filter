"""
Tests for layer2.py.

Unit tests cover scoring/calculation helpers with known boundary inputs.
Integration tests fetch real VIC data and exercise cal_buy_score end-to-end.

Run from backend/:
    uv run python3 -B -m pytest backend/utils/layer2_test.py -v
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.layer2 import (
    BuyScoreBreakdown,
    cal_buy_score,
    # Liquidity
    cal_gtgd20, cal_avg_volume_20d, cal_intraday_gtgd, cal_intraday_volume,
    cal_intraday_ratio, cal_cv_val,
    gtdg20_score, intraday_score, cv_score, liquidity_score,
    # Momentum
    cal_return_n_days, cal_composite_return, price_volatility_score,
    cal_slope_pct, cal_price_vs_ma, cal_ma, cal_ma_n_days_ago,
    score_price_vs_ma, score_slope_pct, ma_score,
    stock_return_n_days, vnindex_return_n_days, cal_rs, cal_rs_weighted, rs_score,
    cal_ad_ratio, ad_score,
    cal_rsi, cal_macd_histogram, score_rsi, score_macd_histogram,
    technical_confirmation_score, momentum_score,
    # Breakout
    cal_high_20_sessions, cal_breakout_ratio, price_breakout_score,
    cal_volume_expected, cal_volume_ratio, volume_confirmation_score,
    cal_pre_vol_avg, cal_dry_up_ratio, volume_dryup_score,
    cal_atr_n_days, cal_narrowing_ratio, base_quality_score,
    cal_holding_ratio_intraday, holding_score,
    breakout_score,
    # Top-level
    buy_score,
)


# ---------------------------------------------------------------------------
# Fixtures — real VIC data fetched once per session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def vic_history():
    from infrastructure.market_data.data import get_trading_history
    history = get_trading_history("VIC", days=120)
    assert len(history) >= 65, "Need at least 65 sessions for VIC history"
    return history


@pytest.fixture(scope="session")
def vic_intraday():
    from infrastructure.market_data.data import get_intraday
    return get_intraday("VIC")


@pytest.fixture(scope="session")
def vnindex_history():
    from infrastructure.market_data.data import get_vnindex_history
    history = get_vnindex_history(days=120)
    assert len(history) >= 64, "Need at least 64 sessions for VNINDEX history"
    return history


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _close(n=70):
    """Synthetic ascending close prices."""
    return [100.0 + i * 0.5 for i in range(n)]


def _volume(n=70, base=1_000_000):
    return [float(base)] * n


# ===========================================================================
# LIQUIDITY
# ===========================================================================

class TestGtgd20Score:
    def test_above_100b(self):
        assert gtdg20_score(100e9) == 100
        assert gtdg20_score(200e9) == 100

    def test_50_to_100b(self):
        assert gtdg20_score(50e9) == 80
        assert gtdg20_score(75e9) == 80

    def test_20_to_50b(self):
        assert gtdg20_score(20e9) == 60
        assert gtdg20_score(35e9) == 60

    def test_5_to_20b(self):
        assert gtdg20_score(5e9) == 40
        assert gtdg20_score(10e9) == 40

    def test_1_to_5b(self):
        assert gtdg20_score(1e9) == 20
        assert gtdg20_score(3e9) == 20

    def test_below_1b(self):
        assert gtdg20_score(0) == 0
        assert gtdg20_score(0.5e9) == 0


class TestIntradayScore:
    def test_above_200pct(self):
        assert intraday_score(2.0) == 100
        assert intraday_score(3.5) == 100

    def test_150_to_200pct(self):
        assert intraday_score(1.5) == 80
        assert intraday_score(1.75) == 80

    def test_100_to_150pct(self):
        assert intraday_score(1.0) == 60
        assert intraday_score(1.2) == 60

    def test_60_to_100pct(self):
        assert intraday_score(0.6) == 40
        assert intraday_score(0.8) == 40

    def test_30_to_60pct(self):
        assert intraday_score(0.3) == 20
        assert intraday_score(0.5) == 20

    def test_below_30pct(self):
        assert intraday_score(0.0) == 0
        assert intraday_score(0.29) == 0


class TestCvScore:
    def test_below_30(self):
        assert cv_score(0) == 100
        assert cv_score(29.9) == 100

    def test_30_to_50(self):
        assert cv_score(30) == 80
        assert cv_score(45) == 80

    def test_50_to_75(self):
        assert cv_score(50) == 60
        assert cv_score(65) == 60

    def test_75_to_100(self):
        assert cv_score(75) == 40
        assert cv_score(90) == 40

    def test_100_to_150(self):
        assert cv_score(100) == 20
        assert cv_score(130) == 20

    def test_above_150(self):
        assert cv_score(150) == 0
        assert cv_score(200) == 0


class TestCalGtgdDaily:
    def test_multiplies_by_1000_for_vnd_conversion(self):
        # close is in thousands VND (vnstock_data convention).
        # close=50.0 means 50,000 VND/share (50 nghìn đồng).
        # gtgd = 50.0 * 1000 * 1_000_000 = 50_000_000_000 (50 tỷ VND)
        close = [50.0]
        volume = [1_000_000.0]
        from utils.layer2 import cal_gtgd_daily
        result = cal_gtgd_daily(close, volume)
        assert result == [50.0 * 1000 * 1_000_000]  # 50 tỷ VND

    def test_realistic_vic_like_values(self):
        # VIC is typically ~50 nghìn/share with ~2M volume → ~100 tỷ/day
        from utils.layer2 import cal_gtgd_daily
        close = [50.0] * 25    # 50 nghìn đồng/share
        volume = [2_000_000.0] * 25
        result = cal_gtgd_daily(close, volume)
        assert result[0] == pytest.approx(100e9)  # 100 tỷ VND


class TestCalGtgd20:
    def test_basic(self):
        # close=10.0 → 10 nghìn VND/share; volume=1000 shares
        # per-day GTGD = 10.0 * 1000 (VND conv) * 1000 (volume) = 10_000_000 (10 triệu VND)
        close = [10.0] * 25
        volume = [1000.0] * 25
        result = cal_gtgd20(close, volume)
        assert result == pytest.approx(10_000_000.0)

    def test_uses_last_20_excluding_today(self):
        # Only the last 21 values (indices -21:-1) should contribute
        close = [1.0] * 5 + [10.0] * 21
        volume = [1.0] * 5 + [1000.0] * 21
        result = cal_gtgd20(close, volume)
        assert result == pytest.approx(10.0 * 1000 * 1000)

    def test_realistic_vic_like_values(self):
        # VIC ~50 nghìn/share, 2M shares/day → ~100 tỷ/day → score 100
        close = [50.0] * 25
        volume = [2_000_000.0] * 25
        result = cal_gtgd20(close, volume)
        assert result == pytest.approx(100e9)
        assert gtdg20_score(result) == 100


class TestCalIntradayGtgd:
    def test_multiplies_price_by_1000(self):
        # price in intraday is also in thousands VND
        # price=50.0 → 50,000 VND/share; 1000 ticks of 100 shares
        from utils.layer2 import cal_intraday_gtgd
        intraday = [{"price": 50.0, "volume": 100}] * 1000
        result = cal_intraday_gtgd(intraday)
        assert result == pytest.approx(50.0 * 1000 * 100 * 1000)  # 5 tỷ VND

    def test_empty_intraday_is_zero(self):
        from utils.layer2 import cal_intraday_gtgd
        assert cal_intraday_gtgd([]) == 0


class TestCalCvVal:
    def test_constant_gtgd_gives_zero_cv(self):
        values = [100e9] * 20
        assert cal_cv_val(values) == pytest.approx(0.0)

    def test_single_value(self):
        assert cal_cv_val([100e9]) == 0.0

    def test_zero_mean(self):
        assert cal_cv_val([0.0] * 5) == 0

    def test_varied(self):
        import statistics
        values = [50e9, 100e9, 150e9, 80e9, 120e9]
        expected = statistics.stdev(values) / statistics.mean(values) * 100
        assert cal_cv_val(values) == pytest.approx(expected)


class TestCalIntradayRatio:
    def test_normal(self):
        ratio = cal_intraday_ratio(gtgd_intraday=50e9, gtgd20=100e9, minutes_elapsed=112.5)
        assert ratio == pytest.approx(1.0)

    def test_zero_expected(self):
        assert cal_intraday_ratio(50e9, 0, 100) == 0


# ===========================================================================
# MOMENTUM
# ===========================================================================

class TestPriceVolatilityScore:
    def test_negative(self):
        assert price_volatility_score(-1) == 0

    def test_0_to_1(self):
        assert price_volatility_score(0) == 20
        assert price_volatility_score(0.9) == 20

    def test_1_to_2(self):
        assert price_volatility_score(1.0) == 40
        assert price_volatility_score(1.9) == 40

    def test_2_to_4(self):
        assert price_volatility_score(2.0) == 60
        assert price_volatility_score(3.5) == 60

    def test_4_to_7(self):
        assert price_volatility_score(4.0) == 80
        assert price_volatility_score(6.5) == 80

    def test_above_7(self):
        assert price_volatility_score(7.0) == 100
        assert price_volatility_score(10.0) == 100


class TestScorePriceVsMa:
    def test_below_ma(self):
        assert score_price_vs_ma(-1) == 0

    def test_0_to_2(self):
        assert score_price_vs_ma(0) == 40
        assert score_price_vs_ma(1.9) == 40

    def test_2_to_5(self):
        assert score_price_vs_ma(2.0) == 70
        assert score_price_vs_ma(4.9) == 70

    def test_above_5(self):
        assert score_price_vs_ma(5.0) == 100
        assert score_price_vs_ma(10.0) == 100


class TestScoreSlopePct:
    def test_negative(self):
        assert score_slope_pct(-1) == 0

    def test_0_to_0_2(self):
        assert score_slope_pct(0) == 30
        assert score_slope_pct(0.19) == 30

    def test_0_2_to_0_5(self):
        assert score_slope_pct(0.2) == 60
        assert score_slope_pct(0.49) == 60

    def test_above_0_5(self):
        assert score_slope_pct(0.5) == 100
        assert score_slope_pct(1.0) == 100


class TestRsScore:
    def test_above_10(self):
        assert rs_score(10.1) == 100
        assert rs_score(20) == 100

    def test_5_to_10(self):
        assert rs_score(5.1) == 80
        assert rs_score(9.9) == 80

    def test_0_to_5(self):
        assert rs_score(0.1) == 60
        assert rs_score(4.9) == 60

    def test_minus5_to_0(self):
        assert rs_score(-0.1) == 40
        assert rs_score(-4.9) == 40

    def test_below_minus5(self):
        assert rs_score(-5) == 20
        assert rs_score(-10) == 20


class TestAdScore:
    def test_above_2(self):
        assert ad_score(2.0) == 100
        assert ad_score(3.0) == 100

    def test_1_5_to_2(self):
        assert ad_score(1.5) == 80

    def test_1_to_1_5(self):
        assert ad_score(1.0) == 60

    def test_0_7_to_1(self):
        assert ad_score(0.7) == 40

    def test_below_0_7(self):
        assert ad_score(0.5) == 20
        assert ad_score(0.0) == 20


class TestCalRsi:
    def test_neutral_fallback(self):
        assert cal_rsi([100.0] * 10) == 50.0

    def test_all_gains_returns_100(self):
        close = [100.0 + i for i in range(20)]
        assert cal_rsi(close) == 100.0

    def test_range(self):
        close = _close(50)
        rsi = cal_rsi(close)
        assert 0 <= rsi <= 100


class TestScoreRsi:
    def test_below_50(self):
        assert score_rsi(49) == 20

    def test_50_to_60(self):
        assert score_rsi(50) == 50
        assert score_rsi(59) == 50

    def test_60_to_70(self):
        assert score_rsi(60) == 80
        assert score_rsi(69) == 80

    def test_above_70(self):
        assert score_rsi(70) == 100
        assert score_rsi(90) == 100


class TestScoreMacdHistogram:
    def test_negative(self):
        assert score_macd_histogram(-0.01) == 20

    def test_0_to_0_05(self):
        assert score_macd_histogram(0) == 50
        assert score_macd_histogram(0.049) == 50

    def test_above_0_05(self):
        assert score_macd_histogram(0.05) == 100
        assert score_macd_histogram(0.1) == 100


# ===========================================================================
# BREAKOUT
# ===========================================================================

class TestPriceBreakoutScore:
    def test_below_1(self):
        assert price_breakout_score(0.99) == 0

    def test_1_to_1_01(self):
        assert price_breakout_score(1.0) == 40
        assert price_breakout_score(1.009) == 40

    def test_1_01_to_1_02(self):
        assert price_breakout_score(1.01) == 70
        assert price_breakout_score(1.019) == 70

    def test_above_1_02(self):
        assert price_breakout_score(1.02) == 100
        assert price_breakout_score(1.05) == 100


class TestVolumeConfirmationScore:
    def test_below_1(self):
        assert volume_confirmation_score(0.9) == 20

    def test_1_to_1_3(self):
        assert volume_confirmation_score(1.0) == 50
        assert volume_confirmation_score(1.29) == 50

    def test_1_3_to_1_8(self):
        assert volume_confirmation_score(1.3) == 80
        assert volume_confirmation_score(1.79) == 80

    def test_above_1_8(self):
        assert volume_confirmation_score(1.8) == 100
        assert volume_confirmation_score(2.5) == 100


class TestVolumeDryupScore:
    def test_below_0_5(self):
        assert volume_dryup_score(0.4) == 100

    def test_0_5_to_0_7(self):
        assert volume_dryup_score(0.5) == 80

    def test_0_7_to_0_9(self):
        assert volume_dryup_score(0.7) == 60

    def test_0_9_to_1_1(self):
        assert volume_dryup_score(0.9) == 40

    def test_above_1_1(self):
        assert volume_dryup_score(1.1) == 20
        assert volume_dryup_score(2.0) == 20


class TestBaseQualityScore:
    def test_below_0_5(self):
        assert base_quality_score(0.4) == 100

    def test_0_5_to_0_7(self):
        assert base_quality_score(0.5) == 80

    def test_0_7_to_0_9(self):
        assert base_quality_score(0.7) == 60

    def test_0_9_to_1_1(self):
        assert base_quality_score(0.9) == 40

    def test_above_1_1(self):
        assert base_quality_score(1.1) == 20
        assert base_quality_score(2.0) == 20


class TestHoldingScore:
    def test_above_90pct(self):
        assert holding_score(0.91) == 100

    def test_70_to_90pct(self):
        assert holding_score(0.7) == 80
        assert holding_score(0.9) == 80

    def test_50_to_70pct(self):
        assert holding_score(0.5) == 60
        assert holding_score(0.69) == 60

    def test_30_to_50pct(self):
        assert holding_score(0.3) == 40
        assert holding_score(0.49) == 40

    def test_below_30pct(self):
        assert holding_score(0.0) == 20
        assert holding_score(0.29) == 20


class TestBreakoutScore:
    def test_gate_not_active(self):
        assert breakout_score(100, 100, 100, 100, 100, breakout_ratio=0.99) == 0

    def test_gate_active_max_scores(self):
        result = breakout_score(100, 100, 100, 100, 100, breakout_ratio=1.05)
        assert result == pytest.approx(100.0)

    def test_gate_active_weights_sum(self):
        result = breakout_score(100, 100, 100, 100, 100, breakout_ratio=1.0)
        assert result == pytest.approx(0.30 * 100 + 0.25 * 100 + 0.20 * 100 + 0.15 * 100 + 0.10 * 100)


# ===========================================================================
# TOP-LEVEL WEIGHTED AGGREGATION
# ===========================================================================

class TestBuyScore:
    def test_all_zero(self):
        assert buy_score(0, 0, 0) == pytest.approx(0.0)

    def test_all_hundred(self):
        assert buy_score(100, 100, 100) == pytest.approx(100.0)

    def test_weights(self):
        assert buy_score(liquidity_score=100, momentum_score=0, breakout_score=0) == pytest.approx(35.0)
        assert buy_score(liquidity_score=0, momentum_score=100, breakout_score=0) == pytest.approx(30.0)
        assert buy_score(liquidity_score=0, momentum_score=0, breakout_score=100) == pytest.approx(35.0)


# ===========================================================================
# INTEGRATION — real VIC data
# ===========================================================================

class TestCalBuyScoreVIC:
    def test_returns_breakdown_type(self, vic_history, vic_intraday, vnindex_history):
        result = cal_buy_score(
            history=vic_history,
            intraday=vic_intraday,
            vnindex_history=vnindex_history,
            minutes_elapsed=112.5,
        )
        assert isinstance(result, BuyScoreBreakdown)

    def test_scores_in_valid_range(self, vic_history, vic_intraday, vnindex_history):
        result = cal_buy_score(
            history=vic_history,
            intraday=vic_intraday,
            vnindex_history=vnindex_history,
            minutes_elapsed=112.5,
        )
        assert 0 <= result.buy_score <= 100
        assert 0 <= result.liquidity_score <= 100
        assert 0 <= result.momentum_score <= 100
        assert 0 <= result.breakout_score <= 100

    def test_breakdown_keys_present(self, vic_history, vic_intraday, vnindex_history):
        result = cal_buy_score(
            history=vic_history,
            intraday=vic_intraday,
            vnindex_history=vnindex_history,
            minutes_elapsed=112.5,
        )
        assert "gtgd20" in result.liquidity
        assert "intraday_ratio" in result.liquidity
        assert "cv" in result.liquidity

        assert "composite_return" in result.momentum
        assert "ma" in result.momentum
        assert "rs" in result.momentum
        assert "ad" in result.momentum
        assert "technical" in result.momentum

        assert "breakout_ratio" in result.breakout
        assert "volume_ratio" in result.breakout
        assert "dry_up_ratio" in result.breakout
        assert "narrowing_ratio" in result.breakout
        assert "holding_ratio" in result.breakout

    def test_gtgd20_positive(self, vic_history, vic_intraday, vnindex_history):
        result = cal_buy_score(
            history=vic_history,
            intraday=vic_intraday,
            vnindex_history=vnindex_history,
            minutes_elapsed=112.5,
        )
        assert result.liquidity["gtgd20"]["value"] > 0

    def test_raises_on_short_history(self, vic_intraday, vnindex_history):
        with pytest.raises(ValueError, match="65 sessions"):
            cal_buy_score(
                history=[{"close": 10, "high": 11, "low": 9, "volume": 1000}] * 10,
                intraday=vic_intraday,
                vnindex_history=vnindex_history,
                minutes_elapsed=112.5,
            )
