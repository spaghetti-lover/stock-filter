"use client";

const SUGGESTIONS = [
  "Lọc cổ phiếu thanh khoản cao",
  "GTGD trên 50 tỷ và biến động thấp",
  "Cổ phiếu sàn HOSE không trần sàn",
];

interface Props {
  onPick: (prompt: string) => void;
}

export function SuggestedPrompts({ onPick }: Props) {
  return (
    <div className="flex flex-col gap-1.5 border-t border-[var(--color-line)] px-4 py-3">
      <div className="tag text-[var(--color-text-dim)]">Suggestions</div>
      {SUGGESTIONS.map((s) => (
        <button
          key={s}
          type="button"
          onClick={() => onPick(s)}
          className="border border-[var(--color-line)] bg-[var(--color-bg)] px-3 py-1.5 text-left text-[12px] text-[var(--color-text-dim)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-text)]"
        >
          {s}
        </button>
      ))}
    </div>
  );
}
