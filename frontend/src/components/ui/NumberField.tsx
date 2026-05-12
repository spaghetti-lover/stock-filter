"use client";

import { useState, useEffect, useRef } from "react";

interface Props {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  suffix?: string;
  disabled?: boolean;
}

export function NumberField({ value, onChange, min, max, step, suffix, disabled }: Props) {
  // Buffer raw string so the user can freely edit (e.g. delete "60" → type "20")
  // without the parent clamping mid-edit.
  const [raw, setRaw] = useState(String(value));
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync display when parent changes value externally (but not while user is typing)
  useEffect(() => {
    if (!focused) setRaw(String(value));
  }, [value, focused]);

  function commit(str: string) {
    const n = parseFloat(str);
    if (Number.isNaN(n)) {
      // Revert to last valid value
      setRaw(String(value));
      return;
    }
    const clamped =
      min !== undefined && max !== undefined
        ? Math.min(max, Math.max(min, n))
        : min !== undefined
        ? Math.max(min, n)
        : max !== undefined
        ? Math.min(max, n)
        : n;
    setRaw(String(clamped));
    onChange(clamped);
  }

  return (
    <div
      className={`group flex items-center border transition-all duration-150 ${
        disabled
          ? "border-[var(--color-line)] opacity-40 cursor-not-allowed"
          : focused
          ? "border-[var(--color-accent)] shadow-[0_0_0_1px_var(--color-accent)]/20"
          : "border-[var(--color-line-2)] hover:border-[var(--color-line-2)]/80"
      }`}
    >
      <input
        ref={inputRef}
        type="text"
        inputMode="numeric"
        value={raw}
        disabled={disabled}
        onFocus={(e) => {
          setFocused(true);
          // Select all so user can immediately overwrite
          e.target.select();
        }}
        onBlur={() => {
          setFocused(false);
          commit(raw);
        }}
        onChange={(e) => setRaw(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            commit(raw);
            inputRef.current?.blur();
          }
          if (e.key === "Escape") {
            setRaw(String(value));
            inputRef.current?.blur();
          }
          // Arrow key nudging
          if (e.key === "ArrowUp" || e.key === "ArrowDown") {
            e.preventDefault();
            const delta = (step ?? 1) * (e.key === "ArrowUp" ? 1 : -1);
            const next = (parseFloat(raw) || value) + delta;
            commit(String(next));
          }
        }}
        className="mono w-full bg-transparent px-2.5 py-2 text-[13px] tabular-nums tracking-tight outline-none disabled:cursor-not-allowed"
      />
      {suffix ? (
        <span
          className="tag shrink-0 border-l border-[var(--color-line)] bg-[var(--color-surface)] px-2.5 py-2 text-[10px]"
          style={{ letterSpacing: "0.12em" }}
        >
          {suffix}
        </span>
      ) : null}
    </div>
  );
}
