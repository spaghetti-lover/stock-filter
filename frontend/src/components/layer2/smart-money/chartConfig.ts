// Spec colors (§5) — fixed semantic colors, do not override with CSS vars.
export const COLORS = {
  foreignBar: "rgba(55,138,221,0.80)",
  propBar: "rgba(29,158,117,0.75)",
  netLine: "#f0c040",
  dotPositive: "#2ecc71",
  dotNegative: "#e74c3c",
  priceLine: "#888888",
  dominanceArea: "#7F77DD",
  dominanceFill: "rgba(127, 119, 221, 0.13)",
  threshold8: "#aaaaaa",
  threshold25: "#9D97E0",
  zeroLine: "rgba(255,255,255,0.22)",
  divergenceAccent: "#EF9F27",
} as const;

// Spec ranges and thresholds (§3, §10).
export const Y_RANGE_MAIN: [number, number] = [-30, 30];
export const Y_RANGE_DOMINANCE: [number, number] = [0, 40];
export const DOMINANCE_THRESHOLDS = { normal: 8, dominant: 25 } as const;
export const PCT_CAP = 25;
export const BLOCK_DEAL_THRESHOLD = 35;
export const BAR_PERCENTAGE = 0.7;

// Tooltip colors (§6).
export const TOOLTIP_COLORS = {
  foreign: "#378ADD",
  prop: "#1D9E75",
  total: "#f0c040",
  dominance: "#7F77DD",
  divergence: "#EF9F27",
} as const;
