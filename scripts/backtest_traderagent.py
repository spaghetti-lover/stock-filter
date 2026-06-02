"""TraderAgent backtest runner — slide-17 LLM variants on Alibaba Qwen.

Runs the full TradingAgents graph per (ticker, trade_date) for two variants:
  - ``full``          : reflection ON  (memory log persisted per ticker)
  - ``no_reflection`` : reflection OFF (memory_log_path = None)

The third slide-17 variant (``no_t25``) is NOT run here — it is derived
offline by ``backend/eval/score_backtest.py`` by replaying the ``full``
decisions with the T+2.5 settlement floor disabled.

Key properties:
  * **No look-ahead**: ``set_as_of(trade_date)`` pins every windowed data
    fetch to bars <= trade_date (see market_data/data.py).
  * **Model fallback ladder**: best Qwen deep model first; on a quota/429
    error the graph is rebuilt one rung down. Quick-tier models degrade
    independently.
  * **5-way ticker parallelism**: each ticker is a worker; its dates run
    sequentially so Phase B reflections accumulate in order.
  * **Resumable**: skips any (ticker, date, variant) already in the output
    JSONL, so re-running the same command continues an interrupted run.

Usage (from repo root):

    # smoke (what the agent runs to prove the code):
    uv run python3 -B scripts/backtest_traderagent.py \
        --tickers VCB --sessions 2 --variants full --smoke

    # full pilot (what the USER runs, unattended):
    uv run python3 -B scripts/backtest_traderagent.py \
        --tickers VCB,FPT,HPG,MWG,MBB --sessions 100 \
        --variants full,no_reflection
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

# Load backend/.env so DASHSCOPE_API_KEY reaches the OpenAI-compatible client
# (mirrors main.py, which load_dotenv()s before importing anything).
from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / "backend" / ".env", override=False)

from infrastructure.market_data.data import (  # noqa: E402
    get_vnindex_history,
    set_as_of,
)
from infrastructure.tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
from infrastructure.tradingagents.graph.trading_graph import TradingAgentsGraph  # noqa: E402
from infrastructure.tradingagents.stats_handler import StatsCallbackHandler  # noqa: E402
from infrastructure.tools import McpToolRegistry  # noqa: E402
from db.connection import init_pool, close_pool  # noqa: E402
from eval.results_io import RESULTS_DIR  # noqa: E402

# Threshold regexes — identical to eval/__main__.py:33-37 so parsing matches.
import re  # noqa: E402

# Primary patterns (markdown-structured PM output).
_SL_RE = re.compile(r"\*\*Stop[\s-]?Loss\*\*:\s*([0-9]+(?:\.[0-9]+)?)%")
_TP_RE = re.compile(r"\*\*Take[\s-]?Profit\*\*:\s*([0-9]+(?:\.[0-9]+)?)%")
_THRESHOLDS_LINE_RE = re.compile(
    r"T_SL\s*=\s*([0-9]+(?:\.[0-9]+)?)%\s*/\s*T_TP\s*=\s*([0-9]+(?:\.[0-9]+)?)%"
)
# Standalone T_SL / T_TP — the PM often emits these inline (bold, separate
# lines), e.g. `T_SL = 3.03%` ... `T_TP = 4.74%`.
_TSL_TOKEN_RE = re.compile(r"T_?SL\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*%")
_TTP_TOKEN_RE = re.compile(r"T_?TP\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*%")
# Prose fallbacks — Qwen frequently emits the numbers in narrative form.
# Both patterns require an UNAMBIGUOUS upside-or-downside cue immediately after
# the number, so a stop-loss number can't be misread as a take-profit and vice
# versa. (Earlier draft did mis-grab, e.g. parsing "3.03% downside" as TP.)
_PROSE_SL_RE = re.compile(
    r"([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:downside|stop[\s-]?loss|stop\b|tolerance)",
    re.IGNORECASE,
)
_PROSE_TP_RE = re.compile(
    r"([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:upside|take[\s-]?profit|profit\s+target|gain\s+target)",
    re.IGNORECASE,
)
# Quant-risk module ALWAYS prepends a line "T_SL = X% / T_TP = Y%" before its
# narrative — fall back to scanning the (typically embedded) risk-debate state
# block too if present.
_QUANT_SL_RE = re.compile(
    r"T_SL\s*=\s*m_sl\s*·?\s*σ\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*%"
)
_QUANT_TP_RE = re.compile(
    r"T_TP\s*=\s*m_tp\s*·?\s*σ\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*%"
)

# ── Model fallback ladders (real DashScope codes; chat-capable only) ──
# Validated against the screenshot of the user's free-tier quota page. The
# "thinking" variant and the "mt-flash" translation model are EXCLUDED because:
#   * qwen3-235b-a22b-thinking-2507 rejects tool_choice=required in thinking
#     mode (observed in the smoke run), incompatible with the agent loop.
#   * qwen-mt-flash is a machine-translation model; it rejects assistant/system
#     roles ("Role must be in [user, assistant]") and is not a chat model.
DEEP_LADDER = [
    "qwen3-max",
    "qwen3.5-plus-2026-02-15",
    "qwen-plus-2025-07-28",
    "qwen-plus",
]
# Quick tier: prefer fresh-quota chat models. qwen-plus / qwen3.5-flash were
# drained during smoke development; qwen3.5-plus-2026-02-15 still has quota
# and works as a chat model for analysts/researchers/trader.
QUICK_LADDER = [
    "qwen3.5-plus-2026-02-15",
    "qwen-plus-2025-07-28",
    "qwen-plus",
    "qwen3.5-flash",
]

DEFAULT_TICKERS = ["VCB", "FPT", "HPG", "MWG", "MBB"]
OUT_JSONL = RESULTS_DIR / "traderagent_decisions.jsonl"
MEMORY_DIR = RESULTS_DIR / "memory"

# Strict quota/rate markers only — must not match unrelated failures like the
# LangGraph "recursion limit reached" message (which is NOT a quota problem and
# should not trigger a model downgrade).
_QUOTA_MARKERS = (
    "insufficient_quota", "insufficient quota", "free allocated quota",
    "429", "too many requests", "rate limit", "ratelimit",
    "throttl", "quota exceeded", "out of quota", "arrearage",
    # Alibaba-specific free-tier exhaustion (HTTP 403):
    "allocationquota.freetieronly", "free tier of the model has been exhausted",
    "free tier", "use free tier only",
)

_write_lock = threading.Lock()


def _is_quota_error(exc: Exception) -> bool:
    s = f"{type(exc).__name__}: {exc}".lower()
    return any(m in s for m in _QUOTA_MARKERS)


def _extract_thresholds(text: str) -> tuple[Optional[float], Optional[float]]:
    # Try in order: explicit THRESHOLDS line, standalone T_SL/T_TP tokens,
    # markdown bold, quant-risk inline formula, then prose narratives.
    thr = _THRESHOLDS_LINE_RE.search(text)
    if thr:
        return float(thr.group(1)), float(thr.group(2))
    tsl, ttp = _TSL_TOKEN_RE.search(text), _TTP_TOKEN_RE.search(text)
    if tsl and ttp:
        return float(tsl.group(1)), float(ttp.group(1))
    sl_m, tp_m = _SL_RE.search(text), _TP_RE.search(text)
    if sl_m and tp_m:
        return float(sl_m.group(1)), float(tp_m.group(1))
    qsl, qtp = _QUANT_SL_RE.search(text), _QUANT_TP_RE.search(text)
    if qsl and qtp:
        return float(qsl.group(1)), float(qtp.group(1))
    psl, ptp = _PROSE_SL_RE.search(text), _PROSE_TP_RE.search(text)
    if psl and ptp:
        return float(psl.group(1)), float(ptp.group(1))
    return None, None


def trading_sessions(n: int) -> list[str]:
    """Most recent ``n`` VN trading-session dates (YYYY-MM-DD), oldest first.

    Sourced from VNINDEX history at real wall-clock (as-of not set here).
    """
    rows = get_vnindex_history(max(n * 2 + 30, 120))
    dates = [str(r["time"])[:10] for r in rows]
    dates = sorted(set(dates))
    return dates[-n:]


def already_done() -> set[tuple[str, str, str]]:
    """Set of (ticker, date, variant) triples present in the output JSONL."""
    done: set[tuple[str, str, str]] = set()
    if OUT_JSONL.exists():
        for line in OUT_JSONL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                done.add((d["ticker"], d["date"], d["variant"]))
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def _append_jsonl(record: dict[str, Any]) -> None:
    with _write_lock:
        with open(OUT_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")


def _build_config(variant: str, ticker: str, deep_idx: int, quick_idx: int) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    cfg["llm_provider"] = "qwen"
    cfg["deep_think_llm"] = DEEP_LADDER[deep_idx]
    cfg["quick_think_llm"] = QUICK_LADDER[quick_idx]
    cfg["backend_url"] = None  # openai_client auto-applies the DashScope URL
    cfg["risk_mode"] = "tradinggroup"  # emits parseable THRESHOLDS line
    cfg["trading_style"] = "day"  # exercises the T+2.5 floor (m_sl=1.6)
    cfg["max_recur_limit"] = 150   # headroom for tool-heavy analyst loops
    if variant == "no_reflection":
        cfg["memory_log_path"] = None
    else:
        # Per-ticker memory file so reflections accumulate within a ticker
        # and variants never cross-contaminate.
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        cfg["memory_log_path"] = str(MEMORY_DIR / f"{variant}_{ticker}.md")
    return cfg


async def _propagate_async(graph: TradingAgentsGraph, ticker: str, date: str):
    """Async equivalent of graph.propagate() — MCP tools are async-only.

    Replicates TradingAgentsGraph._run_graph: resolve pending reflections
    (cheap, sync), build initial state with injected past_context, drive the
    compiled graph via ``ainvoke``, persist the decision for the next
    same-ticker run, and return (final_state, rating).
    """
    # Mirror propagate(): the per-instance `ticker` attr is used downstream
    # by _log_state (Path(...) / self.ticker / ...), so set it before invoking.
    graph.ticker = ticker

    # Phase B: resolve prior pending entries for this ticker (sync, cheap).
    graph._resolve_pending_entries(ticker)

    past_context = graph.memory_log.get_past_context(ticker)
    init_state = graph.propagator.create_initial_state(
        ticker, date, past_context=past_context
    )
    args = graph.propagator.get_graph_args()
    final_state = await graph.graph.ainvoke(init_state, **args)

    graph.curr_state = final_state
    graph._log_state(date, final_state)
    graph.memory_log.store_decision(
        ticker=ticker,
        trade_date=date,
        final_trade_decision=final_state["final_trade_decision"],
    )
    return final_state, graph.process_signal(final_state["final_trade_decision"])


async def run_ticker(
    ticker: str,
    dates: list[str],
    variant: str,
    tool_registry: McpToolRegistry,
    done: set[tuple[str, str, str]],
    verbose: bool,
) -> dict[str, Any]:
    """Run one ticker's whole date series sequentially (for one variant).

    A single StatsCallbackHandler accumulates across the ticker; per-decision
    token cost is the delta between consecutive snapshots. The graph is built
    once and reused; it is only rebuilt when the model ladder degrades on a
    quota error. Runs as one asyncio task; 5 tickers run concurrently.
    """
    deep_idx = quick_idx = 0

    def build() -> tuple[TradingAgentsGraph, StatsCallbackHandler]:
        cfg = _build_config(variant, ticker, deep_idx, quick_idx)
        h = StatsCallbackHandler()
        # NOTE: "social" analyst (F319/F247 forum posts) is excluded on Qwen
        # because Alibaba content moderation rejects raw VN forum text with
        # data_inspection_failed (400). Documented as a backtest-scope
        # limitation; the Market / News / Fundamentals analysts still run.
        g = TradingAgentsGraph(
            selected_analysts=["market", "news", "fundamentals"],
            config=cfg,
            debug=False,
            callbacks=[h],  # MUST be constructor arg → threaded into LLMs
            tool_registry=tool_registry,
        )
        return g, h

    graph, handler = build()
    prev_in = prev_out = 0  # last snapshot of the cumulative handler
    n_done = n_run = n_fail = 0
    tokens_in = tokens_out = 0

    for date in dates:
        if (ticker, date, variant) in done:
            n_done += 1
            continue

        # No look-ahead: pin every windowed fetch in this task's context.
        set_as_of(date)

        decision = None
        last_exc = None
        transient_retries = 0  # same-model retries before downgrading on quota
        # Try down the ladder on quota errors.
        while deep_idx < len(DEEP_LADDER) and quick_idx < len(QUICK_LADDER):
            try:
                final_state, rating = await _propagate_async(graph, ticker, date)
                final_dec = final_state.get("final_trade_decision", "") or ""
                t_sl, t_tp = _extract_thresholds(final_dec)
                stats = handler.get_stats()
                d_in = stats.get("tokens_in", 0) - prev_in
                d_out = stats.get("tokens_out", 0) - prev_out
                prev_in, prev_out = stats.get("tokens_in", 0), stats.get("tokens_out", 0)
                decision = {
                    "ticker": ticker,
                    "date": date,
                    "variant": variant,
                    "rating": rating,
                    "t_sl_pct": t_sl,
                    "t_tp_pct": t_tp,
                    "deep_model": DEEP_LADDER[deep_idx],
                    "quick_model": QUICK_LADDER[quick_idx],
                    "tokens_in": d_in,
                    "tokens_out": d_out,
                }
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if _is_quota_error(exc):
                    # First, retry the SAME model a couple times with backoff —
                    # a lone 429 under concurrency shouldn't burn a ladder rung.
                    if transient_retries < 2:
                        transient_retries += 1
                        wait = 5 * transient_retries
                        if verbose:
                            print(
                                f"  [{ticker} {date}] quota/429 — retry "
                                f"{transient_retries}/2 in {wait}s on "
                                f"{QUICK_LADDER[quick_idx]}",
                                flush=True,
                            )
                        await asyncio.sleep(wait)
                        continue
                    # Persistent: degrade one ladder rung, reset retry counter.
                    transient_retries = 0
                    if quick_idx < len(QUICK_LADDER) - 1:
                        quick_idx += 1
                    elif deep_idx < len(DEEP_LADDER) - 1:
                        deep_idx += 1
                    else:
                        break  # exhausted both ladders
                    if verbose:
                        print(
                            f"  [{ticker} {date}] quota → deep={DEEP_LADDER[deep_idx]} "
                            f"quick={QUICK_LADDER[quick_idx]}",
                            flush=True,
                        )
                    graph, handler = build()
                    prev_in = prev_out = 0
                    continue
                # Non-quota error: record and move on (don't kill the lane).
                break

        set_as_of(None)

        if decision is None:
            n_fail += 1
            _append_jsonl({
                "ticker": ticker, "date": date, "variant": variant,
                "rating": None, "t_sl_pct": None, "t_tp_pct": None,
                "error": f"{type(last_exc).__name__}: {last_exc}"[:300]
                if last_exc else "unknown",
                "deep_model": DEEP_LADDER[min(deep_idx, len(DEEP_LADDER) - 1)],
                "quick_model": QUICK_LADDER[min(quick_idx, len(QUICK_LADDER) - 1)],
            })
            if verbose:
                print(f"  [{ticker} {date}] FAILED: {last_exc}", flush=True)
            continue

        _append_jsonl(decision)
        n_run += 1
        tokens_in += decision["tokens_in"]
        tokens_out += decision["tokens_out"]
        if verbose:
            print(
                f"  [{ticker} {date}] {decision['rating']} "
                f"T_SL={decision['t_sl_pct']} T_TP={decision['t_tp_pct']} "
                f"tok={decision['tokens_in']}+{decision['tokens_out']}",
                flush=True,
            )

    return {
        "ticker": ticker, "variant": variant,
        "done_skipped": n_done, "ran": n_run, "failed": n_fail,
        "tokens_in": tokens_in, "tokens_out": tokens_out,
    }


async def main_async(args) -> None:
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    variants = [v.strip() for v in args.variants.split(",") if v.strip()]
    dates = trading_sessions(args.sessions)
    if not dates:
        raise SystemExit("No trading sessions resolved from VNINDEX history.")
    print(
        f"Backtest: {len(tickers)} tickers × {len(dates)} sessions × "
        f"{len(variants)} variants",
        flush=True,
    )
    print(f"  sessions: {dates[0]} … {dates[-1]}", flush=True)
    print(f"  variants: {variants}", flush=True)

    done = already_done()
    if done:
        print(f"  resume: {len(done)} (ticker,date,variant) already done", flush=True)

    await init_pool()  # discussion_by_ticker tool needs the asyncpg pool
    reg = McpToolRegistry()
    await reg.start()
    t0 = time.monotonic()
    summaries: list[dict] = []
    sem = asyncio.Semaphore(max(1, args.workers))

    async def _guarded(t: str, variant: str) -> dict:
        # Run in a fresh context so each ticker-lane's as-of is isolated.
        async with sem:
            return await run_ticker(t, dates, variant, reg, done, args.verbose)

    try:
        # Variants run sequentially (full first so reflections exist); within a
        # variant, tickers run as concurrent asyncio tasks (each task copies
        # the current context, so set_as_of() stays lane-local), each ticker's
        # dates sequential.
        for variant in variants:
            results = await asyncio.gather(
                *(_guarded(t, variant) for t in tickers),
                return_exceptions=True,
            )
            for t, res in zip(tickers, results):
                if isinstance(res, Exception):
                    print(f"  lane {t}/{variant} crashed: {res}", flush=True)
                    traceback.print_exception(type(res), res, res.__traceback__)
                else:
                    summaries.append(res)
    finally:
        await reg.stop()
        await close_pool()

    elapsed = time.monotonic() - t0
    tot_in = sum(s["tokens_in"] for s in summaries)
    tot_out = sum(s["tokens_out"] for s in summaries)
    tot_ran = sum(s["ran"] for s in summaries)
    tot_fail = sum(s["failed"] for s in summaries)
    print("\n=== Backtest run complete ===", flush=True)
    print(f"  ran={tot_ran}  failed={tot_fail}  skipped(resume)="
          f"{sum(s['done_skipped'] for s in summaries)}", flush=True)
    print(f"  tokens: in={tot_in:,} out={tot_out:,} total={tot_in + tot_out:,}", flush=True)
    print(f"  wall time: {elapsed/60:.1f} min", flush=True)
    if tot_ran:
        print(f"  avg tokens/decision: {(tot_in + tot_out)/tot_ran:,.0f}", flush=True)
    print(f"  decisions log: {OUT_JSONL}", flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description="TraderAgent backtest runner (Qwen)")
    p.add_argument("--tickers", default=",".join(DEFAULT_TICKERS))
    p.add_argument("--sessions", type=int, default=100)
    p.add_argument("--variants", default="full,no_reflection")
    p.add_argument("--workers", type=int, default=5)
    p.add_argument("--verbose", action="store_true", default=True)
    p.add_argument("--smoke", action="store_true",
                   help="Smoke mode: tiny run, extra logging.")
    args = p.parse_args()
    if args.smoke:
        args.verbose = True
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
