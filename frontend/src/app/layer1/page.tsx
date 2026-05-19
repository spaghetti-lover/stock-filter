"use client";

import { useEffect, useState } from "react";
import { FilterSidebar } from "@/components/layer1/FilterSidebar";
import { StreamRunner } from "@/components/layer1/StreamRunner";
import { ResultPanel } from "@/components/layer1/ResultPanel";
import { StockTable } from "@/components/layer1/StockTable";
import { AIFilterStrip } from "@/components/layer1/AIFilterStrip";
import { MatchCountCard } from "@/components/layer1/MatchCountCard";
import { ResultTabs } from "@/components/layer1/ResultTabs";
import { CopilotPane } from "@/components/layer1/copilot/CopilotPane";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Banner } from "@/components/ui/Banner";
import { useCopilotStore, useStocksStore } from "@/lib/store";
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

type Mode = "rule" | "ai";

export default function Layer1Page() {
  const [mode, setMode] = useState<Mode>("rule");

  return (
    <div className="flex">
      {mode === "rule" ? <RuleMode setMode={setMode} /> : <AIMode setMode={setMode} />}
    </div>
  );
}

function ModeTabs({ mode, setMode }: { mode: Mode; setMode: (m: Mode) => void }) {
  return (
    <div className="inline-flex border border-[var(--color-line-2)] bg-[var(--color-surface)]">
      <ModeButton active={mode === "rule"} onClick={() => setMode("rule")} label="Rule-based" />
      <ModeButton active={mode === "ai"} onClick={() => setMode("ai")} label="AI Filter" />
    </div>
  );
}

function ModeButton({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`mono px-4 py-2 text-[11px] tracking-[0.18em] uppercase transition-colors ${
        active
          ? "bg-[var(--color-accent)] text-black"
          : "text-[var(--color-text-dim)] hover:text-[var(--color-text)]"
      }`}
    >
      {label}
    </button>
  );
}

// ── Rule mode (preserved as before) ────────────────────────────────────
function RuleMode({ setMode }: { setMode: (m: Mode) => void }) {
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
    <>
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
            <div className="mt-6">
              <ModeTabs mode="rule" setMode={setMode} />
            </div>
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
          {!running && !data && !error ? <EmptyState mode="rule" /> : null}
          {data ? (
            <div className="pt-8">
              <ResultPanel data={data} />
            </div>
          ) : null}
        </div>
      </section>
    </>
  );
}

// ── AI mode (new FireAnt-style layout) ─────────────────────────────────
function AIMode({ setMode }: { setMode: (m: Mode) => void }) {
  const [error, setError] = useState<string | null>(null);
  const passedStocks = useStocksStore((s) => s.passedStocks);
  const activeConditions = useCopilotStore((s) => s.activeConditions);

  useEffect(() => {
    // Reset transient error when switching into AI mode.
    setError(null);
  }, []);

  return (
    <>
      <section className="min-w-0 flex-1">
        <div className="border-b border-[var(--color-line)]">
          <div className="px-6 pb-5 pt-6">
            <SectionHeader
              index="LYR/01"
              eyebrow="AI Filter · copilot"
              title="Describe a filter. Confirm. Apply."
              description="The copilot on the right parses your request; the active condition strip below holds the filter you can edit live."
            />
            <div className="mt-5">
              <ModeTabs mode="ai" setMode={setMode} />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-[1fr_auto] items-start gap-4 px-6 pt-4">
          <AIFilterStrip onError={setError} />
          <MatchCountCard count={passedStocks.length} conditionCount={activeConditions.length} />
        </div>

        <div className="px-6 pt-4">
          <ResultTabs />
          {error ? (
            <div className="pt-4">
              <Banner tone="danger" label="error">{error}</Banner>
            </div>
          ) : null}

          <div className="pt-4">
            {passedStocks.length > 0 ? (
              <StockTable stocks={passedStocks} />
            ) : (
              <EmptyState mode="ai" />
            )}
          </div>
        </div>
      </section>

      <CopilotPane onError={setError} />
    </>
  );
}

function EmptyState({ mode }: { mode: Mode }) {
  return (
    <div className="flex flex-col items-start gap-4 border border-dashed border-[var(--color-line-2)] px-6 py-10">
      <span className="tag">awaiting input</span>
      <p className="display text-[28px] tracking-tight">
        {mode === "rule" ? (
          <>
            Configure the rail. Press <span className="text-[var(--color-accent)]">Run filter</span>.
          </>
        ) : (
          <>
            Ask the copilot, e.g. <span className="text-[var(--color-accent)]">&quot;Lọc cổ phiếu thanh khoản cao&quot;</span>.
          </>
        )}
      </p>
      <p className="max-w-[60ch] text-[13px] text-[var(--color-text-dim)]">
        {mode === "rule"
          ? "The streaming endpoint will report progress symbol-by-symbol while the scan runs."
          : "Type a prompt on the right. The model emits a confirm card; click Lọc cổ phiếu to apply."}
      </p>
    </div>
  );
}
