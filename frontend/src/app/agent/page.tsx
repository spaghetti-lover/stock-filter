"use client";

import { useEffect, useMemo, useState } from "react";
import { WelcomeBlock } from "@/components/agent/WelcomeBlock";
import { SymbolStep } from "@/components/agent/SymbolStep";
import { DateStep } from "@/components/agent/DateStep";
import { ChoiceStep, type Choice } from "@/components/agent/ChoiceStep";
import { MultiChoiceStep } from "@/components/agent/MultiChoiceStep";
import { ThinkingStep } from "@/components/agent/ThinkingStep";
import { ReportStep, type ReportAnswers } from "@/components/agent/ReportStep";
import { RunningStep } from "@/components/agent/RunningStep";
import { YoutubeUrlsStep } from "@/components/agent/YoutubeUrlsStep";
import { FullReportOverlay } from "@/components/agent/FullReportOverlay";
import {
  fetchCatalog,
  fetchRunReport,
  startRun,
  type CatalogResponse,
  type RunReports,
} from "@/lib/tradingAgent";

const EFFORT_LEVELS: Choice[] = [
  { code: "high", label: "High", hint: "recommended", badge: "rec" },
  { code: "medium", label: "Medium", hint: "balanced" },
  { code: "low", label: "Low", hint: "faster, cheaper" },
];

const REASONING_EFFORT: Choice[] = [
  { code: "medium", label: "Medium", hint: "default" },
  { code: "high", label: "High", hint: "more thorough" },
  { code: "low", label: "Low", hint: "faster" },
];

const GEMINI_THINKING: Choice[] = [
  { code: "high", label: "Enable Thinking", hint: "recommended" },
  { code: "minimal", label: "Minimal", hint: "disable thinking" },
];

const ANALYST_HINTS: Record<string, string> = {
  market: "price action, indicators, momentum",
  social: "sentiment, virality, retail mood",
  news: "macro headlines, filings, events",
  fundamentals: "ratios, earnings, balance sheet",
  youtube: "video transcripts, analyst commentary",
};

const LANGUAGE_HINTS: Record<string, string> = {
  English: "default",
  Chinese: "中文",
  Japanese: "日本語",
  Korean: "한국어",
  Hindi: "हिन्दी",
  Spanish: "Español",
  Portuguese: "Português",
  French: "Français",
  German: "Deutsch",
  Arabic: "العربية",
  Russian: "Русский",
  Vietnamese: "Tiếng Việt",
};

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
  | "youtube_urls"
  | "depth"
  | "provider"
  | "thinking"
  | "effort"
  | "running"
  | "report"
  | "complete";

const ORDER: StepKey[] = [
  "symbol",
  "date",
  "language",
  "analysts",
  "youtube_urls",
  "depth",
  "provider",
  "thinking",
  "effort",
  "running",
  "report",
  "complete",
];

const PROGRESS = [
  { key: "symbol", label: "Ticker" },
  { key: "date", label: "Date" },
  { key: "language", label: "Lang" },
  { key: "analysts", label: "Team" },
  { key: "youtube_urls", label: "Videos" },
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
  youtube_urls: "awaiting youtube videos",
  depth: "awaiting depth",
  provider: "awaiting provider",
  thinking: "awaiting thinking agents",
  effort: "awaiting effort",
  running: "pipeline · live",
  report: "awaiting report ack",
  complete: "session complete",
};

