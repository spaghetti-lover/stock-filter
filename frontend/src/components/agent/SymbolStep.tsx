"use client";

import { useEffect, useRef, useState } from "react";
import { BoxPanel } from "./BoxPanel";

interface Props {
  defaultValue?: string;
  locked?: boolean;
  value?: string;
  onSubmit: (symbol: string) => void;
}

export function SymbolStep({
  defaultValue = "SPY",
  locked = false,
  value,
  onSubmit,
}: Props) {
  const [draft, setDraft] = useState(value ?? "");
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (!locked) inputRef.current?.focus();
  }, [locked]);

  const submit = () => {
    const v = (draft.trim() || defaultValue).toUpperCase();
    onSubmit(v);
  };

  return (
    <BoxPanel title="Step 01 · Ticker Symbol" tone={locked ? "muted" : "accent"}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <p className="display text-[18px] tracking-tight">Ticker Symbol</p>
          <p className="text-[13px] text-[var(--color-text-dim)]">
            Enter the exact ticker symbol to analyze, including exchange suffix
            when needed{" "}
            <span className="text-[var(--color-text-faint)]">
              (examples: SPY, CNC.TO, 7203.T, 0700.HK)
            </span>
          </p>
          <p className="mono text-[11px] text-[var(--color-text-faint)]">
            default · {defaultValue}
          </p>
        </div>

        <div
          className="flex items-stretch border border-[var(--color-line)] bg-[var(--color-bg)]"
          style={{
            boxShadow: locked
              ? "none"
              : "inset 0 0 0 1px color-mix(in srgb, var(--color-accent) 24%, transparent)",
          }}
        >
          <span
            className="mono flex items-center gap-2 border-r border-[var(--color-line)] bg-[var(--color-surface-2)] px-3 text-[12px]"
            style={{ color: "var(--color-accent)" }}
          >
            <span aria-hidden>›</span>
            <span className="text-[var(--color-text-faint)]">
              [{defaultValue}]
            </span>
            <span aria-hidden>:</span>
          </span>
          {locked ? (
            <div className="flex-1 px-3 py-3 font-mono text-[14px] tracking-wide text-[var(--color-text)]">
              {value}
            </div>
          ) : (
            <input
              ref={inputRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") submit();
              }}
              placeholder={defaultValue}
              spellCheck={false}
              autoComplete="off"
              className="flex-1 bg-transparent px-3 py-3 font-mono text-[14px] uppercase tracking-wide text-[var(--color-text)] caret-[var(--color-accent)] outline-none placeholder:text-[var(--color-text-faint)]/60"
            />
          )}
          {!locked ? (
            <button
              onClick={submit}
              className="group mono flex items-center gap-2 border-l border-[var(--color-line)] bg-[var(--color-surface)] px-4 text-[11px] uppercase tracking-[0.18em] text-[var(--color-text-dim)] transition-colors hover:bg-[var(--color-accent)] hover:text-black"
            >
              <span>enter</span>
              <span aria-hidden className="transition-transform group-hover:translate-x-0.5">
                ↵
              </span>
            </button>
          ) : (
            <span
              aria-hidden
              className="mono flex items-center gap-2 border-l border-[var(--color-line)] bg-[var(--color-surface)] px-4 text-[11px] uppercase tracking-[0.18em] text-[var(--color-ok)]"
            >
              <span>✓ confirmed</span>
            </span>
          )}
        </div>
      </div>
    </BoxPanel>
  );
}
