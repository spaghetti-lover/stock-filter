"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { BoxPanel } from "./BoxPanel";

interface Props {
  symbol: string;
  date: string;
  locked?: boolean;
  value?: ReportAnswers;
  onSubmit: (answers: ReportAnswers) => void;
  onReset?: () => void;
  onViewReport?: () => void;
}

export interface ReportAnswers {
  saveReport: boolean;
  savePath: string;
  displayReport: boolean;
}

type SubStep = "save" | "path" | "display" | "done";

const YN_RE = /^(y|yes|n|no)?$/i;

function parseYn(raw: string, fallback: boolean): boolean {
  const v = raw.trim().toLowerCase();
  if (!v) return fallback;
  return v === "y" || v === "yes";
}

function fmtTimestamp(d: Date) {
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  return `${hh}${mm}${ss}`;
}

export function ReportStep({
  symbol,
  date,
  locked = false,
  value,
  onSubmit,
  onReset,
  onViewReport,
}: Props) {
  const sessionStamp = useMemo(() => {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}${mm}${dd}_${fmtTimestamp(d)}`;
  }, []);
  const defaultPath = `/home/appuser/app/reports/${symbol}_${sessionStamp}`;

  const [sub, setSub] = useState<SubStep>(value ? "done" : "save");
  const [saveReport, setSaveReport] = useState<boolean | null>(
    value ? value.saveReport : null,
  );
  const [savePath, setSavePath] = useState<string | null>(
    value ? value.savePath : null,
  );
  const [displayReport, setDisplayReport] = useState<boolean | null>(
    value ? value.displayReport : null,
  );

  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (locked) return;
    if (sub === "done") return;
    inputRef.current?.focus();
  }, [locked, sub]);

  useEffect(() => {
    setDraft("");
    setError(null);
  }, [sub]);

  const advanceSave = () => {
    if (!YN_RE.test(draft.trim())) {
      setError("expected · y / n (Enter for default: Y)");
      return;
    }
    const v = parseYn(draft, true);
    setSaveReport(v);
    if (!v) {
      // skip path prompt
      setSavePath("");
      setSub("display");
    } else {
      setSub("path");
    }
  };

  const advancePath = () => {
    const v = draft.trim() || defaultPath;
    setSavePath(v);
    setSub("display");
  };

  const advanceDisplay = () => {
    if (!YN_RE.test(draft.trim())) {
      setError("expected · y / n (Enter for default: Y)");
      return;
    }
    const v = parseYn(draft, true);
    setDisplayReport(v);
    setSub("done");
    onSubmit({
      saveReport: saveReport ?? true,
      savePath: savePath ?? "",
      displayReport: v,
    });
  };

  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") return;
    if (sub === "save") advanceSave();
    else if (sub === "path") advancePath();
    else if (sub === "display") advanceDisplay();
  };

  const tone = locked ? "muted" : sub === "done" ? "muted" : "accent";

  return (
    <BoxPanel title="Step 10 · Analysis Complete" tone={tone}>
      <div className="flex flex-col gap-5">
        <div className="flex flex-col gap-1">
          <p
            className="display text-[18px] tracking-tight"
            style={{ color: "var(--color-ok)" }}
          >
            Analysis Complete!
          </p>
          <p className="text-[13px] text-[var(--color-text-dim)]">
            The multi-agent pipeline has finished for{" "}
            <span className="mono text-[var(--color-text)]">{symbol}</span> on{" "}
            <span className="mono text-[var(--color-text)]">{date}</span>. Tell
            the runner what to do with the report.
          </p>
        </div>

        <div className="flex flex-col gap-2 border border-[var(--color-line)] bg-[var(--color-bg)] px-4 py-4">
          <TranscriptLine
            prompt="Save report?"
            hint="[Y]"
            answer={saveReport === null ? null : saveReport ? "Y" : "N"}
          />
          {saveReport ? (
            <TranscriptLine
              prompt="Save path (press Enter for default)"
              hint={`[${defaultPath}]`}
              answer={savePath ?? null}
            />
          ) : saveReport === false ? (
            <TranscriptLine
              prompt="Save path"
              hint="skipped"
              answer="—"
              dim
            />
          ) : null}
          {sub === "done" || displayReport !== null ? (
            <TranscriptLine
              prompt="Display full report on screen?"
              hint="[Y]"
              answer={displayReport === null ? null : displayReport ? "Y" : "N"}
            />
          ) : null}

          {sub !== "done" && !locked ? (
            <ActivePrompt
              label={
                sub === "save"
                  ? "Save report?"
                  : sub === "path"
                    ? "Save path (press Enter for default)"
                    : "Display full report on screen?"
              }
              hint={
                sub === "save"
                  ? "[Y]"
                  : sub === "path"
                    ? `[${defaultPath}]`
                    : "[Y]"
              }
              draft={draft}
              setDraft={(v) => {
                setDraft(v);
                if (error) setError(null);
              }}
              inputRef={inputRef}
              onKey={onKey}
              onConfirm={() => {
                if (sub === "save") advanceSave();
                else if (sub === "path") advancePath();
                else advanceDisplay();
              }}
              placeholder={sub === "path" ? defaultPath : "y / n"}
            />
          ) : null}
        </div>

        {error ? (
          <p
            className="mono text-[11px] uppercase tracking-[0.2em]"
            style={{ color: "var(--color-danger)" }}
          >
            ! {error}
          </p>
        ) : null}

        {sub === "done" ? (
          <div className="flex flex-col gap-3 border border-dashed border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-3">
            {saveReport && savePath ? (
              <p
                className="mono text-[12px]"
                style={{ color: "var(--color-ok)" }}
              >
                ✓ Report saved to:{" "}
                <span className="text-[var(--color-text)]">{savePath}</span>
              </p>
            ) : (
              <p
                className="mono text-[12px]"
                style={{ color: "var(--color-text-faint)" }}
              >
                · Report not saved
              </p>
            )}
            <p
              className="mono text-[12px]"
              style={{
                color: displayReport
                  ? "var(--color-accent)"
                  : "var(--color-text-faint)",
              }}
            >
              {displayReport
                ? "↳ Full report displayed on screen"
                : "· On-screen report skipped"}
            </p>
            <div className="mt-1 flex flex-wrap gap-2">
              {displayReport && onViewReport ? (
                <button
                  onClick={onViewReport}
                  className="mono self-start border border-[var(--color-accent)] bg-[var(--color-surface)] px-4 py-2 text-[11px] uppercase tracking-[0.2em] transition-colors hover:bg-[var(--color-accent)] hover:text-black"
                  style={{ color: "var(--color-accent)" }}
                >
                  view full report ↗
                </button>
              ) : null}
              {onReset ? (
                <button
                  onClick={onReset}
                  className="mono self-start border border-[var(--color-line)] px-4 py-2 text-[11px] uppercase tracking-[0.2em] text-[var(--color-text-dim)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
                >
                  restart intake ↺
                </button>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
    </BoxPanel>
  );
}

function TranscriptLine({
  prompt,
  hint,
  answer,
  dim = false,
}: {
  prompt: string;
  hint: string;
  answer: string | null;
  dim?: boolean;
}) {
  if (answer === null) return null;
  return (
    <div className="mono flex flex-wrap items-baseline gap-2 text-[12.5px]">
      <span
        aria-hidden
        style={{ color: dim ? "var(--color-text-faint)" : "var(--color-accent)" }}
      >
        ›
      </span>
      <span
        style={{
          color: dim ? "var(--color-text-faint)" : "var(--color-text-dim)",
        }}
      >
        {prompt}
      </span>
      <span className="text-[var(--color-text-faint)]">{hint}:</span>
      <span
        className="text-[var(--color-text)]"
        style={{ color: dim ? "var(--color-text-faint)" : undefined }}
      >
        {answer}
      </span>
    </div>
  );
}

interface ActivePromptProps {
  label: string;
  hint: string;
  draft: string;
  setDraft: (v: string) => void;
  inputRef: React.MutableRefObject<HTMLInputElement | null>;
  onKey: (e: React.KeyboardEvent<HTMLInputElement>) => void;
  onConfirm: () => void;
  placeholder: string;
}

function ActivePrompt({
  label,
  hint,
  draft,
  setDraft,
  inputRef,
  onKey,
  onConfirm,
  placeholder,
}: ActivePromptProps) {
  return (
    <div
      className="flex items-stretch border border-[var(--color-line)] bg-[var(--color-bg)]"
      style={{
        boxShadow:
          "inset 0 0 0 1px color-mix(in srgb, var(--color-accent) 24%, transparent)",
      }}
    >
      <span
        className="mono flex items-center gap-2 border-r border-[var(--color-line)] bg-[var(--color-surface-2)] px-3 text-[12px]"
        style={{ color: "var(--color-accent)" }}
      >
        <span aria-hidden>›</span>
        <span className="text-[var(--color-text-dim)]">{label}</span>
        <span className="text-[var(--color-text-faint)]">{hint}</span>
        <span aria-hidden>:</span>
      </span>
      <input
        ref={inputRef}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={onKey}
        placeholder={placeholder}
        spellCheck={false}
        autoComplete="off"
        className="flex-1 bg-transparent px-3 py-3 font-mono text-[14px] tracking-wide text-[var(--color-text)] caret-[var(--color-accent)] outline-none placeholder:text-[var(--color-text-faint)]/60"
      />
      <button
        onClick={onConfirm}
        className="group mono flex items-center gap-2 border-l border-[var(--color-line)] bg-[var(--color-surface)] px-4 text-[11px] uppercase tracking-[0.18em] text-[var(--color-text-dim)] transition-colors hover:bg-[var(--color-accent)] hover:text-black"
      >
        <span>enter</span>
        <span aria-hidden className="transition-transform group-hover:translate-x-0.5">
          ↵
        </span>
      </button>
    </div>
  );
}
