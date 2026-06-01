# TradingGroup Risk Module — Final Design

**Status:** Grilling complete. All 11 questions resolved. Ready for implementation.

**Branch:** `help` (in main repo at `/home/ducanh/Project/stock-filter/`). No worktree.

---

## 1. Context

User is writing a paper about **TradingGroup**, a variant of the **TradingAgents** multi-agent trading framework. Paper proposes a new Section 3.6 (Risk-Management Module) that replaces the LLM-based three-debator risk team with a deterministic, style-tiered, volatility-scaled hard-intercept rule:

$$T_{SL} = m_s^{sl} \cdot \bar{\sigma}_{d,10}, \quad T_{TP} = m_s^{tp} \cdot \bar{\sigma}_{d,10}$$

where $\bar{\sigma}_{d,10}$ is the unannualized stddev of daily log-returns over the past 10 trading sessions, and $m_s^{sl}$, $m_s^{tp}$ are style-specific multipliers. Forced sell when PnL ≤ $-T_{SL}$, forced profit-take when PnL ≥ $T_{TP}$.

Implementation must be **switchable at runtime** (config flag) between the existing TradingAgents module and the new TradingGroup module.

No paper deadline.

## 2. Codebase facts

**Existing risk module** at `backend/infrastructure/tradingagents/agents/risk_mgmt/`:
- `aggressive_debator.py`, `conservative_debator.py`, `neutral_debator.py` — three LLM personas
- `backend/infrastructure/tradingagents/agents/managers/portfolio_manager.py` — LLM synthesises debate into `PortfolioDecision` (rating + thesis + optional price_target + time_horizon)

**Graph wiring** in `backend/infrastructure/tradingagents/graph/setup.py:90-185`:
- Nodes lines 91-94. Edges `Trader → Aggressive → (Conservative ↔ Neutral cycle) → Portfolio Manager → END` lines 161-187.
- Cycle controlled by `ConditionalLogic.should_continue_risk_analysis` with `max_risk_discuss_rounds` (default 1).

**Trader proposal** (`schemas.py:109-138`) already has `entry_price`, `stop_loss`, `position_sizing` — advisory text only, nothing reads them back to enforce exits.

**State** is stateless across runs. `TradingAgentsGraph.propagate(company_name, trade_date)` runs once per ticker/date. No position store, no PnL tracking. Only `TradingMemoryLog` persists past decisions + outcomes (raw_return + alpha_return at fixed 5-day hold via `_fetch_returns` in `trading_graph.py:209-247`).

**FE already sends trading style.** `SettingsSidebar.tsx` exposes `{"day", "swing"}`; DTO `trading_agent_dto.py:26` accepts `trading_style: Literal["day", "swing"]`; use case `trading_agent_use_case.py:62` writes `cfg["trading_style"] = payload.get("trading_style", "swing")`. Analysts already read it via `get_trading_style_hint()` (`agent_utils.py:8`).

**Database schema (`backend/db/migrations/001.create_stocks.sql`).** `stock_metrics` is a **snapshot table** — symbol PK + today's aggregates only. **No OHLCV history.** σ_10 must come from a live API call.

**vnstock_data Market API** supports `ohlcv(interval='1m'|'5m'|'15m'|'1H'|'1D'|...)` (confirmed in `.venv/.../vnstock_data/ui/domains/market/base.py`). But VN cash equities are **T+2.5**: shares bought today cannot be sold before T+2 afternoon. No same-day round-trip on cash market. Intraday σ is therefore meaningless for the FE's "day" mode — that mode is really short-horizon swing (T+2.5 to ~5 sessions), not intraday.

**Config** at `backend/infrastructure/tradingagents/default_config.py` — natural home for new flags.

## 3. Locked design (all 11 questions resolved)

### Decision 1: Architecture — replacement, not layering
TradingGroup risk node replaces the three LLM debators at graph-build time. One risk module per ticker invocation. Matches paper's framing, gives cleanest A/B comparison.

### Decision 2: Swap point + default
Modify `GraphSetup.setup_graph()` in `backend/infrastructure/tradingagents/graph/setup.py`:
- Replace lines 90-94 (node creation) and 161-185 (edges) with a conditional on `config["risk_mode"]`.
- `risk_mode: "tradingagents"` (default) → current 3-debator chain. Existing behavior unchanged.
- `risk_mode: "tradinggroup"` → new quant risk node, single node between Trader and Portfolio Manager.

