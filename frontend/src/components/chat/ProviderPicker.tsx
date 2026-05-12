"use client";

import type { Provider } from "@/lib/types";

const OPTIONS: { value: Provider; label: string }[] = [
  { value: "claude", label: "Claude" },
  { value: "gemini", label: "Gemini" },
];

export function ProviderPicker({
  value,
  onChange,
}: {
  value: Provider;
  onChange: (p: Provider) => void;
}) {
  return (
    <div className="flex border border-[var(--color-line-2)]">
      {OPTIONS.map((o) => {
        const active = value === o.value;
        return (
          <button
            key={o.value}
            onClick={() => onChange(o.value)}
            className={`mono px-3 py-1.5 text-[11px] tracking-[0.2em] uppercase transition-colors ${
              active
                ? "bg-[var(--color-accent)] text-black"
                : "text-[var(--color-text-dim)] hover:text-[var(--color-text)]"
            }`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
