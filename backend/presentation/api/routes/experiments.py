"""Serve thesis experiment results as JSON.

Reads canonical result envelopes from ``backend/eval/results/`` so the FE can
demo Monte Carlo / ADF / baseline / TraderAgent backtest numbers without
re-running anything. Files are produced by the scripts in ``scripts/`` and by
``backend/eval/score_backtest.py``.

Endpoints
---------
``GET /experiments`` — list available result file stems.
``GET /experiments/{name}`` — return one envelope.
``GET /experiments/decisions`` — raw TraderAgent decisions (JSONL lines).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException

from eval.results_io import RESULTS_DIR, read_result

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("")
async def list_experiments() -> dict:
    """List names of every result envelope in the results directory."""
    if not RESULTS_DIR.exists():
        return {"available": []}
    names = sorted(p.stem for p in RESULTS_DIR.glob("*.json"))
    return {"available": names}


@router.get("/decisions")
async def get_decisions() -> dict:
    """Return raw TraderAgent decisions (one per line in the JSONL)."""
    path = RESULTS_DIR / "traderagent_decisions.jsonl"
    if not path.exists():
        return {"rows": [], "count": 0}
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"rows": rows, "count": len(rows)}


@router.get("/{name}")
async def get_experiment(name: str) -> dict:
    """Return one experiment envelope by stem (e.g. ``monte_carlo_t25``)."""
    try:
        return read_result(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"no result named {name!r}")
