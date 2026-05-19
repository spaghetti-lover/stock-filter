"use client";

import { normalize, type Weights } from "@/lib/scoring";
import { fmtBillion, fmtPct, fmtRatio, fmtScore } from "@/lib/format";
import { Pill } from "@/components/ui/Pill";
import { PillarGauge } from "./PillarGauge";
import type { Layer2Score } from "@/lib/types";
import type { RecomputedScores } from "@/lib/scoring";

interface Props {
  stock: Layer2Score & { _scores?: RecomputedScores };
  weights: Weights;
}

export function BreakdownPanel({ stock, weights }: Props) {
  const bd = stock.breakdown;
  if (!bd) return null;
  const liq = bd.liquidity;
  const mom = bd.momentum;
  const brk = bd.breakout;

  const r = stock._scores ?? {
    buy: stock.buy_score,
    liq: stock.liquidity_score,
    mom: stock.momentum_score,
    brk: stock.breakout_score,
  };

  const nwL = normalize(weights, ["liq_gtgd20", "liq_intraday", "liq_cv"]);
  const nwM = normalize(weights, ["mom_volatility", "mom_ma", "mom_rs", "mom_ad", "mom_tech"]);
  const gateActive = !!brk.gate_active;

  return (
    <div className="border border-[var(--color-line)] bg-[var(--color-surface)]">
      <header className="flex items-center justify-between border-b border-[var(--color-line)] px-6 py-5">
        <div className="flex items-center gap-4">
          <span className="display text-[36px] tracking-tight">{stock.symbol}</span>
          <Pill>{stock.exchange}</Pill>
        </div>
        <div className="flex items-center gap-8">
          <PillarGauge value={r.liq} label="Liquidity" tone="accent" />
          <PillarGauge value={r.mom} label="Momentum" tone="warn" />
          <PillarGauge value={r.brk} label="Breakout" tone={gateActive ? "accent" : "danger"} />
          <div className="ml-2 border-l border-[var(--color-line)] pl-8">
            <div className="tag mb-2">BUY score</div>
            <div className="serif-num text-[56px] leading-none text-[var(--color-accent)]">
              {fmtScore(r.buy)}
            </div>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-px bg-[var(--color-line)] lg:grid-cols-3">
        {/* Liquidity */}
        <Column title="Liquidity" score={r.liq}>
          <Caption>
            GTGD20 ({pct(nwL.liq_gtgd20)}) · Intraday ({pct(nwL.liq_intraday)}) · CV ({pct(nwL.liq_cv)})
          </Caption>
          <Metric label="GTGD20" value={fmtBillion(liq.gtgd20.value)} score={liq.gtgd20.score} />
          <Metric
            label="Intraday ratio"
            value={fmtPct(liq.intraday_ratio.value * 100)}
            score={liq.intraday_ratio.score}
          />
          <Metric label="CV stability" value={fmtPct(liq.cv.value)} score={liq.cv.score} />
        </Column>

        {/* Momentum */}
        <Column title="Momentum" score={r.mom}>
          <Caption>
            Vol ({pct(nwM.mom_volatility)}) · MA ({pct(nwM.mom_ma)}) · RS ({pct(nwM.mom_rs)}) · A/D ({pct(nwM.mom_ad)}) · Tech ({pct(nwM.mom_tech)})
          </Caption>
          <Metric
            label="Composite return"
            value={fmtPct(mom.composite_return.value)}
            score={mom.composite_return.score}
            detail={detailMomReturn(mom.composite_return.detail)}
          />
          <Metric
            label="MA analysis"
            value=""
            score={mom.ma.score}
            detail={detailMomMA(mom.ma.detail)}
          />
          <Metric
            label="RS vs VN-Index"
            value={fmtPct(mom.rs.value)}
            score={mom.rs.score}
            detail={detailMomRS(mom.rs.detail)}
          />
          <Metric label="A/D ratio" value={fmtRatio(mom.ad.value)} score={mom.ad.score} />
          <Metric
            label="Technical"
            value=""
            score={mom.technical.score}
            detail={detailMomTech(mom.technical.detail)}
          />
        </Column>

        {/* Breakout */}
        <Column title="Breakout" score={r.brk} closed={!gateActive}>
          {!gateActive ? (
            <div className="my-2 border border-dashed border-[var(--color-danger)]/40 px-3 py-2 text-[11px] uppercase tracking-[0.16em] text-[var(--color-danger)]">
              gate closed — pillar = 0
            </div>
          ) : null}
          <Metric label="Breakout ratio" value={fmtRatio(brk.breakout_ratio.value)} score={brk.breakout_ratio.score} />
          <Metric label="Volume ratio" value={fmtRatio(brk.volume_ratio.value)} score={brk.volume_ratio.score} />
          <Metric label="Dry-up ratio" value={fmtRatio(brk.dry_up_ratio.value)} score={brk.dry_up_ratio.score} />
          <Metric label="Base quality (narrowing)" value={fmtRatio(brk.narrowing_ratio.value)} score={brk.narrowing_ratio.score} />
          {brk.closing_strength && <Metric label="Closing strength" value={fmtPct(brk.closing_strength.value)} score={brk.closing_strength.score} />}
        </Column>
      </div>
    </div>
  );
}

