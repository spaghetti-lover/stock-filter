import statistics
from dataclasses import dataclass
from datetime import time as _time


# 09:15 is when the continuous session opens (ATO is 09:00–09:15).
# Spec §3.3.2 requires intraday volume/value to be measured from 09:15 onward.
_ATO_END = _time(9, 15)


def _is_continuous_tick(tick: dict) -> bool:
    """True if a tick belongs to the continuous session (>= 09:15).

    Ticks with no `time` key are kept — synthetic tests use bare
    `{"price": ..., "volume": ...}` dicts.
    """
    t = tick.get("time")
    if t is None:
        return True
    return t >= _ATO_END


@dataclass
class BuyScoreResult:
    buy_score: float
    liquidity_score: float
    momentum_score: float
    breakout_score: float


@dataclass
class BuyScoreBreakdown:
    buy_score: float
    liquidity_score: float
    momentum_score: float
    breakout_score: float
    liquidity: dict
    momentum: dict
    breakout: dict
    debug: dict  # full raw inputs + intermediates for cross-checking every formula


DEFAULT_WEIGHTS = {
    "liquidity": 0.35, "momentum": 0.30, "breakout": 0.35,
    "liq_gtgd20": 0.55, "liq_intraday": 0.30, "liq_cv": 0.15,
    "mom_volatility": 0.30, "mom_ma": 0.20, "mom_rs": 0.20, "mom_flow": 0.25, "mom_tech": 0.10,
    "flow_ad": 0.40, "flow_smf": 0.60,
    "brk_price": 0.30, "brk_vol": 0.25, "brk_dryup": 0.20, "brk_base": 0.15, "brk_closing_strength": 0.10,
    "composite_1d": 0.25, "composite_5d": 0.45, "composite_20d": 0.30,
    "ma_ma20": 0.35, "ma_ma50": 0.30, "ma_slope": 0.35,
    "rs_3m": 0.35, "rs_1m": 0.65,
    "tech_rsi": 0.60, "tech_macd": 0.40,
}


# ---------------------------------------------------------------------------
# Data extraction helpers
# ---------------------------------------------------------------------------

def extract_close(history: list[dict]) -> list[float]:
    return [r["close"] for r in history]

def extract_high(history: list[dict]) -> list[float]:
    return [r["high"] for r in history]

def extract_low(history: list[dict]) -> list[float]:
    return [r["low"] for r in history]

def extract_volume(history: list[dict]) -> list[float]:
    return [r["volume"] for r in history]

def cal_gtgd_daily(close: list[float], volume: list[float]) -> list[float]:
    # close is in thousands VND (vnstock_data convention), multiply by 1000 to get VND
    return [close[i] * 1000 * volume[i] for i in range(len(close))]

def cal_gtgd20(close: list[float], volume: list[float]) -> float:
    gtgd_daily = cal_gtgd_daily(close, volume)
    return sum(gtgd_daily[-21:-1]) / 20

def cal_avg_volume_20d(volume: list[float]) -> float:
    return sum(volume[-21:-1]) / 20

def cal_avg_volume_20d_excl_5(volume: list[float]) -> float:
    """20-session average volume excluding the 5 most recent sessions (T-25..T-6).

    Used as the dry-up denominator so the window does not overlap with the
    4-session pre-volume average (T-4..T-1).
    """
    return sum(volume[-26:-6]) / 20

def cal_intraday_gtgd(intraday: list[dict]) -> float:
    # price is in thousands VND (vnstock_data convention), multiply by 1000 to get VND.
    # Spec §3.3.2: exclude ATO ticks (time < 09:15).
    return sum(t["price"] * 1000 * t["volume"] for t in intraday if _is_continuous_tick(t))

def cal_intraday_volume(intraday: list[dict]) -> float:
    # Spec §3.3.2: exclude ATO ticks (time < 09:15).
    return sum(t["volume"] for t in intraday if _is_continuous_tick(t))

def cal_intraday_ratio(gtgd_intraday: float, gtgd20: float, minutes_elapsed: float) -> float:
    gtgd_expected = gtgd20 * (minutes_elapsed / 225)
    return gtgd_intraday / gtgd_expected if gtgd_expected > 0 else 0

def cal_ma(close: list[float], period: int) -> float:
    return sum(close[-period:]) / period

def cal_ma_n_days_ago(close: list[float], period: int, days_ago: int) -> float:
    end = -days_ago
    start = end - period
    return sum(close[start:end]) / period

def cal_rs_weighted_from_history(
    close: list[float],
    vn_close: list[float],
) -> float:
    stock_r3m = stock_return_n_days(close[-1], close[-64]) if len(close) >= 64 else 0
    stock_r1m = stock_return_n_days(close[-1], close[-22]) if len(close) >= 22 else 0
    vn_r3m = vnindex_return_n_days(vn_close[-1], vn_close[-64]) if len(vn_close) >= 64 else 0
    vn_r1m = vnindex_return_n_days(vn_close[-1], vn_close[-22]) if len(vn_close) >= 22 else 0
    rs_3m = cal_rs(stock_r3m, vn_r3m)
    rs_1m = cal_rs(stock_r1m, vn_r1m)
    return cal_rs_weighted(rs_3m, rs_1m)

def cal_holding_ratio_intraday(intraday: list[dict], high20: float) -> float:
    if not intraday:
        return 0.0
    ticks_above = sum(1 for t in intraday if t["price"] > high20)
    return ticks_above / len(intraday)

# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def cal_buy_score(
    history: list[dict],         # get_trading_history() — sorted oldest→newest, includes today
    intraday: list[dict],        # get_intraday() — today's ticks: {time, price, volume}
    vnindex_history: list[dict], # get_vnindex_history() — same shape as history
    minutes_elapsed: float,      # trading minutes elapsed today (caller computes)
    position_size: float = 50_000_000,  # max VND per position (for safety ratio)
    foreign_buy_vals: list[float] | None = None,   # buy_val per session, newest first (legacy)
    foreign_sell_vals: list[float] | None = None,
    prop_buy_vals: list[float] | None = None,
    prop_sell_vals: list[float] | None = None,
    flow_data: dict | None = None,  # Preferred: pre-aggregated net flow from get_market_flow().
                                    # Shape: {foreign_net_1d, foreign_net_10d, prop_net_*,
                                    #         active_net_*}.
) -> BuyScoreBreakdown:
    """
    Compute Layer 2 BUY score from raw market data.
    Returns full breakdown with all intermediate values and sub-scores.
    Raises ValueError if history is too short (< 65 sessions including today).
    """
    if len(history) < 65:
        raise ValueError(f"Need at least 65 sessions, got {len(history)}")

    close_arr = extract_close(history)
    high_arr  = extract_high(history)
    low_arr   = extract_low(history)
    vol_arr   = extract_volume(history)
    vn_close  = extract_close(vnindex_history)

    close_today = close_arr[-1]
    avg_vol_20d = cal_avg_volume_20d(vol_arr)
    gtgd20_val  = cal_gtgd20(close_arr, vol_arr)

    # ── Liquidity ────────────────────────────────────────────────────────
    gtgd_intraday    = cal_intraday_gtgd(intraday)
    volume_intraday_ = cal_intraday_volume(intraday)
    intraday_ratio_  = cal_intraday_ratio(gtgd_intraday, gtgd20_val, minutes_elapsed)
    cv_val           = cal_cv_val(cal_gtgd_daily(close_arr, vol_arr)[-21:-1])
    safety_ratio_    = cal_safety_ratio(gtgd20_val, position_size)

    s_gtgd20    = safety_ratio_score(safety_ratio_)
    s_intraday  = intraday_score(intraday_ratio_)
    s_cv        = cv_score(cv_val)
    s_liquidity = liquidity_score(s_gtgd20, s_intraday, s_cv)

    liq_breakdown = {
        "gtgd20": {"value": gtgd20_val, "safety_ratio": safety_ratio_, "score": s_gtgd20},
        "intraday_ratio": {
            "value": intraday_ratio_,
            "score": s_intraday,
            "current_price": close_today,
            "volume_intraday": volume_intraday_,
        },
        "cv": {"value": cv_val, "score": s_cv},
    }

    # ── Momentum ─────────────────────────────────────────────────────────
    ret_1d  = cal_return_n_days(close_today, close_arr[-2])
    ret_5d  = cal_return_n_days(close_today, close_arr[-6])
    ret_20d = cal_return_n_days(close_today, close_arr[-21])
    composite_ret = cal_composite_return(ret_1d, ret_5d, ret_20d)
    s_volatility = price_volatility_score(ret_1d, ret_5d, ret_20d)
    s_ret_1d  = score_return_1d(ret_1d)
    s_ret_5d  = score_return_5d(ret_5d)
    s_ret_20d = score_return_20d(ret_20d)
    consistency_mult = consistency_multiplier(ret_1d, ret_5d, ret_20d)

    ma20_today    = cal_ma(close_arr, 20)
    ma50_today    = cal_ma(close_arr, 50)
    ma20_10d_ago  = cal_ma_n_days_ago(close_arr, 20, 10)
    ma50_10d_ago  = cal_ma_n_days_ago(close_arr, 50, 10)
    pv_ma20       = cal_price_vs_ma(close_today, ma20_today)
    pv_ma50       = cal_price_vs_ma(close_today, ma50_today)
    ma20_vs_ma50  = (ma20_today - ma50_today) / ma50_today * 100
    slope_ma20    = cal_slope_pct(ma20_today, ma20_10d_ago)
    slope_ma50    = cal_slope_pct(ma50_today, ma50_10d_ago)
    s_pv_ma20     = score_price_vs_ma20(pv_ma20)
    s_pv_ma50     = score_price_vs_ma50(pv_ma50)
    s_align       = score_alignment(ma20_vs_ma50)
    s_slope_ma20  = score_slope_ma20(slope_ma20)
    s_slope_ma50  = score_slope_ma50(slope_ma50)
    s_ma          = ma_score(pv_ma20, pv_ma50, ma20_vs_ma50, slope_ma20, slope_ma50)

    stock_r3m = stock_return_n_days(close_arr[-1], close_arr[-64]) if len(close_arr) >= 64 else 0
    stock_r1m = stock_return_n_days(close_arr[-1], close_arr[-22]) if len(close_arr) >= 22 else 0
    vn_r3m    = vnindex_return_n_days(vn_close[-1], vn_close[-64]) if len(vn_close) >= 64 else 0
    vn_r1m    = vnindex_return_n_days(vn_close[-1], vn_close[-22]) if len(vn_close) >= 22 else 0
    rs_3m_val = cal_rs(stock_r3m, vn_r3m)
    rs_1m_val = cal_rs(stock_r1m, vn_r1m)
    rs_w_val  = cal_rs_weighted(rs_3m_val, rs_1m_val)
    s_rs      = rs_score(rs_w_val, rs_1m_val, rs_3m_val)
    rs_accel_mult_val = rs_acceleration_mult(rs_1m_val, rs_3m_val)

    ad_val    = cal_ad_ratio(close_arr[-21:], vol_arr[-21:])
    s_ad      = ad_score(ad_val)

    # Smart Money Flow — prefer the new market-wide net dict (Insights().flow.*)
    # which gives pre-aggregated 10-day net values; fall back to the legacy
    # 5-day buy/sell pair calculation for backwards compat.
    gtgd_daily = cal_gtgd_daily(close_arr, vol_arr)
    a_pct = None
    s_active = None

    if flow_data is not None:
        # Denominator: GTGD over the last 10 completed sessions (excludes today).
        gtgd_10d = sum(gtgd_daily[-11:-1])
        f_net = flow_data.get("foreign_net_10d")
        p_net = flow_data.get("prop_net_10d")
        a_net = flow_data.get("active_net_10d")
        f_pct = cal_net_pct(f_net, gtgd_10d) if f_net is not None else None
        p_pct = cal_net_pct(p_net, gtgd_10d) if p_net is not None else None
        a_pct = cal_net_pct(a_net, gtgd_10d) if a_net is not None else None

        s_f = foreign_net_score(f_pct) if f_pct is not None else 40
        s_p = prop_net_score(p_pct) if p_pct is not None else 40
        if a_pct is not None:
            s_active = active_net_score(a_pct)
            s_smart_money = cal_smart_money_score_3c(s_f, s_p, s_active)
        else:
            s_smart_money = cal_smart_money_score(s_f, s_p)
    elif (foreign_buy_vals and foreign_sell_vals and len(foreign_buy_vals) >= 5
            and prop_buy_vals and prop_sell_vals and len(prop_buy_vals) >= 5):
        # Legacy path: per-symbol buy/sell pairs over 5 sessions.
        gtgd_5d = sum(gtgd_daily[-6:-1])
        f_pct = cal_foreign_net_pct(foreign_buy_vals, foreign_sell_vals, gtgd_5d)
        p_pct = cal_prop_net_pct(prop_buy_vals, prop_sell_vals, gtgd_5d)
        s_smart_money = cal_smart_money_score(foreign_net_score(f_pct), prop_net_score(p_pct))
    else:
        f_pct = p_pct = None
        s_smart_money = 40  # neutral when data unavailable

    s_flow, flow_base_val, convergence_mult_val = cal_score_flow(s_ad, s_smart_money)

    # RSI uses the live last tick price as today's close (docs/filter.md §3.2.5.1).
    # MACD and every other formula continue to use the EOD close.
    close_for_rsi = close_arr
    if intraday:
        last_tick_price = intraday[-1].get("price")
        if last_tick_price:
            close_for_rsi = close_arr[:-1] + [last_tick_price]
    rsi_val   = cal_rsi(close_for_rsi)
    macd_val  = cal_macd_histogram(close_arr, close_today)
    s_rsi     = score_rsi(rsi_val)
    s_macd    = score_macd_histogram(macd_val)
    s_tech    = technical_confirmation_score(rsi_val, macd_val)

    s_momentum = momentum_score(s_volatility, s_ma, s_rs, s_flow, s_tech)

    mom_breakdown = {
        "composite_return": {
            "value": composite_ret, "score": s_volatility,
            "detail": {
                "return_1d":  {"value": ret_1d,  "score": s_ret_1d},
                "return_5d":  {"value": ret_5d,  "score": s_ret_5d},
                "return_20d": {"value": ret_20d, "score": s_ret_20d},
                "consistency_mult": consistency_mult,
            },
        },
        "ma": {
            "score": s_ma,
            "detail": {
                "price_vs_ma20": {"value": pv_ma20,      "score": s_pv_ma20},
                "price_vs_ma50": {"value": pv_ma50,      "score": s_pv_ma50},
                "alignment":     {"value": ma20_vs_ma50, "score": s_align},
                "slope_ma20":    {"value": slope_ma20,   "score": s_slope_ma20},
                "slope_ma50":    {"value": slope_ma50,   "score": s_slope_ma50},
            },
        },
        "rs": {
            "value": rs_w_val, "score": s_rs,
            "detail": {
                "rs_3m": rs_3m_val,
                "rs_1m": rs_1m_val,
                "acceleration": rs_1m_val - rs_3m_val,
                "accel_mult": rs_accel_mult_val,
            },
        },
        "flow": {
            "value": flow_base_val,
            "score": round(s_flow, 2),
            "detail": {
                "score_ad": s_ad,
                "ad_value": ad_val,
                "score_smf": s_smart_money,
                "foreign_net_pct": f_pct,
                "prop_net_pct": p_pct,
                "active_net_pct": a_pct,
                "score_active": s_active,
                "active_band": _flow_band(s_active) if s_active is not None else None,
                "convergence_mult": convergence_mult_val,
                "flow_base": flow_base_val,
                "ad_band": _flow_band(s_ad),
                "smf_band": _flow_band(s_smart_money),
            },
        },
        "technical": {
            "score": s_tech,
            "detail": {
                "rsi": {"value": rsi_val, "score": s_rsi},
                "macd_histogram_pct": {"value": macd_val, "score": s_macd},
            },
        },
    }

    # ── Breakout ─────────────────────────────────────────────────────────
    close20_val    = cal_close_20_sessions(close_arr[-21:])
    b_ratio        = cal_breakout_ratio(close_today, close20_val)
    vol_ratio_val  = cal_volume_ratio(
        cal_intraday_volume(intraday),
        cal_volume_expected(avg_vol_20d, minutes_elapsed),
    )
    dry_up_val     = cal_dry_up_ratio(cal_pre_vol_avg(vol_arr), cal_avg_volume_20d_excl_5(vol_arr))
    atr_5d_val     = cal_atr_n_days(high_arr, low_arr, 5, close_arr)
    narrowing_val  = cal_narrowing_ratio(
        atr_5d_val,
        cal_atr_n_days(high_arr, low_arr, 20, close_arr),
    )
    cs_val         = cal_closing_strength(close_today, high_arr[-1], low_arr[-1])
    risk_ratio_val = cal_risk_ratio(b_ratio, atr_5d_val, close_today)
    risk_coeff_val = risk_coefficient(risk_ratio_val)

    s_price_brk  = price_breakout_score(b_ratio)
    s_vol_conf   = volume_confirmation_score(vol_ratio_val)
    s_dryup      = volume_dryup_score(dry_up_val)
    s_base       = base_quality_score(narrowing_val)
    s_cs         = closing_strength_score(cs_val)
    gate_active  = b_ratio >= 1.0
    s_breakout   = breakout_score(s_price_brk, s_vol_conf, s_dryup, s_base, s_cs, b_ratio, risk_coeff_val)

    brk_breakdown = {
        "breakout_ratio": {"value": b_ratio, "score": s_price_brk},
        "volume_ratio": {"value": vol_ratio_val, "score": s_vol_conf},
        "dry_up_ratio": {"value": dry_up_val, "score": s_dryup},
        "narrowing_ratio": {"value": narrowing_val, "score": s_base},
        "closing_strength": {"value": cs_val, "score": s_cs},
        "risk_ratio": {"value": risk_ratio_val, "coefficient": risk_coeff_val},
        "gate_active": gate_active,
    }

    # ── Debug: full raw inputs + intermediates (cross-check every formula) ──
    gtgd_daily_all = cal_gtgd_daily(close_arr, vol_arr)
    gtgd_5d_val    = sum(gtgd_daily_all[-6:-1])  # last 5 sessions excl. today (3.2.5 denominator)
    ad_close       = close_arr[-21:]
    ad_vol         = vol_arr[-21:]
    up_vol_list    = cal_up_days_vol(ad_close, ad_vol)
    down_vol_list  = cal_down_days_vol(ad_close, ad_vol)

    if (foreign_buy_vals and foreign_sell_vals and len(foreign_buy_vals) >= 5
            and prop_buy_vals and prop_sell_vals and len(prop_buy_vals) >= 5):
        foreign_buy_5d  = foreign_buy_vals[:5]
        foreign_sell_5d = foreign_sell_vals[:5]
        prop_buy_5d     = prop_buy_vals[:5]
        prop_sell_5d    = prop_sell_vals[:5]
        foreign_net_5d  = sum(b - s for b, s in zip(foreign_buy_5d, foreign_sell_5d))
        prop_net_5d     = sum(b - s for b, s in zip(prop_buy_5d, prop_sell_5d))
        smart_data_ok   = True
    else:
        foreign_buy_5d = foreign_sell_5d = prop_buy_5d = prop_sell_5d = None
        foreign_net_5d = prop_net_5d = None
        smart_data_ok  = False

    debug = {
        "inputs": {
            "close_21": ad_close,
            "volume_21": ad_vol,
            "high_21": high_arr[-21:],
            "low_21": low_arr[-21:],
            "vn_close_64": vn_close[-64:],
            "minutes_elapsed": minutes_elapsed,
            "n_sessions": len(history),
            "position_size": position_size,
            # docs/filter.md §3.2.5.1: last close fed into RSI is live tick price
            "close_for_rsi_last": close_for_rsi[-1],
        },
        "gtgd": {
            "gtgd_daily_21": gtgd_daily_all[-21:],
            "gtgd20": gtgd20_val,
            "gtgd_5d": gtgd_5d_val,
            "avg_vol_20d": avg_vol_20d,
        },
        "intraday": {
            "gtgd_intraday": gtgd_intraday,
            "volume_intraday": volume_intraday_,
            "gtgd_expected": gtgd20_val * (minutes_elapsed / 225) if minutes_elapsed else 0,
        },
        "ad": {
            "up_days_vol": up_vol_list,
            "down_days_vol": down_vol_list,
            "up_count": len(up_vol_list),
            "down_count": len(down_vol_list),
            "mean_up": (sum(up_vol_list) / len(up_vol_list)) if up_vol_list else None,
            "mean_down": (sum(down_vol_list) / len(down_vol_list)) if down_vol_list else None,
            "ad_ratio": ad_val,
            "note": "all 20 sessions up => down_count=0 => ad_ratio=999 => score 100",
        },
        "smart_money": {
            "data_available": smart_data_ok or (flow_data is not None),
            "source": "market_flow_10d" if flow_data is not None else "per_symbol_5d",
            # legacy 5d-pair fields (None when using market-wide flow_data path)
            "foreign_buy_5d": foreign_buy_5d,
            "foreign_sell_5d": foreign_sell_5d,
            "foreign_net_5d": foreign_net_5d,
            "prop_buy_5d": prop_buy_5d,
            "prop_sell_5d": prop_sell_5d,
            "prop_net_5d": prop_net_5d,
            "gtgd_5d": gtgd_5d_val,
            # current-path percentages (computed against gtgd_5d OR gtgd_10d)
            "foreign_net_pct": f_pct,
            "prop_net_pct": p_pct,
            "active_net_pct": a_pct,
            # market-wide raw net values when present
            "flow_data": flow_data,
            "gtgd_10d": sum(gtgd_daily_all[-11:-1]) if flow_data is not None else None,
        },
    }

    return BuyScoreBreakdown(
        buy_score=round(buy_score(s_liquidity, s_momentum, s_breakout), 2),
        liquidity_score=round(s_liquidity, 2),
        momentum_score=round(s_momentum, 2),
        breakout_score=round(s_breakout, 2),
        liquidity=liq_breakdown,
        momentum=mom_breakdown,
        breakout=brk_breakdown,
        debug=debug,
    )


