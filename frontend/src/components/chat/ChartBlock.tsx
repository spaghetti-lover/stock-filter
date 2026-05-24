"use client";

import { useMemo } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type OHLCV = {
  time: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
};

type IndicatorPayload = {
  kind: "overlay" | "oscillator";
  name: string;
  pane?: "rsi" | "macd";
  series: Record<string, (number | null)[]>;
};

type ChartPayload = {
  symbol: string;
  chart_type: "candlestick" | "line" | "area";
  days: number;
  ohlcv: OHLCV[];
  overlays: IndicatorPayload[];
  oscillators: IndicatorPayload[];
};

const OVERLAY_COLORS = ["#22c55e", "#f59e0b", "#3b82f6", "#ec4899", "#a855f7", "#14b8a6"];
const RSI_COLOR = "#f59e0b";
const MACD_COLOR = "#3b82f6";
const SIGNAL_COLOR = "#ec4899";
const HIST_UP = "#22c55e";
const HIST_DOWN = "#ef4444";
const CANDLE_UP = "#22c55e";
const CANDLE_DOWN = "#ef4444";
const VOLUME_COLOR = "#64748b";

function shortDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function buildRows(payload: ChartPayload) {
  const overlayCols: Record<string, (number | null)[]> = {};
  for (const ov of payload.overlays) {
    for (const [k, arr] of Object.entries(ov.series)) overlayCols[k] = arr;
  }
  return payload.ohlcv.map((bar, i) => {
    const close = bar.close;
    const open = bar.open;
    const isUp = close != null && open != null && close >= open;
    const row: Record<string, number | string | null | [number, number]> = {
      time: bar.time,
      label: shortDate(bar.time),
      open,
      high: bar.high,
      low: bar.low,
      close,
      volume: bar.volume,
      candleColor: isUp ? CANDLE_UP : CANDLE_DOWN,
    };
    if (bar.low != null && bar.high != null) row.wick = [bar.low, bar.high];
    if (open != null && close != null) row.body = [Math.min(open, close), Math.max(open, close)];
    for (const [k, arr] of Object.entries(overlayCols)) row[k] = arr[i] ?? null;
    return row;
  });
}

function buildOscillatorRows(
  payload: ChartPayload,
  pane: "rsi" | "macd",
): Record<string, number | string | null>[] {
  return payload.ohlcv.map((bar, i) => {
    const row: Record<string, number | string | null> = { time: bar.time, label: shortDate(bar.time) };
    for (const osc of payload.oscillators) {
      if (osc.pane !== pane) continue;
      for (const [k, arr] of Object.entries(osc.series)) row[k] = arr[i] ?? null;
    }
    return row;
  });
}

