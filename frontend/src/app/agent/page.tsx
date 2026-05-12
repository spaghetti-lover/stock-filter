"use client";

import { useMemo, useState } from "react";
import { WelcomeBlock } from "@/components/agent/WelcomeBlock";
import { SymbolStep } from "@/components/agent/SymbolStep";
import { DateStep } from "@/components/agent/DateStep";
import { ChoiceStep } from "@/components/agent/ChoiceStep";
import { MultiChoiceStep } from "@/components/agent/MultiChoiceStep";
import { ThinkingStep } from "@/components/agent/ThinkingStep";
import { ReportStep, type ReportAnswers } from "@/components/agent/ReportStep";
import { RunningStep } from "@/components/agent/RunningStep";
import { FullReportOverlay } from "@/components/agent/FullReportOverlay";
import {
  ANALYSTS,
  EFFORT_LEVELS,
  LLM_PROVIDERS,
  PROVIDER_ENGINES,
  RESEARCH_DEPTH,
} from "@/components/agent/catalog";

const LANGUAGES = [
  { code: "en", label: "English", hint: "default" },
  { code: "zh", label: "Chinese", hint: "中文" },
  { code: "ja", label: "Japanese", hint: "日本語" },
  { code: "ko", label: "Korean", hint: "한국어" },
  { code: "hi", label: "Hindi", hint: "हिन्दी" },
  { code: "es", label: "Spanish", hint: "Español" },
  { code: "pt", label: "Portuguese", hint: "Português" },
  { code: "fr", label: "French", hint: "Français" },
  { code: "de", label: "German", hint: "Deutsch" },
  { code: "ar", label: "Arabic", hint: "العربية" },
  { code: "ru", label: "Russian", hint: "Русский" },
  { code: "vi", label: "Vietnamese", hint: "Tiếng Việt" },
  { code: "custom", label: "Custom language" },
];

const TODAY_ISO = (() => {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
})();

type StepKey =
  | "symbol"
  | "date"
  | "language"
  | "analysts"
  | "depth"
  | "provider"
  | "thinking"
  | "effort"
  | "ready"
  | "running"
  | "report"
  | "complete";

const ORDER: StepKey[] = [
  "symbol",
  "date",
  "language",
  "analysts",
  "depth",
  "provider",
  "thinking",
  "effort",
  "ready",
  "running",
  "report",
  "complete",
];

const PROGRESS = [
  { key: "symbol", label: "Ticker" },
  { key: "date", label: "Date" },
  { key: "language", label: "Lang" },
  { key: "analysts", label: "Team" },
  { key: "depth", label: "Depth" },
  { key: "provider", label: "Provider" },
  { key: "thinking", label: "Thinking" },
  { key: "effort", label: "Effort" },
  { key: "running", label: "Run" },
  { key: "report", label: "Report" },
] as const;

const STATUS_LABEL: Record<StepKey, string> = {
  symbol: "awaiting ticker",
  date: "awaiting date",
  language: "awaiting language",
  analysts: "awaiting team",
  depth: "awaiting depth",
  provider: "awaiting provider",
  thinking: "awaiting thinking agents",
  effort: "awaiting effort",
  ready: "ready · primed",
  running: "pipeline · live",
  report: "awaiting report ack",
  complete: "session complete",
};

