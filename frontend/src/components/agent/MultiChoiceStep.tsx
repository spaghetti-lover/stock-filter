"use client";

import { useEffect, useRef, useState } from "react";
import { BoxPanel } from "./BoxPanel";
import { KeyHint, type Choice } from "./ChoiceStep";

interface Props {
  stepLabel: string;
  title: string;
  description?: string;
  promptKey?: string;
  options: Choice[];
  defaultCodes?: string[];
  locked?: boolean;
  value?: string[];
  onSubmit: (codes: string[], labels: string[]) => void;
}

export function MultiChoiceStep({
  stepLabel,
  title,
  description,
  promptKey = "selected",
  options,
  defaultCodes,
  locked = false,
  value,
  onSubmit,
}: Props) {
  const [active, setActive] = useState(0);
  const [chosen, setChosen] = useState<Set<string>>(
    () => new Set(value ?? defaultCodes ?? options.map((o) => o.code)),
  );
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
        key !== " " &&
        key !== "a" &&
        key !== "A" &&
        key !== "Home" &&
        key !== "End"
      )
        return;
      e.preventDefault();
      if (key === "ArrowDown") {
        setActive((i) => (i + 1) % total);
        return;
      }
      if (key === "ArrowUp") {
        setActive((i) => (i - 1 + total) % total);
        return;
      }
      if (key === "Home") {
        setActive(0);
        return;
      }
      if (key === "End") {
        setActive(total - 1);
        return;
      }
      if (key === " ") {
        setChosen((prev) => {
          const next = new Set(prev);
          const code = options[active].code;
          if (next.has(code)) next.delete(code);
          else next.add(code);
          return next;
        });
        return;
      }
      if (key === "a" || key === "A") {
        setChosen((prev) =>
          prev.size === total ? new Set() : new Set(options.map((o) => o.code)),
        );
        return;
      }
      if (key === "Enter") {
        if (chosen.size === 0) return;
        const codes = options.filter((o) => chosen.has(o.code)).map((o) => o.code);
        const labels = options.filter((o) => chosen.has(o.code)).map((o) => o.label);
        onSubmit(codes, labels);
      }
    };
    window.addEventListener("keydown", handler);
    return () => {
      window.clearTimeout(armTimer);
      window.removeEventListener("keydown", handler);
    };
  }, [active, chosen, locked, onSubmit, options]);

  useEffect(() => {
    if (locked) return;
    tileRefs.current[active]?.scrollIntoView({ block: "nearest" });
  }, [active, locked]);

  const lockedLabels = (value ?? [])
    .map((c) => options.find((o) => o.code === c)?.label ?? c);

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
              <KeyHint keys={["space"]} label="toggle" mono={false} />
              <KeyHint keys={["a"]} label="all / none" mono={false} />
              <KeyHint keys={["↵"]} label="confirm" />
              <KeyHint keys={["click"]} label="toggle" mono={false} />
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
            <div className="flex flex-1 flex-wrap items-center gap-2 px-3 py-2.5 font-mono text-[13px] text-[var(--color-text)]">
              <span className="mono text-[11px] uppercase tracking-[0.2em] text-[var(--color-text-faint)]">
                done ({lockedLabels.length})
              </span>
              {lockedLabels.map((l) => (
                <span
                  key={l}
                  className="mono border border-[var(--color-line)] bg-[var(--color-surface-2)] px-2 py-0.5 text-[11.5px]"
                >
                  {l.toLowerCase()}
                </span>
              ))}
            </div>
            <span
              aria-hidden
              className="mono flex items-center gap-2 border-l border-[var(--color-line)] bg-[var(--color-surface)] px-4 text-[11px] uppercase tracking-[0.18em] text-[var(--color-ok)]"
            >
              <span>✓ confirmed</span>
            </span>
          </div>
        ) : (
          <>
            <ul
              className="flex flex-col border border-[var(--color-line)] bg-[var(--color-bg)]"
              role="listbox"
              aria-multiselectable
            >
              {options.map((opt, i) => {
                const isActive = i === active;
                const isChecked = chosen.has(opt.code);
                return (
                  <li
                    key={opt.code}
                    ref={(el) => {
                      tileRefs.current[i] = el;
                    }}
                    role="option"
                    aria-selected={isChecked}
                    onMouseEnter={() => setActive(i)}
                    onClick={() => {
                      setActive(i);
                      setChosen((prev) => {
                        const next = new Set(prev);
                        if (next.has(opt.code)) next.delete(opt.code);
                        else next.add(opt.code);
                        return next;
                      });
                    }}
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
                      aria-hidden
                      className="mono inline-flex h-[14px] w-[14px] items-center justify-center border text-[10px]"
                      style={{
                        borderColor: isChecked
                          ? "var(--color-accent)"
                          : "var(--color-line-2)",
                        background: isChecked
                          ? "var(--color-accent)"
                          : "transparent",
                        color: isChecked ? "#000" : "transparent",
                        boxShadow: isChecked
                          ? "0 0 8px color-mix(in srgb, var(--color-accent) 60%, transparent)"
                          : "none",
                      }}
                    >
                      ✓
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
            <div className="flex items-center justify-between gap-3">
              <span className="mono text-[11px] uppercase tracking-[0.2em] text-[var(--color-text-faint)]">
                {chosen.size === 0
                  ? "no selections"
                  : `${chosen.size} selection${chosen.size === 1 ? "" : "s"}`}
              </span>
              <button
                disabled={chosen.size === 0}
                onClick={() => {
                  const codes = options
                    .filter((o) => chosen.has(o.code))
                    .map((o) => o.code);
                  const labels = options
                    .filter((o) => chosen.has(o.code))
                    .map((o) => o.label);
                  onSubmit(codes, labels);
                }}
                className="mono border border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-1.5 text-[11px] uppercase tracking-[0.2em] text-[var(--color-text-dim)] transition-colors enabled:hover:border-[var(--color-accent)] enabled:hover:bg-[var(--color-accent)] enabled:hover:text-black disabled:opacity-45"
              >
                done ({chosen.size})
              </button>
            </div>
          </>
        )}
      </div>
    </BoxPanel>
  );
}