### Q4: Math-grounded LLM node (4b)
Python deterministically computes $T_{SL}$, $T_{TP}$. **One** LLM call writes a paragraph anchored to those numbers — narrates the risk, flags edge cases (e.g. abnormally low σ). The paper's contribution is the **rule** (deterministic thresholds), not the elimination of LLM reasoning. Determinism lives in the numbers; LLM only narrates around them.

### Q5: Style from FE (existing wiring)
Read `config["trading_style"]` — already populated by the FE for every `/agent` call. Style set is `{"day", "swing"}` (not the original `{scalper, swing, position}` placeholder).

**Hand-tuned multipliers (starting values; treat as hyperparameters):**

| FE label | $m^{sl}$ | $m^{tp}$ | R:R   | notes                                                                |
| -------- | -------- | -------- | ----- | -------------------------------------------------------------------- |
| day      | 1.5      | 2.5      | 1.67x | T+2.5 floor: must respect $\sqrt{2.5} \approx 1.58$ vol scaling     |
| swing    | 2.5      | 4.0      | 1.60x | wider band for multi-day hold                                       |

**T+2.5 microstructure floor** — stops are not enforceable before T+2.5 on VN cash equities. Document explicitly in the paper as a *contribution*, not a hack: US-data papers do not face this constraint. The replay harness (Q10) must honor it.

### Q6: Vol window — configurable, default 10 (6c)
Add `risk_vol_window: int = 10` to `DEFAULT_CONFIG`. Paper says "10-session lookback by default; sensitivity to window length examined in §4.X." Ablation sweep: $\{5, 10, 20, 30\}$.

### Q7: Data source — live API (7b)
DB schema has no OHLCV history (snapshot only), so 7a not available. Use the existing `infrastructure.market_data.data.get_trading_history(symbol, days=20)` — already imported in `trading_graph.py:34`. ~14 trading sessions of headroom for window=10.

**σ computation:**
```python
history = get_trading_history(symbol, days=20)
closes = [d["close"] for d in history[-(window+1):]]
log_returns = [log(closes[i] / closes[i-1]) for i in range(1, len(closes))]
sigma = stdev(log_returns)  # unannualized daily σ
```

**Edge cases:**
- Symbol with `< window+1` history (newly listed) → fall back to σ = 0.03, LLM flags thresholds as uncalibrated.
- API failure → same fallback.

### Q8: State plumbing — reuse `risk_debate_state` (8a)
Populate:
```python
risk_debate_state = {
    "history": llm_commentary,
    "aggressive_history": "",
    "conservative_history": "",
    "neutral_history": "",
    "latest_speaker": "Quant Risk Module",
    "current_aggressive_response": "",
    "current_conservative_response": "",
    "current_neutral_response": "",
    "count": 1,        # short-circuits should_continue_risk_analysis
    "judge_decision": ""
}
```
No PM prompt changes for state shape. PM sees a single coherent risk narrative.

### Q9: PM schema extension (9b-pct)
Add to `PortfolioDecision` in `backend/infrastructure/tradingagents/agents/schemas.py`:
```python
stop_loss_pct: Optional[float] = Field(
    default=None,
    description="Stop-loss threshold as a percentage (e.g. 4.5 = 4.5%). Populated by the quant risk module in TradingGroup mode; None in TradingAgents mode.",
)
take_profit_pct: Optional[float] = Field(
    default=None,
    description="Take-profit threshold as a percentage. Populated by the quant risk module in TradingGroup mode; None in TradingAgents mode.",
)
```
Extend `render_pm_decision()` to append `**Stop Loss**: 4.5%` / `**Take Profit**: 7.2%` when non-None — mirrors the existing `price_target` / `time_horizon` pattern. Memory log + CLI + report files keep working unchanged.

**Percentages**, not absolute prices: matches the formula's natural output and is portable across tickers in the eval.

### Q10: Replay harness with T+2.5 floor (10b)
The existing `_fetch_returns` measures a fixed 5-day hold — it does NOT simulate forced exits. The paper's claim (hard-intercept thresholds improve outcomes) requires enforcement simulation.

