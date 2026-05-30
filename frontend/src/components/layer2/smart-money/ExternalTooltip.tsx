import type { TooltipModel } from "chart.js";
import type { SmartMoneyFlowRow } from "./types";
import { TOOLTIP_COLORS } from "./chartConfig";

const TOOLTIP_ID = "smart-money-tooltip";

function getOrCreateEl(chartCanvas: HTMLCanvasElement): HTMLDivElement {
  const parent = chartCanvas.parentNode as HTMLElement | null;
  if (!parent) throw new Error("chart canvas has no parent");
  let el = parent.querySelector<HTMLDivElement>(`#${TOOLTIP_ID}`);
  if (!el) {
    el = document.createElement("div");
    el.id = TOOLTIP_ID;
    el.style.position = "absolute";
    el.style.pointerEvents = "none";
    el.style.transition = "opacity 0.1s";
    el.style.zIndex = "20";
    parent.appendChild(el);
  }
  return el;
}

function fmtPct(v: number): string {
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(1)}%`;
}

function fmtPrice(v: number): string {
  // close is in VND × 1000; multiply for display in VND
  return Math.round(v * 1000).toLocaleString("en-US") + " đ";
}

function fmtDate(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function divergenceCopy(t: SmartMoneyFlowRow["divergence_type"]): string | null {
  if (t === "prop_taking_profit") return "⚡ Phân kỳ: Prop đang chốt lời";
  if (t === "prop_supporting") return "⚡ Phân kỳ: Prop đang đỡ giá";
  return null;
}

function rowHtml(label: string, value: string, color: string, bold = false): string {
  const weight = bold ? "600" : "400";
  return `
    <div style="display:flex;justify-content:space-between;gap:14px;font-size:11px;line-height:1.5;">
      <span style="color:var(--color-text-dim);">${label}</span>
      <span style="color:${color};font-weight:${weight};font-variant-numeric:tabular-nums;">${value}</span>
    </div>
  `;
}

export function makeExternalTooltip(rows: SmartMoneyFlowRow[]) {
  return function externalTooltip(ctx: { chart: { canvas: HTMLCanvasElement }; tooltip: TooltipModel<"bar" | "line"> }) {
    const { chart, tooltip } = ctx;
    const el = getOrCreateEl(chart.canvas);

    if (tooltip.opacity === 0) {
      el.style.opacity = "0";
      return;
    }

    const idx = tooltip.dataPoints?.[0]?.dataIndex;
    if (idx == null || idx < 0 || idx >= rows.length) {
      el.style.opacity = "0";
      return;
    }
    const r = rows[idx];

    const capNote = Math.abs(r.sm_net_pct_uncapped) > Math.abs(r.sm_net_pct)
      ? ` <span style="color:var(--color-text-dim);font-size:9.5px;">(thực tế ${fmtPct(r.sm_net_pct_uncapped)})</span>`
      : "";

    const divergenceLine = divergenceCopy(r.divergence_type);

    el.innerHTML = `
      <div style="
        background: var(--color-surface);
        border: 1px solid var(--color-line);
        padding: 8px 10px;
        min-width: 220px;
        font-family: inherit;
        box-shadow: 0 4px 16px rgba(0,0,0,0.35);
      ">
        <div style="font-size:10px;color:var(--color-text-dim);letter-spacing:0.06em;text-transform:uppercase;margin-bottom:4px;">
          ${fmtDate(r.date)}${r.block_deal ? ` <span style="color:${TOOLTIP_COLORS.divergence};">⚡</span>` : ""}
        </div>
        ${rowHtml("Foreign net", fmtPct(r.foreign_net_pct), TOOLTIP_COLORS.foreign)}
        ${rowHtml("Prop net", fmtPct(r.prop_net_pct), TOOLTIP_COLORS.prop)}
        ${rowHtml("Tổng net", `${fmtPct(r.sm_net_pct)}${capNote}`, TOOLTIP_COLORS.total, true)}
        ${rowHtml("Giá đóng cửa", fmtPrice(r.close_price), "var(--color-text)")}
        ${rowHtml("Dominance", `${r.dominance_pct.toFixed(1)}%`, TOOLTIP_COLORS.dominance)}
        ${rowHtml("Signal", r.signal_label, r.signal_color)}
        ${divergenceLine ? `<div style="margin-top:4px;font-size:11px;color:${TOOLTIP_COLORS.divergence};">${divergenceLine}</div>` : ""}
      </div>
    `;

    const { offsetLeft, offsetTop } = chart.canvas;
    el.style.opacity = "1";
    el.style.left = `${offsetLeft + tooltip.caretX + 8}px`;
    el.style.top = `${offsetTop + tooltip.caretY - 4}px`;
  };
}