export default function AgentPage() {
  const [step, setStep] = useState<StepKey>("symbol");
  const [symbol, setSymbol] = useState<string | null>(null);
  const [date, setDate] = useState<string | null>(null);
  const [language, setLanguage] = useState<{ code: string; label: string } | null>(null);
  const [analysts, setAnalysts] = useState<{ codes: string[]; labels: string[] } | null>(null);
  const [depth, setDepth] = useState<{ code: string; label: string } | null>(null);
  const [provider, setProvider] = useState<{ code: string; label: string } | null>(null);
  const [thinking, setThinking] = useState<{
    quick: { code: string; label: string };
    deep: { code: string; label: string };
  } | null>(null);
  const [effort, setEffort] = useState<{ code: string; label: string } | null>(null);
  const [report, setReport] = useState<ReportAnswers | null>(null);
  const [showFullReport, setShowFullReport] = useState(false);

  const reset = () => {
    setStep("symbol");
    setSymbol(null);
    setDate(null);
    setLanguage(null);
    setAnalysts(null);
    setDepth(null);
    setProvider(null);
    setThinking(null);
    setEffort(null);
    setReport(null);
    setShowFullReport(false);
  };

  const advance = (next: StepKey) => setStep(next);

  const engines = useMemo(
    () => (provider ? PROVIDER_ENGINES[provider.code] : null),
    [provider],
  );

  const shouldRender = (key: StepKey) =>
    ORDER.indexOf(step) >= ORDER.indexOf(key);

  return (
    <div className="relative">
      <div className="hairline-grid border-b border-[var(--color-line)]">
        <div className="mx-auto flex max-w-[1080px] flex-col gap-3 px-8 pb-10 pt-12">
          <div className="flex items-center gap-3 text-[var(--color-text-dim)]">
            <span className="mono text-[10px]">AGNT/00</span>
            <span className="tag">Trading agent · session</span>
          </div>
          <div className="flex items-end justify-between gap-6">
            <h1
              className="display text-[40px] leading-[0.95] tracking-tight md:text-[48px]"
              style={{ fontVariationSettings: '"opsz" 144, "SOFT" 30' }}
            >
              Initialize a trading session.
            </h1>
            <StatusTicker step={step} />
          </div>
          <p className="max-w-[64ch] text-[13px] text-[var(--color-text-dim)]">
            A CLI-style intake that primes the multi-agent pipeline. Answer each
            prompt; the next reveals only after the current step is confirmed.
          </p>
        </div>
      </div>

      <div className="mx-auto flex max-w-[1080px] flex-col gap-12 px-8 py-14">
        <WelcomeBlock />

        <div className="relative pt-3">
          <ProgressRail step={step} />

          <div className="flex flex-col gap-10">
            <SymbolStep
              defaultValue="SPY"
              locked={step !== "symbol"}
              value={symbol ?? undefined}
              onSubmit={(v) => {
                setSymbol(v);
                advance("date");
              }}
            />

            {shouldRender("date") ? (
              <DateStep
                defaultValue={TODAY_ISO}
                locked={step !== "date"}
                value={date ?? undefined}
                onSubmit={(v) => {
                  setDate(v);
                  advance("language");
                }}
              />
            ) : null}

            {shouldRender("language") ? (
              <ChoiceStep
                stepLabel="Step 03 · Output Language"
                title="Output Language"
                description="Select the language for analyst reports and final decision."
                promptKey="lang"
                options={LANGUAGES}
                defaultCode="en"
                locked={step !== "language"}
                value={language?.code}
                onSubmit={(code, label) => {
                  setLanguage({ code, label });
                  advance("analysts");
                }}
              />
            ) : null}

            {shouldRender("analysts") ? (
              <MultiChoiceStep
                stepLabel="Step 04 · Analysts Team"
                title="Analysts Team"
                description="Select your LLM analyst agents for the analysis."
                promptKey="analysts"
                options={ANALYSTS}
                defaultCodes={["market", "social", "news", "fundamentals"]}
                locked={step !== "analysts"}
                value={analysts?.codes}
                onSubmit={(codes, labels) => {
                  setAnalysts({ codes, labels });
                  advance("depth");
                }}
              />
            ) : null}

            {shouldRender("depth") ? (
              <ChoiceStep
                stepLabel="Step 05 · Research Depth"
                title="Research Depth"
                description="Select your research depth level."
                promptKey="depth"
                options={RESEARCH_DEPTH}
                defaultCode="shallow"
                locked={step !== "depth"}
                value={depth?.code}
                onSubmit={(code, label) => {
                  setDepth({ code, label });
                  advance("provider");
                }}
              />
            ) : null}

            {shouldRender("provider") ? (
              <ChoiceStep
                stepLabel="Step 06 · LLM Provider"
                title="LLM Provider"
                description="Select your LLM provider."
                promptKey="provider"
                options={LLM_PROVIDERS}
                defaultCode="anthropic"
                locked={step !== "provider"}
                value={provider?.code}
                onSubmit={(code, label) => {
                  setProvider({ code, label });
                  setThinking(null);
                  advance("thinking");
                }}
              />
            ) : null}

            {shouldRender("thinking") && engines ? (
              <ThinkingStep
                stepLabel="Step 07 · Thinking Agents"
                title="Thinking Agents"
                description="Select the quick-thinking and deep-thinking engines for analysis."
                quickOptions={engines.quick}
                deepOptions={engines.deep}
                locked={step !== "thinking"}
                value={
                  thinking
                    ? { quick: thinking.quick.code, deep: thinking.deep.code }
                    : undefined
                }
                onSubmit={(quick, deep) => {
                  setThinking({ quick, deep });
                  advance("effort");
                }}
              />
            ) : null}

            {shouldRender("effort") ? (
              <ChoiceStep
                stepLabel="Step 08 · Effort Level"
                title="Effort Level"
                description={`Configure ${provider?.label ?? "model"} effort level.`}
                promptKey="effort"
                options={EFFORT_LEVELS}
                defaultCode="high"
                locked={step !== "effort"}
                value={effort?.code}
                onSubmit={(code, label) => {
                  setEffort({ code, label });
                  advance("running");
                }}
              />
            ) : null}

            {shouldRender("running") ? (
              <RunningStep
                symbol={symbol!}
                date={date!}
                analystCodes={analysts!.codes}
                locked={step !== "running"}
                done={step !== "running" && ORDER.indexOf(step) > ORDER.indexOf("running")}
                onComplete={() => {
                  if (step === "running") advance("report");
                }}
              />
            ) : null}

            {shouldRender("report") ? (
              <ReportStep
                symbol={symbol!}
                date={date!}
                locked={step !== "report"}
                value={report ?? undefined}
                onSubmit={(answers) => {
                  setReport(answers);
                  if (answers.displayReport) setShowFullReport(true);
                  advance("complete");
                }}
                onReset={reset}
                onViewReport={() => setShowFullReport(true)}
              />
            ) : null}
          </div>
        </div>
      </div>

      <FullReportOverlay
        open={showFullReport}
        onClose={() => setShowFullReport(false)}
      />
    </div>
  );
}

