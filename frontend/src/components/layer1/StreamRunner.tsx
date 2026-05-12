"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { openSSE } from "@/lib/sse";
import { API_BASE } from "@/lib/api";
import type { FilteredStocksResponse, Layer1Filters, SSEEvent } from "@/lib/types";

interface Props {
  active: boolean;
  filters: Layer1Filters;
  onResult: (data: FilteredStocksResponse) => void;
  onError: (msg: string) => void;
  onDone: () => void;
}

export function StreamRunner({ active, filters, onResult, onError, onDone }: Props) {
  const [progress, setProgress] = useState<{ processed: number; total: number; symbol: string } | null>(null);
  const handle = useRef<{ close: () => void } | null>(null);

  useEffect(() => {
    if (!active) return;
    setProgress(null);
    const qs = filtersToQuery(filters);
    handle.current = openSSE(
      `${API_BASE}/layer1/stream?${qs.toString()}`,
      (e: SSEEvent) => {
        if (e.type === "progress") {
          setProgress({ processed: e.processed, total: e.total, symbol: e.symbol });
        } else if (e.type === "result") {
          onResult(e.data);
          onDone();
        } else if (e.type === "error") {
          onError(e.detail || "Streaming error");
          onDone();
        }
      },
    );
    return () => handle.current?.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  if (!active) return null;
  const pct = progress && progress.total ? (progress.processed / progress.total) * 100 : 0;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="border border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-4"
    >
      <div className="flex items-baseline justify-between pb-3">
        <div className="flex items-center gap-3">
          <span className="tag text-[var(--color-accent)]">streaming</span>
          <span className="mono text-[12px] text-[var(--color-text-dim)]">
            {progress ? `${progress.processed}/${progress.total}` : "initializing"}
          </span>
        </div>
        <span className="mono text-[12px] text-[var(--color-text)]">
          {progress?.symbol ?? "—"}
        </span>
      </div>
      <div className="thin-progress">
        <span style={{ width: `${pct}%` }} />
      </div>
      <div className="pt-3 text-[12px] text-[var(--color-text-faint)]">
        scanning {filters.exchanges.join(" · ") || "—"} · min GTGD20 ≥ {filters.min_gtgd20}B
      </div>
    </motion.div>
  );
}

function filtersToQuery(f: Layer1Filters): URLSearchParams {
  const qs = new URLSearchParams();
  f.exchanges.forEach((e) => qs.append("exchanges", e));
  qs.set("min_gtgd", String(f.min_gtgd20));
  f.statuses.forEach((s) => qs.append("statuses", s));
  qs.set("min_history", String(f.min_history));
  qs.set("min_price", String(f.min_price));
  qs.set("min_intraday_ratio", String(f.min_intraday_pct / 100));
  qs.set("min_volume", String(f.min_volume_million * 1e6));
  qs.set("use_exchange", String(f.use_exchange));
  qs.set("use_gtgd20", String(f.use_gtgd20));
  qs.set("use_status", String(f.use_status));
  qs.set("use_history", String(f.use_history));
  qs.set("use_price", String(f.use_price));
  qs.set("use_intraday", String(f.use_intraday));
  qs.set("use_volume", String(f.use_volume));
  qs.set("exclude_ceiling_floor", String(f.exclude_ceiling_floor));
  qs.set("cv_cap", String(f.cv_cap));
  qs.set("use_cv", String(f.use_cv));
  qs.set("market_regime_gate", String(f.market_regime_gate));
  return qs;
}