# Buy Score
"""
BUY Score = 0.35 × Điểm Thanh khoản + 0.30 × Điểm Động lượng + 0.35 × Điểm Breakout
"""

def buy_score(liquidity_score, momentum_score, breakout_score):
    return 0.35 * liquidity_score + 0.30 * momentum_score + 0.35 * breakout_score

# Diem thanh khoan
"""
Diểm thanh khoản = 0.55 × Diem GTDG20 + 0.30 x Diem hoat dong intraday + 0.15 x Diem on dinh thanh khoan (CV)
"""
def liquidity_score(gtdg20_score, intraday_score, cv_score):
    return 0.55 * gtdg20_score + 0.30 * intraday_score + 0.15 * cv_score

# Diem GTGD20 (Safety Ratio)
"""
Trả lời câu hỏi: Với quy mô lệnh của tôi, mã này có đủ thanh khoản để vào/ra mà không bị trượt giá không?

safety_ratio = GTGD20 / position_size

| Safety ratio | Điểm | Ý nghĩa                                         |
| ------------ | ---- | ----------------------------------------------- |
| ≥ 200×       | 100  | Lệnh chìm trong dòng tiền thị trường - vào/ra tự do |
| 100-200×     | 80   | Rất thoải mái, không lo trượt giá              |
| 50-100×      | 60   | Tốt, trượt giá không đáng kể                   |
| 20-50×       | 40   | Chấp nhận được, có thể cần chia lệnh           |
| 10-20×       | 20   | Rủi ro trượt giá rõ rệt, cẩn thận khi thoát   |
| < 10×        | 0    | Không nên vào - lệnh quá lớn so với thị trường |
"""
def cal_safety_ratio(gtgd20: float, position_size: float) -> float:
    if position_size == 0:
        return 0.0
    return gtgd20 / position_size

