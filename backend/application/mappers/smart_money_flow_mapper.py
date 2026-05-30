from datetime import datetime, timezone, timedelta

from domain.entities.smart_money_flow_series import SmartMoneyFlowSeries
from application.dto.smart_money_flow_dto import SmartMoneyFlowResponse, SmartMoneyFlowRow


_PCT_CAP = 25.0
_BLOCK_DEAL_THRESHOLD = 35.0

# §7 signal tiers (rolling 5-day sm_net_pct)
_SIGNAL_STRONG_ACCUMULATION = ("✦ Tích lũy mạnh", "#1D6B4F")
_SIGNAL_ACCUMULATION = ("↑ Tích lũy", "#1D9E75")
_SIGNAL_NEUTRAL = ("→ Trung tính", "#888888")
_SIGNAL_DISTRIBUTION = ("↓ Phân phối", "#D85A30")
_SIGNAL_STRONG_DISTRIBUTION = ("⚠ Phân phối mạnh", "#A32D2D")
_SIGNAL_INSUFFICIENT = ("— Insufficient history", "#888888")


def _signal_for(sm_net_5d: float | None) -> tuple[str, str]:
    if sm_net_5d is None:
        return _SIGNAL_INSUFFICIENT
    if sm_net_5d > 5.0:
        return _SIGNAL_STRONG_ACCUMULATION
    if sm_net_5d > 2.0:
        return _SIGNAL_ACCUMULATION
    if sm_net_5d >= -2.0:
        return _SIGNAL_NEUTRAL
    if sm_net_5d >= -5.0:
        return _SIGNAL_DISTRIBUTION
    return _SIGNAL_STRONG_DISTRIBUTION


def _divergence_for(foreign_net_pct: float, prop_net_pct: float):
    if foreign_net_pct > 3.0 and prop_net_pct < -1.0:
        return "prop_taking_profit"
    if foreign_net_pct < -3.0 and prop_net_pct > 1.0:
        return "prop_supporting"
    return None


def _cap(v: float) -> float:
    if v > _PCT_CAP:
        return _PCT_CAP
    if v < -_PCT_CAP:
        return -_PCT_CAP
    return v


class SmartMoneyFlowMapper:
    @staticmethod
    def to_response(series: SmartMoneyFlowSeries) -> SmartMoneyFlowResponse:
        rows = series.rows

        # Pre-compute uncapped sm_net_pct for rolling calculation.
        sm_uncapped: list[float] = []
        f_pcts: list[float] = []
        p_pcts: list[float] = []
        for r in rows:
            f_net = r.foreign_buy_value - r.foreign_sell_value
            p_net = r.prop_buy_value - r.prop_sell_value
            f_pct = (f_net / r.total_gtgd) * 100.0 if r.total_gtgd else 0.0
            p_pct = (p_net / r.total_gtgd) * 100.0 if r.total_gtgd else 0.0
            f_pcts.append(f_pct)
            p_pcts.append(p_pct)
            sm_uncapped.append(f_pct + p_pct)

        out_rows: list[SmartMoneyFlowRow] = []
        for i, r in enumerate(rows):
            f_pct = f_pcts[i]
            p_pct = p_pcts[i]
            sm_unc = sm_uncapped[i]
            sm = _cap(sm_unc)

            sm_gross = (
                r.foreign_buy_value + r.foreign_sell_value
                + r.prop_buy_value + r.prop_sell_value
            )
            dominance = (sm_gross / r.total_gtgd) * 100.0 if r.total_gtgd else 0.0

            if i >= 4:
                window = sm_uncapped[i - 4 : i + 1]
                sm_5d: float | None = sum(window) / 5.0
            else:
                sm_5d = None

            label, color = _signal_for(sm_5d)
            divergence = _divergence_for(f_pct, p_pct)

            out_rows.append(SmartMoneyFlowRow(
                date=r.date,
                foreign_buy_value=r.foreign_buy_value,
                foreign_sell_value=r.foreign_sell_value,
                prop_buy_value=r.prop_buy_value,
                prop_sell_value=r.prop_sell_value,
                total_gtgd=r.total_gtgd,
                close_price=r.close_price,
                foreign_net_pct=round(f_pct, 4),
                prop_net_pct=round(p_pct, 4),
                sm_net_pct=round(sm, 4),
                sm_net_pct_uncapped=round(sm_unc, 4),
                dominance_pct=round(dominance, 4),
                sm_net_5d=round(sm_5d, 4) if sm_5d is not None else None,
                block_deal=dominance > _BLOCK_DEAL_THRESHOLD,
                divergence_type=divergence,
                signal_label=label,
                signal_color=color,
            ))

        fetched_at = datetime.now(tz=timezone(timedelta(hours=7))).isoformat()
        return SmartMoneyFlowResponse(
            symbol=series.symbol,
            days_requested=series.days_requested,
            fetched_at=fetched_at,
            rows=out_rows,
        )
