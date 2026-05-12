"use client";

import { useEffect, useState } from "react";
import { fmtSeconds } from "@/lib/format";

const REFRESH = 300;

export function CountdownBar({ nextRefreshIn, scoredAt }: { nextRefreshIn: number; scoredAt: string | null }) {
  const [remaining, setRemaining] = useState(nextRefreshIn);
  useEffect(() => setRemaining(nextRefreshIn), [nextRefreshIn]);
  useEffect(() => {
    const id = setInterval(() => setRemaining((r) => Math.max(0, r - 1)), 1000);
    return () => clearInterval(id);
  }, []);

  const pct = Math.max(0, Math.min(100, ((REFRESH - remaining) / REFRESH) * 100));
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between">
        <div className="flex items-center gap-3">
          <span className="tag">cache · refreshes every 5m</span>
          {scoredAt ? (
            <span className="mono text-[11px] text-[var(--color-text-faint)]">
              scored at {scoredAt.slice(0, 19)}
            </span>
          ) : null}
        </div>
        <span className="mono text-[12px] text-[var(--color-text-dim)]">
          next in <span className="text-[var(--color-text)]">{fmtSeconds(remaining)}</span>
        </span>
      </div>
      <div className="thin-progress">
        <span style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