def safety_ratio_score(safety_ratio: float) -> int:
    if safety_ratio >= 200:
        return 100
    elif 100 <= safety_ratio < 200:
        return 80
    elif 50 <= safety_ratio < 100:
        return 60
    elif 20 <= safety_ratio < 50:
        return 40
    elif 10 <= safety_ratio < 20:
        return 20
    else:
        return 0

def gtdg20_score(gtdg20):
    """Legacy absolute-value scorer — kept for backward compat. Prefer safety_ratio_score."""
    if gtdg20 >= 100e9:
        return 100
    elif 50e9 <= gtdg20 < 100e9:
        return 80
    elif 20e9 <= gtdg20 < 50e9:
        return 60
    elif 5e9 <= gtdg20 < 20e9:
        return 40
    elif 1e9 <= gtdg20 < 5e9:
        return 20
    else:
        return 0

# Diem hoat dong intraday
"""
_Hôm nay có dòng tiền vào không - không chỉ thanh khoản nền mà còn hôm nay cụ thể?_

GTGD_intraday = price_hiện_tại × volume_intraday

time_ratio = minutes_elapsed / 225 # 225 phút thực giao dịch (loại ATO 15ph + ATC 15ph)

GTGD_kỳ_vọng = GTGD20 × time_ratio

intraday_ratio = GTGD_intraday / GTGD_kỳ_vọng

_225 phút = Sáng (9:15-11:30 = 135ph) + Chiều (13:00-14:45 = 105ph) - loại ATO và ATC_

| **Intraday ratio** | **Điểm** | **Ý nghĩa**             |
| ------------------ | -------- | ----------------------- |
| ≥ 200%             | 100      | Cực kỳ sôi động         |
| 150-200%           | 80       | Rất tích cực            |
| 100-150%           | 60       | Tốt                     |
| 60-100%            | 40       | Bình thường             |
| 30-60%             | 20       | Yếu                     |
| < 30%              | 0        | Gần như không giao dịch |
"""

def intraday_score(intraday_ratio):
    if intraday_ratio >= 2.0:
        return 100
    elif 1.5 <= intraday_ratio < 2.0:
        return 80
    elif 1.0 <= intraday_ratio < 1.5:
        return 60
    elif 0.6 <= intraday_ratio < 1.0:
        return 40
    elif 0.3 <= intraday_ratio < 0.6:
        return 20
    else:
        return 0

# Diem on dinh thanh khoan (CV)
"""
_Thanh khoản đều đặn hay chỉ bùng lên vài phiên - phân biệt thanh khoản thật vs bẫy volume?_

CV = std(GTGD_20_phiên) / mean(GTGD_20_phiên) × 100

| **CV**   | **Điểm** |
| -------- | -------- |
| < 30%    | 100      |
| 30-50%   | 80       |
| 50-75%   | 60       |
| 75-100%  | 40       |
| 100-150% | 20       |
| ≥ 150%   | 0        |
"""
def cal_cv_val(gtdg20_values):
    if len(gtdg20_values) < 2:
        return 0.0
    mean_val = statistics.mean(gtdg20_values)
    if mean_val == 0:
        return 0
    return statistics.stdev(gtdg20_values) / mean_val * 100


def cv_score(cv):
    if cv < 30:
        return 100
    elif 30 <= cv < 50:
        return 80
    elif 50 <= cv < 75:
        return 60
    elif 75 <= cv < 100:
        return 40
    elif 100 <= cv < 150:
        return 20
    else:
        return 0