export function ChartBlock({ raw }: { raw: string }) {
  const payload = useMemo<ChartPayload | null>(() => {
    try {
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || !Array.isArray(parsed.ohlcv)) return null;
      return parsed as ChartPayload;
    } catch {
      return null;
    }
  }, [raw]);

  if (!payload) {
    return (
      <pre className="md-pre">
        <code>{raw}</code>
      </pre>
    );
  }

  const rows = useMemo(() => buildRows(payload), [payload]);
  const rsiRows = useMemo(() => buildOscillatorRows(payload, "rsi"), [payload]);
  const macdRows = useMemo(() => buildOscillatorRows(payload, "macd"), [payload]);

  const hasRsi = payload.oscillators.some((o) => o.pane === "rsi");
  const hasMacd = payload.oscillators.some((o) => o.pane === "macd");

  const priceMin = Math.min(
    ...payload.ohlcv.map((b) => b.low ?? Number.POSITIVE_INFINITY),
  );
  const priceMax = Math.max(
    ...payload.ohlcv.map((b) => b.high ?? Number.NEGATIVE_INFINITY),
  );
  const pricePad = (priceMax - priceMin) * 0.05;

  const overlayKeys: string[] = [];
  payload.overlays.forEach((ov) => Object.keys(ov.series).forEach((k) => overlayKeys.push(k)));

  return (
    <div className="my-4 flex flex-col gap-3 border border-[var(--color-line)] bg-[var(--color-surface)] p-3">
      <div className="flex items-center justify-between">
        <span className="mono text-[11px] tracking-[0.18em] uppercase text-[var(--color-text-dim)]">
          chart · {payload.symbol} · {payload.chart_type} · {payload.days}d
        </span>
      </div>

      <div className="h-[320px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {payload.chart_type === "line" ? (
            <LineChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--color-line-2)" strokeDasharray="3 3" />
              <XAxis dataKey="label" stroke="var(--color-text-dim)" fontSize={11} />
              <YAxis
                stroke="var(--color-text-dim)"
                fontSize={11}
                domain={[priceMin - pricePad, priceMax + pricePad]}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={legendStyle} />
              <Line type="monotone" dataKey="close" stroke="#22c55e" dot={false} strokeWidth={1.5} />
              {overlayKeys.map((k, i) => (
                <Line
                  key={k}
                  type="monotone"
                  dataKey={k}
                  stroke={OVERLAY_COLORS[i % OVERLAY_COLORS.length]}
                  dot={false}
                  strokeWidth={1}
                />
              ))}
            </LineChart>
          ) : payload.chart_type === "area" ? (
            <AreaChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--color-line-2)" strokeDasharray="3 3" />
              <XAxis dataKey="label" stroke="var(--color-text-dim)" fontSize={11} />
              <YAxis
                stroke="var(--color-text-dim)"
                fontSize={11}
                domain={[priceMin - pricePad, priceMax + pricePad]}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={legendStyle} />
              <Area type="monotone" dataKey="close" stroke="#22c55e" fill="#22c55e22" />
              {overlayKeys.map((k, i) => (
                <Line
                  key={k}
                  type="monotone"
                  dataKey={k}
                  stroke={OVERLAY_COLORS[i % OVERLAY_COLORS.length]}
                  dot={false}
                  strokeWidth={1}
                />
              ))}
            </AreaChart>
          ) : (
            <ComposedChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--color-line-2)" strokeDasharray="3 3" />
              <XAxis dataKey="label" stroke="var(--color-text-dim)" fontSize={11} />
              <YAxis
                stroke="var(--color-text-dim)"
                fontSize={11}
                domain={[priceMin - pricePad, priceMax + pricePad]}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={legendStyle} />
              <Bar dataKey="wick" shape={<WickShape />} legendType="none" />
              <Bar dataKey="body" shape={<BodyShape />} name="OHLC" />
              {overlayKeys.map((k, i) => (
                <Line
                  key={k}
                  type="monotone"
                  dataKey={k}
                  stroke={OVERLAY_COLORS[i % OVERLAY_COLORS.length]}
                  dot={false}
                  strokeWidth={1}
                />
              ))}
            </ComposedChart>
          )}
        </ResponsiveContainer>
      </div>

      <div className="h-[80px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
            <XAxis dataKey="label" stroke="var(--color-text-dim)" fontSize={10} hide />
            <YAxis stroke="var(--color-text-dim)" fontSize={10} width={40} />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="volume" fill={VOLUME_COLOR} opacity={0.5} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {hasRsi ? (
        <div className="h-[120px] w-full">
          <span className="mono text-[10px] uppercase text-[var(--color-text-dim)]">RSI</span>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rsiRows} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--color-line-2)" strokeDasharray="3 3" />
              <XAxis dataKey="label" stroke="var(--color-text-dim)" fontSize={10} />
              <YAxis stroke="var(--color-text-dim)" fontSize={10} domain={[0, 100]} />
              <Tooltip contentStyle={tooltipStyle} />
              <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" />
              <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" />
              {payload.oscillators
                .filter((o) => o.pane === "rsi")
                .flatMap((o) =>
                  Object.keys(o.series).map((k) => (
                    <Line
                      key={k}
                      type="monotone"
                      dataKey={k}
                      stroke={RSI_COLOR}
                      dot={false}
                      strokeWidth={1.2}
                    />
                  )),
                )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}

      {hasMacd ? (
        <div className="h-[140px] w-full">
          <span className="mono text-[10px] uppercase text-[var(--color-text-dim)]">MACD</span>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={macdRows} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--color-line-2)" strokeDasharray="3 3" />
              <XAxis dataKey="label" stroke="var(--color-text-dim)" fontSize={10} />
              <YAxis stroke="var(--color-text-dim)" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <ReferenceLine y={0} stroke="var(--color-line)" />
              <Bar
                dataKey="histogram"
                shape={(props: { x?: number; y?: number; width?: number; height?: number; payload?: { histogram?: number | null } }) => {
                  const { x = 0, y = 0, width = 0, height = 0, payload: p } = props;
                  const v = p?.histogram;
                  const color = (v ?? 0) >= 0 ? HIST_UP : HIST_DOWN;
                  return <rect x={x} y={y} width={width} height={height} fill={color} opacity={0.6} />;
                }}
              />
              <Line type="monotone" dataKey="MACD" stroke={MACD_COLOR} dot={false} strokeWidth={1.2} />
              <Line type="monotone" dataKey="signal" stroke={SIGNAL_COLOR} dot={false} strokeWidth={1.2} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </div>
  );
}

const tooltipStyle = {
  background: "var(--color-surface)",
  border: "1px solid var(--color-line)",
  fontSize: 11,
};

const legendStyle = { fontSize: 11, color: "var(--color-text-dim)" };

type CandleShapeProps = {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  payload?: {
    open: number | null;
    close: number | null;
    high: number | null;
    low: number | null;
    candleColor?: string;
    wick?: [number, number];
    body?: [number, number];
  };
};

function BodyShape(props: CandleShapeProps) {
  const { x = 0, y = 0, width = 0, height = 0, payload } = props;
  if (!payload || payload.open == null || payload.close == null) return null;
  const color = payload.candleColor ?? CANDLE_UP;
  const minH = Math.max(height, 1);
  return <rect x={x} y={y} width={width} height={minH} fill={color} stroke={color} />;
}

function WickShape(props: CandleShapeProps) {
  const { x = 0, y = 0, width = 0, height = 0, payload } = props;
  if (!payload) return null;
  const color = payload.candleColor ?? CANDLE_UP;
  const cx = x + width / 2;
  return <line x1={cx} x2={cx} y1={y} y2={y + height} stroke={color} strokeWidth={1} />;
}
