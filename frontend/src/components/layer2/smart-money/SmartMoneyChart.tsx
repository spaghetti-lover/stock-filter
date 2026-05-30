"use client";

import { useMemo, useState } from "react";
import { Banner } from "@/components/ui/Banner";
import { useSmartMoneyData } from "./useSmartMoneyData";
import { MainPanel } from "./MainPanel";
import { DominancePanel } from "./DominancePanel";
import type { Timeframe } from "./types";

const TIMEFRAMES: Timeframe[] = [5, 20, 60];

export function SmartMoneyChart({ symbol }: { symbol: string }) {
  const [tf, setTf] = useState<Timeframe>(20);
  const { data, isLoading, error, refetch, isFetching } = useSmartMoneyData(symbol);

  const slicedRows = useMemo(() => {
    if (!data?.rows?.length) return [];
    return data.rows.slice(-tf);
  }, [data, tf]);

  if (isLoading) {
    return <Banner tone="info">Loading smart money flow…</Banner>;
  }
  if (error) {
    return (
      <Banner tone="danger" label="error">
        Failed to load smart money data.{" "}
        <button
          type="button"
          onClick={() => refetch()}
          className="underline underline-offset-2 hover:text-[var(--color-accent)]"
        >
          Retry
        </button>
      </Banner>
    );
  }
  if (!data?.rows?.length) {
    return (
      <Banner tone="info">
        No smart money flow data available for this symbol over the last 60 sessions.
      </Banner>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-end gap-2">
        <span className="tag text-[10px]">Phiên</span>
        <div className="flex border border-[var(--color-line)]">
          {TIMEFRAMES.map((v) => {
            const active = v === tf;
            return (
              <button
                key={v}
                type="button"
                onClick={() => setTf(v)}
                className={`px-3 py-1 text-[11px] tabular-nums transition-colors ${
                  active
                    ? "bg-[var(--color-accent)] text-[var(--color-bg)]"
                    : "bg-transparent text-[var(--color-text-dim)] hover:text-[var(--color-text)]"
                }`}
              >
                {v}
              </button>
            );
          })}
        </div>
        {isFetching ? (
          <span className="text-[10px] text-[var(--color-text-dim)]">refreshing…</span>
        ) : null}
      </div>
      <MainPanel rows={slicedRows} />
      <DominancePanel rows={slicedRows} />
    </div>
  );
}
