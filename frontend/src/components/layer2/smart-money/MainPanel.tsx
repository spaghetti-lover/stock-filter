"use client";

import { useMemo, useRef, useEffect } from "react";
import { Chart as ChartJS } from "chart.js";
import type { ChartOptions, ChartData } from "chart.js";
import { ensureChartJsRegistered } from "@/lib/chartjs-setup";
import { COLORS, Y_RANGE_MAIN, BAR_PERCENTAGE } from "./chartConfig";
import { makeExternalTooltip } from "./ExternalTooltip";
import type { SmartMoneyFlowRow } from "./types";

const HEIGHT = 260;

export function MainPanel({ rows }: { rows: SmartMoneyFlowRow[] }) {
  ensureChartJsRegistered();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<ChartJS | null>(null);

  const data = useMemo<ChartData<"bar" | "line">>(() => {
    const labels = rows.map((r) => {
      const [, m, d] = r.date.split("-");
      return `${d}/${m}`;
    });
    const dotColors = rows.map((r) => (r.sm_net_pct >= 0 ? COLORS.dotPositive : COLORS.dotNegative));
    return {
      labels,
      datasets: [
        {
          type: "bar" as const,
          label: "Foreign net%",
          data: rows.map((r) => Math.max(-25, Math.min(25, r.foreign_net_pct))),
          backgroundColor: COLORS.foreignBar,
          stack: "sm",
          yAxisID: "yPct",
          barPercentage: BAR_PERCENTAGE,
          categoryPercentage: 0.9,
        },
        {
          type: "bar" as const,
          label: "Prop net%",
          data: rows.map((r) => Math.max(-25, Math.min(25, r.prop_net_pct))),
          backgroundColor: COLORS.propBar,
          stack: "sm",
          yAxisID: "yPct",
          barPercentage: BAR_PERCENTAGE,
          categoryPercentage: 0.9,
        },
        {
          type: "line" as const,
          label: "Net tổng",
          data: rows.map((r) => r.sm_net_pct),
          borderColor: COLORS.netLine,
          borderWidth: 2.5,
          tension: 0.3,
          pointRadius: 4,
          pointHoverRadius: 5,
          pointBackgroundColor: dotColors,
          pointBorderColor: dotColors,
          yAxisID: "yPct",
        },
        {
          type: "line" as const,
          label: "Close",
          data: rows.map((r) => r.close_price),
          borderColor: COLORS.priceLine,
          borderWidth: 1.8,
          borderDash: [5, 3],
          pointRadius: 0,
          tension: 0.2,
          yAxisID: "yPrice",
        },
      ],
    };
  }, [rows]);

  const options = useMemo<ChartOptions<"bar" | "line">>(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        enabled: false,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        external: makeExternalTooltip(rows) as any,
      },
    },
    scales: {
      x: {
        stacked: true,
        ticks: {
          color: "rgba(255,255,255,0.55)",
          font: { size: 10 },
          maxTicksLimit: 10,
          autoSkip: true,
        },
        grid: { color: "rgba(255,255,255,0.05)" },
      },
      yPct: {
        type: "linear",
        position: "left",
        stacked: true,
        min: Y_RANGE_MAIN[0],
        max: Y_RANGE_MAIN[1],
        ticks: {
          color: "rgba(255,255,255,0.55)",
          font: { size: 10 },
          callback: (v) => `${v}%`,
        },
        grid: {
          color: (ctx) =>
            ctx.tick.value === 0 ? COLORS.zeroLine : "rgba(255,255,255,0.05)",
          lineWidth: (ctx) => (ctx.tick.value === 0 ? 1.2 : 1),
        },
      },
      yPrice: {
        type: "linear",
        position: "right",
        ticks: { color: "rgba(255,255,255,0.4)", font: { size: 9 } },
        grid: { display: false },
      },
    },
  }), [rows]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    chartRef.current = new ChartJS(canvas, {
      type: "bar",
      data: data as ChartData<"bar">,
      options: options as ChartOptions<"bar">,
    });
    return () => {
      chartRef.current?.destroy();
      chartRef.current = null;
    };
  }, [data, options]);

  return (
    <div style={{ position: "relative", height: HEIGHT, width: "100%" }}>
      <canvas ref={canvasRef} />
    </div>
  );
}
