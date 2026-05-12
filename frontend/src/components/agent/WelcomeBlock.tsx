"use client";

import { useEffect, useState } from "react";
import { AsciiBanner } from "./AsciiBanner";
import { BoxPanel } from "./BoxPanel";
import { fetchAnnouncements } from "@/lib/tradingAgent";

const STEPS = [
  { numeral: "I", label: "Analyst Team" },
  { numeral: "II", label: "Research Team" },
  { numeral: "III", label: "Trader" },
  { numeral: "IV", label: "Risk Management" },
  { numeral: "V", label: "Portfolio Management" },
];

export function WelcomeBlock() {
  const [announcements, setAnnouncements] = useState<string[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchAnnouncements()
      .then((data) => {
        if (cancelled) return;
        setAnnouncements(data.announcements ?? []);
      })
      .catch(() => {
        if (cancelled) return;
        setAnnouncements([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-8">
      <BoxPanel title="Welcome · TradingAgents" tone="accent">
        <div className="flex flex-col items-center gap-6 py-2 text-center">
          <AsciiBanner />
          <div className="flex flex-col gap-2">
            <p className="mono text-[11px] uppercase tracking-[0.28em] text-[var(--color-text-dim)]">
              Multi-Agents LLM Financial Trading Framework
            </p>
          </div>

          <div className="mt-2 flex w-full max-w-[820px] flex-col items-stretch gap-3">
            <span className="tag text-left">Workflow</span>
            <ol className="flex flex-wrap items-center justify-center gap-x-1 gap-y-2">
              {STEPS.map((s, i) => (
                <li key={s.numeral} className="flex items-center gap-2">
                  <span
                    className="mono text-[10px] uppercase tracking-[0.2em]"
                    style={{ color: "var(--color-accent)" }}
                  >
                    {s.numeral}.
                  </span>
                  <span className="text-[13px] text-[var(--color-text)]">
                    {s.label}
                  </span>
                  {i < STEPS.length - 1 ? (
                    <span
                      aria-hidden
                      className="mono px-1 text-[12px] text-[var(--color-text-faint)]"
                    >
                      →
                    </span>
                  ) : null}
                </li>
              ))}
            </ol>
          </div>
        </div>
      </BoxPanel>

      <BoxPanel title="Announcements" tone="muted">
        <div className="flex flex-col gap-2">
          {announcements === null ? (
            <p className="mono text-[12px] text-[var(--color-text-faint)]">
              · fetching announcements…
            </p>
          ) : announcements.length === 0 ? (
            <p className="mono text-[12px] text-[var(--color-text-faint)]">
              · no announcements
            </p>
          ) : (
            announcements.map((line, i) => (
              <p key={i} className="text-[13px] text-[var(--color-text-dim)]">
                {line}
              </p>
            ))
          )}
        </div>
      </BoxPanel>
    </div>
  );
}