# Diem dong luong
"""
Điểm động lượng = 0.30 × Điểm biến động giá composite
               + 0.20 × Điểm phân tích MA
               + 0.20 × Điểm sức mạnh tương đối (RS)
               + 0.25 × score_flow (A/D + SMF + convergence)
               + 0.10 × Điểm xác nhận kỹ thuật (RSI+MACD)
(Tổng = 1.05 → normalize nội bộ)
"""
def momentum_score(price_volatility_score, ma_score, rs_score, flow_score, technical_confirmation_score):
    raw_weights = (0.30, 0.20, 0.20, 0.25, 0.10)
    total = sum(raw_weights)
    w = [x / total for x in raw_weights]
    return (w[0] * price_volatility_score + w[1] * ma_score + w[2] * rs_score
            + w[3] * flow_score + w[4] * technical_confirmation_score)

# Diem bien dong gia composite
"""
_Mã có đang chạy mạnh hơn bình thường không - xét đa khung thời gian để lọc noise?_
return_1d = (close_hôm_nay - close_1d_trước) / close_1d_trước × 100
return_5d = (close_hôm_nay - close_5d_trước) / close_5d_trước × 100
return_20d = (close_hôm_nay - close_20d_trước) / close_20d_trước × 100
composite = 0.50 × return_1d + 0.30 × return_5d + 0.20 × return_20d
_(Trọng số 50/30/20: Lướt sóng ưu tiên tín hiệu ngắn nhất, nhưng 5D và 20D xác nhận momentum có nền.)_

| **Composite return** | **Điểm** |
| -------------------- | -------- |
| < 0%                 | 0        |
| 0-1%                 | 20       |
| 1-2%                 | 40       |
| 2-4%                 | 60       |
| 4-7%                 | 80       |
| > 7%                | 100      |
"""
def cal_return_n_days(close_today, close_n_days_ago):
    return (close_today - close_n_days_ago) / close_n_days_ago * 100

def cal_composite_return(return_1d, return_5d, return_20d):
    return 0.50 * return_1d + 0.30 * return_5d + 0.20 * return_20d

def score_return_1d(r: float) -> float:
    if r < -1:   return 0
    if r < 0:    return 20
    if r < 1:    return 50
    if r < 3:    return 75
    return 90

def score_return_5d(r: float) -> float:
    if r < -3:   return 0
    if r < 0:    return 15
    if r < 2:    return 40
    if r < 5:    return 70
    if r < 10:   return 90
    if r <= 15:  return 100
    return 65  # extended weekly soft cap

def score_return_20d(r: float) -> float:
    if r < -5:   return 0
    if r < 0:    return 20
    if r < 5:    return 50
    if r < 15:   return 80
    if r <= 25:  return 100
    return 75   # extended monthly soft cap

def consistency_multiplier(r1: float, r5: float, r20: float) -> float:
    pos = sum(1 for r in (r1, r5, r20) if r > 0)
    if pos == 3: return 1.10
    if pos == 2: return 1.00
    if pos == 1: return 0.85
    return 0.70

def price_volatility_score(ret_1d: float, ret_5d: float, ret_20d: float) -> float:
    s = (0.15 * score_return_1d(ret_1d)
       + 0.50 * score_return_5d(ret_5d)
       + 0.35 * score_return_20d(ret_20d))
    return min(100.0, s * consistency_multiplier(ret_1d, ret_5d, ret_20d))

# Diem phan tich MA (RevC: 4 components, 10-phien slope lookback, composite MA20+MA50)
# Spec: docs/filter.md §3.2.2

def cal_slope_pct(ma_today, ma_n_days_ago):
    return (ma_today - ma_n_days_ago) / ma_n_days_ago * 100

def cal_price_vs_ma(close_today, ma):
    return (close_today - ma) / ma * 100

def score_price_vs_ma20(pv: float) -> float:
    if pv < -2:    return 0
    if pv < 0:     return 15
    if pv < 1.5:   return 75
    if pv < 3.5:   return 90
    if pv < 6:     return 65
    if pv < 9:     return 30
    return 0

def score_price_vs_ma50(pv: float) -> float:
    if pv < -2:    return 0
    if pv < 0:     return 15
    if pv < 3:     return 50
    if pv < 8:     return 80
    if pv <= 15:   return 100
    return 70

def score_alignment(ma20_vs_ma50_pct: float) -> float:
    x = ma20_vs_ma50_pct
    if x < -3:     return 0
    if x < -1:     return 20
    if x < 0:      return 40
    if x < 1:      return 65
    if x < 3:      return 85
    return 100

def score_slope_ma20(slope: float) -> float:
    if slope < -0.3:  return 0
    if slope < 0:     return 15
    if slope < 0.3:   return 40
    if slope < 0.6:   return 70
    return 100

def score_slope_ma50(slope: float) -> float:
    if slope < -0.2:  return 0
    if slope < 0:     return 20
    if slope < 0.2:   return 50
    if slope < 0.4:   return 80
    return 100

def ma_score(
    pv_ma20: float, pv_ma50: float,
    ma20_vs_ma50_pct: float,
    slope_ma20_pct: float, slope_ma50_pct: float,
) -> float:
    s_slope = 0.55 * score_slope_ma20(slope_ma20_pct) + 0.45 * score_slope_ma50(slope_ma50_pct)
    return (0.35 * score_price_vs_ma20(pv_ma20)
          + 0.20 * score_price_vs_ma50(pv_ma50)
          + 0.20 * score_alignment(ma20_vs_ma50_pct)
          + 0.25 * s_slope)

# Diem suc manh tuong doi vs VN-Index (RS)
"""
_Tham khảo từ: VCP - Relative Strength component (15% weight trong VCP)_

rs_3m = stock_return_3M - vnindex_return_3M
rs_1m = stock_return_1M - vnindex_return_1M
rs_weighted = 0.35 × rs_3m + 0.65 × rs_1m
_(Lý do: Swing trade cần mã đang dẫn dắt ngay bây giờ, không phải 3 tháng trước. 1M weight cao hơn bắt được rotation sớm hơn.)_

stock_return_3M = (close_today - close_63d_ago) / close_63d_ago × 100
vnindex_return_3M = (vnindex_close_today - vnindex_close_63d_ago) / vnindex_close_63d_ago × 100

| **RS weighted** | **Điểm** | **Ý nghĩa**          |
| --------------- | -------- | -------------------- |
| > +10%         | 100      | Leader rõ ràng       |
| +5 đến +10%     | 80       | Outperform tốt       |
| 0 đến +5%       | 60       | Nhỉnh hơn index      |
| -5 đến 0%      | 40       | Underperform nhẹ     |
| < -5%           | 20       | Yếu hơn index rõ rệt |
"""

def stock_return_n_days(close_today, close_n_days_ago):
    return (close_today - close_n_days_ago) / close_n_days_ago * 100

def vnindex_return_n_days(vnindex_close_today, vnindex_close_n_days_ago):
    return (vnindex_close_today - vnindex_close_n_days_ago) / vnindex_close_n_days_ago * 100

def cal_rs(stock_return, vnindex_return):
    return stock_return - vnindex_return

def cal_rs_weighted(rs_3m, rs_1m):
    return 0.35 * rs_3m + 0.65 * rs_1m

def rs_base_score(rs_weighted: float) -> float:
    if rs_weighted > 15:   return 100
    if rs_weighted > 8:    return 85
    if rs_weighted > 3:    return 65
    if rs_weighted > 0:    return 45
    if rs_weighted > -5:   return 20
    return 0

