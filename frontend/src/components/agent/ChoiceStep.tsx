"use client";

import { useEffect, useRef, useState } from "react";
import { BoxPanel } from "./BoxPanel";

export interface Choice {
  code: string;
  label: string;
  hint?: string;
  description?: string;
  badge?: string;
}

interface Props {
  stepLabel: string;
  title: string;
  description?: string;
  promptKey?: string;
  options: Choice[];
  defaultCode?: string;
  locked?: boolean;
  value?: string;
  onSubmit: (code: string, label: string) => void;
}

export function ChoiceStep({
  stepLabel,
  title,
  description,
  promptKey = "select",
  options,
  defaultCode,
  locked = false,
  value,
  onSubmit,
}: Props) {
  const initial = Math.max(
    0,
    options.findIndex((o) => o.code === (value ?? defaultCode)),
  );
  const [active, setActive] = useState(initial >= 0 ? initial : 0);
  const tileRefs = useRef<(HTMLLIElement | null)[]>([]);

  useEffect(() => {
    if (locked) return;
    let armed = false;
    const armTimer = window.setTimeout(() => {
      armed = true;
    }, 120);
    const total = options.length;
    const handler = (e: KeyboardEvent) => {
      if (!armed) return;
      const key = e.key;
      if (
        key !== "ArrowDown" &&
        key !== "ArrowUp" &&
        key !== "Enter" &&
        key !== "Home" &&
        key !== "End"
      )
        return;
      e.preventDefault();
      if (key === "Enter") {
        const opt = options[active];
        onSubmit(opt.code, opt.label);
        return;
      }
      setActive((i) => {
        if (key === "Home") return 0;
        if (key === "End") return total - 1;
        if (key === "ArrowDown") return (i + 1) % total;
        if (key === "ArrowUp") return (i - 1 + total) % total;
        return i;
      });
    };
    window.addEventListener("keydown", handler);
    return () => {
      window.clearTimeout(armTimer);
      window.removeEventListener("keydown", handler);
    };
  }, [active, locked, onSubmit, options]);

  useEffect(() => {
    if (locked) return;
    tileRefs.current[active]?.scrollIntoView({ block: "nearest" });
  }, [active, locked]);

  const selected = options.find((o) => o.code === value);

  return (
    <BoxPanel title={stepLabel} tone={locked ? "muted" : "accent"}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <p className="display text-[18px] tracking-tight">{title}</p>
          {description ? (
            <p className="text-[13px] text-[var(--color-text-dim)]">
              {description}
            </p>
          ) : null}
          {!locked ? (
            <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1">
              <KeyHint keys={["↑", "↓"]} label="navigate" />
              <KeyHint keys={["↵"]} label="select" />
              <KeyHint keys={["click"]} label="pick" mono={false} />
            </div>
          ) : null}
        </div>

        {locked ? (
          <div className="flex items-stretch border border-[var(--color-line)] bg-[var(--color-bg)]">
            <span
              className="mono flex items-center gap-2 border-r border-[var(--color-line)] bg-[var(--color-surface-2)] px-3 text-[12px]"
              style={{ color: "var(--color-accent)" }}
            >
              <span aria-hidden>›</span>
              <span>{promptKey}</span>
              <span aria-hidden>:</span>
            </span>
            <div className="flex-1 px-3 py-3 font-mono text-[14px] tracking-wide text-[var(--color-text)]">
              {selected?.label ?? value ?? "—"}
              {selected?.hint ? (
                <span className="ml-2 text-[var(--color-text-faint)]">
                  — {selected.hint}
                </span>
              ) : null}
            </div>
            <span
              aria-hidden
              className="mono flex items-center gap-2 border-l border-[var(--color-line)] bg-[var(--color-surface)] px-4 text-[11px] uppercase tracking-[0.18em] text-[var(--color-ok)]"
            >
              <span>✓ confirmed</span>
            </span>
          </div>
        ) : (
          <ul
            className="flex flex-col border border-[var(--color-line)] bg-[var(--color-bg)]"
            role="listbox"
          >
            {options.map((opt, i) => {
              const isActive = i === active;
              return (
                <li
                  key={opt.code}
                  ref={(el) => {
                    tileRefs.current[i] = el;
                  }}
                  role="option"
                  aria-selected={isActive}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => onSubmit(opt.code, opt.label)}
                  className="group relative flex cursor-pointer items-baseline gap-2 px-4 py-1.5 transition-colors"
                  style={
                    isActive
                      ? {
                          background:
                            "color-mix(in srgb, var(--color-accent) 12%, transparent)",
                        }
                      : undefined
                  }
                >
                  {isActive ? (
                    <span
                      aria-hidden
                      className="pointer-events-none absolute inset-y-0 left-0 w-[2px]"
                      style={{
                        background: "var(--color-accent)",
                        boxShadow: "0 0 10px var(--color-accent)",
                      }}
                    />
                  ) : null}
                  <span
                    aria-hidden
                    className="mono w-3 text-[13px]"
                    style={{
                      color: isActive
                        ? "var(--color-accent)"
                        : "transparent",
                    }}
                  >
                    »
                  </span>
                  <span
                    className="mono text-[13.5px] leading-[1.5]"
                    style={{
                      color: isActive
                        ? "var(--color-accent)"
                        : "var(--color-text)",
                      fontWeight: isActive ? 600 : 500,
                    }}
                  >
                    {opt.label}
                  </span>
                  {opt.badge ? (
                    <span
                      className="mono text-[10px] uppercase tracking-[0.18em]"
                      style={{
                        color: isActive
                          ? "color-mix(in srgb, var(--color-accent) 85%, white)"
                          : "var(--color-text-faint)",
                      }}
                    >
                      [{opt.badge}]
                    </span>
                  ) : null}
                  {opt.hint ? (
                    <span
                      className="mono text-[12.5px] leading-[1.5]"
                      style={{
                        color: isActive
                          ? "color-mix(in srgb, var(--color-accent) 70%, var(--color-text-dim))"
                          : "var(--color-text-faint)",
                      }}
                    >
                      — {opt.hint}
                    </span>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </BoxPanel>
  );
}

export function KeyHint({
  keys,
  label,
  mono = true,
}: {
  keys: string[];
  label: string;
  mono?: boolean;
}) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="flex items-center gap-1">
        {keys.map((k) => (
          <kbd
            key={k}
            className={`${mono ? "mono" : ""} inline-flex min-w-[1.5em] items-center justify-center border border-[var(--color-line)] bg-[var(--color-surface-2)] px-1.5 py-px text-[10px] uppercase tracking-[0.08em] text-[var(--color-text-dim)]`}
          >
            {k}
          </kbd>
        ))}
      </span>
      <span className="mono text-[10px] uppercase tracking-[0.22em] text-[var(--color-text-faint)]">
        {label}
      </span>
    </span>
  );
}
