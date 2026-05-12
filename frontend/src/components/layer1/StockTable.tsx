"use client";

import { motion } from "motion/react";
import { Pill } from "@/components/ui/Pill";
import { fmtPrice } from "@/lib/format";
import type { Stock } from "@/lib/types";

interface Props {
  stocks: Stock[];
  showReason?: boolean;
}

export function StockTable({ stocks, showReason = false }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="mono w-full text-[13px] tabular-nums">
        <thead>
          <tr className="border-y border-[var(--color-line-2)] text-left text-[var(--color-text-dim)]">
            <Th>Sym</Th>
            <Th>Exch</Th>
            <Th>Status</Th>
            <Th align="right">Price</Th>
            <Th align="right">GTGD20</Th>
            <Th align="right">Hist</Th>
            <Th align="right">Today</Th>
            <Th align="right">Expected</Th>
            <Th align="right">Intra%</Th>
            <Th align="right">CV%</Th>
            {showReason ? <Th>Rejected</Th> : null}
          </tr>
        </thead>
        <tbody>
          {stocks.map((s, i) => (
            <motion.tr
              key={s.symbol}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(i * 0.012, 0.4), duration: 0.25 }}
              className="data-row border-b border-[var(--color-line)]"
            >
              <Td>
                <span className="display text-[16px] text-[var(--color-text)] tracking-tight">{s.symbol}</span>
              </Td>
              <Td>
                <Pill>{s.exchange}</Pill>
              </Td>
              <Td>
                <StatusPill status={s.status} />
              </Td>
              <Td align="right">{fmtPrice(s.current_price)}</Td>
              <Td align="right">{(s.gtgd20 / 1e9).toFixed(1)}B</Td>
              <Td align="right">{s.history_sessions}</Td>
              <Td align="right">{(s.today_value / 1e9).toFixed(2)}B</Td>
              <Td align="right">{(s.avg_intraday_expected / 1e9).toFixed(2)}B</Td>
              <Td align="right">
                {s.intraday_ratio != null ? `${Math.round(s.intraday_ratio * 100)}%` : "—"}
              </Td>
              <Td align="right">{s.cv != null ? s.cv.toFixed(0) : "—"}</Td>
              {showReason ? (
                <Td>
                  <span className="text-[var(--color-danger)]">{s.reject_reason ?? ""}</span>
                </Td>
              ) : null}
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <th className={`tag whitespace-nowrap px-3 py-2.5 font-normal ${align === "right" ? "text-right" : "text-left"}`}>
      {children}
    </th>
  );
}

function Td({ children, align = "left" }: { children: React.ReactNode; align?: "left" | "right" }) {
  return (
    <td className={`whitespace-nowrap px-3 py-2.5 ${align === "right" ? "text-right" : "text-left"}`}>
      {children}
    </td>
  );
}

function StatusPill({ status }: { status: string }) {
  const tone =
    status === "normal" ? "ok" : status === "warning" ? "warn" : status === "control" || status === "restriction" ? "danger" : "neutral";
  return <Pill tone={tone}>{status}</Pill>;
}