def rs_acceleration_mult(rs_1m: float, rs_3m: float) -> float:
    accel = rs_1m - rs_3m
    if accel > 5:    return 1.10
    if accel > 0:    return 1.00
    if accel > -5:   return 0.90
    return 0.80

def rs_score(rs_weighted: float, rs_1m: float = 0.0, rs_3m: float = 0.0) -> float:
    return min(100.0, rs_base_score(rs_weighted) * rs_acceleration_mult(rs_1m, rs_3m))

# Diem tich luy / phan phoi (A/D Ratio)
"""
_Tham khảo từ: CANSLIM - S component (Supply & Demand, 15% weight)_

20 phiên gần nhất:
up_days_vol = [volume[i] for i in range(20) if close[i] > close[i-1]]
down_days_vol = [volume[i] for i in range(20) if close[i] < close[i-1]]
ad_ratio = mean(up_days_vol) / mean(down_days_vol)

| **A/D ratio** | **Điểm** | **Ý nghĩa**                     |
| ------------- | -------- | ------------------------------- |
| ≥ 2.0         | 100      | Tích lũy mạnh (smart money vào) |
| 1.5-2.0       | 80       | Tích lũy rõ ràng                |
| 1.0-1.5       | 60       | Trung tính / tích lũy nhẹ       |
| 0.7-1.0       | 40       | Phân phối nhẹ                   |
| < 0.7         | 20       | Phân phối rõ (smart money ra)   |
"""
def cal_up_days_vol(close, volume):
    return [volume[i] for i in range(1, len(close)) if close[i] > close[i-1]]

def cal_down_days_vol(close, volume):
    return [volume[i] for i in range(1, len(close)) if close[i] < close[i-1]]

def cal_ad_ratio(close, volume):
    up_vol = cal_up_days_vol(close, volume)
    down_vol = cal_down_days_vol(close, volume)
    if len(down_vol) == 0:
        return 999.0  # all sessions up → score 100
    if len(up_vol) == 0:
        return 0.0
    return sum(up_vol) / len(up_vol) / (sum(down_vol) / len(down_vol))

def ad_score(ad_ratio):
    if ad_ratio >= 2.0:
        return 100
    elif 1.5 <= ad_ratio < 2.0:
        return 80
    elif 1.0 <= ad_ratio < 1.5:
        return 60
    elif 0.7 <= ad_ratio < 1.0:
        return 40
    else:
        return 20

