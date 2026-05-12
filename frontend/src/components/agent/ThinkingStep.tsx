"use client";

import { useEffect, useRef, useState } from "react";
import { BoxPanel } from "./BoxPanel";
import { KeyHint, type Choice } from "./ChoiceStep";

interface Props {
  stepLabel: string;
  title: string;
  description?: string;
  quickOptions: Choice[];
  deepOptions: Choice[];
  locked?: boolean;
  value?: { quick: string; deep: string };
  onSubmit: (
    quick: { code: string; label: string },
    deep: { code: string; label: string },
  ) => void;
}

type Phase = "quick" | "deep";

export function ThinkingStep({
  stepLabel,
  title,
  description,
  quickOptions,
  deepOptions,
  locked = false,
  value,
  onSubmit,
}: Props) {
  const [phase, setPhase] = useState<Phase>("quick");
  const [quickIdx, setQuickIdx] = useState(0);
  const [deepIdx, setDeepIdx] = useState(0);
  const [picked, setPicked] = useState<{ quick?: Choice; deep?: Choice }>({});
  const tileRefs = useRef<(HTMLLIElement | null)[]>([]);

  const activeOptions = phase === "quick" ? quickOptions : deepOptions;
  const activeIdx = phase === "quick" ? quickIdx : deepIdx;
  const setActiveIdx = phase === "quick" ? setQuickIdx : setDeepIdx;

  useEffect(() => {
    if (locked) return;
    let armed = false;
    const armTimer = window.setTimeout(() => {
      armed = true;
    }, 120);
    const total = activeOptions.length;
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
      if (key === "ArrowDown") {
        setActiveIdx((i) => (i + 1) % total);
        return;
      }
      if (key === "ArrowUp") {
        setActiveIdx((i) => (i - 1 + total) % total);
        return;
      }
      if (key === "Home") {
        setActiveIdx(0);
        return;
      }
      if (key === "End") {
        setActiveIdx(total - 1);
        return;
      }
      if (key === "Enter") {
        const opt = activeOptions[activeIdx];
        if (phase === "quick") {
          setPicked((p) => ({ ...p, quick: opt }));
          setPhase("deep");
        } else {
          const quick = picked.quick!;
          onSubmit(
            { code: quick.code, label: quick.label },
            { code: opt.code, label: opt.label },
          );
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => {
      window.clearTimeout(armTimer);
      window.removeEventListener("keydown", handler);
    };
  }, [
    activeIdx,
    activeOptions,
    locked,
    onSubmit,
    phase,
    picked.quick,
    setActiveIdx,
  ]);

  useEffect(() => {
    if (locked) return;
    tileRefs.current[activeIdx]?.scrollIntoView({ block: "nearest" });
  }, [activeIdx, locked, phase]);

  const lockedQuick = quickOptions.find((o) => o.code === value?.quick);
  const lockedDeep = deepOptions.find((o) => o.code === value?.deep);

  return (
    <BoxPanel title={stepLabel} tone={locked ? "muted" : "accent"}>
      <div className="flex flex-col gap-5">
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

        {/* Quick-Thinking */}
        <SubBlock
          label="Quick-Thinking LLM Engine"
          confirmed={picked.quick ?? lockedQuick}
        >
          {locked || picked.quick ? null : (
            <PickerList
              options={quickOptions}
              activeIdx={activeIdx}
              tileRefs={tileRefs}
              onHover={setActiveIdx}
              onPick={(opt) => {
                setPicked((p) => ({ ...p, quick: opt }));
                setPhase("deep");
                setDeepIdx(0);
              }}
              show={phase === "quick"}
            />
          )}
        </SubBlock>

        {/* Deep-Thinking */}
        <SubBlock
          label="Deep-Thinking LLM Engine"
          confirmed={locked ? lockedDeep : undefined}
        >
          {locked ? null : phase === "deep" ? (
            <PickerList
              options={deepOptions}
              activeIdx={activeIdx}
              tileRefs={tileRefs}
              onHover={setActiveIdx}
              onPick={(opt) => {
                const quick = picked.quick!;
                onSubmit(
                  { code: quick.code, label: quick.label },
                  { code: opt.code, label: opt.label },
                );
              }}
              show
            />
          ) : (
            <p className="mono px-1 text-[11px] uppercase tracking-[0.2em] text-[var(--color-text-faint)]">
              — awaiting quick-thinking choice
            </p>
          )}
        </SubBlock>
      </div>
    </BoxPanel>
  );
}

function SubBlock({
  label,
  confirmed,
  children,
}: {
  label: string;
  confirmed?: Choice;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-3">
        <span
          className="mono text-[10.5px] uppercase tracking-[0.24em]"
          style={{
            color: confirmed
              ? "var(--color-ok)"
              : "var(--color-text-dim)",
          }}
        >
          {confirmed ? "✓" : "?"} {label}
        </span>
        {confirmed ? (
          <span className="mono text-[12.5px] text-[var(--color-accent)]">
            {confirmed.label}
            {confirmed.hint ? (
              <span className="text-[var(--color-text-faint)]">
                {" "}
                — {confirmed.hint}
              </span>
            ) : null}
          </span>
        ) : null}
      </div>
      {children}
    </div>
  );
}

function PickerList({
  options,
  activeIdx,
  tileRefs,
  onHover,
  onPick,
  show,
}: {
  options: Choice[];
  activeIdx: number;
  tileRefs: React.MutableRefObject<(HTMLLIElement | null)[]>;
  onHover: (i: number) => void;
  onPick: (opt: Choice) => void;
  show: boolean;
}) {
  if (!show) return null;
  return (
    <ul
      className="flex flex-col border border-[var(--color-line)] bg-[var(--color-bg)]"
      role="listbox"
    >
      {options.map((opt, i) => {
        const isActive = i === activeIdx;
        return (
          <li
            key={opt.code}
            ref={(el) => {
              tileRefs.current[i] = el;
            }}
            role="option"
            aria-selected={isActive}
            onMouseEnter={() => onHover(i)}
            onClick={() => onPick(opt)}
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
                color: isActive ? "var(--color-accent)" : "transparent",
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
  );
}
