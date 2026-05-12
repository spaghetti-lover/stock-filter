"use client";

import { motion } from "motion/react";
import { Pill } from "@/components/ui/Pill";
import { fmtScore } from "@/lib/format";
import type { Layer2Score } from "@/lib/types";
import type { RecomputedScores } from "@/lib/scoring";

type Row = Layer2Score & { _scores?: RecomputedScores };

export function ScoresTable({
  rows,
  selected,
  onSelect,
}: {
  rows: Row[];
  selected: string | null;
  onSelect: (sym: string) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="mono w-full text-[12px] tabular-nums">
        <thead>
          <tr className="border-y border-[var(--color-line-2)] text-left text-[var(--color-text-dim)]">
            <Th>Sym</Th>
            <Th>Exch</Th>
            <Th>BUY</Th>
            <Th align="right">Liquidity</Th>
            <Th align="right">Momentum</Th>
            <Th align="right">Breakout</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const buy = r._scores?.buy ?? r.buy_score;
            const liq = r._scores?.liq ?? r.liquidity_score;
            const mom = r._scores?.mom ?? r.momentum_score;
            const brk = r._scores?.brk ?? r.breakout_score;
            const active = r.symbol === selected;
            return (
              <motion.tr
                key={r.symbol}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: Math.min(i * 0.012, 0.5), duration: 0.25 }}
                onClick={() => onSelect(r.symbol)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelect(r.symbol);
                  }
                }}
                tabIndex={0}
                role="button"
                aria-pressed={active}
                aria-label={`Select ${r.symbol}`}
                className={`data-row cursor-pointer border-b border-[var(--color-line)] outline-none focus-visible:bg-[var(--color-surface)] focus-visible:shadow-[inset_2px_0_0_var(--color-accent)] ${
                  active ? "bg-[var(--color-surface)]" : ""
                }`}
              >
                <Td>
                  <span className={`display text-[15px] tracking-tight ${active ? "text-[var(--color-accent)]" : ""}`}>
                    {r.symbol}
                  </span>
                </Td>
                <Td>
                  <Pill>{r.exchange}</Pill>
                </Td>
                <Td>
                  <BuyBar value={buy} />
                </Td>
                <Td align="right">{fmtScore(liq)}</Td>
                <Td align="right">{fmtScore(mom)}</Td>
                <Td align="right">{fmtScore(brk)}</Td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function BuyBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="flex w-[220px] items-center gap-3">
      <span className="serif-num w-[36px] text-right text-[16px] text-[var(--color-accent)]">{fmtScore(value)}</span>
      <div className="relative h-[2px] flex-1 bg-[var(--color-line-2)]">
        <div
          className="absolute left-0 top-0 h-full bg-[var(--color-accent)]"
          style={{ width: `${pct}%`, boxShadow: "0 0 10px var(--color-accent)" }}
        />
      </div>
    </div>
  );
}

function Th({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <th className={`tag whitespace-nowrap px-3 py-2 font-normal ${align === "right" ? "text-right" : "text-left"}`}>
      {children}
    </th>
  );
}

function Td({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <td className={`whitespace-nowrap px-3 py-2 ${align === "right" ? "text-right" : "text-left"}`}>
      {children}
    </td>
  );
}
