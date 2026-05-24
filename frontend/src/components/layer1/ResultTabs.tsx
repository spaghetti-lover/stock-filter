"use client";

const TABS = [
  { key: "result", label: "Kết quả", enabled: true },
  { key: "stats", label: "Thống kê", enabled: false },
  { key: "fundamentals", label: "Cơ bản", enabled: false },
  { key: "heatmap", label: "Bản đồ nhiệt", enabled: false },
];

export function ResultTabs() {
  return (
    <div className="flex items-center gap-1 border-b border-[var(--color-line)] bg-[var(--color-surface)] px-5">
      {TABS.map((t) => (
        <button
          key={t.key}
          type="button"
          disabled={!t.enabled}
          className={`mono px-3 py-2 text-[11px] tracking-[0.18em] uppercase transition-colors ${
            t.enabled
              ? "border-b-2 border-[var(--color-accent)] text-[var(--color-accent)]"
              : "text-[var(--color-text-dim)]/50 cursor-not-allowed"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
