"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchLayer2Latest } from "@/lib/api";
import { recomputeScores } from "@/lib/scoring";
import { useWeightsStore } from "@/lib/store";
import { WeightsSidebar } from "@/components/layer2/WeightsSidebar";
import { CountdownBar } from "@/components/layer2/CountdownBar";
import { ScoresTable } from "@/components/layer2/ScoresTable";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Banner } from "@/components/ui/Banner";
import type { Layer2Score } from "@/lib/types";
import type { RecomputedScores } from "@/lib/scoring";

export default function Layer2Page() {
  const weights = useWeightsStore((s) => s.weights);

  const query = useQuery({
    queryKey: ["layer2-latest"],
    queryFn: fetchLayer2Latest,
    refetchInterval: 1_000,
    refetchIntervalInBackground: false,
  });

  const rows = useMemo<(Layer2Score & { _scores?: RecomputedScores })[]>(() => {
    const scores = query.data?.scores ?? [];
    return scores.map((s) =>
      s.breakdown ? { ...s, _scores: recomputeScores(s.breakdown, weights) } : { ...s },
    );
  }, [query.data, weights]);

  const [selected, setSelected] = useState<string | null>(null);

  function handleSelect(sym: string) {
    setSelected((prev) => (prev === sym ? null : sym));
  }

  return (
    <div className="flex">
      <WeightsSidebar />

      <section className="min-w-0 flex-1">
        <div className="hairline-grid border-b border-[var(--color-line)]">
          <div className="mx-auto max-w-[1320px] px-8 pb-10 pt-12">
            <SectionHeader
              index="LYR/02"
              eyebrow="BUY score · cached"
              title="Three pillars. One number."
              description="Server-cached scores refresh every five minutes. Tune the weights in the rail and the table reorders in place — numerical parity with the Streamlit reference is intentional."
            />
          </div>
        </div>

        <div className="mx-auto flex max-w-[1320px] flex-col gap-6 px-8 py-8">
          {query.isLoading ? (
            <Banner tone="info">Loading scores…</Banner>
          ) : query.error ? (
            <Banner tone="danger" label="error">
              {(query.error as Error).message}
            </Banner>
          ) : !query.data?.scores?.length ? (
            <Banner tone="info">
              No Layer 2 scores yet. The scheduler refreshes every 5 minutes once Layer 1 has passed symbols.
            </Banner>
          ) : (
            <>
              <CountdownBar
                nextRefreshIn={query.data.next_refresh_in ?? 300}
                scoredAt={query.data.scored_at}
              />

              <div className="flex items-center gap-6 border-b border-dashed border-[var(--color-line)] pb-5">
                <Stat label="Scored" value={String(rows.length)} />
                <div className="h-6 w-px bg-[var(--color-line)]" />
                <Stat
                  label="Top BUY"
                  value={rows.length ? String(Math.max(...rows.map((r) => r._scores?.buy ?? r.buy_score)).toFixed(1)) : "—"}
                  accent
                />
                <div className="h-6 w-px bg-[var(--color-line)]" />
                <Stat
                  label="With breakout"
                  value={String(rows.filter((r) => (r._scores?.brk ?? r.breakout_score) > 0).length)}
                />
              </div>

              <ScoresTable
                rows={rows}
                selected={selected}
                onSelect={handleSelect}
                weights={weights}
              />
            </>
          )}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="tag text-[10px]">{label}</span>
      <span
        className="serif-num text-[22px] leading-none"
        style={{ color: accent ? "var(--color-accent)" : "var(--color-text)" }}
      >
        {value}
      </span>
    </div>
  );
}
