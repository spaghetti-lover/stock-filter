"use client";

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

interface Props {
  label: string;
  onRemove?: () => void;
  popover?: ReactNode;
  applied?: boolean;
}

export function EditableChip({ label, onRemove, popover, applied = true }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  return (
    <div ref={ref} className="relative inline-flex">
      <span
        className={`mono inline-flex items-center gap-2 border px-2.5 py-1 text-[11px] tracking-[0.04em] ${
          applied
            ? "border-[var(--color-accent)]/60 bg-[var(--color-accent)]/10 text-[var(--color-text)]"
            : "border-[var(--color-line-2)] bg-[var(--color-surface)] text-[var(--color-text-dim)]"
        }`}
      >
        <span className="text-[var(--color-ok)]">✓</span>
        {popover ? (
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="text-left hover:text-[var(--color-accent)] focus:outline-none"
          >
            {label}
          </button>
        ) : (
          <span>{label}</span>
        )}
        {onRemove ? (
          <button
            type="button"
            onClick={onRemove}
            aria-label={`Remove ${label}`}
            className="text-[var(--color-text-dim)] transition-colors hover:text-[var(--color-danger)]"
          >
            ×
          </button>
        ) : null}
      </span>

      {open && popover ? (
        <div className="absolute left-0 top-full z-30 mt-2 min-w-[220px] border border-[var(--color-line-2)] bg-[var(--color-surface)] p-3 shadow-lg">
          {popover}
        </div>
      ) : null}
    </div>
  );
}