# Diem xac nhan ky thuat (RSI + MACD)
"""
RSI 14 phiên:
| **RSI (14 phiên)** | **Điểm** |
| ------------------ | -------- |
| < 50               | 20       |
| 50-60              | 50       |
| 60-70              | 80       |
| > 70               | 100      |

MACD:
histogram = macd_line - signal_line
histogram_pct = histogram / close_today × 100

| **Histogram%** | **Điểm** |
| -------------- | -------- |
| < 0%           | 20       |
| 0-0.05%        | 50       |
| > 0.05%        | 100      |

score_technical = 0.60 × score_rsi + 0.40 × score_macd
"""
def cal_rsi(close: list[float], period: int = 14) -> float:
    """Wilder's RSI. Requires at least period+1 values."""
    if len(close) < period + 1:
        return 50.0  # neutral fallback
    changes = [close[i] - close[i - 1] for i in range(1, len(close))]
    gains = [max(c, 0) for c in changes[-period:]]
    losses = [abs(min(c, 0)) for c in changes[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def _ema(values: list[float], period: int) -> list[float]:
    k = 2 / (period + 1)
    ema = [values[0]]
    for v in values[1:]:
        ema.append(v * k + ema[-1] * (1 - k))
    return ema

def cal_macd_histogram(close: list[float], close_today: float, fast: int = 12, slow: int = 26, signal: int = 9) -> float:
    """Standard MACD histogram normalised by close_today (%)."""
    if len(close) < slow + signal:
        return 0.0
    ema_fast   = _ema(close, fast)
    ema_slow   = _ema(close, slow)
    macd_line  = [ema_fast[i] - ema_slow[i] for i in range(len(ema_slow))]
    signal_line = _ema(macd_line, signal)
    histogram  = macd_line[-1] - signal_line[-1]
    return histogram / close_today * 100 if close_today else 0.0

def score_rsi(rsi):
    # Non-monotonic: sweet spot 60-70 for T+2.5 swing (strong but room to run)
    if rsi < 40:
        return 0
    elif rsi < 45:
        return 10
    elif rsi < 50:
        return 35
    elif rsi < 60:
        return 60
    elif rsi < 70:
        return 100
    elif rsi < 80:
        return 60
    else:
        return 20

def score_macd_histogram(histogram_pct):
    if histogram_pct < -0.10:
        return 0
    elif histogram_pct < 0:
        return 20
    elif histogram_pct < 0.05:
        return 50
    elif histogram_pct < 0.20:
        return 75
    else:
        return 100

def technical_confirmation_score(rsi, histogram_pct):
    return 0.60 * score_rsi(rsi) + 0.40 * score_macd_histogram(histogram_pct)

# Diem Breakout
"""
Gate condition:
if breakout_ratio < 1.0:
    return breakout_score = 0  # Chưa breakout → toàn bộ Breakout score = 0

Điểm breakout = 0.30 × Điểm vượt cản giá
             + 0.25 × Điểm xác nhận volume breakout
             + 0.20 × Điểm volume dry-up trước breakout
             + 0.15 × Điểm chất lượng nền giá
             + 0.10 × Điểm sức mạnh đóng cửa (closing_strength)
             × risk_coefficient (penalty: 1.0 / 0.85 / 0.70 / 0.50)
"""
def breakout_score(price_breakout_score, volume_confirmation_score, volume_dryup_score, base_quality_score, closing_strength_score, breakout_ratio, risk_coeff=1.0):
    if breakout_ratio < 1.0:
        return 0
    raw = (0.30 * price_breakout_score
           + 0.25 * volume_confirmation_score
           + 0.20 * volume_dryup_score
           + 0.15 * base_quality_score
           + 0.10 * closing_strength_score)
    return raw * risk_coeff

# Diem vuot can gia
"""
Close20 = max(close, 20_sessions)  # không tính hôm nay
breakout_ratio = close_today / Close20

| **Breakout ratio** | **Điểm**          |
| ------------------ | ----------------- |
| < 1.00             | Gate: toàn bộ = 0 |
| 1.00-1.01          | 40                |
| 1.01-1.02          | 70                |
| > 1.02             | 100               |
"""
def cal_close_20_sessions(close):
    return max(close[:-1])  # Không tính hôm nay

def cal_breakout_ratio(close_today, close_20_sessions):
    return close_today / close_20_sessions

def price_breakout_score(breakout_ratio):
    if breakout_ratio < 1.0:
        return 0
    elif 1.0 <= breakout_ratio < 1.01:
        return 40
    elif 1.01 <= breakout_ratio < 1.02:
        return 70
    else:
        return 100

# Diem xac nhan volume breakout
"""
volume_expected = avg_volume_20d × (minutes_elapsed / 225)
volume_ratio = volume_intraday / volume_expected

| **Volume ratio** | **Điểm** |
| ---------------- | -------- |
| < 1.0            | 20       |
| 1.0-1.3          | 50       |
| 1.3-1.8          | 80       |
| > 1.8            | 100      |
"""

def cal_volume_expected(avg_volume_20d, minutes_elapsed):
    return avg_volume_20d * (minutes_elapsed / 225)

def cal_volume_ratio(volume_intraday, volume_expected):
    if volume_expected == 0:
        return 0.0
    return volume_intraday / volume_expected

def volume_confirmation_score(volume_ratio):
    if volume_ratio < 1.0:
        return 0
    elif volume_ratio < 1.3:
        return 50
    elif volume_ratio < 1.8:
        return 80
    else:
        return 100

# Diem volume dry-up truoc breakout
"""
_Học từ: VCP - Volume Pattern component_

pre_vol_avg = mean(volume[-5:-1])  # 4 phiên gần nhất trước T0
dry_up_ratio = pre_vol_avg / avg_volume_20d

| **Dry-up ratio** | **Điểm** | **Ý nghĩa**                                |
| ---------------- | -------- | ------------------------------------------ |
| < 0.5            | 100      | Sellers gần hết - breakout rất tin cậy     |
| 0.5-0.7          | 80       | Dry-up tốt                                 |
| 0.7-0.9          | 60       | Dry-up vừa                                 |
| 0.9-1.1          | 40       | Volume bình thường                         |
| > 1.1            | 20       | Sellers vẫn đang bán - breakout rủi ro cao |
"""
def cal_pre_vol_avg(volume):
    return sum(volume[-5:-1]) / 4  # Trung bình 4 phiên gần nhất trước T0

def cal_dry_up_ratio(pre_vol_avg, avg_volume_20d):
    if avg_volume_20d == 0:
        return 1.0
    return pre_vol_avg / avg_volume_20d

def volume_dryup_score(dry_up_ratio):
    if dry_up_ratio < 0.5:
        return 100
    elif 0.5 <= dry_up_ratio < 0.7:
        return 80
    elif 0.7 <= dry_up_ratio < 0.9:
        return 60
    elif 0.9 <= dry_up_ratio < 1.1:
        return 40
    else:
        return 20

# Diem chat luong nen gia (Base Quality)
"""
_Học từ: VCP - Contraction Quality component_

atr_5d = mean(high[-5:] - low[-5:])   # biên độ trung bình 5 phiên gần nhất
atr_20d = mean(high[-20:] - low[-20:]) # biên độ trung bình 20 phiên
narrowing_ratio = atr_5d / atr_20d

| **Narrowing ratio** | **Điểm** | **Ý nghĩa**                                 |
| ------------------- | -------- | ------------------------------------------- |
| < 0.5               | 100      | Nền cực chặt - VCP textbook                 |
| 0.5-0.7             | 80       | Nền tốt                                     |
| 0.7-0.9             | 60       | Nền vừa phải                                |
| 0.9-1.1             | 40       | Biên độ ổn định, không co lại               |
| > 1.1              | 20       | Biên độ mở rộng - nền loạn, breakout rủi ro |
"""
def cal_atr_n_days(high, low, n, close=None, exclude_today: bool = True):
    """Average True Range over the last n completed sessions (excludes today by default).

    True Range = max(H-L, |H-prev_C|, |L-prev_C|) when close is provided,
    else just H-L. Spec (docs/filter.md §3.3.4, §3.3.6): the 5d/20d ATRs
    used by base quality and risk_ratio must NOT include today.
    """
    end = -1 if exclude_today else 0
    start = end - n
    trs = []
    for i in range(start, end):
        hl = high[i] - low[i]
        if close is not None:
            prev_c = close[i - 1]
            tr = max(hl, abs(high[i] - prev_c), abs(low[i] - prev_c))
        else:
            tr = hl
        trs.append(tr)
    return sum(trs) / n

def cal_narrowing_ratio(atr_5d, atr_20d):
    if atr_20d == 0:
        return 1.0
    return atr_5d / atr_20d

def base_quality_score(narrowing_ratio):
    if narrowing_ratio < 0.5:
        return 100
    elif 0.5 <= narrowing_ratio < 0.7:
        return 80
    elif 0.7 <= narrowing_ratio < 0.9:
        return 60
    elif 0.9 <= narrowing_ratio < 1.1:
        return 40
    else:
        return 20

# Diem giu gia sau breakout
"""
minutes_above_high20 = số phút close > High20 từ t_breakout đến hiện tại
minutes_since_breakout = phút từ t_breakout đến hiện tại
holding_ratio = minutes_above_high20 / minutes_since_breakout

| **Holding ratio** | **Điểm** |
| ----------------- | -------- |
| > 90%            | 100      |
| 70-90%            | 80       |
| 50-70%            | 60       |
| 30-50%            | 40       |
| < 30%             | 20       |
"""
def cal_minutes_above_high20(close, high_20_sessions):
    return sum(1 for c in close if c > high_20_sessions)

def cal_minutes_since_breakout(t_breakout, t_current):
    return (t_current - t_breakout).total_seconds() / 60

def cal_holding_ratio(minutes_above_high20, minutes_since_breakout):
    if minutes_since_breakout == 0:
        return 0  # Tránh chia cho 0
    return minutes_above_high20 / minutes_since_breakout

def holding_score(holding_ratio):
    if holding_ratio > 0.9:
        return 100
    elif 0.7 <= holding_ratio <= 0.9:
        return 80
    elif 0.5 <= holding_ratio < 0.7:
        return 60
    elif 0.3 <= holding_ratio < 0.5:
        return 40
    else:
        return 20


# Diem suc manh dong cua (Closing Strength)
"""
closing_strength = (close - low) / (high - low) × 100

| Closing strength | Điểm | Ý nghĩa                                              |
| ---------------- | ---- | ---------------------------------------------------- |
| > 80%            | 100  | Đóng cửa gần high - buyers kiểm soát đến cuối phiên |
| 60-80%           | 80   | Khá tốt                                              |
| 40-60%           | 60   | Trung tính                                           |
| 20-40%           | 40   | Yếu                                                  |
| < 20%            | 20   | Đóng cửa gần low - sellers kiểm soát cuối phiên      |
"""
def cal_closing_strength(close_today: float, high_today: float, low_today: float) -> float:
    if high_today == low_today:
        return 50.0
    return (close_today - low_today) / (high_today - low_today) * 100

def closing_strength_score(cs: float) -> int:
    if cs > 80:
        return 100
    elif 60 <= cs <= 80:
        return 80
    elif 40 <= cs < 60:
        return 60
    elif 20 <= cs < 40:
        return 40
    else:
        return 20


# He so danh gia rui ro bi khoa T+2.5 (risk_ratio)
"""
risk_ratio = breakout_ratio × (atr_5d / close × 100)

| risk_ratio | Hệ số | Ý nghĩa                              |
| ---------- | ----- | ------------------------------------ |
| < 3        | × 1.0 | Breakout gần + ổn định → giữ nguyên  |
| 3–5        | × 0.85| Rủi ro vừa → giảm nhẹ 15%           |
| 5–7        | × 0.70| Rủi ro cao → giảm 30%               |
| > 7        | × 0.50| Rất nguy hiểm → giảm 50%            |
"""
def cal_risk_ratio(breakout_ratio: float, atr_5d: float, close_today: float) -> float:
    if close_today == 0:
        return 0.0
    return breakout_ratio * (atr_5d / close_today * 100)

def risk_coefficient(risk_ratio: float) -> float:
    if risk_ratio < 3:
        return 1.0
    elif risk_ratio < 5:
        return 0.85
    elif risk_ratio < 7:
        return 0.70
    else:
        return 0.50


# Smart Money Flow
"""
foreign_net_pct = foreign_net_5d / sum(GTGD_daily[-6:-1]) × 100
prop_net_pct    = prop_net_5d / sum(GTGD_daily[-6:-1]) × 100
smart_money_composite = 0.60 × score(foreign) + 0.40 × score(prop)

| Foreign net % (5d) | Điểm |   | Prop net % (5d)   | Điểm |
| ------------------- | ---- | - | ----------------- | ---- |
| > +5%               | 100  |   | > +3%             | 100  |
| +2% đến +5%         | 80   |   | +1% đến +3%       | 80   |
| +0.5% đến +2%       | 60   |   | +0.3% đến +1%     | 60   |
| -0.5% đến +0.5%     | 40   |   | -0.3% đến +0.3%   | 40   |
| -2% đến -0.5%       | 20   |   | -1% đến -0.3%     | 20   |
| < -2%               | 0    |   | < -1%             | 0    |
"""
def cal_foreign_net_pct(foreign_buy_vals: list[float], foreign_sell_vals: list[float], gtgd_5d: float) -> float:
    # Data is newest-first (index 0 = most recent session) → take first 5
    # gtgd_5d = sum of actual daily GTGD for the last 5 sessions
    if gtgd_5d == 0:
        return 0.0
    net_5d = sum(b - s for b, s in zip(foreign_buy_vals[:5], foreign_sell_vals[:5]))
    return net_5d / gtgd_5d * 100

def cal_prop_net_pct(prop_buy_vals: list[float], prop_sell_vals: list[float], gtgd_5d: float) -> float:
    if gtgd_5d == 0:
        return 0.0
    net_5d = sum(b - s for b, s in zip(prop_buy_vals[:5], prop_sell_vals[:5]))
    return net_5d / gtgd_5d * 100

def foreign_net_score(pct: float) -> int:
    if pct > 5:    return 100
    elif pct > 2:  return 80
    elif pct > 0.5: return 60
    elif pct > -0.5: return 40
    elif pct > -2:  return 20
    else:           return 0

def prop_net_score(pct: float) -> int:
    if pct > 3:    return 100
    elif pct > 1:  return 80
    elif pct > 0.3: return 60
    elif pct > -0.3: return 40
    elif pct > -1:  return 20
    else:           return 0

def cal_smart_money_score(f_score: int, p_score: int) -> float:
    """Legacy 2-component SMF (foreign + prop). Used when active flow data
    is unavailable. Weights: 0.60 foreign + 0.40 prop."""
    return 0.60 * f_score + 0.40 * p_score


# ---------------------------------------------------------------------------
# Smart Money Flow — 3-component (Foreign + Prop + Active)
# Spec §3.2.5 — vnstock_data >= 3.2.0 (Insights().flow.{foreign,proprietary,active})
# ---------------------------------------------------------------------------
"""
The new market-wide flow APIs return pre-aggregated NET values over 10
trading sessions (value_10d). We divide by GTGD_10d to express the
inflow/outflow as a percentage of total trading value.

Active flow (dòng tiền chủ động) captures aggressive buy/sell orders
across the whole market; magnitudes tend to be larger than foreign or
prop, so the band table is wider:

| Active net % (10d)  | Điểm |
| ------------------- | ---- |
| > +10%              | 100  |
| +4% đến +10%        | 80   |
| +1% đến +4%         | 60   |
| -1% đến +1%         | 40   |
| -4% đến -1%         | 20   |
| < -4%               | 0    |

3-component composite weights: foreign 0.40 + prop 0.30 + active 0.30.
Foreign keeps the largest share (institutional alpha is the strongest
signal); prop and active get equal smaller shares.
"""


def cal_net_pct(net_value: float | None, gtgd_window: float) -> float | None:
    """Generic helper: net buy/sell value as % of GTGD over the same window.

    Returns None when either input is missing or the denominator is zero.
    """
    if net_value is None or gtgd_window == 0:
        return None
    return net_value / gtgd_window * 100


def active_net_score(pct: float) -> int:
    if pct > 10:    return 100
    elif pct > 4:   return 80
    elif pct > 1:   return 60
    elif pct > -1:  return 40
    elif pct > -4:  return 20
    else:           return 0


def cal_smart_money_score_3c(f_score: int, p_score: int, a_score: int) -> float:
    """3-component SMF: 0.40 foreign + 0.30 prop + 0.30 active."""
    return 0.40 * f_score + 0.30 * p_score + 0.30 * a_score


# ---------------------------------------------------------------------------
# Score Flow (A/D + SMF + Convergence Multiplier) — spec §3.2.4
# ---------------------------------------------------------------------------
"""
flow_base = 0.40 × score_AD + 0.60 × score_SMF
score_flow = min(100, flow_base × convergence_mult)

Convergence multiplier is a 3×3 lookup over (A/D band, SMF band) where the
bands are: LOW ≤39, MID 40-69, HIGH ≥70.
"""

def _flow_band(score: float) -> str:
    if score <= 39:
        return "LOW"
    if score <= 69:
        return "MID"
    return "HIGH"


_CONVERGENCE_TABLE = {
    ("HIGH", "HIGH"): 1.20, ("MID", "HIGH"): 1.10, ("LOW", "HIGH"): 0.90,
    ("HIGH", "MID"):  1.05, ("MID", "MID"):  1.00, ("LOW", "MID"):  0.92,
    ("HIGH", "LOW"):  0.85, ("MID", "LOW"):  0.90, ("LOW", "LOW"):  0.70,
}


def cal_convergence_mult(ad_score_val: float, smf_score_val: float) -> float:
    return _CONVERGENCE_TABLE[(_flow_band(ad_score_val), _flow_band(smf_score_val))]


def cal_score_flow(
    ad_score_val: float,
    smf_score_val: float,
    w_ad: float = 0.40,
    w_smf: float = 0.60,
) -> tuple[float, float, float]:
    """Return (score_flow, flow_base, convergence_mult)."""
    flow_base = w_ad * ad_score_val + w_smf * smf_score_val
    mult = cal_convergence_mult(ad_score_val, smf_score_val)
    return min(100.0, flow_base * mult), flow_base, mult
