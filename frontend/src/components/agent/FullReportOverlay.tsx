"use client";

import { useEffect, useState } from "react";
import { Markdown } from "@/components/chat/Markdown";
import type { RunReports } from "@/lib/tradingAgent";

type ReportRenderMode = "markdown" | "raw";

interface Props {
  open: boolean;
  onClose: () => void;
  reports?: RunReports | null;
  ticker?: string;
  analysisDate?: string;
  loading?: boolean;
  error?: string | null;
}

const SECTIONS: { key: keyof RunReports; label: string }[] = [
  { key: "market_report", label: "Market Analyst" },
  { key: "sentiment_report", label: "Social Analyst" },
  { key: "news_report", label: "News Analyst" },
  { key: "fundamentals_report", label: "Fundamentals Analyst" },
  { key: "investment_plan", label: "Research Team Decision" },
  { key: "trader_investment_plan", label: "Trader" },
  { key: "final_trade_decision", label: "Portfolio Manager" },
];

export function FullReportOverlay({
  open,
  onClose,
  reports,
  ticker,
  analysisDate,
  loading = false,
  error = null,
}: Props) {
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  const [mode, setMode] = useState<ReportRenderMode>("markdown");

  if (!open) return null;

  const filledSections = SECTIONS.filter(
    (s) => reports && reports[s.key] && reports[s.key]!.trim().length > 0,
  );

  return (
    <div
      className="fixed inset-0 z-[60] flex flex-col"
      role="dialog"
      aria-modal="true"
      aria-label="Full analysis report"
      style={{ background: "var(--color-bg)" }}
    >
      <header className="flex items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-surface)] px-6 py-3">
        <div className="flex items-center gap-3">
          <span className="mono text-[10px] uppercase tracking-[0.24em] text-[var(--color-text-faint)]">
            ~/TradingAgents
          </span>
          <span
            aria-hidden
            className="block h-2 w-2"
            style={{
              background: error ? "var(--color-warn)" : "var(--color-ok)",
              boxShadow: `0 0 10px ${error ? "var(--color-warn)" : "var(--color-ok)"}`,
            }}
          />
          <span className="mono text-[11px] uppercase tracking-[0.22em] text-[var(--color-text-dim)]">
            {error
              ? "full report · failed"
              : loading
                ? "full report · loading"
                : "full report · ready"}
          </span>
          {ticker || analysisDate ? (
            <span className="mono text-[11px] uppercase tracking-[0.22em] text-[var(--color-text-dim)]">
              · {ticker} {analysisDate ? `· ${analysisDate}` : ""}
            </span>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <div
            className="mono flex items-stretch overflow-hidden border border-[var(--color-line)] text-[10px] uppercase tracking-[0.2em]"
            role="group"
            aria-label="Report render mode"
          >
            {(["markdown", "raw"] as ReportRenderMode[]).map((m) => {
              const active = mode === m;
              return (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  aria-pressed={active}
                  className="px-3 py-1.5 transition-colors"
                  style={{
                    background: active ? "var(--color-accent)" : "transparent",
                    color: active ? "var(--color-bg)" : "var(--color-text-dim)",
                  }}
                >
                  {m}
                </button>
              );
            })}
          </div>
          <button
            onClick={onClose}
            className="mono border border-[var(--color-line)] px-3 py-1.5 text-[11px] uppercase tracking-[0.2em] text-[var(--color-text-dim)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
          >
            close · esc
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-[1100px] flex-col gap-8 px-6 py-10">
          <ReportTitle />

          {loading ? (
            <p className="mono text-center text-[12px] text-[var(--color-text-dim)]">
              · fetching report…
            </p>
          ) : error ? (
            <p
              className="mono text-center text-[12px]"
              style={{ color: "var(--color-warn)" }}
            >
              ! {error}
            </p>
          ) : filledSections.length === 0 ? (
            <p className="mono text-center text-[12px] text-[var(--color-text-faint)]">
              · no report available
            </p>
          ) : (
            filledSections.map((s) => (
              <ReportSection
                key={s.key}
                name={s.label}
                body={reports![s.key]!}
                accent={s.key === "final_trade_decision"}
                mode={mode}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function ReportTitle() {
  return (
    <div className="flex items-center gap-4">
      <span aria-hidden className="h-px flex-1 bg-[var(--color-line)]" />
      <span
        className="mono text-[12px] uppercase tracking-[0.28em]"
        style={{ color: "var(--color-text-dim)" }}
      >
        Complete Analysis Report
      </span>
      <span aria-hidden className="h-px flex-1 bg-[var(--color-line)]" />
    </div>
  );
}

function ReportSection({
  name,
  body,
  accent = false,
  mode,
}: {
  name: string;
  body: string;
  accent?: boolean;
  mode: ReportRenderMode;
}) {
  return (
    <section
      className="relative border bg-[var(--color-bg)]"
      style={{
        borderColor: accent ? "var(--color-accent)" : "var(--color-line)",
        boxShadow: accent
          ? "inset 0 0 0 1px color-mix(in srgb, var(--color-accent) 16%, transparent)"
          : undefined,
      }}
    >
      <div
        className="pointer-events-none absolute left-6 -top-2 px-2"
        style={{ background: "var(--color-bg)" }}
      >
        <span
          className="mono text-[10px] uppercase tracking-[0.24em]"
          style={{ color: accent ? "var(--color-accent)" : "var(--color-text-dim)" }}
        >
          {name}
        </span>
      </div>
      {mode === "markdown" ? (
        <div className="px-5 py-6">
          <Markdown>{body}</Markdown>
        </div>
      ) : (
        <pre className="whitespace-pre-wrap px-5 py-6 font-mono text-[12.5px] leading-[1.65] text-[var(--color-text)]">
          {body}
        </pre>
      )}
    </section>
  );
}
