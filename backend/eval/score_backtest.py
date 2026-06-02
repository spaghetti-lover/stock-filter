"""Offline scorer for the TraderAgent backtest — no LLM calls.

Consumes ``backend/eval/results/traderagent_decisions.jsonl`` (produced by
``scripts/backtest_traderagent.py``) plus realised prices, and produces the
six slide-17 rows + ablations in ``traderagent_backtest.json``.

What it computes per LLM variant (``full``, ``no_reflection``):
  * Per-trade replay of every BUY/Overweight decision via
    ``eval.replay.replay_one`` (T+2.5 floor enforced, horizon = N sessions).
  * A portfolio equity curve under the slide-18 position policy
    (equal-weight, 10% per BUY, max 10 concurrent) → CR / Sharpe / MDD,
    under two cost scenarios (0% and 0.6% round-trip).

Derived for free (no extra LLM):
  * ``no_t25`` ablation = re-replay the ``full`` BUY decisions with
    ``enforce_settlement_floor=False`` (and m_sl→1.0 via multiplier_scale).
  * Reflection temporal check = first-half vs second-half mean trade PnL of
    the ``full`` variant (evidence the agent improves as lessons accumulate).

Baselines are pulled from the already-written ``baselines.json`` so the FE
sees all six slide-17 rows in one file.

Usage (from repo root):
    uv run python3 -B backend/eval/score_backtest.py
    uv run python3 -B backend/eval/score_backtest.py --horizon 5 --cost 0.006
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Optional

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from eval.replay import replay_one  # noqa: E402
from eval.results_io import RESULTS_DIR, read_result, write_result  # noqa: E402

DECISIONS_JSONL = RESULTS_DIR / "traderagent_decisions.jsonl"
BUY_RATINGS = {"buy", "overweight"}
TRADING_DAYS = 252
POSITION_FRACTION = 0.10   # 10% of capital per BUY
MAX_CONCURRENT = 10


def load_decisions() -> list[dict]:
    if not DECISIONS_JSONL.exists():
        raise SystemExit(f"No decisions file at {DECISIONS_JSONL}")
    out = []
    for line in DECISIONS_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _is_buy(rating: Optional[str]) -> bool:
    return bool(rating) and rating.strip().lower() in BUY_RATINGS


def _trade_pnls(
    decisions: list[dict],
    horizon: int,
    enforce_floor: bool,
    multiplier_scale: float = 1.0,
) -> list[dict]:
    """Replay every BUY decision; return per-trade records with realised PnL."""
    trades = []
    for d in decisions:
        if not _is_buy(d.get("rating")):
            continue
        sl, tp = d.get("t_sl_pct"), d.get("t_tp_pct")
        if sl is None or tp is None:
            continue
        r = replay_one(
            ticker=d["ticker"],
            entry_date=d["date"],
            t_sl_pct=sl * multiplier_scale,
            t_tp_pct=tp * multiplier_scale,
            horizon_days=horizon,
            enforce_settlement_floor=enforce_floor,
        )
        if r is None:
            continue
        trades.append({
            "ticker": r.ticker,
            "entry_date": r.entry_date,
            "exit_day": r.exit_day,
            "pnl": r.pnl,
            "triggered": r.triggered,
        })
    return trades


def _portfolio_metrics(trades: list[dict], cost_round_trip: float) -> dict[str, Any]:
    """Equity-curve metrics under equal-weight, 10%/BUY, max-10-concurrent.

    Simplification faithful to slide 18: each BUY commits POSITION_FRACTION of
    capital and returns ``pnl`` over its holding window; daily portfolio return
    is the mean of that day's *open* positions' marginal returns. We model each
    trade's return as realised at exit, distributed evenly across its holding
    days, capped at MAX_CONCURRENT simultaneous positions.
    """
    if not trades:
        return {"n_trades": 0, "cumulative_return": 0.0, "sharpe": 0.0,
                "max_drawdown": 0.0, "win_rate": 0.0, "avg_holding_days": 0.0,
                "hit_rate": 0.0}

    # Build a daily timeline keyed by entry_date order.
    # Each trade contributes a per-day return = (net_pnl) / holding_days to each
    # day it is open. Net pnl subtracts round-trip cost.
    from collections import defaultdict
    daily = defaultdict(list)  # date -> list of per-day position returns
    # Order trades by entry date; enforce max concurrent by skipping overflow.
    trades_sorted = sorted(trades, key=lambda t: t["entry_date"])
    for t in trades_sorted:
        hold = max(t["exit_day"], 1)
        net = t["pnl"] - cost_round_trip
        per_day = net / hold
        # Spread across sequential index days from entry.
        for k in range(hold):
            daily[(t["entry_date"], k)].append(per_day)

    # Aggregate: each (entry_date,k) bucket is one "portfolio day"; cap to
    # MAX_CONCURRENT positions per bucket; equal-weight average.
    day_keys = sorted(daily.keys())
    port_returns = []
    for key in day_keys:
        rets = daily[key][:MAX_CONCURRENT]
        # Equal weight: average of open positions' marginal returns, scaled by
        # how much capital is deployed (n/MAX_CONCURRENT * POSITION_FRACTION*10).
        deployed = min(len(rets), MAX_CONCURRENT) / MAX_CONCURRENT
        port_returns.append(statistics.fmean(rets) * deployed)

    # Equity curve
    equity = [1.0]
    for r in port_returns:
        equity.append(equity[-1] * (1.0 + r))
    cr = equity[-1] - 1.0

    if len(port_returns) >= 2:
        mu = statistics.fmean(port_returns)
        sd = statistics.stdev(port_returns)
        sharpe = (mu / sd * math.sqrt(TRADING_DAYS)) if sd > 0 else 0.0
    else:
        sharpe = 0.0

    peak = equity[0]
    mdd = 0.0
    for v in equity:
        peak = max(peak, v)
        mdd = min(mdd, v / peak - 1.0)

    pnls = [t["pnl"] for t in trades]
    return {
        "n_trades": len(trades),
        "cumulative_return": round(cr, 6),
        "sharpe": round(sharpe, 4),
        "max_drawdown": round(mdd, 6),
        "win_rate": round(sum(1 for p in pnls if p > 0) / len(pnls), 4),
        "avg_holding_days": round(statistics.fmean(t["exit_day"] for t in trades), 2),
        "hit_rate": round(
            sum(1 for t in trades if t["triggered"] == "take_profit") / len(trades), 4
        ),
    }


def _reflection_temporal(full_trades: list[dict]) -> dict[str, Any]:
    """First-half vs second-half mean PnL of the full variant (by entry date)."""
    if len(full_trades) < 4:
        return {"available": False, "reason": "too few trades"}
    ts = sorted(full_trades, key=lambda t: t["entry_date"])
    mid = len(ts) // 2
    first = [t["pnl"] for t in ts[:mid]]
    second = [t["pnl"] for t in ts[mid:]]
    return {
        "available": True,
        "first_half_mean_pnl": round(statistics.fmean(first), 6),
        "second_half_mean_pnl": round(statistics.fmean(second), 6),
        "delta": round(statistics.fmean(second) - statistics.fmean(first), 6),
        "n_first": len(first),
        "n_second": len(second),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Offline TraderAgent backtest scorer")
    p.add_argument("--horizon", type=int, default=5, help="Holding horizon (sessions)")
    p.add_argument("--cost", type=float, default=0.006, help="Round-trip cost (0.006=0.6%)")
    args = p.parse_args()

    decisions = load_decisions()
    by_variant: dict[str, list[dict]] = {}
    for d in decisions:
        if "error" in d:
            continue
        by_variant.setdefault(d["variant"], []).append(d)

    print(f"Loaded {len(decisions)} decisions across variants: "
          f"{ {k: len(v) for k, v in by_variant.items()} }", flush=True)

    rows: list[dict[str, Any]] = []

    # Baselines from the already-written JSON (keeps all six rows in one file).
    try:
        baselines = read_result("baselines")["rows"]
        for b in baselines:
            rows.append({
                "strategy": b["strategy"],
                "kind": "baseline",
                "cost_pct": b["cost_pct"],
                "cumulative_return": b["cumulative_return"],
                "sharpe": b["sharpe"],
                "max_drawdown": b["max_drawdown"],
                "n_trades": b.get("n_trades"),
            })
    except Exception as exc:  # noqa: BLE001
        print(f"  (baselines.json not loaded: {exc})", flush=True)

    full_trades_floor: list[dict] = []

    for variant in ("full", "no_reflection"):
        ds = by_variant.get(variant, [])
        if not ds:
            continue
        trades = _trade_pnls(ds, args.horizon, enforce_floor=True)
        if variant == "full":
            full_trades_floor = trades
        for cost_label, cost in (("0.0", 0.0), (f"{args.cost}", args.cost)):
            m = _portfolio_metrics(trades, cost)
            rows.append({
                "strategy": f"TraderAgent ({variant})",
                "kind": "traderagent",
                "variant": variant,
                "cost_pct": round(cost, 4),
                **m,
            })

    # ── no_t25 ablation: re-replay full decisions with floor OFF + m_sl→1.0 ──
    ablations: dict[str, Any] = {}
    full_ds = by_variant.get("full", [])
    if full_ds:
        no_floor_trades = _trade_pnls(
            full_ds, args.horizon, enforce_floor=False, multiplier_scale=1.0
        )
        for cost_label, cost in (("0.0", 0.0), (f"{args.cost}", args.cost)):
            m = _portfolio_metrics(no_floor_trades, cost)
            rows.append({
                "strategy": "TraderAgent (no_t25_floor)",
                "kind": "traderagent",
                "variant": "no_t25",
                "cost_pct": round(cost, 4),
                **m,
            })
        floor_m = _portfolio_metrics(full_trades_floor, 0.0)
        nofloor_m = _portfolio_metrics(no_floor_trades, 0.0)
        ablations["t25_floor"] = {
            "with_floor_mdd": floor_m["max_drawdown"],
            "without_floor_mdd": nofloor_m["max_drawdown"],
            "mdd_delta": round(
                nofloor_m["max_drawdown"] - floor_m["max_drawdown"], 6
            ),
            "with_floor_sharpe": floor_m["sharpe"],
            "without_floor_sharpe": nofloor_m["sharpe"],
        }

    # ── reflection temporal check ──
    ablations["reflection_temporal"] = _reflection_temporal(full_trades_floor)

    # Token / model provenance.
    tok_in = sum(d.get("tokens_in", 0) or 0 for d in decisions if "error" not in d)
    tok_out = sum(d.get("tokens_out", 0) or 0 for d in decisions if "error" not in d)
    models_used = sorted(
        {d["deep_model"] for d in decisions if d.get("deep_model")}
        | {d["quick_model"] for d in decisions if d.get("quick_model")}
    )

    out = write_result(
        "traderagent_backtest",
        experiment="TraderAgent backtest — VN equities (Qwen)",
        params={
            "horizon_days": args.horizon,
            "cost_round_trip": args.cost,
            "position_fraction": POSITION_FRACTION,
            "max_concurrent": MAX_CONCURRENT,
            "variants": sorted(by_variant.keys()),
            "n_decisions": len(decisions),
        },
        rows=rows,
        summary={
            "ablations": ablations,
            "tokens_used": {"in": tok_in, "out": tok_out, "total": tok_in + tok_out},
            "models_used": models_used,
        },
    )
    print(f"\nSaved: {out}", flush=True)
    for r in rows:
        if r.get("kind") == "traderagent":
            print(
                f"  {r['strategy']:<34} cost={r['cost_pct']}  "
                f"CR={r.get('cumulative_return')}  SR={r.get('sharpe')}  "
                f"MDD={r.get('max_drawdown')}  n={r.get('n_trades')}",
                flush=True,
            )
    if ablations.get("t25_floor"):
        print(f"\n  T+2.5 ablation: {ablations['t25_floor']}", flush=True)
    if ablations.get("reflection_temporal", {}).get("available"):
        print(f"  Reflection temporal: {ablations['reflection_temporal']}", flush=True)


if __name__ == "__main__":
    main()