**Harness** (offline, runs against `TradingMemoryLog`, no LLM calls):
```python
def replay_with_thresholds(entries, horizon_days):
    results = []
    for e in entries:
        if e["stop_loss_pct"] is None or e["take_profit_pct"] is None:
            continue
        prices = get_trading_history(e["ticker"], horizon_days + 14)
        from_entry = [p for p in prices if p["time"].date() >= parse(e["date"])]
        if len(from_entry) < 2: continue
        entry_price = from_entry[0]["close"]
        t_sl = e["stop_loss_pct"] / 100
        t_tp = e["take_profit_pct"] / 100
        exit_day = horizon_days
        exit_price = from_entry[min(horizon_days, len(from_entry)-1)]["close"]
        for i, bar in enumerate(from_entry[1:horizon_days+1], 1):
            if i < 3:                       # T+2.5 lock-in: cannot exit
                continue
            pnl = (bar["close"] - entry_price) / entry_price
            if pnl <= -t_sl or pnl >= t_tp:
                exit_day, exit_price = i, bar["close"]
                break
        results.append({
            "ticker": e["ticker"],
            "pnl": (exit_price - entry_price) / entry_price,
            "days": exit_day,
        })
    return results
```

**Baseline:** TradingAgents mode = same entries, hold-to-horizon (no forced exits).

**Ablations:**
- Multipliers ±20% per style
- Horizon $H \in \{5, 10, 15\}$
- Vol window $\in \{5, 10, 20, 30\}$

**Statistics:** t-test or bootstrap on mean PnL difference; report Sharpe-like ratios and hit rate.

### Q11: PR split — 3 PRs
- **PR1 — TradingGroup risk module end-to-end behind flag.** Adds `risk_mode`, `risk_style` (read from existing `trading_style` config), `risk_vol_window`, multipliers to `DEFAULT_CONFIG`. Implements the quant node: σ computation + threshold formula + one LLM commentary call + populates `risk_debate_state.history` with `count=1`. Branches `GraphSetup.setup_graph()` on `risk_mode`. Default `"tradingagents"` — existing behavior unchanged.
- **PR2 — `PortfolioDecision` schema extension.** Adds `stop_loss_pct` / `take_profit_pct` (Optional[float]). Updates PM prompt (one or two lines) to populate them when the quant module provides numbers. Extends `render_pm_decision()`. Memory log writes them through.
- **PR3 — Evaluation harness.** Standalone module under `backend/eval/` (or `backend/scripts/`): replay logic with T+2.5 floor, multiplier/horizon/window ablations, result tables. No production code touched. Reads from `TradingMemoryLog`.

Sequence: PR1 → PR2 → PR3 (PR3 depends on PR2's structured fields).

## 4. Paper framing notes (for §3.6 and §4)

- **T+2.5 microstructure is a contribution.** Stops are not enforceable before T+2.5 on VN cash equities. Acknowledging this is honest and distinguishes the work from US-data papers that ignore the constraint. Formula reinterpretation: "threshold at first legal exit opportunity."
- **Multipliers are hyperparameters.** Sensitivity ablation (±20%) demonstrates robustness.
- **Vol window is a hyperparameter.** σ sweep across $\{5, 10, 20, 30\}$ shows the rule is not fragile.
- **Day-style intraday σ is future work.** VN30 futures (T+0) would be a natural extension; cash-equity day mode currently uses daily σ because the instrument cannot be exited intraday.
- **Formula in §3.6 is exact:** $T_{SL} = m_s^{sl} \cdot \bar{\sigma}_{d,10}$, $T_{TP} = m_s^{tp} \cdot \bar{\sigma}_{d,10}$, with $s \in \{\text{day}, \text{swing}\}$. The window subscript 10 is the default; the paper notes it as a hyperparameter.

## 5. Implementation pointers (for the next agent)

- Config flags go in `backend/infrastructure/tradingagents/default_config.py`.
- Graph branching in `backend/infrastructure/tradingagents/graph/setup.py:setup_graph` lines 90-185.
- New quant risk node module: `backend/infrastructure/tradingagents/agents/risk_mgmt/quant_risk.py` (sibling to the three debators).
- σ utility: small helper, can live in same file or under `infrastructure/market_data/` if reused elsewhere.
- LLM commentary: use existing `provider_kwargs` pattern from `trading_graph.py` (`_get_provider_kwargs`, line 178).
- Schema changes in `backend/infrastructure/tradingagents/agents/schemas.py` (PR2).
- Eval harness in `backend/eval/replay.py` or `backend/scripts/replay_thresholds.py` (PR3).
- Backend runs from `backend/` as CWD. Use `python3`, `uv run`, `uv add`. `make remove_pycache` to clean.
