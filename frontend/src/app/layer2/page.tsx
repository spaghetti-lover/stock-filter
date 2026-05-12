"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchLayer2Latest } from "@/lib/api";
import { recomputeScores } from "@/lib/scoring";
import { useWeightsStore } from "@/lib/store";
import { WeightsSidebar } from "@/components/layer2/WeightsSidebar";
import { CountdownBar } from "@/components/layer2/CountdownBar";
import { ScoresTable } from "@/components/layer2/ScoresTable";
import { BreakdownPanel } from "@/components/layer2/BreakdownPanel";
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
    const enriched: (Layer2Score & { _scores?: RecomputedScores })[] = scores.map((s) =>
      s.breakdown ? { ...s, _scores: recomputeScores(s.breakdown, weights) } : { ...s },
    );
    return enriched.sort(
      (a, b) => (b._scores?.buy ?? b.buy_score) - (a._scores?.buy ?? a.buy_score),
    );
  }, [query.data, weights]);

  const [selected, setSelected] = useState<string | null>(null);
  const selectedStock = useMemo(
    () => rows.find((r) => r.symbol === selected) ?? rows[0],
    [rows, selected],
  );

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

        <div className="mx-auto flex max-w-[1320px] flex-col gap-8 px-8 py-10">
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

              <div className="flex items-baseline gap-3">
                <span className="display text-[24px] tracking-tight">Scored</span>
                <span className="mono text-[13px] text-[var(--color-text-dim)]">
                  ({rows.length})
                </span>
              </div>

              <ScoresTable
                rows={rows}
                selected={selectedStock?.symbol ?? null}
                onSelect={setSelected}
              />

              {selectedStock?.breakdown ? (
                <div className="pt-2">
                  <div className="tag pb-3">Breakdown · {selectedStock.symbol}</div>
                  <BreakdownPanel stock={selectedStock} weights={weights} />
                </div>
              ) : null}
            </>
          )}
        </div>
      </section>
    </div>
  );
}
