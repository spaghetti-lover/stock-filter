# TraderAgent backtest — run playbook

End-to-end procedure for reproducing the slide-17 numbers on Alibaba Qwen
free quota. All experiment outputs are written as JSON envelopes to
`backend/eval/results/` so the Next.js frontend can read them.

## 0. Prerequisites (one-time)

```bash
# DashScope API key in backend/.env
grep DASHSCOPE_API_KEY backend/.env  # must be set

# Postgres up (Layer 1 metrics + discussion store)
make db_start  # or: docker start stock_db
```

## 1. Convert / refresh static experiment JSONs (cheap)

The Monte Carlo, ADF/autocorrelation and baseline backtest scripts each
emit both their original CSV (under `docs/thuyetrinh/`) AND a JSON envelope
(under `backend/eval/results/`). Re-running is OPTIONAL; they were already
serialised from existing CSVs in this work session.

```bash
uv run python3 -B scripts/mc_t25_floor.py             # writes monte_carlo_t25.json
uv run python3 -B scripts/adf_autocorrelation.py      # writes adf_autocorrelation.json
uv run python3 -B scripts/backtest_baselines.py       # writes baselines.json
```

## 2. TraderAgent LLM pilot

Default ladder uses `qwen3-max` (deep) and `qwen3.5-plus-2026-02-15`
(quick). On quota / 429 the runner first retries the same model with
backoff, then walks down the ladder per-tier. All decisions land in
`backend/eval/results/traderagent_decisions.jsonl` (append-only); the run
is resumable — re-launching the same command skips already-done
`(ticker, date, variant)` triples without spending tokens.

Pilot sized for fit + signal under Qwen free quota (≈232K tokens /
decision observed at the strong rung):

```bash
# Pilot (3 tickers × 4 sessions × 2 variants ≈ 24 LLM decisions ≈ 6M tokens):
uv run python3 -B scripts/backtest_traderagent.py \
    --tickers VCB,FPT,HPG \
    --sessions 4 \
    --variants full,no_reflection \
    --workers 3
```

Wall time estimate: ~9 min / decision per lane × 4 sessions × 2 variants
≈ 70-90 min. Will hop ladder rungs on quota exhaustion; lower rungs keep
working as long as their per-model 1M quota lasts.

**To re-launch / continue after an interruption**: just re-run the same
command. It reads the JSONL on startup and skips done triples.

## 3. Offline scoring + ablations

Once decisions are produced, the scorer is fast (no LLM):

```bash
uv run python3 -B backend/eval/score_backtest.py --horizon 5 --cost 0.006
```

This consumes `traderagent_decisions.jsonl` plus realised prices and
writes `backend/eval/results/traderagent_backtest.json`. Within it:

- One row per variant per cost scenario (`0.0` and `0.006` round-trip):
  - `TraderAgent (full)`
  - `TraderAgent (no_reflection)`
  - `TraderAgent (no_t25_floor)` — derived offline by replaying the
    `full` decisions with the T+2.5 settlement floor disabled and
    `m_sl=1.0`; **no LLM cost**.
- Baselines from `baselines.json` (Buy & Hold VN-Index, Equal-weight
  VN30, SMA(10/50)) so the FE sees all six slide-17 rows in one place.
- An `ablations` block with:
  - `t25_floor`: MDD and Sharpe with vs without the floor.
  - `reflection_temporal`: first-half vs second-half mean trade PnL of
    the `full` variant — evidence that the agent improves as Phase B
    reflections accumulate.
- `tokens_used` and `models_used` provenance.

## 4. Where the JSONs land (for the FE)

```
backend/eval/results/
  monte_carlo_t25.json
  adf_autocorrelation.json
  baselines.json
  traderagent_decisions.jsonl   (raw, one row per decision)
  traderagent_backtest.json     (scored, FE-ready)
```

All five files share the same envelope:

```json
{ "experiment": "...", "generated_at": "...", "params": {...},
  "rows": [...], "summary": {...} }
```

except `traderagent_decisions.jsonl` which is one decision per line.

## Documented limitations of the Qwen-hosted run

The runner forces a couple of compromises that should be cited in slide 19
("Limitations"):

1. **Sentiment Analyst (F319/F247 forum posts) excluded** under
   `risk_mode="tradinggroup"` on Qwen, because Alibaba's content
   moderator rejects raw Vietnamese forum text with
   `data_inspection_failed` (HTTP 400). The other three analysts
   (Market, News, Fundamentals) still run.
2. **Look-ahead is closed** for all per-symbol OHLCV + flow fetches
   (via `set_as_of()` and a contextvar-backed clock in
   `backend/infrastructure/market_data/data.py`). The market-wide
   `Insights().flow.*` aggregates are pre-windowed by vendor and cannot
   be clamped — they are NOT used in the backtest path.
3. **Threshold parsing is regex-based**: the quant-risk node emits a
   canonical `THRESHOLDS: T_SL=.. / T_TP=..` line, but the PM may
   re-render the numbers in prose. The parser tries (a) the canonical
   line, (b) standalone `T_SL = X% / T_TP = Y%` tokens, (c) bold
   markdown, (d) quant-risk inline formula, (e) prose with strict
   upside/downside cues.
