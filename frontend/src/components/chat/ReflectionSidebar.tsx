"use client";

import { useState, useEffect } from "react";

interface ReflectionEntry {
  date: string;
  rating: string;
  raw: string | null;
  alpha: string | null;
  holding: string | null;
  reflection: string;
}

interface ReflectionResponse {
  ticker: string;
  count: number;
  entries: ReflectionEntry[];
}

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export function ReflectionSidebar({ tickers }: { tickers: string[] }) {
  const [data, setData] = useState<Record<string, ReflectionEntry[]>>({});
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!tickers.length) {
      setData({});
      return;
    }
    let cancelled = false;
    const fetchAll = async () => {
      const out: Record<string, ReflectionEntry[]> = {};
      for (const t of tickers.slice(0, 5)) {
        try {
          const res = await fetch(`${BACKEND_URL}/reflections/${t}?limit=3`);
          if (!res.ok) continue;
          const json = (await res.json()) as ReflectionResponse;
          if (json.entries.length) out[t] = json.entries;
        } catch {
          // silently ignore — sidebar is best-effort
        }
      }
      if (!cancelled) setData(out);
    };
    void fetchAll();
    return () => {
      cancelled = true;
    };
  }, [tickers.join(",")]);

  const total = Object.values(data).reduce((s, e) => s + e.length, 0);
  if (!total) return null;

  return (
    <div className="border border-[var(--color-line)] bg-[var(--color-surface)]">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="tag text-[var(--color-text-dim)]">
          past reflections · {total} entries
        </span>
        <span className="mono text-[11px] text-[var(--color-text-dim)]">
          {expanded ? "−" : "+"}
        </span>
      </button>
      {expanded ? (
        <div className="border-t border-[var(--color-line)] p-4">
          {Object.entries(data).map(([ticker, entries]) => (
            <div key={ticker} className="mb-4 last:mb-0">
              <div className="mono mb-2 text-[12px] font-medium uppercase tracking-[0.18em] text-[var(--color-text)]">
                {ticker}
              </div>
              {entries.map((e, i) => (
                <div
                  key={`${ticker}-${i}`}
                  className="mb-2 border-l-2 border-[var(--color-line-2)] pl-3 text-[12px] text-[var(--color-text)]"
                >
                  <div className="mono mb-1 text-[10px] text-[var(--color-text-dim)]">
                    {e.date} · {e.rating} · alpha {e.alpha ?? "n/a"} · {e.holding ?? "n/a"}
                  </div>
                  <div>{e.reflection}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