function Column({
  title,
  score,
  closed,
  children,
}: {
  title: string;
  score: number;
  closed?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-[var(--color-surface)] px-6 py-5">
      <div className="flex items-baseline justify-between pb-3">
        <div className="tag">{title}</div>
        <div className={`serif-num text-[26px] ${closed ? "text-[var(--color-danger)]" : "text-[var(--color-text)]"}`}>
          {fmtScore(score)}
        </div>
      </div>
      <div className="flex flex-col gap-3">{children}</div>
    </div>
  );
}

function Metric({
  label,
  value,
  score,
  detail,
}: {
  label: string;
  value: string;
  score: number;
  detail?: string | null;
}) {
  return (
    <div className="border-t border-dashed border-[var(--color-line)] pt-2">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-[12px] text-[var(--color-text)]">{label}</span>
        <span className="mono text-[12px] tabular-nums text-[var(--color-text)]">{value}</span>
      </div>
      <div className="flex items-baseline justify-between gap-3 pt-0.5">
        <span className="tag">score</span>
        <span className="mono text-[11px] text-[var(--color-accent)]">{fmtScore(score)}</span>
      </div>
      {detail ? <div className="pt-1 text-[10.5px] leading-snug text-[var(--color-text-faint)]">{detail}</div> : null}
    </div>
  );
}

function Caption({ children }: { children: React.ReactNode }) {
  return <div className="-mt-2 pb-2 text-[10.5px] text-[var(--color-text-faint)]">{children}</div>;
}

const pct = (v: number) => `${Math.round(v * 100)}%`;

function num(v: unknown): number {
  return typeof v === "number" ? v : 0;
}
function obj(v: unknown): Record<string, unknown> {
  return v && typeof v === "object" ? (v as Record<string, unknown>) : {};
}

function detailMomReturn(d: unknown): string {
  const o = obj(d);
  return `1D ${fmtPct(num(o.return_1d))} · 5D ${fmtPct(num(o.return_5d))} · 20D ${fmtPct(num(o.return_20d))}`;
}
function detailMomMA(d: unknown): string {
  const o = obj(d);
  const m20 = obj(o.price_vs_ma20);
  const m50 = obj(o.price_vs_ma50);
  const sl = obj(o.slope_pct);
  return `MA20 ${fmtPct(num(m20.value))}→${fmtScore(num(m20.score))} · MA50 ${fmtPct(num(m50.value))}→${fmtScore(num(m50.score))} · slope ${fmtPct(num(sl.value))}→${fmtScore(num(sl.score))}`;
}
function detailMomRS(d: unknown): string {
  const o = obj(d);
  return `3M ${fmtPct(num(o.rs_3m))} · 1M ${fmtPct(num(o.rs_1m))}`;
}
function detailMomTech(d: unknown): string {
  const o = obj(d);
  const rsi = obj(o.rsi);
  const macd = obj(o.macd_histogram_pct);
  return `RSI ${num(rsi.value).toFixed(1)}→${fmtScore(num(rsi.score))} · MACD ${fmtPct(num(macd.value))}→${fmtScore(num(macd.score))}`;
}
