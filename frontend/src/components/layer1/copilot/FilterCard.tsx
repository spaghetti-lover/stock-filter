"use client";

import { Banner } from "@/components/ui/Banner";
import type { AIFilterCondition } from "@/lib/aiFilterTypes";

interface Props {
  summary: string;
  conditions: AIFilterCondition[];
  unsupported: string[];
  applied?: boolean;
  onApply: () => void;
}

export function FilterCard({ summary, conditions, unsupported, applied, onApply }: Props) {
  return (
    <div className="flex flex-col gap-3 border border-[var(--color-line-2)] bg-[var(--color-surface)] p-3">
      <div className="tag text-[var(--color-text-dim)]">Filter conditions</div>
      {summary ? (
        <p className="text-[12px] text-[var(--color-text-dim)]">{summary}</p>
      ) : null}

      {conditions.length > 0 ? (
        <div className="flex flex-col gap-1.5">
          {conditions.map((c, i) => (
            <div
              key={`${c.key}-${i}`}
              className="flex items-center justify-between gap-2 border border-[var(--color-line)] bg-[var(--color-bg)] px-2.5 py-1.5"
            >
              <span className="mono text-[12px] text-[var(--color-text)]">{c.label}</span>
              <span className="text-[var(--color-ok)]">✓</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[12px] text-[var(--color-text-dim)]">No matching condition.</p>
      )}

      {unsupported.length > 0 ? (
        <Banner
          tone={unsupported.includes("provider_error") ? "danger" : "warn"}
          label={unsupported.includes("provider_error") ? "provider error" : "not supported"}
        >
          {unsupported.includes("provider_error")
            ? summary
            : `AI couldn't map: ${unsupported.join(", ")}`}
        </Banner>
      ) : null}

      {conditions.length > 0 ? (
        <button
          type="button"
          onClick={onApply}
          disabled={applied}
          className="mt-1 w-full border border-[var(--color-accent)] bg-[var(--color-accent)] py-2 text-center text-[11px] font-medium tracking-[0.22em] uppercase text-black transition-colors hover:bg-[var(--color-accent-dim)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {applied ? "Applied" : "Lọc cổ phiếu"}
        </button>
      ) : null}
    </div>
  );
}
