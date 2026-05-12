// Ports of the _fmt_* helpers in frontend/app_pages/layer2.py.

export const fmtBillion = (val: number): string => `${(val / 1e9).toFixed(1)}B`;

export const fmtPct = (val: number): string => `${val.toFixed(2)}%`;

export const fmtRatio = (val: number): string => val.toFixed(3);

export function fmtScore(val: number): string {
  if (Number.isInteger(val)) return String(val);
  return val.toFixed(1);
}

export const fmtPrice = (val: number): string =>
  (val * 1000).toLocaleString("en-US", { maximumFractionDigits: 0 });

export function fmtSeconds(secs: number): string {
  const m = Math.floor(secs / 60);
  const s = Math.max(0, secs - m * 60);
  return `${m}m ${String(s).padStart(2, "0")}s`;
}
