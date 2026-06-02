"""Monte Carlo validation of the T+2.5 stop-loss floor.

For each coefficient m in a grid, we resample observed VN30 daily log-returns
into 10,000 holding paths of length ceil(2.5) = 3 sessions. We count how often
the minimum cumulative log-return crosses -m * sigma_d, where sigma_d is the
realised daily std for that ticker.

If the theoretical floor m >= sqrt(2.5) is correct, the empirical stop-out
rate from pure noise should drop sharply near m ~ 1.58.

Output:
- docs/thuyetrinh/mc_t25_floor.png : plot for slide 12
- docs/thuyetrinh/mc_t25_floor_results.csv : numbers for defense notes

Usage (from project root):
    uv run python3 -B scripts/mc_t25_floor.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from infrastructure.market_data.data import get_trading_history  # noqa: E402

VN30 = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
]

M_GRID = [1.0, 1.2, 1.4, math.sqrt(2.0), math.sqrt(2.5), 1.7, 1.8, 2.0, 2.5]
HOLD_SESSIONS = 3
N_PATHS = 10_000
HISTORY_DAYS = 365
SEED = 42


def fetch_log_returns(symbol: str) -> np.ndarray | None:
    rows = get_trading_history(symbol, days=HISTORY_DAYS)
    if not rows:
        return None
    df = pd.DataFrame(rows).sort_values("time")
    close = df["close"].astype(float).to_numpy()
    if len(close) < 30:
        return None
    return np.diff(np.log(close))


def stop_out_rate(returns: np.ndarray, m: float, rng: np.random.Generator) -> float:
    sigma_d = float(np.std(returns, ddof=1))
    if sigma_d <= 0:
        return float("nan")
    threshold = -m * sigma_d
    samples = rng.choice(returns, size=(N_PATHS, HOLD_SESSIONS), replace=True)
    paths = np.cumsum(samples, axis=1)
    min_per_path = paths.min(axis=1)
    return float((min_per_path < threshold).mean())


def main() -> None:
    rng = np.random.default_rng(SEED)
    per_ticker_returns: dict[str, np.ndarray] = {}
    for sym in VN30:
        r = fetch_log_returns(sym)
        if r is not None:
            per_ticker_returns[sym] = r
        else:
            print(f"  skip {sym}: insufficient history")

    if not per_ticker_returns:
        raise SystemExit("No VN30 tickers loaded — check market_data provider")

    print(f"Loaded {len(per_ticker_returns)} / {len(VN30)} VN30 tickers")

    records: list[dict] = []
    for m in M_GRID:
        rates: list[float] = []
        for sym, r in per_ticker_returns.items():
            rate = stop_out_rate(r, m, rng)
            if not math.isnan(rate):
                rates.append(rate)
        mean_rate = float(np.mean(rates))
        std_rate = float(np.std(rates, ddof=1))
        records.append({"m": m, "mean_stop_out": mean_rate, "std_stop_out": std_rate})
        print(f"  m={m:.3f}  stop_out={mean_rate:.4f} +/- {std_rate:.4f}")

    out_dir = REPO_ROOT / "docs" / "thuyetrinh"
    out_dir.mkdir(parents=True, exist_ok=True)
    df_out = pd.DataFrame(records)
    df_out.to_csv(out_dir / "mc_t25_floor_results.csv", index=False)

    # JSON for the FE — same numbers, structured envelope.
    from eval.results_io import write_result

    floor_val = math.sqrt(2.5)
    floor_row = min(records, key=lambda r: abs(r["m"] - floor_val))
    json_path = write_result(
        "monte_carlo_t25",
        experiment="Monte Carlo — T+2.5 stop-loss floor",
        params={
            "universe": "VN30",
            "n_tickers": len(per_ticker_returns),
            "m_grid": [round(m, 4) for m in M_GRID],
            "hold_sessions": HOLD_SESSIONS,
            "n_paths": N_PATHS,
            "history_days": HISTORY_DAYS,
            "seed": SEED,
            "floor": round(floor_val, 4),
        },
        rows=[
            {
                "m": round(r["m"], 4),
                "mean_stop_out": round(r["mean_stop_out"], 6),
                "std_stop_out": round(r["std_stop_out"], 6),
            }
            for r in records
        ],
        summary={
            "floor_m": round(floor_val, 4),
            "stop_out_at_floor": round(floor_row["mean_stop_out"], 4),
            "stop_out_at_m1": round(
                next(r["mean_stop_out"] for r in records if abs(r["m"] - 1.0) < 1e-9), 4
            ),
        },
    )
    print(f"Saved: {json_path}")

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(
        df_out["m"],
        df_out["mean_stop_out"],
        yerr=df_out["std_stop_out"],
        marker="o",
        capsize=3,
        linewidth=1.5,
    )
    floor = math.sqrt(2.5)
    ax.axvline(floor, color="crimson", linestyle="--", label=f"√2.5 ≈ {floor:.3f}")
    ax.set_xlabel("Stop-loss coefficient $m^{sl}$")
    ax.set_ylabel("Noise-induced stop-out rate (3 sessions)")
    ax.set_title("T+2.5 Floor — Monte Carlo on VN30 (2024)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "mc_t25_floor.png", dpi=150)
    print(f"Saved: {out_dir / 'mc_t25_floor.png'}")
    print(f"Saved: {out_dir / 'mc_t25_floor_results.csv'}")


if __name__ == "__main__":
    main()
