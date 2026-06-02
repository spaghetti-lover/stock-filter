"""Shared JSON writer for all thesis experiments.

Every experiment (Monte Carlo T+2.5 floor, ADF/autocorrelation, baseline
backtest, TraderAgent backtest) serializes through ``write_result`` so the
Next.js frontend can load them from one folder with one schema.

Canonical envelope::

    {
      "experiment": "<slug>",
      "generated_at": "<ISO-8601 string>",
      "params": { ... run configuration ... },
      "rows":   [ ... per-item records ... ],
      "summary": { ... aggregates / headline numbers ... }
    }

Output lives in ``backend/eval/results/<name>.json``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_result(
    name: str,
    *,
    experiment: str,
    params: dict[str, Any],
    rows: list[Any],
    summary: dict[str, Any],
    generated_at: str | None = None,
) -> Path:
    """Write one experiment result to ``backend/eval/results/<name>.json``.

    Args:
        name: file stem (no extension), e.g. ``"monte_carlo_t25"``.
        experiment: human-readable experiment id stored in the envelope.
        params: run configuration (universe, period, thresholds, ...).
        rows: list of per-item records (JSON-serializable).
        summary: aggregate / headline numbers.
        generated_at: ISO timestamp; defaults to current UTC time.

    Returns:
        The path written.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "experiment": experiment,
        "generated_at": generated_at or _now_iso(),
        "params": params,
        "rows": rows,
        "summary": summary,
    }
    out_path = RESULTS_DIR / f"{name}.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return out_path


def read_result(name: str) -> dict[str, Any]:
    """Load a previously written result envelope. Raises if missing."""
    return json.loads((RESULTS_DIR / f"{name}.json").read_text(encoding="utf-8"))
