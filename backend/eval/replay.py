"""TradingGroup risk-module evaluation harness.

Offline replay of historical decisions under two exit policies:

- Baseline (TradingAgents mode): hold to horizon H. PnL = (P_H - P_0) / P_0.
- TradingGroup mode: walk forward day-by-day, force-exit at the first bar
  where realized PnL ≤ -T_SL or ≥ T_TP. Otherwise exit at H. Honors the
  VN T+2.5 microstructure floor — no exit before T+2 afternoon (bar index >= 3).

Designed to run against historical entries read from `TradingMemoryLog` or
from any list of dicts with `ticker`, `date`, `stop_loss_pct`,
`take_profit_pct`. The replay never calls the trading graph or any LLM;
it just fetches daily OHLCV via `get_trading_history`.

Ablations supported:
- Multipliers ±X% per style
- Horizon sweep {5, 10, 15}
- Vol-window sweep {5, 10, 20, 30} (only meaningful if you re-derive
  thresholds — see `replay_with_recomputed_thresholds`).
"""

from __future__ import annotations

import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from statistics import stdev
from typing import Iterable, Optional

from infrastructure.market_data.data import get_trading_history

logger = logging.getLogger(__name__)


# T+2.5 floor: position cannot be exited before T+2 afternoon. We index
# bars 0..N from entry; bar 0 is the entry session close. The earliest
# legal exit is bar 3 (afternoon of T+2), which we approximate as the
# close of the third forward session.
T_SETTLEMENT_FLOOR_BARS = 3


@dataclass
class ReplayResult:
    ticker: str
    entry_date: str
    entry_price: float
    exit_day: int
    exit_price: float
    pnl: float
    triggered: str  # "stop_loss" | "take_profit" | "horizon"


@dataclass
class ReplaySummary:
    n: int
    mean_pnl: float
    median_pnl: float
    stdev_pnl: float
    win_rate: float
    avg_holding_days: float
    stop_loss_hits: int
    take_profit_hits: int
    horizon_exits: int
    per_trade: list[ReplayResult] = field(default_factory=list)


def _parse_date(s) -> datetime:
    if hasattr(s, "date"):
        return s if isinstance(s, datetime) else datetime.combine(s.date(), datetime.min.time())
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _bars_from_entry(symbol: str, entry_date: str, horizon: int) -> list[dict]:
    """Return forward bars starting at the entry session, length up to horizon+1."""
    history = get_trading_history(symbol, days=horizon + 21)
    if not history:
        return []
    start = _parse_date(entry_date).date()
    cut: list[dict] = []
    for row in history:
        rt = row["time"]
        rt_date = rt.date() if hasattr(rt, "date") else _parse_date(rt).date()
        if rt_date >= start:
            cut.append(row)
    return cut[: horizon + 1]


def replay_one(
    ticker: str,
    entry_date: str,
    t_sl_pct: float,
    t_tp_pct: float,
    horizon_days: int = 5,
    enforce_settlement_floor: bool = True,
) -> Optional[ReplayResult]:
    """Replay a single entry. Returns None if price data is unavailable."""
    bars = _bars_from_entry(ticker, entry_date, horizon_days)
    if len(bars) < 2:
        return None

    entry_price = float(bars[0]["close"])
    if entry_price <= 0:
        return None

    t_sl = t_sl_pct / 100.0
    t_tp = t_tp_pct / 100.0

    exit_day = min(horizon_days, len(bars) - 1)
    exit_price = float(bars[exit_day]["close"])
    triggered = "horizon"

    for i in range(1, min(horizon_days + 1, len(bars))):
        if enforce_settlement_floor and i < T_SETTLEMENT_FLOOR_BARS:
            continue
        pnl = (float(bars[i]["close"]) - entry_price) / entry_price
        if pnl <= -t_sl:
            exit_day = i
            exit_price = float(bars[i]["close"])
            triggered = "stop_loss"
            break
        if pnl >= t_tp:
            exit_day = i
            exit_price = float(bars[i]["close"])
            triggered = "take_profit"
            break

    pnl = (exit_price - entry_price) / entry_price
    return ReplayResult(
        ticker=ticker,
        entry_date=str(entry_date)[:10],
        entry_price=entry_price,
        exit_day=exit_day,
        exit_price=exit_price,
        pnl=pnl,
        triggered=triggered,
    )


def replay_baseline_one(
    ticker: str,
    entry_date: str,
    horizon_days: int = 5,
) -> Optional[ReplayResult]:
    """Hold-to-horizon baseline (no thresholds). Mirrors TradingAgents mode."""
    bars = _bars_from_entry(ticker, entry_date, horizon_days)
    if len(bars) < 2:
        return None
    entry_price = float(bars[0]["close"])
    exit_day = min(horizon_days, len(bars) - 1)
    exit_price = float(bars[exit_day]["close"])
    return ReplayResult(
        ticker=ticker,
        entry_date=str(entry_date)[:10],
        entry_price=entry_price,
        exit_day=exit_day,
        exit_price=exit_price,
        pnl=(exit_price - entry_price) / entry_price,
        triggered="horizon",
    )


