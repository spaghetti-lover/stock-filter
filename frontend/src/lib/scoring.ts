// Port of `recompute_scores` and `_normalize` from
// `frontend/app_pages/layer2.py:48-88`. Numerical parity is required.

import type { ScoreBreakdown } from "./types";

export type Weights = Record<string, number>;

export const DEFAULT_WEIGHTS: Weights = {
  liquidity: 0.35,
  momentum: 0.30,
  breakout: 0.35,
  liq_gtgd20: 0.55,
  liq_intraday: 0.30,
  liq_cv: 0.15,
  mom_volatility: 0.30,
  mom_ma: 0.20,
  mom_rs: 0.20,
  mom_flow: 0.25,
  mom_tech: 0.10,
  flow_ad: 0.40,
  flow_smf: 0.60,
  brk_price: 0.30,
  brk_vol: 0.25,
  brk_dryup: 0.20,
  brk_base: 0.15,
  brk_closing_strength: 0.10,
  composite_1d: 0.15,
  composite_5d: 0.50,
  composite_20d: 0.35,
  ma_ma20: 0.35,
  ma_ma50: 0.20,
  ma_alignment: 0.20,
  ma_slope: 0.25,
  rs_3m: 0.35,
  rs_1m: 0.65,
  tech_rsi: 0.50,
  tech_macd: 0.50,
};

export function normalize(weights: Weights, keys: string[]): Weights {
  const total = keys.reduce((acc, k) => acc + (weights[k] ?? 0), 0);
  if (total === 0) {
    return Object.fromEntries(keys.map((k) => [k, 0]));
  }
  return Object.fromEntries(keys.map((k) => [k, (weights[k] ?? 0) / total]));
}

export interface RecomputedScores {
  buy: number;
  liq: number;
  mom: number;
  brk: number;
}

export function recomputeScores(breakdown: ScoreBreakdown, w: Weights): RecomputedScores {
  const liq = breakdown.liquidity;
  const nwL = normalize(w, ["liq_gtgd20", "liq_intraday", "liq_cv"]);
  const liqScore =
    nwL.liq_gtgd20 * liq.gtgd20.score +
    nwL.liq_intraday * liq.intraday_ratio.score +
    nwL.liq_cv * liq.cv.score;

  const mom = breakdown.momentum;
  const nwM = normalize(w, ["mom_volatility", "mom_ma", "mom_rs", "mom_flow", "mom_tech"]);

  // score_flow = min(100, (flow_ad×score_AD + flow_smf×score_SMF) × convergence_mult).
  // The convergence multiplier is computed by the backend (band lookup) and exposed
  // via mom.flow.detail; the frontend re-derives the base if the user changes the
  // internal AD/SMF weights.
  //
  // Backward-compat: older cached payloads (pre-flow migration) carried `ad` and
  // `smart_money` cells instead of `flow`. Synthesize a flow score from those so
  // stale rows still render until they're re-scored.
  const momLegacy = mom as unknown as {
    ad?: { score?: number };
    smart_money?: { score?: number };
  };
  const flowDetail = (mom.flow?.detail ?? {}) as Partial<{
    score_ad: number; score_smf: number; convergence_mult: number;
  }>;
  const flowW = normalize(w, ["flow_ad", "flow_smf"]);
  const adScore  = flowDetail.score_ad  ?? momLegacy.ad?.score          ?? 0;
  const smfScore = flowDetail.score_smf ?? momLegacy.smart_money?.score ?? 40;
  const flowBase = flowW.flow_ad * adScore + flowW.flow_smf * smfScore;
  // No multiplier available in legacy payloads → use 1.0 (no convergence boost/penalty).
  const flowScore = Math.min(100, flowBase * (flowDetail.convergence_mult ?? 1));

  const momScore =
    nwM.mom_volatility * mom.composite_return.score +
    nwM.mom_ma * mom.ma.score +
    nwM.mom_rs * mom.rs.score +
    nwM.mom_flow * flowScore +
    nwM.mom_tech * mom.technical.score;

  const brk = breakdown.breakout;
  let brkScore = 0;
  if (brk.gate_active) {
    const nwB = normalize(w, ["brk_price", "brk_vol", "brk_dryup", "brk_base", "brk_closing_strength"]);
    brkScore =
      nwB.brk_price * brk.breakout_ratio.score +
      nwB.brk_vol * brk.volume_ratio.score +
      nwB.brk_dryup * brk.dry_up_ratio.score +
      nwB.brk_base * brk.narrowing_ratio.score +
      nwB.brk_closing_strength * (brk.closing_strength?.score ?? 50);
  }

  const nwT = normalize(w, ["liquidity", "momentum", "breakout"]);
  const buy = nwT.liquidity * liqScore + nwT.momentum * momScore + nwT.breakout * brkScore;

  return {
    buy: round2(buy),
    liq: round2(liqScore),
    mom: round2(momScore),
    brk: round2(brkScore),
  };
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}
