"use client";

import { Toggle } from "@/components/ui/Toggle";
import { NumberField } from "@/components/ui/NumberField";
import { Slider } from "@/components/ui/Slider";
import { MultiSelect } from "@/components/ui/MultiSelect";
import type { Exchange, Layer1Filters, TradingStatus } from "@/lib/types";

const EXCHANGES: readonly Exchange[] = ["HOSE", "HNX", "UPCOM"];
const STATUSES: readonly TradingStatus[] = ["normal", "warning", "control", "restriction"];

interface Props {
  filters: Layer1Filters;
  onChange: (next: Layer1Filters) => void;
  onRun: () => void;
  running: boolean;
}

export function FilterSidebar({ filters, onChange, onRun, running }: Props) {
  const set = <K extends keyof Layer1Filters>(k: K, v: Layer1Filters[K]) =>
    onChange({ ...filters, [k]: v });

  return (
    <aside className="sidebar-scroll sticky top-16 flex h-[calc(100vh-4rem)] w-[320px] shrink-0 flex-col border-r border-[var(--color-line)] bg-[var(--color-bg)]">
      <div className="border-b border-[var(--color-line)] px-5 py-5">
        <div className="tag">01 · Parameters</div>
        <h2 className="display mt-1 text-[24px] tracking-tight">Hard filters</h2>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        <Block>
          <Toggle
            checked={filters.use_exchange}
            onChange={(v) => set("use_exchange", v)}
            label="Exchange"
          />
          <div className="pt-1.5">
            <MultiSelect
              options={EXCHANGES}
              selected={filters.exchanges}
              onChange={(s) => set("exchanges", s)}
              disabled={!filters.use_exchange}
            />
          </div>
        </Block>

        <Block>
          <Toggle
            checked={filters.use_gtgd20}
            onChange={(v) => set("use_gtgd20", v)}
            label="Min GTGD20"
            hint="20-session avg trading value"
          />
          <NumberField
            value={filters.min_gtgd20}
            onChange={(v) => set("min_gtgd20", v)}
            min={1}
            max={500}
            step={1}
            suffix="B VND"
            disabled={!filters.use_gtgd20}
          />
        </Block>

        <Block>
          <Toggle
            checked={filters.use_status}
            onChange={(v) => set("use_status", v)}
            label="Allowed statuses"
          />
          <div className="pt-1.5">
            <MultiSelect
              options={STATUSES}
              selected={filters.statuses}
              onChange={(s) => set("statuses", s)}
              disabled={!filters.use_status}
            />
          </div>
        </Block>

        <Block>
          <Toggle
            checked={filters.use_history}
            onChange={(v) => set("use_history", v)}
            label="Min history"
            hint="Trading sessions"
          />
          <NumberField
            value={filters.min_history}
            onChange={(v) => set("min_history", v)}
            min={20}
            max={500}
            step={5}
            suffix="sessions"
            disabled={!filters.use_history}
          />
        </Block>

        <Block>
          <Toggle
            checked={filters.use_price}
            onChange={(v) => set("use_price", v)}
            label="Min price"
          />
          <NumberField
            value={filters.min_price}
            onChange={(v) => set("min_price", v)}
            min={100}
            max={1_000_000}
            step={500}
            suffix="VND"
            disabled={!filters.use_price}
          />
        </Block>

        <Block>
          <Toggle
            checked={filters.use_volume}
            onChange={(v) => set("use_volume", v)}
            label="Min volume today"
          />
          <NumberField
            value={filters.min_volume_million}
            onChange={(v) => set("min_volume_million", v)}
            min={0}
            max={10000}
            step={1}
            suffix="M VND"
            disabled={!filters.use_volume}
          />
        </Block>

        <Block>
          <Toggle
            checked={filters.use_intraday}
            onChange={(v) => set("use_intraday", v)}
            label="Intraday activity ≥"
            hint="vs expected at this time of day"
          />
          <Slider
            value={filters.min_intraday_pct}
            onChange={(v) => set("min_intraday_pct", v)}
            min={0}
            max={100}
            step={5}
            suffix="%"
            disabled={!filters.use_intraday}
          />
        </Block>

        <Block>
          <Toggle
            checked={filters.exclude_ceiling_floor}
            onChange={(v) => set("exclude_ceiling_floor", v)}
            label="Exclude ceiling/floor"
          />
        </Block>

        <Block>
          <Toggle
            checked={filters.use_cv}
            onChange={(v) => set("use_cv", v)}
            label="CV stability cap"
            hint="std / mean × 100"
          />
          <Slider
            value={filters.cv_cap}
            onChange={(v) => set("cv_cap", v)}
            min={0}
            max={500}
            step={10}
            suffix="% CV"
            disabled={!filters.use_cv}
          />
        </Block>

        <Block>
          <Toggle
            checked={filters.market_regime_gate}
            onChange={(v) => set("market_regime_gate", v)}
            label="Market regime gate"
            hint="Suspend in downtrend"
          />
        </Block>
      </div>

      <div className="border-t border-[var(--color-line)] px-5 py-4">
        <button
          onClick={onRun}
          disabled={running}
          className="group relative w-full overflow-hidden border border-[var(--color-accent)] bg-[var(--color-accent)] py-3 text-center text-[12px] font-medium tracking-[0.22em] uppercase text-black transition-colors hover:bg-[var(--color-accent-dim)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {running ? "Scanning…" : "Run filter"}
        </button>
      </div>
    </aside>
  );
}

function Block({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 border-b border-dashed border-[var(--color-line)] py-3 last:border-b-0">
      {children}
    </div>
  );
}
