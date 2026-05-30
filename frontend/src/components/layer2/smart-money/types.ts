export type DivergenceType = "prop_taking_profit" | "prop_supporting" | null;

export interface SmartMoneyFlowRow {
  date: string;
  foreign_buy_value: number;
  foreign_sell_value: number;
  prop_buy_value: number;
  prop_sell_value: number;
  total_gtgd: number;
  close_price: number;

  foreign_net_pct: number;
  prop_net_pct: number;
  sm_net_pct: number;
  sm_net_pct_uncapped: number;
  dominance_pct: number;
  sm_net_5d: number | null;

  block_deal: boolean;
  divergence_type: DivergenceType;
  signal_label: string;
  signal_color: string;
}

export interface SmartMoneyFlowResponse {
  symbol: string;
  days_requested: number;
  fetched_at: string;
  rows: SmartMoneyFlowRow[];
}

export type Timeframe = 5 | 20 | 60;