export default function AgentPage() {
  const [catalog, setCatalog] = useState<CatalogResponse | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);

  const [step, setStep] = useState<StepKey>("symbol");
  const [symbol, setSymbol] = useState<string | null>(null);
  const [date, setDate] = useState<string | null>(null);
  const [language, setLanguage] = useState<{ code: string; label: string } | null>(null);
  const [analysts, setAnalysts] = useState<{ codes: string[]; labels: string[] } | null>(null);
  const [youtubeUrls, setYoutubeUrls] = useState<string[] | null>(null);
  const [depth, setDepth] = useState<{ code: string; label: string; value: number } | null>(null);
  const [provider, setProvider] = useState<{ code: string; label: string } | null>(null);
  const [thinking, setThinking] = useState<{
    quick: { code: string; label: string };
    deep: { code: string; label: string };
  } | null>(null);
  const [effort, setEffort] = useState<{ code: string; label: string } | null>(null);
  const [report, setReport] = useState<ReportAnswers | null>(null);
  const [showFullReport, setShowFullReport] = useState(false);

  const [runId, setRunId] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [runDone, setRunDone] = useState(false);
  const [fullReports, setFullReports] = useState<RunReports | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCatalog()
      .then((c) => {
        if (cancelled) return;
        setCatalog(c);
      })
      .catch((err) => {
        if (cancelled) return;
        setCatalogError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const reset = () => {
    setStep("symbol");
    setSymbol(null);
    setDate(null);
    setLanguage(null);
    setAnalysts(null);
    setYoutubeUrls(null);
    setDepth(null);
    setProvider(null);
    setThinking(null);
    setEffort(null);
    setReport(null);
    setShowFullReport(false);
    setRunId(null);
    setRunError(null);
    setRunDone(false);
    setFullReports(null);
    setReportError(null);
  };

  const advance = (next: StepKey) => setStep(next);

  // Build dropdown options from the live catalog
  const languageChoices = useMemo<Choice[]>(() => {
    const langs = catalog?.languages ?? Object.keys(LANGUAGE_HINTS);
    return langs.map((label) => ({
      code: label,
      label,
      hint: LANGUAGE_HINTS[label],
    }));
  }, [catalog]);

  const analystChoices = useMemo<Choice[]>(() => {
    const ids = catalog?.analysts ?? ["market", "social", "news", "fundamentals"];
    return ids.map((code) => ({
      code,
      label: code.replace(/^./, (c) => c.toUpperCase()) + " Analyst",
      hint: ANALYST_HINTS[code],
    }));
  }, [catalog]);

  const depthChoices = useMemo<Choice[]>(() => {
    const items = catalog?.depths ?? [
      { label: "Shallow", value: 1, hint: "quick research" },
      { label: "Medium", value: 3, hint: "moderate" },
      { label: "Deep", value: 5, hint: "comprehensive" },
    ];
    return items.map((d) => ({
      code: String(d.value),
      label: d.label,
      hint: d.hint,
    }));
  }, [catalog]);

  const providerChoices = useMemo<Choice[]>(() => {
    const items = catalog?.providers ?? [];
    return items.map((p) => ({
      code: p.key,
      label: p.label,
    }));
  }, [catalog]);

  const engines = useMemo(() => {
    if (!provider || !catalog) return null;
    const m = catalog.models[provider.code];
    if (!m) return null;
    return {
      quick: m.quick.map((c) => ({ code: c.value, label: c.label })) as Choice[],
      deep: m.deep.map((c) => ({ code: c.value, label: c.label })) as Choice[],
    };
  }, [provider, catalog]);

  const providerEffortChoices = useMemo<Choice[]>(() => {
    if (!provider) return EFFORT_LEVELS;
    if (provider.code === "openai") return REASONING_EFFORT;
    if (provider.code === "google") return GEMINI_THINKING;
    return EFFORT_LEVELS;
  }, [provider]);

  const shouldRender = (key: StepKey) =>
    ORDER.indexOf(step) >= ORDER.indexOf(key);

  // Kick off backend run once intake completes
  const launchRun = async (chosen: { code: string; label: string }) => {
    setEffort(chosen);
    setRunError(null);
    setRunDone(false);
    if (!symbol || !date || !analysts || !depth || !provider || !thinking || !language) {
      setRunError("incomplete intake");
      advance("running");
      return;
    }

    const providerInfo = catalog?.providers.find((p) => p.key === provider.code);

    const payload = {
      ticker: symbol,
      analysis_date: date,
      output_language: language.label,
      analysts: analysts.codes,
      research_depth: depth.value as 1 | 3 | 5,
      llm_provider: provider.code,
      shallow_thinker: thinking.quick.code,
      deep_thinker: thinking.deep.code,
      google_thinking_level: provider.code === "google" ? chosen.code : null,
      openai_reasoning_effort: provider.code === "openai" ? chosen.code : null,
      anthropic_effort: provider.code === "anthropic" ? chosen.code : null,
      backend_url: providerInfo?.backend_url ?? null,
      youtube_urls: youtubeUrls && youtubeUrls.length > 0 ? youtubeUrls : null,
    };

    advance("running");
    try {
      const res = await startRun(payload);
      setRunId(res.run_id);
    } catch (err) {
      setRunError(err instanceof Error ? err.message : String(err));
    }
  };

  // Fetch the report after the run finishes (or when the user wants to view it)
  const loadReportIfNeeded = async () => {
    if (!runId || fullReports || reportLoading) return;
    setReportLoading(true);
    setReportError(null);
    try {
      const data = await fetchRunReport(runId);
      setFullReports(data.reports);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : String(err));
    } finally {
      setReportLoading(false);
    }
  };

  useEffect(() => {
    if (runDone && runId && !fullReports) {
      void loadReportIfNeeded();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runDone, runId]);

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
          {catalogError ? (
            <p
              className="mono text-[11px] uppercase tracking-[0.2em]"
              style={{ color: "var(--color-warn)" }}
            >
              ! catalog unreachable: {catalogError}
            </p>
          ) : !catalog ? (
            <p className="mono text-[11px] uppercase tracking-[0.2em] text-[var(--color-text-faint)]">
              · fetching trading-agent catalog…
            </p>
          ) : null}
        </div>
      </div>

      <div className="mx-auto flex max-w-[1080px] flex-col gap-12 px-8 py-14">
        <WelcomeBlock />

        <div className="relative pt-3">
          <ProgressRail step={step} />

          <div className="flex flex-col gap-10">
            <SymbolStep
              defaultValue="FPT"
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
                options={languageChoices}
                defaultCode="English"
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
                options={analystChoices}
                defaultCodes={["market", "social", "news", "fundamentals", "youtube"]}
                locked={step !== "analysts"}
                value={analysts?.codes}
                onSubmit={(codes, labels) => {
                  setAnalysts({ codes, labels });
                  if (codes.includes("youtube")) {
                    advance("youtube_urls");
                  } else {
                    advance("depth");
                  }
                }}
              />
            ) : null}

            {shouldRender("youtube_urls") && analysts?.codes.includes("youtube") ? (
              <YoutubeUrlsStep
                locked={step !== "youtube_urls"}
                value={youtubeUrls ?? undefined}
                onSubmit={(urls) => {
                  setYoutubeUrls(urls);
                  advance("depth");
                }}
                onSkip={() => {
                  setYoutubeUrls([]);
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
                options={depthChoices}
                defaultCode="1"
                locked={step !== "depth"}
                value={depth?.code}
                onSubmit={(code, label) => {
                  setDepth({ code, label, value: Number(code) });
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
                options={providerChoices}
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
                title={
                  provider?.code === "google"
                    ? "Thinking Mode"
                    : provider?.code === "openai"
                      ? "Reasoning Effort"
                      : "Effort Level"
                }
                description={`Configure ${provider?.label ?? "model"} effort.`}
                promptKey="effort"
                options={providerEffortChoices}
                defaultCode={providerEffortChoices[0]?.code ?? "high"}
                locked={step !== "effort"}
                value={effort?.code}
                onSubmit={(code, label) => {
                  void launchRun({ code, label });
                }}
              />
            ) : null}

            {shouldRender("running") ? (
              <RunningStep
                runId={runId}
                symbol={symbol!}
                date={date!}
                analystCodes={analysts!.codes}
                locked={step !== "running"}
                done={step !== "running" && ORDER.indexOf(step) > ORDER.indexOf("running")}
                onComplete={({ error }) => {
                  setRunDone(true);
                  setRunError(error);
                  if (step === "running") advance("report");
                }}
              />
            ) : null}

            {runError && step === "running" ? (
              <p
                className="mono text-[12px]"
                style={{ color: "var(--color-warn)" }}
              >
                ! run failed: {runError}
              </p>
            ) : null}

            {shouldRender("report") ? (
              <ReportStep
                runId={runId}
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
                onViewReport={() => {
                  void loadReportIfNeeded();
                  setShowFullReport(true);
                }}
              />
            ) : null}
          </div>
        </div>
      </div>

      <FullReportOverlay
        open={showFullReport}
        onClose={() => setShowFullReport(false)}
        reports={fullReports}
        ticker={symbol ?? undefined}
        analysisDate={date ?? undefined}
        loading={reportLoading}
        error={reportError}
      />
    </div>
  );
}

function StatusTicker({ step }: { step: StepKey }) {
  const color =
    step === "complete" ? "var(--color-ok)" : "var(--color-accent)";
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
