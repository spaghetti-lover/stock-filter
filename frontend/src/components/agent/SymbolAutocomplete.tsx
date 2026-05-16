"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { fetchSymbols, type SymbolEntry } from "@/lib/tradingAgent";

interface Props {
  value: SymbolEntry | null;
  onCommit: (entry: SymbolEntry) => void;
  disabled?: boolean;
}

const MAX_RESULTS = 50;

export function SymbolAutocomplete({ value, onCommit, disabled }: Props) {
  const [all, setAll] = useState<SymbolEntry[] | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [draft, setDraft] = useState(value ? `${value.exchange}:${value.symbol}` : "");
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchSymbols()
      .then((rows) => { if (!cancelled) setAll(rows); })
      .catch((err) => { if (!cancelled) setFetchError(err instanceof Error ? err.message : String(err)); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (value) setDraft(`${value.exchange}:${value.symbol}`);
  }, [value]);

  const filtered = useMemo<SymbolEntry[]>(() => {
    if (!all) return [];
    const q = draft.trim().toUpperCase();
    if (!q) return all.slice(0, MAX_RESULTS);
    const exact: SymbolEntry[] = [];
    const prefix: SymbolEntry[] = [];
    const sub: SymbolEntry[] = [];
    for (const row of all) {
      const sym = row.symbol.toUpperCase();
      const full = `${row.exchange}:${sym}`;
      if (sym === q || full === q) exact.push(row);
      else if (sym.startsWith(q) || full.startsWith(q)) prefix.push(row);
      else if (sym.includes(q)) sub.push(row);
    }
    return [...exact, ...prefix, ...sub].slice(0, MAX_RESULTS);
  }, [all, draft]);

  useEffect(() => {
    setHighlight(0);
  }, [draft]);

  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!containerRef.current) return;
      if (!containerRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const commit = (entry: SymbolEntry) => {
    onCommit(entry);
    setDraft(`${entry.exchange}:${entry.symbol}`);
    setOpen(false);
    inputRef.current?.blur();
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setHighlight((h) => Math.min(h + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter" || e.key === "Tab") {
      if (filtered[highlight]) {
        e.preventDefault();
        commit(filtered[highlight]);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-[640px]">
      <div className="flex items-center gap-3 border border-[var(--color-line)] bg-[var(--color-bg)] px-4 py-3"
        style={{ boxShadow: open ? "inset 0 0 0 1px color-mix(in srgb, var(--color-accent) 32%, transparent)" : "none" }}>
        <span className="mono text-[11px] uppercase tracking-[0.2em] text-[var(--color-accent)]">ticker</span>
        <input
          ref={inputRef}
          value={draft}
          disabled={disabled}
          onChange={(e) => { setDraft(e.target.value.toUpperCase()); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder={all ? "Type a symbol (e.g. FPT, DSE, VIC)" : fetchError ? `! ${fetchError}` : "loading symbols…"}
          spellCheck={false}
          autoComplete="off"
          className="flex-1 bg-transparent font-mono text-[15px] uppercase tracking-wide text-[var(--color-text)] caret-[var(--color-accent)] outline-none placeholder:text-[var(--color-text-faint)]/60"
        />
        {value ? (
          <span className="mono text-[10px] uppercase tracking-[0.2em] text-[var(--color-ok)]">✓ {value.exchange}:{value.symbol}</span>
        ) : null}
      </div>

      {open && filtered.length > 0 ? (
        <div className="absolute left-0 right-0 top-full z-30 mt-1 max-h-[320px] overflow-y-auto border border-[var(--color-line)] bg-[var(--color-bg)] shadow-lg">
          {filtered.map((row, i) => {
            const active = i === highlight;
            return (
              <button
                key={`${row.exchange}-${row.symbol}`}
                type="button"
                onMouseEnter={() => setHighlight(i)}
                onMouseDown={(e) => { e.preventDefault(); commit(row); }}
                className="mono flex w-full items-center gap-3 px-4 py-2 text-left text-[13px] transition-colors"
                style={{
                  background: active ? "color-mix(in srgb, var(--color-accent) 14%, transparent)" : "transparent",
                  color: active ? "var(--color-text)" : "var(--color-text-dim)",
                }}
              >
                <span className="w-[60px] text-[11px] uppercase tracking-[0.18em]" style={{ color: active ? "var(--color-accent)" : "var(--color-text-faint)" }}>{row.exchange}</span>
                <span className="font-mono text-[14px] tracking-wide text-[var(--color-text)]">{row.symbol}</span>
              </button>
            );
          })}
        </div>
      ) : null}

      <p className="mono mt-2 text-[10px] uppercase tracking-[0.2em] text-[var(--color-text-faint)]">
        ↑↓ navigate · enter/tab to select · esc to close
      </p>
    </div>
  );
}
