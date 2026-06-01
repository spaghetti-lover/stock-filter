"""CLI entry-point for the TradingGroup replay harness.

Usage (from `backend/` as CWD):

    uv run python3 -B -m eval --horizon 5
    uv run python3 -B -m eval --ablate-multipliers --ablate-horizon
    uv run python3 -B -m eval --recompute --vol-windows 5,10,20,30

The harness loads resolved entries from `TradingMemoryLog`, extracts the
`**Stop Loss**: X%` / `**Take Profit**: Y%` lines that the
TradingGroup-mode Portfolio Manager wrote, and replays them under two
exit policies (baseline = hold-to-horizon, TradingGroup = forced
exit at thresholds with T+2.5 floor).
"""

from __future__ import annotations

import argparse
import re
from typing import Optional

from infrastructure.tradingagents.agents.utils.memory import TradingMemoryLog
from infrastructure.tradingagents.default_config import DEFAULT_CONFIG

from .replay import (
    format_summary,
    replay_baseline,
    replay_batch,
    replay_with_recomputed_thresholds,
)


_SL_RE = re.compile(r"\*\*Stop Loss\*\*:\s*([0-9]+(?:\.[0-9]+)?)%")
_TP_RE = re.compile(r"\*\*Take Profit\*\*:\s*([0-9]+(?:\.[0-9]+)?)%")
_THRESHOLDS_LINE_RE = re.compile(
    r"T_SL\s*=\s*([0-9]+(?:\.[0-9]+)?)%\s*/\s*T_TP\s*=\s*([0-9]+(?:\.[0-9]+)?)%"
)


def _extract_thresholds(decision_text: str) -> tuple[Optional[float], Optional[float]]:
    """Extract `stop_loss_pct` / `take_profit_pct` from PM markdown.

    Tries the schema-rendered lines first (PR2 output) and falls back to
    the `THRESHOLDS: T_SL=X% / T_TP=Y%` line the quant node always
    appends to its commentary.
    """
    sl_m = _SL_RE.search(decision_text)
    tp_m = _TP_RE.search(decision_text)
    if sl_m and tp_m:
        return float(sl_m.group(1)), float(tp_m.group(1))
    thr_m = _THRESHOLDS_LINE_RE.search(decision_text)
    if thr_m:
        return float(thr_m.group(1)), float(thr_m.group(2))
    return None, None


def _load_entries() -> list[dict]:
    log = TradingMemoryLog(DEFAULT_CONFIG)
    out: list[dict] = []
    for e in log.load_entries():
        if e.get("pending"):
            continue
        sl, tp = _extract_thresholds(e.get("decision", ""))
        out.append({
            "ticker": e["ticker"],
            "date": e["date"],
            "rating": e["rating"],
            "stop_loss_pct": sl,
            "take_profit_pct": tp,
            "trading_style": "swing",  # not stored in the log tag; assume default
        })
    return out


def _parse_csv_ints(s: str) -> list[int]:
    return [int(x) for x in s.split(",") if x.strip()]


def _parse_csv_floats(s: str) -> list[float]:
    return [float(x) for x in s.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="TradingGroup replay evaluation")
    parser.add_argument("--horizon", type=int, default=5,
                        help="Holding horizon in trading sessions (default 5)")
    parser.add_argument("--no-floor", action="store_true",
                        help="Disable T+2.5 settlement floor (debug only)")
    parser.add_argument("--ablate-multipliers", action="store_true",
                        help="Sweep multiplier scales 0.8/1.0/1.2")
    parser.add_argument("--ablate-horizon", action="store_true",
                        help="Sweep horizons 5/10/15")
    parser.add_argument("--multiplier-scales", type=str, default="0.8,1.0,1.2")
    parser.add_argument("--horizons", type=str, default="5,10,15")
    parser.add_argument("--recompute", action="store_true",
                        help="Recompute σ + thresholds at each entry date (vol-window ablation)")
    parser.add_argument("--vol-windows", type=str, default="5,10,20,30")
    args = parser.parse_args()

    entries = _load_entries()
    with_thresholds = [e for e in entries if e["stop_loss_pct"] is not None]
    print(f"Loaded {len(entries)} resolved entries "
          f"({len(with_thresholds)} carry quant thresholds).")

    enforce_floor = not args.no_floor

    print("\n=== Baseline (hold-to-horizon, TradingAgents mode) ===")
    base = replay_baseline(entries, horizon_days=args.horizon)
    print(format_summary(f"baseline H={args.horizon}", base))

    print("\n=== TradingGroup (forced exits at thresholds) ===")
    tg = replay_batch(
        with_thresholds,
        horizon_days=args.horizon,
        multiplier_scale=1.0,
        enforce_settlement_floor=enforce_floor,
    )
    print(format_summary(f"tradinggroup H={args.horizon} m×1.0", tg))

    if args.ablate_multipliers:
        print("\n=== Ablation: multiplier scale ===")
        for scale in _parse_csv_floats(args.multiplier_scales):
            s = replay_batch(
                with_thresholds,
                horizon_days=args.horizon,
                multiplier_scale=scale,
                enforce_settlement_floor=enforce_floor,
            )
            print(format_summary(f"  m×{scale:.2f}", s))

    if args.ablate_horizon:
        print("\n=== Ablation: horizon ===")
        for h in _parse_csv_ints(args.horizons):
            b = replay_baseline(entries, horizon_days=h)
            t = replay_batch(
                with_thresholds,
                horizon_days=h,
                multiplier_scale=1.0,
                enforce_settlement_floor=enforce_floor,
            )
            print(format_summary(f"  baseline H={h}", b))
            print(format_summary(f"  tradinggroup H={h}", t))

    if args.recompute:
        print("\n=== Ablation: vol-window (recomputed thresholds, no look-ahead) ===")
        multipliers = DEFAULT_CONFIG["risk_multipliers"]
        for w in _parse_csv_ints(args.vol_windows):
            r = replay_with_recomputed_thresholds(
                entries,
                horizon_days=args.horizon,
                vol_window=w,
                style_multipliers=multipliers,
                enforce_settlement_floor=enforce_floor,
            )
            print(format_summary(f"  window={w} H={args.horizon}", r))


if __name__ == "__main__":
    main()
