"use client";

import { useEffect, useMemo, useRef } from "react";
import { Chart as ChartJS } from "chart.js";
import type { ChartOptions, ChartData } from "chart.js";
import { ensureChartJsRegistered } from "@/lib/chartjs-setup";
import { COLORS, Y_RANGE_DOMINANCE, DOMINANCE_THRESHOLDS } from "./chartConfig";
import type { SmartMoneyFlowRow } from "./types";

const HEIGHT = 90;

export function DominancePanel({ rows }: { rows: SmartMoneyFlowRow[] }) {
  ensureChartJsRegistered();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<ChartJS | null>(null);

  const data = useMemo<ChartData<"line">>(() => {
    const labels = rows.map((r) => {
      const [, m, d] = r.date.split("-");
      return `${d}/${m}`;
    });
    const n = rows.length;
    return {
      labels,
      datasets: [
        {
          label: "Dominance%",
          data: rows.map((r) => Math.min(Y_RANGE_DOMINANCE[1], r.dominance_pct)),
          borderColor: COLORS.dominanceArea,
          borderWidth: 2,
          backgroundColor: COLORS.dominanceFill,
          fill: true,
          tension: 0.25,
          pointRadius: 0,
        },
        {
          label: "8%",
          data: new Array(n).fill(DOMINANCE_THRESHOLDS.normal),
          borderColor: COLORS.threshold8,
          borderWidth: 1,
          borderDash: [4, 3],
          pointRadius: 0,
          fill: false,
        },
        {
          label: "25%",
          data: new Array(n).fill(DOMINANCE_THRESHOLDS.dominant),
          borderColor: COLORS.threshold25,
          borderWidth: 1,
          borderDash: [4, 3],
          pointRadius: 0,
          fill: false,
        },
      ],
    };
  }, [rows]);

  const options = useMemo<ChartOptions<"line">>(() => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false },
    },
    scales: {
      x: {
        ticks: {
          color: "rgba(255,255,255,0.4)",
          font: { size: 9 },
          maxTicksLimit: 10,
          autoSkip: true,
        },
        grid: { color: "rgba(255,255,255,0.04)" },
      },
      y: {
        min: Y_RANGE_DOMINANCE[0],
        max: Y_RANGE_DOMINANCE[1],
        ticks: {
          color: "rgba(255,255,255,0.45)",
          font: { size: 9 },
          stepSize: 10,
          callback: (v) => `${v}%`,
        },
        grid: { color: "rgba(255,255,255,0.04)" },
      },
    },
  }), []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    chartRef.current = new ChartJS(canvas, {
      type: "line",
      data,
      options,
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
