"use client";

// Hidden cross-check page (no nav link). Dumps the FULL per-symbol breakdown —
// including raw inputs + every intermediate value — so each formula can be
// verified step by step. URL: /layer2/log
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchLayer2Latest } from "@/lib/api";
import { Banner } from "@/components/ui/Banner";

export default function Layer2LogPage() {
  const query = useQuery({
    queryKey: ["layer2-latest"],
    queryFn: fetchLayer2Latest,
    refetchInterval: 5_000,
    refetchIntervalInBackground: false,
  });

  const [search, setSearch] = useState("");
  const [copied, setCopied] = useState(false);

  const scores = query.data?.scores ?? [];

  // { "VIC": {liquidity, momentum, breakout, debug}, ... }
  const bySymbol = useMemo<Record<string, unknown>>(() => {
    const term = search.trim().toUpperCase();
    const filtered = term
      ? scores.filter((s) => s.symbol.toUpperCase().includes(term))
      : scores;
    return Object.fromEntries(filtered.map((s) => [s.symbol, s.breakdown ?? null]));
  }, [scores, search]);

  const json = useMemo(() => JSON.stringify(bySymbol, null, 2), [bySymbol]);
  const shownCount = Object.keys(bySymbol).length;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <div className="mx-auto max-w-[1320px] px-8 py-10">
      <div className="mb-6 flex flex-col gap-1">
        <span className="tag text-[10px]">LYR/02 · LOG</span>
        <h1 className="serif-num text-[22px] leading-none text-[var(--color-text)]">
          Full breakdown — cross-check
        </h1>
        <p className="text-[13px] text-[var(--color-text-dim)]">
          Mọi raw input và bước tính trung gian của từng mã. Dùng để đối chiếu công thức.
        </p>
      </div>

      {query.isLoading ? (
        <Banner tone="info">Loading…</Banner>
      ) : query.error ? (
        <Banner tone="danger" label="error">
          {(query.error as Error).message}
        </Banner>
      ) : !scores.length ? (
        <Banner tone="info">
          Chưa có Layer 2 scores. Scheduler refresh mỗi 5 phút sau khi Layer 1 có mã pass.
        </Banner>
      ) : (
        <>
          <div className="mb-4 flex flex-wrap items-center gap-4">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Lọc theo symbol… (vd: VIC)"
              className="w-56 rounded border border-[var(--color-line)] bg-[var(--color-surface)] px-3 py-1.5 text-[13px] text-[var(--color-text)] outline-none focus:border-[var(--color-accent)]"
            />
            <span className="text-[12px] text-[var(--color-text-dim)]">
              {shownCount} / {scores.length} mã
            </span>
            {query.data?.scored_at ? (
              <span className="text-[12px] text-[var(--color-text-faint)]">
                scored_at: {query.data.scored_at}
              </span>
            ) : null}
            <button
              onClick={handleCopy}
              className="ml-auto rounded border border-[var(--color-line)] px-3 py-1.5 text-[12px] text-[var(--color-text)] transition-colors hover:border-[var(--color-accent)]"
            >
              {copied ? "Copied ✓" : "Copy JSON"}
            </button>
          </div>

          <pre className="max-h-[75vh] overflow-auto rounded border border-[var(--color-line)] bg-[var(--color-surface)] p-4 font-mono text-[12px] leading-[1.5] text-[var(--color-text)]">
            {json}
          </pre>
        </>
      )}
    </div>
  );
}
