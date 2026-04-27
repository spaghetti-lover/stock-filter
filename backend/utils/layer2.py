import statistics
from dataclasses import dataclass


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


DEFAULT_WEIGHTS = {
    "liquidity": 0.35, "momentum": 0.30, "breakout": 0.35,
    "liq_gtgd20": 0.55, "liq_intraday": 0.30, "liq_cv": 0.15,
    "mom_volatility": 0.30, "mom_ma": 0.20, "mom_rs": 0.20, "mom_ad": 0.15, "mom_tech": 0.15,
    "brk_price": 0.30, "brk_vol": 0.25, "brk_dryup": 0.20, "brk_base": 0.15, "brk_hold": 0.10,
    "composite_1d": 0.50, "composite_5d": 0.30, "composite_20d": 0.20,
    "ma_ma20": 0.35, "ma_ma50": 0.30, "ma_slope": 0.35,
    "rs_3m": 0.60, "rs_1m": 0.40,
    "tech_rsi": 0.50, "tech_macd": 0.50,
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

def cal_intraday_gtgd(intraday: list[dict]) -> float:
    return sum(t["price"] * t["volume"] for t in intraday)

def cal_intraday_volume(intraday: list[dict]) -> float:
    return sum(t["volume"] for t in intraday)

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
    gtgd_intraday   = cal_intraday_gtgd(intraday)
    intraday_ratio_ = cal_intraday_ratio(gtgd_intraday, gtgd20_val, minutes_elapsed)
    cv_val          = cal_cv_val(cal_gtgd_daily(close_arr, vol_arr)[-21:-1])

    s_gtgd20    = gtdg20_score(gtgd20_val)
    s_intraday  = intraday_score(intraday_ratio_)
    s_cv        = cv_score(cv_val)
    s_liquidity = liquidity_score(s_gtgd20, s_intraday, s_cv)

    liq_breakdown = {
        "gtgd20": {"value": gtgd20_val, "score": s_gtgd20},
        "intraday_ratio": {"value": intraday_ratio_, "score": s_intraday},
        "cv": {"value": cv_val, "score": s_cv},
    }

    # ── Momentum ─────────────────────────────────────────────────────────
    ret_1d  = cal_return_n_days(close_today, close_arr[-2])
    ret_5d  = cal_return_n_days(close_today, close_arr[-6])
    ret_20d = cal_return_n_days(close_today, close_arr[-21])
    composite_ret = cal_composite_return(ret_1d, ret_5d, ret_20d)
    s_volatility = price_volatility_score(composite_ret)

    ma20_today   = cal_ma(close_arr, 20)
    ma50_today   = cal_ma(close_arr, 50)
    ma20_5d_ago  = cal_ma_n_days_ago(close_arr, 20, 5)
    pv_ma20      = cal_price_vs_ma(close_today, ma20_today)
    pv_ma50      = cal_price_vs_ma(close_today, ma50_today)
    slope_val    = cal_slope_pct(ma20_today, ma20_5d_ago)
    s_pv_ma20    = score_price_vs_ma(pv_ma20)
    s_pv_ma50    = score_price_vs_ma(pv_ma50)
    s_slope      = score_slope_pct(slope_val)
    s_ma         = ma_score(pv_ma20, pv_ma50, slope_val)

    stock_r3m = stock_return_n_days(close_arr[-1], close_arr[-64]) if len(close_arr) >= 64 else 0
    stock_r1m = stock_return_n_days(close_arr[-1], close_arr[-22]) if len(close_arr) >= 22 else 0
    vn_r3m    = vnindex_return_n_days(vn_close[-1], vn_close[-64]) if len(vn_close) >= 64 else 0
    vn_r1m    = vnindex_return_n_days(vn_close[-1], vn_close[-22]) if len(vn_close) >= 22 else 0
    rs_3m_val = cal_rs(stock_r3m, vn_r3m)
    rs_1m_val = cal_rs(stock_r1m, vn_r1m)
    rs_w_val  = cal_rs_weighted(rs_3m_val, rs_1m_val)
    s_rs      = rs_score(rs_w_val)

    ad_val    = cal_ad_ratio(close_arr[-21:], vol_arr[-21:])
    s_ad      = ad_score(ad_val)

    rsi_val   = cal_rsi(close_arr)
    macd_val  = cal_macd_histogram(close_arr, close_today)
    s_rsi     = score_rsi(rsi_val)
    s_macd    = score_macd_histogram(macd_val)
    s_tech    = technical_confirmation_score(rsi_val, macd_val)

    s_momentum = momentum_score(s_volatility, s_ma, s_rs, s_ad, s_tech)

    mom_breakdown = {
        "composite_return": {
            "value": composite_ret, "score": s_volatility,
            "detail": {"return_1d": ret_1d, "return_5d": ret_5d, "return_20d": ret_20d},
        },
        "ma": {
            "score": s_ma,
            "detail": {
                "price_vs_ma20": {"value": pv_ma20, "score": s_pv_ma20},
                "price_vs_ma50": {"value": pv_ma50, "score": s_pv_ma50},
                "slope_pct": {"value": slope_val, "score": s_slope},
            },
        },
        "rs": {
            "value": rs_w_val, "score": s_rs,
            "detail": {"rs_3m": rs_3m_val, "rs_1m": rs_1m_val},
        },
        "ad": {"value": ad_val, "score": s_ad},
        "technical": {
            "score": s_tech,
            "detail": {
                "rsi": {"value": rsi_val, "score": s_rsi},
                "macd_histogram_pct": {"value": macd_val, "score": s_macd},
            },
        },
    }

    # ── Breakout ─────────────────────────────────────────────────────────
    high20_val     = cal_high_20_sessions(high_arr[-21:])
    b_ratio        = cal_breakout_ratio(close_today, high20_val)
    vol_ratio_val  = cal_volume_ratio(
        cal_intraday_volume(intraday),
        cal_volume_expected(avg_vol_20d, minutes_elapsed),
    )
    dry_up_val     = cal_dry_up_ratio(cal_pre_vol_avg(vol_arr), avg_vol_20d)
    narrowing_val  = cal_narrowing_ratio(
        cal_atr_n_days(high_arr, low_arr, 5),
        cal_atr_n_days(high_arr, low_arr, 20),
    )
    holding_val    = cal_holding_ratio_intraday(intraday, high20_val)

    s_price_brk  = price_breakout_score(b_ratio)
    s_vol_conf   = volume_confirmation_score(vol_ratio_val)
    s_dryup      = volume_dryup_score(dry_up_val)
    s_base       = base_quality_score(narrowing_val)
    s_hold       = holding_score(holding_val)
    gate_active  = b_ratio >= 1.0
    s_breakout   = breakout_score(s_price_brk, s_vol_conf, s_dryup, s_base, s_hold, b_ratio)

    brk_breakdown = {
        "breakout_ratio": {"value": b_ratio, "score": s_price_brk},
        "volume_ratio": {"value": vol_ratio_val, "score": s_vol_conf},
        "dry_up_ratio": {"value": dry_up_val, "score": s_dryup},
        "narrowing_ratio": {"value": narrowing_val, "score": s_base},
        "holding_ratio": {"value": holding_val, "score": s_hold},
        "gate_active": gate_active,
    }

    return BuyScoreBreakdown(
        buy_score=round(buy_score(s_liquidity, s_momentum, s_breakout), 2),
        liquidity_score=round(s_liquidity, 2),
        momentum_score=round(s_momentum, 2),
        breakout_score=round(s_breakout, 2),
        liquidity=liq_breakdown,
        momentum=mom_breakdown,
        breakout=brk_breakdown,
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

# Diem GTGD20
"""
Quy mô tiền giao dịch nền - mã này bình thường có đủ tiền quay vòng không?_

GTGD_ngay = close × volume

GTGD20 = mean(GTGD_ngay, 20_phiên)

| **GTGD20** | **Điểm** | **Phân loại**                       |
| ---------- | -------- | ----------------------------------- |
| ≥ 100 tỷ   | 100      | Thanh khoản cực cao (VCB, HPG, VHM) |
| 50-100 tỷ  | 80       | Thanh khoản cao                     |
| 20-50 tỷ   | 60       | Thanh khoản khá                     |
| 5-20 tỷ    | 40       | Trung bình                          |
| 1-5 tỷ     | 20       | Thấp                                |
| < 1 tỷ     | 0        | Rất thấp                            |

"""
def gtdg20_score(gtdg20):
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
_Ý nghĩa: Phân biệt mã thanh khoản tốt nhưng đi ngang với mã đang tăng thật. Với lướt sóng, chỉ cần bắt được đà đang mạnh - không cần dự báo dài hạn._

Điểm động lượng = 0.30 × Điểm biến động giá composite + 0.20 × Điểm phân tích MA + 0.20 × Điểm sức mạnh tương đối (RS) ← học từ VCP + 0.15 × Điểm tích lũy/phân phối (A/D) ← học từ CANSLIM + 0.15 × Điểm xác nhận kỹ thuật (RSI+MACD)
"""
def momentum_score(price_volatility_score, ma_score, rs_score, ad_score, technical_confirmation_score):
    return 0.30 * price_volatility_score + 0.20 * ma_score + 0.20 * rs_score + 0.15 * ad_score + 0.15 * technical_confirmation_score

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

def price_volatility_score(composite_return):
    if composite_return < 0:
        return 0
    elif 0 <= composite_return < 1:
        return 20
    elif 1 <= composite_return < 2:
        return 40
    elif 2 <= composite_return < 4:
        return 60
    elif 4 <= composite_return < 7:
        return 80
    else:
        return 100

# Diem phan tich MA
"""
Điểm này đo 2 thứ

**1. Vị trí giá so với MA - "Giá đang ở đâu?"**

Giá > MA50 > MA20 → Bullish alignment → điểm cao

Giá < MA20 → Yếu → điểm thấp/0

**2. Độ dốc MA20 - "Momentum có đang tăng tốc không?"**

slope_pct = (MA20_hôm_nay - MA20_cách_5_phiên) / MA20_cách_5_phiên × 100

ma20 = mean(close, 20)
ma50 = mean(close, 50)
slope_pct = (ma20_today - ma20_5d_ago) / ma20_5d_ago × 100
price_vs_ma20 = (close_today - ma20) / ma20 × 100
price_vs_ma50 = (close_today - ma50) / ma50 × 100

Bảng điểm áp dụng chung cho cả MA20 và MA50:
| **% so với MA** | **Điểm** |
| --------------- | -------- |
| Dưới MA (< 0%)  | 0        |
| 0-2% trên       | 40       |
| 2-5% trên       | 70       |
| > 5% trên      | 100      |

Slope MA20:
| **Slope%** | **Điểm** |
| ---------- | -------- |
| < 0%       | 0        |
| 0-0.2%     | 30       |
| 0.2-0.5%   | 60       |
| > 0.5%    | 100      |

score_ma = 0.35 × score(price_vs_ma20) + 0.30 × score(price_vs_ma50) + 0.35 × score(slope_pct)
"""

def cal_slope_pct(ma20_today, ma20_5d_ago):
    return (ma20_today - ma20_5d_ago) / ma20_5d_ago * 100

def cal_price_vs_ma(close_today, ma):
    return (close_today - ma) / ma * 100

def score_price_vs_ma(price_vs_ma):
    if price_vs_ma < 0:
        return 0
    elif 0 <= price_vs_ma < 2:
        return 40
    elif 2 <= price_vs_ma < 5:
        return 70
    else:
        return 100

def score_slope_pct(slope_pct):
    if slope_pct < 0:
        return 0
    elif 0 <= slope_pct < 0.2:
        return 30
    elif 0.2 <= slope_pct < 0.5:
        return 60
    else:
        return 100

def ma_score(price_vs_ma20, price_vs_ma50, slope_pct):
    score20 = score_price_vs_ma(price_vs_ma20)
    score50 = score_price_vs_ma(price_vs_ma50)
    score_slope = score_slope_pct(slope_pct)
    return 0.35 * score20 + 0.30 * score50 + 0.35 * score_slope

# Diem suc manh tuong doi vs VN-Index (RS)
"""
_Tham khảo từ: VCP - Relative Strength component (15% weight trong VCP)_

rs_3m = stock_return_3M - vnindex_return_3M
rs_1m = stock_return_1M - vnindex_return_1M
rs_weighted = 0.60 × rs_3m + 0.40 × rs_1m

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
    return 0.60 * rs_3m + 0.40 * rs_1m

def rs_score(rs_weighted):
    if rs_weighted > 10:
        return 100
    elif 5 < rs_weighted <= 10:
        return 80
    elif 0 < rs_weighted <= 5:
        return 60
    elif -5 < rs_weighted <= 0:
        return 40
    else:
        return 20

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
    if len(down_vol) == 0:  # Tránh chia cho 0
        return float('inf')  # Rất tích lũy
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

score_technical = 0.50 × score_rsi + 0.50 × score_macd
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
    if rsi < 50:
        return 20
    elif 50 <= rsi < 60:
        return 50
    elif 60 <= rsi < 70:
        return 80
    else:
        return 100

def score_macd_histogram(histogram_pct):
    if histogram_pct < 0:
        return 20
    elif 0 <= histogram_pct < 0.05:
        return 50
    else:
        return 100

def technical_confirmation_score(rsi, histogram_pct):
    return 0.50 * score_rsi(rsi) + 0.50 * score_macd_histogram(histogram_pct)

# Diem Breakout
"""
Gate condition:
if breakout_ratio < 1.0:
    return breakout_score = 0  # Chưa breakout → toàn bộ Breakout score = 0

Điểm breakout = 0.30 × Điểm vượt cản giá
             + 0.25 × Điểm xác nhận volume breakout
             + 0.20 × Điểm volume dry-up trước breakout
             + 0.15 × Điểm chất lượng nền giá
             + 0.10 × Điểm giữ giá sau breakout
"""
def breakout_score(price_breakout_score, volume_confirmation_score, volume_dryup_score, base_quality_score, holding_score, breakout_ratio):
    if breakout_ratio < 1.0:
        return 0
    return (0.30 * price_breakout_score
            + 0.25 * volume_confirmation_score
            + 0.20 * volume_dryup_score
            + 0.15 * base_quality_score
            + 0.10 * holding_score)

# Diem vuot can gia
"""
High20 = max(high, 20_sessions)  # không tính hôm nay
breakout_ratio = close_today / High20

| **Breakout ratio** | **Điểm**          |
| ------------------ | ----------------- |
| < 1.00             | Gate: toàn bộ = 0 |
| 1.00-1.01          | 40                |
| 1.01-1.02          | 70                |
| > 1.02             | 100               |
"""
def cal_high_20_sessions(high):
    return max(high[:-1])  # Không tính hôm nay

def cal_breakout_ratio(close_today, high_20_sessions):
    return close_today / high_20_sessions

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
        return 20
    elif 1.0 <= volume_ratio < 1.3:
        return 50
    elif 1.3 <= volume_ratio < 1.8:
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
def cal_atr_n_days(high, low, n):
    return sum([high[i] - low[i] for i in range(-n, 0)]) / n

def cal_narrowing_ratio(atr_5d, atr_20d):
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
