"""ADF + autocorrelation analysis on VN30 daily log-returns.

Defense ammunition for the i.i.d. assumption underlying the T+2.5 floor.
We claim daily log-returns are approximately i.i.d.; this script gives
the empirical evidence:

- ADF unit-root test (statsmodels) on each ticker's log-return series.
  ADF rejects unit root → series is stationary → no permanent trend,
  consistent with i.i.d.-zero-mean assumption.
- ACF(1) — first-lag autocorrelation. Close to 0 → no short memory.
- Ljung-Box(10) — joint test for autocorrelation up to lag 10.

Output: console table + CSV in docs/thuyetrinh/.

Usage (from project root):
    uv run python3 -B scripts/adf_autocorrelation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, acf
from statsmodels.stats.diagnostic import acorr_ljungbox

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from infrastructure.market_data.data import get_trading_history  # noqa: E402

VN30 = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
]

HISTORY_DAYS = 500


def log_returns(symbol: str) -> np.ndarray | None:
    rows = get_trading_history(symbol, days=HISTORY_DAYS)
    if not rows:
        return None
    df = pd.DataFrame(rows).sort_values("time")
    close = df["close"].astype(float).to_numpy()
    if len(close) < 60:
        return None
    return np.diff(np.log(close))


def main() -> None:
    records: list[dict] = []
    for sym in VN30:
        r = log_returns(sym)
        if r is None:
            print(f"  skip {sym}: insufficient history")
            continue
        # ADF (unit root test). H0: series has unit root (non-stationary).
        # Small p-value (< 0.05) ⇒ reject H0 ⇒ stationary.
        adf_stat, adf_p, _, _, _, _ = adfuller(r, autolag="AIC")
        # ACF(1): first-lag autocorrelation. ~0 ⇒ no short memory.
        acf_vals = acf(r, nlags=1, fft=False)
        acf1 = float(acf_vals[1])
        # Ljung-Box at lag 10. H0: no autocorrelation up to lag 10.
        lb = acorr_ljungbox(r, lags=[10], return_df=True)
        lb_p = float(lb["lb_pvalue"].iloc[0])
        records.append({
            "ticker": sym,
            "n": len(r),
            "adf_stat": adf_stat,
            "adf_p": adf_p,
            "acf_1": acf1,
            "ljung_box_10_p": lb_p,
        })
        print(
            f"  {sym}: n={len(r)} adf_p={adf_p:.4f} acf1={acf1:+.4f} lb_p={lb_p:.4f}"
        )

    df = pd.DataFrame(records)
    out_dir = REPO_ROOT / "docs" / "thuyetrinh"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "adf_autocorrelation_results.csv", index=False)

    print("\n=== Summary ===")
    print(f"Tickers tested: {len(df)}")
    print(f"ADF rejects unit root (p<0.05): {(df['adf_p'] < 0.05).sum()} / {len(df)}")
    print(f"|ACF(1)| < 0.1: {(df['acf_1'].abs() < 0.1).sum()} / {len(df)}")
    print(f"Ljung-Box(10) fails to reject no-autocorr (p>0.05): "
          f"{(df['ljung_box_10_p'] > 0.05).sum()} / {len(df)}")
    print(f"\nMean ACF(1): {df['acf_1'].mean():+.4f}")
    print(f"Median ADF p-value: {df['adf_p'].median():.4f}")
    print(f"\nSaved: {out_dir / 'adf_autocorrelation_results.csv'}")

    from eval.results_io import write_result

    json_path = write_result(
        "adf_autocorrelation",
        experiment="ADF + autocorrelation — VN30 daily log-returns",
        params={"universe": "VN30", "n_tickers": int(len(df)), "history_days": HISTORY_DAYS},
        rows=[
            {
                "ticker": rec["ticker"],
                "n": int(rec["n"]),
                "adf_stat": round(float(rec["adf_stat"]), 4),
                "adf_p": round(float(rec["adf_p"]), 6),
                "acf_1": round(float(rec["acf_1"]), 6),
                "ljung_box_10_p": round(float(rec["ljung_box_10_p"]), 6),
            }
            for rec in records
        ],
        summary={
            "adf_rejects_unit_root": int((df["adf_p"] < 0.05).sum()),
            "abs_acf1_lt_0_1": int((df["acf_1"].abs() < 0.1).sum()),
            "ljung_box_no_autocorr": int((df["ljung_box_10_p"] > 0.05).sum()),
            "mean_acf1": round(float(df["acf_1"].mean()), 4),
            "median_adf_p": round(float(df["adf_p"].median()), 6),
        },
    )
    print(f"Saved: {json_path}")


if __name__ == "__main__":
    main()
