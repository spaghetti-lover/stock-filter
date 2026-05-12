"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Pill } from "@/components/ui/Pill";
import { fmtScore } from "@/lib/format";
import { BreakdownPanel } from "@/components/layer2/BreakdownPanel";
import type { Layer2Score } from "@/lib/types";
import type { RecomputedScores, Weights } from "@/lib/scoring";

type Row = Layer2Score & { _scores?: RecomputedScores };
type SortKey = "buy" | "liq" | "mom" | "brk";
type SortDir = "desc" | "asc";

const COL_SPAN = 7;

function getVal(r: Row, key: SortKey): number {
  switch (key) {
    case "buy": return r._scores?.buy ?? r.buy_score;
    case "liq": return r._scores?.liq ?? r.liquidity_score;
    case "mom": return r._scores?.mom ?? r.momentum_score;
    case "brk": return r._scores?.brk ?? r.breakout_score;
  }
}

function scoreColor(v: number): string {
  if (v >= 70) return "var(--color-ok)";
  if (v >= 45) return "var(--color-warn)";
  return "var(--color-text-faint)";
}

function MiniBar({ value, color }: { value: number; color: string }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="relative h-[3px] w-[64px] overflow-hidden rounded-full bg-[var(--color-line)]">
      <motion.div
        className="absolute left-0 top-0 h-full rounded-full"
        style={{ background: color, boxShadow: `0 0 8px ${color}` }}
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.5, ease: [0.2, 0.7, 0.2, 1] }}
      />
    </div>
  );
}

function ScoreCell({ value }: { value: number }) {
  const color = scoreColor(value);
  return (
    <div className="flex flex-col items-end gap-1.5">
      <span className="mono tabular-nums text-[13px]" style={{ color }}>
        {fmtScore(value)}
      </span>
      <MiniBar value={value} color={color} />
    </div>
  );
}

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  return (
    <span className="inline-flex flex-col gap-[2px] ml-1.5" style={{ opacity: active ? 1 : 0.35 }}>
      <span style={{ display: "block", width: 0, height: 0, borderLeft: "3.5px solid transparent", borderRight: "3.5px solid transparent", borderBottom: `4px solid ${active && dir === "asc" ? "var(--color-accent)" : "var(--color-text-faint)"}` }} />
      <span style={{ display: "block", width: 0, height: 0, borderLeft: "3.5px solid transparent", borderRight: "3.5px solid transparent", borderTop: `4px solid ${active && dir === "desc" ? "var(--color-accent)" : "var(--color-text-faint)"}` }} />
    </span>
  );
}

function InlineBreakdown({ row, weights }: { row: Row; weights: Weights }) {
  const ref = useRef<HTMLTableRowElement>(null);

  useEffect(() => {
    ref.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, []);

  return (
    <tr ref={ref}>
      <td colSpan={COL_SPAN} className="p-0">
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.25, ease: [0.2, 0.7, 0.2, 1] }}
          style={{ overflow: "hidden" }}
        >
          <div className="border-t border-[var(--color-line)] bg-[var(--color-bg)]">
            <BreakdownPanel stock={row} weights={weights} />
          </div>
        </motion.div>
      </td>
    </tr>
  );
}