function StatusTicker({ step }: { step: StepKey }) {
  const color =
    step === "ready" ? "var(--color-ok)" : "var(--color-accent)";
  return (
    <div className="hidden items-center gap-2 md:flex">
      <span
        aria-hidden
        className="block h-2 w-2"
        style={{
          background: color,
          boxShadow: `0 0 12px ${color}`,
        }}
      />
      <span className="mono text-[11px] uppercase tracking-[0.22em] text-[var(--color-text-dim)]">
        {STATUS_LABEL[step]}
      </span>
    </div>
  );
}

function ProgressRail({ step }: { step: StepKey }) {
  const idx = ORDER.indexOf(step);
  const allDone = step === "complete";
  return (
    <div className="mb-10 flex items-center gap-3 overflow-x-auto">
      <span className="mono text-[10px] uppercase tracking-[0.22em] text-[var(--color-text-faint)]">
        intake
      </span>
      <div className="flex flex-1 items-center gap-2">
        {PROGRESS.map((s, i) => {
          const done = i < idx || allDone;
          const active = i === idx && !allDone;
          return (
            <div key={s.key} className="flex flex-1 items-center gap-2">
              <span
                aria-hidden
                className="block h-[2px] flex-1"
                style={{
                  background:
                    done || active ? "var(--color-accent)" : "var(--color-line)",
                  boxShadow: active ? "0 0 10px var(--color-accent)" : "none",
                }}
              />
              <span
                className="mono whitespace-nowrap text-[10px] uppercase tracking-[0.2em]"
                style={{
                  color: done
                    ? "var(--color-accent)"
                    : active
                      ? "var(--color-text)"
                      : "var(--color-text-faint)",
                }}
              >
                {String(i + 1).padStart(2, "0")} · {s.label}
              </span>
            </div>
          );
        })}
        <span
          aria-hidden
          className="block h-[2px] flex-1"
          style={{
            background: allDone ? "var(--color-accent)" : "var(--color-line)",
            boxShadow: allDone ? "0 0 10px var(--color-accent)" : "none",
          }}
        />
      </div>
    </div>
  );
}

