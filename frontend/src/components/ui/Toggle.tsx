"use client";

interface Props {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  hint?: string;
}

export function Toggle({ checked, onChange, label, hint }: Props) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className="group flex w-full items-center justify-between gap-3 py-2 text-left"
    >
      <span className="flex flex-col gap-0.5 min-w-0">
        <span
          className={`text-[14px] tracking-tight transition-colors ${
            checked ? "text-[var(--color-text)]" : "text-[var(--color-text-dim)]"
          }`}
        >
          {label}
        </span>
        {hint ? (
          <span className="text-[11px] text-[var(--color-text-faint)] leading-snug">{hint}</span>
        ) : null}
      </span>
      <span
        aria-hidden
        className={`relative h-[14px] w-[28px] shrink-0 border transition-colors ${
          checked
            ? "border-[var(--color-accent)] bg-[var(--color-accent)]/15"
            : "border-[var(--color-line-2)] bg-transparent"
        }`}
      >
        <span
          className={`absolute top-[2px] block h-[8px] w-[8px] transition-all ${
            checked ? "left-[16px] bg-[var(--color-accent)]" : "left-[2px] bg-[var(--color-text-dim)]"
          }`}
        />
      </span>
    </button>
  );
}
