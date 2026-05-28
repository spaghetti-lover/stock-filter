"use client";

import { useState, useEffect, useRef } from "react";
import { useWeightsStore } from "@/lib/store";

const PILLARS = [
  { key: "liquidity", label: "Liquidity" },
  { key: "momentum", label: "Momentum" },
  { key: "breakout", label: "Breakout" },
];

const GROUPS: { title: string; keys: { key: string; label: string }[] }[] = [
  {
    title: "Liquidity sub-weights",
    keys: [
      { key: "liq_gtgd20", label: "GTGD20" },
      { key: "liq_intraday", label: "Intraday activity" },
      { key: "liq_cv", label: "CV stability" },
    ],
  },
  {
    title: "Momentum sub-weights",
    keys: [
      { key: "mom_volatility", label: "Price volatility" },
      { key: "mom_ma", label: "MA analysis" },
      { key: "mom_rs", label: "Relative strength" },
      { key: "mom_flow", label: "Flow (A/D + SMF)" },
      { key: "mom_tech", label: "Technical (RSI+MACD)" },
    ],
  },
  {
    title: "Flow sub-weights",
    keys: [
      { key: "flow_ad", label: "A/D within flow" },
      { key: "flow_smf", label: "SMF within flow" },
    ],
  },
  {
    title: "Breakout sub-weights",
    keys: [
      { key: "brk_price", label: "Price breakout" },
      { key: "brk_vol", label: "Volume confirm" },
      { key: "brk_dryup", label: "Volume dry-up" },
      { key: "brk_base", label: "Base quality" },
      { key: "brk_closing_strength", label: "Closing strength" },
    ],
  },
];

export function WeightsSidebar() {
  const weights = useWeightsStore((s) => s.weights);
  const setWeight = useWeightsStore((s) => s.setWeight);
  const reset = useWeightsStore((s) => s.reset);
  const [open, setOpen] = useState<Record<string, boolean>>({});

  const pillarSum = PILLARS.reduce((a, p) => a + (weights[p.key] ?? 0), 0);

  return (
    <aside className="sidebar-scroll sticky top-16 flex h-[calc(100vh-4rem)] w-[320px] shrink-0 flex-col border-r border-[var(--color-line)] bg-[var(--color-bg)]">
      <div className="border-b border-[var(--color-line)] px-5 py-5">
        <div className="tag">02 · Weights</div>
        <h2 className="display mt-1 text-[24px] tracking-tight">BUY score</h2>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        <div className="mb-4">
          <button
            onClick={reset}
            className="mono w-full border border-[var(--color-line-2)] py-2.5 text-[12px] tracking-[0.2em] uppercase text-[var(--color-text-dim)] hover:border-[var(--color-line)] hover:text-[var(--color-text)] transition-colors"
          >
            Reset to defaults
          </button>
        </div>

        <div className="border-b border-dashed border-[var(--color-line)] pb-4">
          <div className="tag mb-3 text-[11px]">Pillar weights</div>
          {PILLARS.map((p) => (
            <WeightRow
              key={p.key}
              label={p.label}
              value={weights[p.key] ?? 0}
              onChange={(v) => setWeight(p.key, v)}
            />
          ))}
          <SumChip total={pillarSum} />
        </div>

        {GROUPS.map((g) => {
          const sum = g.keys.reduce((a, k) => a + (weights[k.key] ?? 0), 0);
          const isOpen = !!open[g.title];
          return (
            <div key={g.title} className="border-b border-dashed border-[var(--color-line)] py-4 last:border-b-0">
              <button
                onClick={() => setOpen((s) => ({ ...s, [g.title]: !s[g.title] }))}
                className="flex w-full items-center justify-between text-left"
              >
                <span className="tag text-[11px]">{g.title}</span>
                <span className="mono text-[14px] text-[var(--color-text-dim)]">
                  {isOpen ? "−" : "+"}
                </span>
              </button>
              {isOpen ? (
                <div className="pt-3">
                  {g.keys.map((k) => (
                    <WeightRow
                      key={k.key}
                      label={k.label}
                      value={weights[k.key] ?? 0}
                      onChange={(v) => setWeight(k.key, v)}
                    />
                  ))}
                  <SumChip total={sum} />
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </aside>
  );
}

function WeightRow({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  const [raw, setRaw] = useState(value.toString());
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!focused) setRaw(value.toString());
  }, [value, focused]);

  function commit(str: string) {
    const n = parseFloat(str);
    if (Number.isNaN(n)) { setRaw(value.toString()); return; }
    const clamped = Math.min(1, Math.max(0, n));
    setRaw(clamped.toString());
    onChange(clamped);
  }

  return (
    <div className="flex items-center gap-3 py-2">
      <span className="flex-1 text-[13px] text-[var(--color-text-dim)]">{label}</span>
      <div
        className={`flex items-center border transition-all duration-150 ${
          focused
            ? "border-[var(--color-accent)]"
            : "border-[var(--color-line-2)] hover:border-[var(--color-line)]"
        }`}
      >
        <input
          ref={inputRef}
          type="text"
          inputMode="decimal"
          value={raw}
          onFocus={(e) => { setFocused(true); e.target.select(); }}
          onBlur={() => { setFocused(false); commit(raw); }}
          onChange={(e) => setRaw(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") { commit(raw); inputRef.current?.blur(); }
            if (e.key === "Escape") { setRaw(value.toString()); inputRef.current?.blur(); }
            if (e.key === "ArrowUp") { e.preventDefault(); commit(String(Math.round((parseFloat(raw || "0") + 0.05) * 100) / 100)); }
            if (e.key === "ArrowDown") { e.preventDefault(); commit(String(Math.round((parseFloat(raw || "0") - 0.05) * 100) / 100)); }
          }}
          className="mono w-[64px] bg-transparent px-2 py-1.5 text-right text-[13px] tabular-nums outline-none"
        />
      </div>
    </div>
  );
}

function SumChip({ total }: { total: number }) {
  const ok = Math.abs(total - 1.0) < 0.001;
  return (
    <div className="pt-2">
      <span
        className={`mono text-[11px] tracking-[0.18em] uppercase ${
          ok ? "text-[var(--color-ok)]" : "text-[var(--color-warn)]"
        }`}
      >
        sum {total.toFixed(2)}
        {ok ? " · ok" : " · will be normalized"}
      </span>
    </div>
  );
}
