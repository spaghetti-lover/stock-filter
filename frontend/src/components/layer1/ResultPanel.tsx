"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { Banner } from "@/components/ui/Banner";
import { KPI } from "@/components/ui/KPI";
import { StockTable } from "./StockTable";
import type { FilteredStocksResponse } from "@/lib/types";

export function ResultPanel({ data }: { data: FilteredStocksResponse }) {
  const [showRejected, setShowRejected] = useState(false);
  const regime = data.market_regime;

  return (
    <div className="flex flex-col gap-8">
      {regime ? <RegimeBanner regime={regime} /> : null}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <KPI label="Total scanned" value={data.passed.length + data.rejected.length} />
        <KPI label="Passed" value={data.passed.length} emphasize />
        <KPI label="Filtered out" value={data.rejected.length} />
      </div>

      <section>
        <header className="flex items-end justify-between pb-3">
          <h3 className="display text-[24px] tracking-tight">
            Passed
            <span className="mono ml-3 text-[13px] text-[var(--color-text-dim)]">
              ({data.passed.length})
            </span>
          </h3>
        </header>
        {data.passed.length ? (
          <StockTable stocks={data.passed} />
        ) : (
          <Banner tone="warn" label="empty set">
            No stocks passed all filters.
          </Banner>
        )}
      </section>

      <section>
        <button
          onClick={() => setShowRejected((v) => !v)}
          className="group flex w-full items-center justify-between border-y border-[var(--color-line-2)] py-3 text-left"
        >
          <span className="flex items-baseline gap-3">
            <span className="tag text-[var(--color-text-dim)]">02</span>
            <span className="display text-[22px] tracking-tight">Filtered out</span>
            <span className="mono text-[13px] text-[var(--color-text-dim)]">
              ({data.rejected.length})
            </span>
          </span>
          <motion.span
            animate={{ rotate: showRejected ? 90 : 0 }}
            className="text-[var(--color-text-dim)]"
          >
            ›
          </motion.span>
        </button>
        {showRejected ? (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden pt-4"
          >
            {data.rejected.length ? (
              <StockTable stocks={data.rejected} showReason />
            ) : (
              <Banner tone="info">All scanned stocks passed.</Banner>
            )}
          </motion.div>
        ) : null}
      </section>
    </div>
  );
}

function RegimeBanner({ regime }: { regime: NonNullable<FilteredStocksResponse["market_regime"]> }) {
  const state = regime.state;
  if (state === "downtrend")
    return (
      <Banner tone="danger" label="market regime · downtrend">
        {regime.message || "Market in downtrend — screener suspended."}
      </Banner>
    );
  if (state === "choppy")
    return (
      <Banner tone="warn" label="market regime · choppy">
        {regime.message || "Market caution — VN-Index in choppy range."}
      </Banner>
    );
  if (state === "unknown" && regime.message)
    return (
      <Banner tone="info" label="market regime · unknown">
        {regime.message}
      </Banner>
    );
  return null;
}
