"""Baseline backtest for slide 17 — VN-Index buy & hold, equal-weight VN30,
SMA(10/50) crossover. No LLM calls — runs in seconds.

Produces a CSV + console table with CR / SR / MDD for each baseline,
under zero-cost and 0.6% round-trip cost scenarios.

Usage (from project root):
    uv run python3 -B scripts/backtest_baselines.py
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from infrastructure.market_data.data import get_trading_history, get_vnindex_history  # noqa: E402

# Same VN30 list as the Monte Carlo script — consistent universe.
VN30 = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
]

PERIOD_START = date(2025, 3, 1)  # after SMA(50) warm-up on Jan-Feb data
PERIOD_END = date(2026, 5, 31)
LOOKBACK_DAYS = 500  # API caps near here; covers full available history
COST_PER_SIDE = 0.003  # 0.3% per side → 0.6% round-trip
RISK_FREE = 0.0  # VN risk-free not material at daily annualization for thesis


@dataclass
class BacktestResult:
    name: str
    cost_pct: float  # round-trip cost applied
    cumulative_return: float
    sharpe: float
    max_drawdown: float
    n_trades: int


def _fetch_closes(symbol: str) -> Optional[pd.Series]:
    """Return Series indexed by date, values = close, restricted to the period."""
    rows = get_trading_history(symbol, days=LOOKBACK_DAYS)
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["time"]).dt.date
    df = df.set_index("date")[["close"]].astype(float).sort_index()
    return df["close"]


def _fetch_vnindex() -> Optional[pd.Series]:
    rows = get_vnindex_history(LOOKBACK_DAYS)
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["time"]).dt.date
    df = df.set_index("date")[["close"]].astype(float).sort_index()
    return df["close"]


def _restrict_to_period(s: pd.Series) -> pd.Series:
    return s[(s.index >= PERIOD_START) & (s.index <= PERIOD_END)]


def _metrics_from_equity(
    equity: pd.Series, n_trades: int, name: str, cost_pct: float
) -> BacktestResult:
    if len(equity) < 2:
        return BacktestResult(name, cost_pct, 0.0, 0.0, 0.0, n_trades)
    returns = equity.pct_change().dropna()
    cr = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    mu = float(returns.mean())
    sigma = float(returns.std(ddof=1))
    sharpe = float((mu - RISK_FREE) / sigma * math.sqrt(252)) if sigma > 0 else 0.0
    rolling_max = equity.cummax()
    drawdown = equity / rolling_max - 1.0
    mdd = float(drawdown.min())
    return BacktestResult(name, cost_pct, cr, sharpe, mdd, n_trades)


def buy_and_hold_vnindex() -> tuple[BacktestResult, BacktestResult]:
    s = _fetch_vnindex()
    if s is None:
        raise SystemExit("VN-Index history unavailable")
    s = _restrict_to_period(s)
    equity_zero = s / s.iloc[0]
    # Single round-trip cost = enter at start, exit at end.
    equity_cost = equity_zero * (1.0 - 2 * COST_PER_SIDE)
    return (
        _metrics_from_equity(equity_zero, 1, "Buy & Hold VN-Index", 0.0),
        _metrics_from_equity(equity_cost, 1, "Buy & Hold VN-Index", 2 * COST_PER_SIDE),
    )


def equal_weight_vn30(closes: dict[str, pd.Series]) -> tuple[BacktestResult, BacktestResult]:
    """Equal-weight portfolio rebalanced daily."""
    df = pd.DataFrame(closes)
    df = df[(df.index >= PERIOD_START) & (df.index <= PERIOD_END)]
    df = df.dropna(axis=1, how="all")
    df = df.ffill().dropna()
    if df.empty:
        raise SystemExit("No VN30 close data")
    daily_ret = df.pct_change().dropna()
    portfolio_ret = daily_ret.mean(axis=1)
    equity = (1.0 + portfolio_ret).cumprod()
    equity = pd.concat([pd.Series([1.0], index=[df.index[0]]), equity])
    equity_cost = equity * (1.0 - 2 * COST_PER_SIDE)
    return (
        _metrics_from_equity(equity, 1, "Equal-weight VN30", 0.0),
        _metrics_from_equity(equity_cost, 1, "Equal-weight VN30", 2 * COST_PER_SIDE),
    )


def sma_crossover(
    closes: dict[str, pd.Series], fast: int = 10, slow: int = 50
) -> tuple[BacktestResult, BacktestResult]:
    """Long when SMA(fast) > SMA(slow), flat otherwise; equal weight across signals."""
    df = pd.DataFrame(closes)
    df = df.ffill()
    sma_fast = df.rolling(fast).mean()
    sma_slow = df.rolling(slow).mean()
    signal = (sma_fast > sma_slow).astype(int)  # 1 = long, 0 = flat
    # Restrict to period (signals before period are used for state, not measured)
    signal = signal[(signal.index >= PERIOD_START) & (signal.index <= PERIOD_END)]
    df_period = df[(df.index >= PERIOD_START) & (df.index <= PERIOD_END)]
    daily_ret = df_period.pct_change().fillna(0.0)
    # Position taken at close of T applies to T+1's return.
    weighted = signal.shift(1).fillna(0) * daily_ret
    # Equal weight across active signals each day
    active = signal.shift(1).fillna(0).sum(axis=1).replace(0, np.nan)
    portfolio_ret = (weighted.sum(axis=1) / active).fillna(0.0)
    # Count round-trip trades as cross-overs
    flips = (signal != signal.shift(1).fillna(0)).sum().sum()
    n_round_trips = int(flips // 2)
    equity = (1.0 + portfolio_ret).cumprod()
    # Cost model: subtract turnover * cost_per_side from each day
    turnover = (signal - signal.shift(1).fillna(0)).abs().sum(axis=1) / df_period.shape[1]
    cost_drag = (turnover * COST_PER_SIDE).cumsum()
    equity_cost = equity * np.exp(-cost_drag)
    return (
        _metrics_from_equity(equity, n_round_trips, "SMA(10/50) crossover", 0.0),
        _metrics_from_equity(
            equity_cost, n_round_trips, "SMA(10/50) crossover", 2 * COST_PER_SIDE
        ),
    )


def main() -> None:
    print(f"Loading {len(VN30)} VN30 tickers + VN-Index ...")
    closes: dict[str, pd.Series] = {}
    for sym in VN30:
        s = _fetch_closes(sym)
        if s is not None and len(s) >= 60:
            closes[sym] = s
        else:
            print(f"  skip {sym}: insufficient history")
    print(f"  loaded {len(closes)} / {len(VN30)} VN30 tickers")

    results: list[BacktestResult] = []

    bh_zero, bh_cost = buy_and_hold_vnindex()
    results += [bh_zero, bh_cost]

    ew_zero, ew_cost = equal_weight_vn30(closes)
    results += [ew_zero, ew_cost]

    sma_zero, sma_cost = sma_crossover(closes)
    results += [sma_zero, sma_cost]

    out_dir = REPO_ROOT / "docs" / "thuyetrinh"
    out_dir.mkdir(parents=True, exist_ok=True)
    df_out = pd.DataFrame(
        [
            {
                "strategy": r.name,
                "cost_pct": f"{r.cost_pct * 100:.1f}%",
                "CR": f"{r.cumulative_return:+.2%}",
                "SR": f"{r.sharpe:+.2f}",
                "MDD": f"{r.max_drawdown:.2%}",
                "n_trades": r.n_trades,
            }
            for r in results
        ]
    )
    df_out.to_csv(out_dir / "backtest_baselines.csv", index=False)

    print("\n=== Backtest Baselines — VN30 ===")
    print(df_out.to_string(index=False))
    print(f"\nSaved: {out_dir / 'backtest_baselines.csv'}")

    from eval.results_io import write_result

    json_path = write_result(
        "baselines",
        experiment="Baseline backtest — VN-Index / EW-VN30 / SMA(10,50)",
        params={
            "universe": "VN30",
            "n_tickers": len(closes),
            "period_start": str(PERIOD_START),
            "period_end": str(PERIOD_END),
            "cost_per_side": COST_PER_SIDE,
        },
        rows=[
            {
                "strategy": r.name,
                "cost_pct": round(r.cost_pct, 4),
                "cumulative_return": round(r.cumulative_return, 6),
                "sharpe": round(r.sharpe, 4),
                "max_drawdown": round(r.max_drawdown, 6),
                "n_trades": r.n_trades,
            }
            for r in results
        ],
        summary={"strategies": sorted({r.name for r in results})},
    )
    print(f"Saved: {json_path}")


if __name__ == "__main__":
    main()