export function ScoresTable({
  rows,
  selected,
  onSelect,
  weights,
}: {
  rows: Row[];
  selected: string | null;
  onSelect: (sym: string) => void;
  weights: Weights;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("buy");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const handleSort = useCallback(
    (key: SortKey) => {
      if (key === sortKey) {
        setSortDir((d) => (d === "desc" ? "asc" : "desc"));
      } else {
        setSortKey(key);
        setSortDir("desc");
      }
    },
    [sortKey],
  );

  const sorted = [...rows].sort((a, b) => {
    const av = getVal(a, sortKey);
    const bv = getVal(b, sortKey);
    return sortDir === "desc" ? bv - av : av - bv;
  });

  const cols: { key: SortKey; label: string }[] = [
    { key: "buy", label: "BUY score" },
    { key: "liq", label: "Liquidity" },
    { key: "mom", label: "Momentum" },
    { key: "brk", label: "Breakout" },
  ];

  return (
    <div className="overflow-x-auto rounded-sm border border-[var(--color-line)] bg-[var(--color-surface)]">
      <table className="w-full">
        <thead>
          <tr className="border-b border-[var(--color-line)] bg-[var(--color-surface-2)]">
            <th className="tag px-4 py-3 text-left font-normal text-[10px] tracking-[0.2em] text-[var(--color-text-faint)] w-[40px]">#</th>
            <th className="tag px-4 py-3 text-left font-normal text-[10px] tracking-[0.2em] text-[var(--color-text-faint)]">Symbol</th>
            <th className="tag px-4 py-3 text-left font-normal text-[10px] tracking-[0.2em] text-[var(--color-text-faint)]">Exchange</th>
            {cols.map(({ key, label }) => (
              <th key={key} className="px-4 py-3 text-right">
                <button
                  onClick={() => handleSort(key)}
                  className={`inline-flex items-center gap-1 transition-colors ml-auto ${
                    sortKey === key
                      ? "text-[var(--color-accent)]"
                      : "text-[var(--color-text-faint)] hover:text-[var(--color-text-dim)]"
                  }`}
                >
                  <span className="tag font-normal text-[10px] tracking-[0.2em] uppercase" style={{ color: "inherit" }}>
                    {label}
                  </span>
                  <SortIcon active={sortKey === key} dir={sortDir} />
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <AnimatePresence mode="popLayout" initial={false}>
            {sorted.map((r, i) => {
              const buy = r._scores?.buy ?? r.buy_score;
              const liq = r._scores?.liq ?? r.liquidity_score;
              const mom = r._scores?.mom ?? r.momentum_score;
              const brk = r._scores?.brk ?? r.breakout_score;
              const active = r.symbol === selected;
              const buyColor = scoreColor(buy);

              return (
                <>
                  <motion.tr
                    key={r.symbol}
                    layout
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ delay: Math.min(i * 0.01, 0.4), duration: 0.22 }}
                    onClick={() => onSelect(r.symbol)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(r.symbol); }
                    }}
                    tabIndex={0}
                    role="button"
                    aria-pressed={active}
                    aria-label={`Select ${r.symbol}`}
                    className={`group cursor-pointer border-b border-[var(--color-line)] outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-accent)] focus-visible:ring-inset transition-colors ${
                      active
                        ? "bg-[color-mix(in_srgb,var(--color-accent)_5%,transparent)] shadow-[inset_3px_0_0_var(--color-accent)]"
                        : "hover:bg-[var(--color-surface-2)]"
                    }`}
                  >
                    <td className="px-4 py-3.5">
                      <span className="mono text-[11px] tabular-nums text-[var(--color-text-faint)]">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-2">
                        <span
                          className="display text-[16px] tracking-tight transition-colors"
                          style={{ color: active ? "var(--color-accent)" : "var(--color-text)" }}
                        >
                          {r.symbol}
                        </span>
                        {active && (
                          <span className="mono text-[9px] tracking-[0.15em] text-[var(--color-accent)] opacity-70">▾</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <Pill>{r.exchange}</Pill>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex items-center justify-end gap-3">
                        <div className="relative h-[3px] w-[100px] overflow-hidden rounded-full bg-[var(--color-line)]">
                          <motion.div
                            className="absolute left-0 top-0 h-full rounded-full"
                            style={{ background: buyColor, boxShadow: `0 0 10px ${buyColor}` }}
                            animate={{ width: `${Math.max(0, Math.min(100, buy))}%` }}
                            transition={{ duration: 0.5, ease: [0.2, 0.7, 0.2, 1] }}
                          />
                        </div>
                        <span className="serif-num text-[18px] tabular-nums w-[40px] text-right" style={{ color: buyColor }}>
                          {fmtScore(buy)}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3.5"><ScoreCell value={liq} /></td>
                    <td className="px-4 py-3.5"><ScoreCell value={mom} /></td>
                    <td className="px-4 py-3.5"><ScoreCell value={brk} /></td>
                  </motion.tr>

                  <AnimatePresence>
                    {active && r.breakdown && (
                      <InlineBreakdown key={`bd-${r.symbol}`} row={r} weights={weights} />
                    )}
                  </AnimatePresence>
                </>
              );
            })}
          </AnimatePresence>
        </tbody>
      </table>
    </div>
  );
}
