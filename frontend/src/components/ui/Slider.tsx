"use client";

import { useState, useRef, useCallback } from "react";

interface Props {
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step?: number;
  suffix?: string;
  disabled?: boolean;
}

export function Slider({ value, onChange, min, max, step = 1, suffix, disabled }: Props) {
  const pct = ((value - min) / (max - min)) * 100;

  // Inline editing: click the number label to type a value directly
  const [editing, setEditing] = useState(false);
  const [raw, setRaw] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  function clamp(n: number) {
    const stepped = Math.round((n - min) / step) * step + min;
    return Math.min(max, Math.max(min, stepped));
  }

  function commitEdit(str: string) {
    const n = parseFloat(str);
    if (!Number.isNaN(n)) onChange(clamp(n));
    setEditing(false);
  }

  // Drag-to-scrub on the track — gives more control than native range
  const handleTrackPointer = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (disabled) return;
      const el = trackRef.current;
      if (!el) return;

      dragging.current = true;
      el.setPointerCapture(e.pointerId);

      function update(clientX: number) {
        const rect = el!.getBoundingClientRect();
        const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width));
        onChange(clamp(min + ratio * (max - min)));
      }

      update(e.clientX);

      function onMove(ev: PointerEvent) {
        if (dragging.current) update(ev.clientX);
      }
      function onUp() {
        dragging.current = false;
        el!.removeEventListener("pointermove", onMove);
        el!.removeEventListener("pointerup", onUp);
      }

      el.addEventListener("pointermove", onMove);
      el.addEventListener("pointerup", onUp);
    },
    [disabled, min, max, step, onChange]
  );

  return (
    <div className={`flex flex-col gap-2.5 ${disabled ? "opacity-40 pointer-events-none" : ""}`}>
      {/* Value row */}
      <div className="flex items-baseline justify-between gap-2">
        {editing ? (
          <input
            ref={inputRef}
            type="text"
            inputMode="numeric"
            defaultValue={value}
            autoFocus
            onFocus={(e) => { setRaw(String(value)); e.target.select(); }}
            onChange={(e) => setRaw(e.target.value)}
            onBlur={() => commitEdit(raw)}
            onKeyDown={(e) => {
              if (e.key === "Enter") { commitEdit(raw); }
              if (e.key === "Escape") { setEditing(false); }
            }}
            className="mono w-20 bg-transparent text-[15px] tabular-nums tracking-tight outline-none border-b border-[var(--color-accent)] text-[var(--color-text)]"
          />
        ) : (
          <button
            type="button"
            onClick={() => !disabled && setEditing(true)}
            title="Click to type a value"
            className="mono text-[15px] tabular-nums tracking-tight text-[var(--color-text)] hover:text-[var(--color-accent)] transition-colors cursor-text"
          >
            {value}
          </button>
        )}
        {suffix ? (
          <span className="tag text-[10px] text-[var(--color-text-faint)]" style={{ letterSpacing: "0.14em" }}>
            {suffix}
          </span>
        ) : null}
      </div>

      {/* Track */}
      <div
        ref={trackRef}
        onPointerDown={handleTrackPointer}
        className="group relative h-5 w-full cursor-pointer select-none"
        style={{ touchAction: "none" }}
      >
        {/* Rail */}
        <div className="absolute left-0 top-1/2 h-[2px] w-full -translate-y-1/2 bg-[var(--color-line-2)]" />
        {/* Fill */}
        <div
          className="absolute left-0 top-1/2 h-[2px] -translate-y-1/2 bg-[var(--color-accent)]"
          style={{
            width: `${pct}%`,
            boxShadow: "0 0 8px var(--color-accent)",
          }}
        />
        {/* Thumb — large hit area, small visual */}
        <div
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 flex items-center justify-center"
          style={{ left: `${pct}%` }}
        >
          {/* Outer ring shows on hover/drag */}
          <div className="absolute h-5 w-5 rounded-full bg-[var(--color-accent)]/10 scale-0 group-hover:scale-100 transition-transform" />
          {/* Inner diamond */}
          <div
            className="h-2.5 w-2.5 rotate-45 bg-[var(--color-accent)] border border-[var(--color-bg)]"
            style={{ boxShadow: "0 0 6px var(--color-accent)" }}
          />
        </div>

        {/* Tick marks at step intervals (sparse, decorative) */}
        <div className="absolute left-0 top-1/2 w-full -translate-y-1/2 pointer-events-none">
          {Array.from({ length: Math.min(10, Math.floor((max - min) / step)) + 1 }).map((_, i, arr) => {
            const tickPct = (i / (arr.length - 1)) * 100;
            return (
              <div
                key={i}
                className="absolute top-3 h-1 w-px bg-[var(--color-line-2)]"
                style={{ left: `${tickPct}%` }}
              />
            );
          })}
        </div>
      </div>

      {/* Min/max labels */}
      <div className="flex justify-between">
        <span className="mono text-[10px] text-[var(--color-text-faint)] tabular-nums">{min}</span>
        <span className="mono text-[10px] text-[var(--color-text-faint)] tabular-nums">{max}</span>
      </div>
    </div>
  );
}
