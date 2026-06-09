"use client";

import { useState } from "react";
import { FilterSidebar } from "@/components/layer1/FilterSidebar";
import { StreamRunner } from "@/components/layer1/StreamRunner";
import { ResultPanel } from "@/components/layer1/ResultPanel";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Banner } from "@/components/ui/Banner";
import { useStocksStore } from "@/lib/store";
import type { FilteredStocksResponse, Layer1Filters } from "@/lib/types";

const DEFAULTS: Layer1Filters = {
  exchanges: ["HOSE", "HNX"],
  min_gtgd20: 20,
  statuses: ["normal"],
  min_history: 60,
  min_price: 5000,
  min_volume_million: 5,
  min_intraday_pct: 30,
  exclude_ceiling_floor: true,
  cv_cap: 200,
  market_regime_gate: true,
  use_exchange: true,
  use_gtgd20: true,
  use_status: true,
  use_history: true,
  use_price: true,
  use_volume: true,
  use_intraday: true,
  use_cv: true,
};

export default function Layer1Page() {
  const [filters, setFilters] = useState<Layer1Filters>(DEFAULTS);
  const [running, setRunning] = useState(false);
  const [data, setData] = useState<FilteredStocksResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [runKey, setRunKey] = useState(0);
  const setStocks = useStocksStore((s) => s.setStocks);

  const onRun = () => {
    setError(null);
    setData(null);
    setRunning(true);
    setRunKey((k) => k + 1);
  };

  return (
    <div className="flex">
      <FilterSidebar filters={filters} onChange={setFilters} onRun={onRun} running={running} />
      <section className="min-w-0 flex-1">
        <div className="hairline-grid border-b border-[var(--color-line)]">
          <div className="mx-auto max-w-[1240px] px-8 pb-10 pt-12">
            <SectionHeader
              index="LYR/01"
              eyebrow="Hard filters · streaming scan"
              title="Filter the market down to what trades."
              description="Live SSE scan over HOSE / HNX / UPCOM. Configure thresholds in the rail, run the filter, then ship the passing set to the assistant or to Layer 2."
            />
          </div>
        </div>

        <div className="mx-auto max-w-[1240px] px-8 py-10">
          {error ? <Banner tone="danger" label="error">{error}</Banner> : null}
          {running ? (
            <StreamRunner
              key={runKey}
              active={running}
              filters={filters}
              onResult={(d) => {
                setData(d);
                setStocks(d.passed, d.rejected);
              }}
              onError={(m) => setError(m)}
              onDone={() => setRunning(false)}
            />
          ) : null}
          {!running && !data && !error ? (
            <div className="flex flex-col items-start gap-4 border border-dashed border-[var(--color-line-2)] px-6 py-10">
              <span className="tag">awaiting input</span>
              <p className="display text-[28px] tracking-tight">
                Configure the rail. Press <span className="text-[var(--color-accent)]">Run filter</span>.
              </p>
              <p className="max-w-[60ch] text-[13px] text-[var(--color-text-dim)]">
                The streaming endpoint will report progress symbol-by-symbol while the scan runs.
              </p>
            </div>
          ) : null}
          {data ? (
            <div className="pt-8">
              <ResultPanel data={data} />
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}
