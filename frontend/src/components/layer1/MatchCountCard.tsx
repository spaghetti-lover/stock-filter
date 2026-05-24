"use client";

interface Props {
  count: number;
  conditionCount: number;
}

export function MatchCountCard({ count, conditionCount }: Props) {
  return (
    <div className="flex flex-col gap-1 border border-[var(--color-line-2)] bg-[var(--color-surface)] px-5 py-4 text-right">
      <div className="tag text-[var(--color-text-dim)]">
        {conditionCount > 0
          ? `Matching all ${conditionCount} condition${conditionCount === 1 ? "" : "s"}`
          : "No active conditions"}
      </div>
      <div className="display text-[28px] tabular-nums leading-tight text-[var(--color-accent)]">
        {count}
        <span className="mono ml-2 text-[12px] tracking-[0.16em] text-[var(--color-text-dim)]">
          stocks
        </span>
      </div>
    </div>
  );
}
