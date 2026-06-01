"""TradingGroup quant risk node.

Replaces the three LLM debators (aggressive / conservative / neutral) with
a single deterministic node that:

1. Computes σ_d,N — unannualized stddev of the last N daily log-returns —
   from `get_trading_history`.
2. Picks style multipliers from `config["risk_multipliers"]` keyed by
   `config["trading_style"]` (already populated by the FE).
3. Derives T_SL = m_s^sl · σ, T_TP = m_s^tp · σ (as percentages).
4. Calls one LLM to write a paragraph of risk commentary anchored on
   those numbers. The LLM does NOT decide the numbers — it narrates them.
5. Populates `risk_debate_state.history` with the commentary so the
   Portfolio Manager's existing prompt works unchanged. `count` is set
   to 1 to short-circuit `should_continue_risk_analysis`.

The deterministic threshold numbers are appended verbatim to the
commentary in a parseable `T_SL=X% / T_TP=Y%` line so the PM can copy
them into its structured output (`stop_loss_pct` / `take_profit_pct`).
"""

from __future__ import annotations

import logging
import math
from statistics import stdev

from infrastructure.market_data.data import get_trading_history
from infrastructure.tradingagents.runtime_config import get_config

logger = logging.getLogger(__name__)


def _compute_sigma(symbol: str, window: int, fallback: float) -> tuple[float, bool]:
    """Return (sigma_daily, used_fallback).

    Pulls window+1 closes (plus padding for non-trading days) and computes
    stddev of log-returns. Falls back to the configured default if the
    history is too short or the API call fails.
    """
    try:
        # window+1 closes are needed for window log-returns; pad for holidays.
        history = get_trading_history(symbol, days=max(window * 3, window + 14))
    except Exception as exc:
        logger.warning("Quant risk: get_trading_history failed for %s: %s", symbol, exc)
        return fallback, True

    if not history or len(history) < window + 1:
        logger.info(
            "Quant risk: insufficient history for %s (%d rows, need %d), using fallback σ=%.4f",
            symbol, len(history) if history else 0, window + 1, fallback,
        )
        return fallback, True

    closes = [float(row["close"]) for row in history[-(window + 1):]]
    log_returns = []
    for i in range(1, len(closes)):
        prev, curr = closes[i - 1], closes[i]
        if prev <= 0 or curr <= 0:
            continue
        log_returns.append(math.log(curr / prev))

    if len(log_returns) < 2:
        return fallback, True

    return stdev(log_returns), False


def _resolve_multipliers(style: str, config_multipliers: dict) -> tuple[float, float, str]:
    """Return (m_sl, m_tp, resolved_style). Falls back to 'swing' for unknown styles."""
    style_norm = (style or "swing").lower()
    if style_norm not in config_multipliers:
        logger.info("Quant risk: unknown style %r, falling back to 'swing'", style_norm)
        style_norm = "swing"
    m = config_multipliers[style_norm]
    return float(m["sl"]), float(m["tp"]), style_norm


def create_quant_risk_node(llm):
    """Build the TradingGroup quant risk node.

    Reads its hyperparameters from the runtime config singleton so that
    per-request overrides (via `set_config`) flow through without needing
    to re-build the graph.
    """

    def quant_risk_node(state) -> dict:
        config = get_config()
        symbol = state["company_of_interest"]
        window = int(config.get("risk_vol_window", 10))
        fallback = float(config.get("risk_sigma_fallback", 0.03))
        style_in = config.get("trading_style", "swing")
        multipliers = config.get("risk_multipliers", {
            "day":   {"sl": 1.5, "tp": 2.5},
            "swing": {"sl": 2.5, "tp": 4.0},
        })

        sigma, used_fallback = _compute_sigma(symbol, window, fallback)
        m_sl, m_tp, style = _resolve_multipliers(style_in, multipliers)

        t_sl_pct = m_sl * sigma * 100.0
        t_tp_pct = m_tp * sigma * 100.0

        sigma_note = (
            f" (FALLBACK — symbol lacked {window+1} sessions of history)"
            if used_fallback else ""
        )
        microstructure_note = (
            " VN cash-equity T+2.5 settlement means the stop is only "
            "enforceable from the T+2 afternoon session onward; treat the "
            "threshold as the level at which the position will be cut at "
            "first legal exit opportunity."
            if style == "day" else ""
        )

        trader_plan = state.get("trader_investment_plan", "")
        research_plan = state.get("investment_plan", "")

        prompt = f"""You are the Quant Risk Module. The thresholds below were computed
deterministically from market data — DO NOT change the numbers. Your job
is to write a single paragraph (4-6 sentences) of risk commentary that:

- Cites σ_{window}, T_SL, and T_TP verbatim
- Interprets what these thresholds mean for the trader's proposal
- Flags edge cases (e.g. abnormally low σ, the fallback flag, microstructure constraints)
- Ends with the line `THRESHOLDS: T_SL={t_sl_pct:.2f}% / T_TP={t_tp_pct:.2f}%` exactly

Inputs:
- Symbol: {symbol}
- Trading style: {style}
- Vol window: {window} sessions
- σ_{window} (daily log-return stddev, unannualized): {sigma:.4f} = {sigma*100:.2f}%{sigma_note}
- Style multipliers: m_sl={m_sl}, m_tp={m_tp}
- T_SL = m_sl · σ = {t_sl_pct:.2f}%
- T_TP = m_tp · σ = {t_tp_pct:.2f}%{microstructure_note}

Research plan (context): {research_plan[:600]}
Trader proposal (context): {trader_plan[:600]}
"""

        try:
            response = llm.invoke(prompt)
            commentary = response.content
        except Exception as exc:
            logger.warning("Quant risk LLM call failed for %s: %s — using fallback prose", symbol, exc)
            commentary = (
                f"Quant Risk Module: σ_{window} = {sigma*100:.2f}%{sigma_note}. "
                f"Style '{style}' multipliers (m_sl={m_sl}, m_tp={m_tp}) yield "
                f"T_SL = {t_sl_pct:.2f}% and T_TP = {t_tp_pct:.2f}%. "
                f"Exit the position when realized PnL ≤ -T_SL or ≥ T_TP.{microstructure_note}\n"
                f"THRESHOLDS: T_SL={t_sl_pct:.2f}% / T_TP={t_tp_pct:.2f}%"
            )

        tagged = f"Quant Risk Module: {commentary}"

        new_risk_debate_state = {
            "history": tagged,
            "aggressive_history": "",
            "conservative_history": "",
            "neutral_history": "",
            "latest_speaker": "Quant Risk Module",
            "current_aggressive_response": "",
            "current_conservative_response": "",
            "current_neutral_response": "",
            # count=1 short-circuits should_continue_risk_analysis if it ever
            # gets called; the graph wiring routes this node straight to PM
            # but the defensive value keeps any future cycle bounded.
            "count": 1,
            "judge_decision": "",
        }

        return {"risk_debate_state": new_risk_debate_state}

    return quant_risk_node