def summarize(results: list[ReplayResult]) -> ReplaySummary:
    if not results:
        return ReplaySummary(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0, [])
    pnls = [r.pnl for r in results]
    holds = [r.exit_day for r in results]
    return ReplaySummary(
        n=len(results),
        mean_pnl=statistics.fmean(pnls),
        median_pnl=statistics.median(pnls),
        stdev_pnl=stdev(pnls) if len(pnls) >= 2 else 0.0,
        win_rate=sum(1 for p in pnls if p > 0) / len(pnls),
        avg_holding_days=statistics.fmean(holds),
        stop_loss_hits=sum(1 for r in results if r.triggered == "stop_loss"),
        take_profit_hits=sum(1 for r in results if r.triggered == "take_profit"),
        horizon_exits=sum(1 for r in results if r.triggered == "horizon"),
        per_trade=results,
    )


def replay_batch(
    entries: Iterable[dict],
    horizon_days: int = 5,
    multiplier_scale: float = 1.0,
    enforce_settlement_floor: bool = True,
) -> ReplaySummary:
    """Replay entries that already carry `stop_loss_pct` / `take_profit_pct`.

    Args:
        entries: iterable of dicts with keys `ticker`, `date`,
            `stop_loss_pct`, `take_profit_pct`. Entries missing thresholds
            are skipped.
        horizon_days: maximum holding period in trading sessions.
        multiplier_scale: scales both thresholds (e.g. 0.8, 1.0, 1.2 for
            the ±20% ablation).
        enforce_settlement_floor: if True, no exit before T+2.5.
    """
    results: list[ReplayResult] = []
    for e in entries:
        sl = e.get("stop_loss_pct")
        tp = e.get("take_profit_pct")
        if sl is None or tp is None:
            continue
        r = replay_one(
            ticker=e["ticker"],
            entry_date=e["date"],
            t_sl_pct=sl * multiplier_scale,
            t_tp_pct=tp * multiplier_scale,
            horizon_days=horizon_days,
            enforce_settlement_floor=enforce_settlement_floor,
        )
        if r is not None:
            results.append(r)
    return summarize(results)


def replay_baseline(
    entries: Iterable[dict],
    horizon_days: int = 5,
) -> ReplaySummary:
    """Hold-to-horizon baseline over the same entries."""
    results: list[ReplayResult] = []
    for e in entries:
        r = replay_baseline_one(e["ticker"], e["date"], horizon_days)
        if r is not None:
            results.append(r)
    return summarize(results)


def replay_with_recomputed_thresholds(
    entries: Iterable[dict],
    horizon_days: int,
    vol_window: int,
    style_multipliers: dict,
    style_key: str = "trading_style",
    sigma_fallback: float = 0.03,
    enforce_settlement_floor: bool = True,
) -> ReplaySummary:
    """Recompute σ_d,window at each entry date, derive fresh thresholds, replay.

    Useful for vol-window ablations — recomputes σ from the bars *strictly
    before* the entry session (no look-ahead bias).
    """
    results: list[ReplayResult] = []
    for e in entries:
        ticker = e["ticker"]
        entry_date = e["date"]
        style = (e.get(style_key) or "swing").lower()
        m = style_multipliers.get(style) or style_multipliers.get("swing")
        if m is None:
            continue

        sigma = _sigma_strict_before(ticker, entry_date, vol_window, sigma_fallback)
        t_sl_pct = m["sl"] * sigma * 100.0
        t_tp_pct = m["tp"] * sigma * 100.0

        r = replay_one(
            ticker=ticker,
            entry_date=entry_date,
            t_sl_pct=t_sl_pct,
            t_tp_pct=t_tp_pct,
            horizon_days=horizon_days,
            enforce_settlement_floor=enforce_settlement_floor,
        )
        if r is not None:
            results.append(r)
    return summarize(results)


def _sigma_strict_before(symbol: str, entry_date, window: int, fallback: float) -> float:
    """σ of log-returns using bars strictly before entry_date (no look-ahead)."""
    history = get_trading_history(symbol, days=window * 3 + 14)
    if not history:
        return fallback
    cut_date = _parse_date(entry_date).date()
    before = [
        r for r in history
        if (r["time"].date() if hasattr(r["time"], "date") else _parse_date(r["time"]).date()) < cut_date
    ]
    if len(before) < window + 1:
        return fallback
    closes = [float(r["close"]) for r in before[-(window + 1):]]
    log_returns = []
    for i in range(1, len(closes)):
        if closes[i - 1] > 0 and closes[i] > 0:
            log_returns.append(math.log(closes[i] / closes[i - 1]))
    if len(log_returns) < 2:
        return fallback
    return stdev(log_returns)


def format_summary(label: str, s: ReplaySummary) -> str:
    """Human-readable one-block summary for CLI / paper tables."""
    if s.n == 0:
        return f"[{label}] n=0 (no resolvable entries)"
    return (
        f"[{label}] n={s.n}  "
        f"mean={s.mean_pnl:+.2%}  median={s.median_pnl:+.2%}  "
        f"σ={s.stdev_pnl:.2%}  win_rate={s.win_rate:.1%}  "
        f"avg_hold={s.avg_holding_days:.1f}d  "
        f"SL={s.stop_loss_hits} TP={s.take_profit_hits} H={s.horizon_exits}"
    )
