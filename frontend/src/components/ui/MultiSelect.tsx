"use client";

interface Props<T extends string> {
  options: readonly T[];
  selected: T[];
  onChange: (next: T[]) => void;
  disabled?: boolean;
}

export function MultiSelect<T extends string>({ options, selected, onChange, disabled }: Props<T>) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => {
        const active = selected.includes(opt);
        return (
          <button
            key={opt}
            type="button"
            disabled={disabled}
            onClick={() => {
              if (active) onChange(selected.filter((s) => s !== opt));
              else onChange([...selected, opt]);
            }}
            className={`mono border px-2.5 py-1.5 text-[12px] tracking-wide transition-colors ${
              active
                ? "border-[var(--color-accent)] bg-[var(--color-accent)]/10 text-[var(--color-accent)]"
                : "border-[var(--color-line-2)] text-[var(--color-text-dim)] hover:border-[var(--color-line)] hover:text-[var(--color-text)]"
            } ${disabled ? "opacity-40" : ""}`}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}
