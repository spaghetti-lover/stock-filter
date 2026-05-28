// Mirrors backend Pydantic models in `backend/application/dto/`.

export type TradingStatus = "normal" | "warning" | "control" | "restriction";
export type Exchange = "HOSE" | "HNX" | "UPCOM";

export interface Stock {
  symbol: string;
  exchange: string;
  status: string;
  current_price: number;
  gtgd20: number;
  history_sessions: number;
  today_value: number;
  avg_intraday_expected: number;
  intraday_ratio: number | null;
  cv: number | null;
  reject_reason?: string | null;
}

export interface MarketRegime {
  state: "uptrend" | "choppy" | "downtrend" | "unknown" | string;
  message?: string | null;
}

export interface FilteredStocksResponse {
  passed: Stock[];
  rejected: Stock[];
  market_regime?: MarketRegime | null;
}

// ── SSE event payloads ────────────────────────────────────────────────
export type SSEProgress = { type: "progress"; processed: number; total: number; symbol: string };
export type SSEResult = { type: "result"; data: FilteredStocksResponse };
export type SSEError = { type: "error"; detail: string };
export type SSEEvent = SSEProgress | SSEResult | SSEError;

// ── Layer 1 filter state (drives query params) ────────────────────────
export interface Layer1Filters {
  exchanges: Exchange[];
  min_gtgd20: number;            // billion VND in UI; converted to raw on submit
  statuses: TradingStatus[];
  min_history: number;
  min_price: number;
  min_volume_million: number;
  min_intraday_pct: number;       // 0..100; submitted as 0..1
  exclude_ceiling_floor: boolean;
  cv_cap: number;
  market_regime_gate: boolean;
  use_exchange: boolean;
  use_gtgd20: boolean;
  use_status: boolean;
  use_history: boolean;
  use_price: boolean;
  use_volume: boolean;
  use_intraday: boolean;
  use_cv: boolean;
}

// ── Layer 2 ───────────────────────────────────────────────────────────
export interface MetricCell {
  value: number;
  score: number;
  detail?: Record<string, unknown>;
}

export interface LiquidityBreakdown {
  gtgd20: MetricCell;
  intraday_ratio: MetricCell;
  cv: MetricCell;
}

export interface FlowDetail {
  score_ad: number;
  ad_value: number;
  score_smf: number;
  foreign_net_pct: number | null;
  prop_net_pct: number | null;
  // 3-component SMF — only populated when vnstock_data >= 3.2.0 active flow is available.
  score_active?: number | null;
  active_net_pct?: number | null;
  active_band?: "LOW" | "MID" | "HIGH" | null;
  convergence_mult: number;
  flow_base: number;
  ad_band: "LOW" | "MID" | "HIGH";
  smf_band: "LOW" | "MID" | "HIGH";
}

export interface MomentumBreakdown {
  composite_return: MetricCell;
  ma: MetricCell;
  rs: MetricCell;
  flow: MetricCell;        // detail: FlowDetail
  technical: MetricCell;
}

export interface BreakoutBreakdown {
  breakout_ratio: MetricCell;
  volume_ratio: MetricCell;
  dry_up_ratio: MetricCell;
  narrowing_ratio: MetricCell;
  closing_strength?: MetricCell;
  gate_active?: boolean;
}

export interface ScoreBreakdown {
  liquidity: LiquidityBreakdown;
  momentum: MomentumBreakdown;
  breakout: BreakoutBreakdown;
  // Full raw inputs + intermediates for cross-checking. Shape is intentionally loose.
  debug?: Record<string, unknown>;
}

export interface Layer2Score {
  symbol: string;
  exchange: string;
  buy_score: number;
  liquidity_score: number;
  momentum_score: number;
  breakout_score: number;
  breakdown?: ScoreBreakdown | null;
}

export interface Layer2Response {
  scores: Layer2Score[];
  scored_at: string | null;
  next_refresh_in: number;
}

// ── Chat ──────────────────────────────────────────────────────────────
export type ChatRole = "user" | "assistant";
export interface ChatMessage {
  role: ChatRole;
  content: string;
}
export type Provider = "claude" | "gemini";
