"use client";

import type { Provider } from "@/lib/types";
import { MODEL_OPTIONS } from "./modelCatalog";

export function ModelPicker({
  provider,
  value,
  onChange,
}: {
  provider: Provider;
  value: string;
  onChange: (m: string) => void;
}) {
  const options = MODEL_OPTIONS[provider];
  return (
    <div className="flex border border-[var(--color-line-2)]">
      {options.map((o) => {
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
