"use client";

import { useEffect, useState } from "react";
import { SettingsSidebar, type AgentSettings } from "@/components/agent/SettingsSidebar";
import { SymbolAutocomplete } from "@/components/agent/SymbolAutocomplete";
import { ReportStep, type ReportAnswers } from "@/components/agent/ReportStep";
import { RunningStep } from "@/components/agent/RunningStep";
import { FullReportOverlay } from "@/components/agent/FullReportOverlay";
import {
  fetchCatalog,
  fetchRunReport,
  startRun,
  type CatalogResponse,
  type RunReports,
  type SymbolEntry,
} from "@/lib/tradingAgent";

const TODAY_ISO = (() => {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
})();

const DEFAULT_SETTINGS: AgentSettings = {
  trading_style: "swing",
  analysis_date: TODAY_ISO,
  output_language: "English",
  analysts: ["market", "social", "news", "fundamentals", "youtube"],
  youtube_urls: "",
  research_depth: 1,
  llm_provider: "anthropic",
  shallow_thinker: "claude-sonnet-4-6",
  deep_thinker: "claude-opus-4-6",
  agent_models: {},
};

type Phase = "intake" | "running" | "report" | "complete";

export default function AgentPage() {
  const [catalog, setCatalog] = useState<CatalogResponse | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);

  const [settings, setSettings] = useState<AgentSettings>(DEFAULT_SETTINGS);
  const [symbolEntry, setSymbolEntry] = useState<SymbolEntry | null>(null);

  const [phase, setPhase] = useState<Phase>("intake");
  const [runId, setRunId] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [runDone, setRunDone] = useState(false);
  const [fullReports, setFullReports] = useState<RunReports | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [reportAnswers, setReportAnswers] = useState<ReportAnswers | null>(null);
  const [showFullReport, setShowFullReport] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchCatalog()
      .then((c) => {
        if (cancelled) return;
        setCatalog(c);
        setSettings((s) => {
          const quickDefault = c.models?.[s.llm_provider]?.quick?.[0]?.value;
          const deepDefault = c.models?.[s.llm_provider]?.deep?.[0]?.value;
          return {
            ...s,
            shallow_thinker: quickDefault ?? s.shallow_thinker,
            deep_thinker: deepDefault ?? s.deep_thinker,
          };
        });
      })
      .catch((err) => {
        if (cancelled) return;
        setCatalogError(err instanceof Error ? err.message : String(err));
      });
    return () => { cancelled = true; };
  }, []);

  const canRun = !!symbolEntry && settings.analysts.length > 0 && !!settings.analysis_date;

  const launchRun = async () => {
    if (!symbolEntry || !canRun) return;
    setRunError(null);
    setRunDone(false);
    setFullReports(null);
    setReportAnswers(null);
    setReportError(null);
    setPhase("running");

    const providerInfo = catalog?.providers.find((p) => p.key === settings.llm_provider);
    const ytUrls = settings.youtube_urls
      .split(/\r?\n/)
      .map((u) => u.trim())
      .filter(Boolean);

    try {
      const res = await startRun({
        ticker: symbolEntry.symbol,
        analysis_date: settings.analysis_date,
        output_language: settings.output_language,
        analysts: settings.analysts,
        research_depth: settings.research_depth,
        llm_provider: settings.llm_provider,
        shallow_thinker: settings.shallow_thinker,
        deep_thinker: settings.deep_thinker,
        google_thinking_level: null,
        openai_reasoning_effort: null,
        anthropic_effort: null,
        backend_url: providerInfo?.backend_url ?? null,
        youtube_urls: ytUrls.length ? ytUrls : null,
        trading_style: settings.trading_style,
        agent_models: settings.agent_models,
      });
      setRunId(res.run_id);
    } catch (err) {
      setRunError(err instanceof Error ? err.message : String(err));
      setPhase("intake");
    }
  };

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

  const reset = () => {
    setSymbolEntry(null);
    setPhase("intake");
    setRunId(null);
    setRunError(null);
    setRunDone(false);
    setFullReports(null);
    setReportError(null);
    setReportAnswers(null);
    setShowFullReport(false);
  };

  return (
    <div className="flex">
      <SettingsSidebar
        settings={settings}
        onChange={setSettings}
        onRun={launchRun}
        running={phase === "running"}
        catalog={catalog}
        catalogError={catalogError}
        canRun={canRun}
      />

      <section className="min-w-0 flex-1">
        <div className="hairline-grid border-b border-[var(--color-line)]">
          <div className="px-8 pb-8 pt-12">
            <div className="flex items-center gap-3 text-[var(--color-text-dim)]">
              <span className="mono text-[10px]">AGNT/00</span>
              <span className="tag">Trading Agent · session</span>
            </div>
            <h1
              className="display mt-3 text-[40px] leading-[0.95] tracking-tight md:text-[48px]"
              style={{ fontVariationSettings: '"opsz" 144, "SOFT" 30' }}
            >
              Initialize a trading session.
            </h1>
            <p className="mt-3 max-w-[72ch] text-[13px] text-[var(--color-text-dim)]">
              Configure the rail. Pick a symbol. Press <span className="text-[var(--color-accent)]">Run pipeline</span>.
            </p>
          </div>
        </div>

        <div className="px-8 py-10">
          {phase === "intake" ? (
            <div className="flex flex-col gap-4">
              <SymbolAutocomplete
                value={symbolEntry}
                onCommit={setSymbolEntry}
                disabled={phase !== "intake"}
              />
              {runError ? (
                <p className="mono text-[12px]" style={{ color: "var(--color-warn)" }}>! {runError}</p>
              ) : null}
            </div>
          ) : null}

          {(phase === "running" || phase === "report" || phase === "complete") && symbolEntry ? (
            <div className="flex flex-col gap-8">
              <RunningStep
                runId={runId}
                symbol={symbolEntry.symbol}
                date={settings.analysis_date}
                analystCodes={settings.analysts}
                locked={phase !== "running"}
                done={phase !== "running"}
                onComplete={({ error }) => {
                  setRunDone(true);
                  setRunError(error);
                  if (phase === "running") setPhase("report");
                }}
              />

              {runError && phase === "running" ? (
                <p className="mono text-[12px]" style={{ color: "var(--color-warn)" }}>! run failed: {runError}</p>
              ) : null}

              {phase === "report" || phase === "complete" ? (
                <ReportStep
                  runId={runId}
                  symbol={symbolEntry.symbol}
                  date={settings.analysis_date}
                  locked={phase !== "report"}
                  value={reportAnswers ?? undefined}
                  onSubmit={(answers) => {
                    setReportAnswers(answers);
                    if (answers.displayReport) setShowFullReport(true);
                    setPhase("complete");
                  }}
                  onReset={reset}
                  onViewReport={() => {
                    void loadReportIfNeeded();
                    setShowFullReport(true);
                  }}
                />
              ) : null}
            </div>
          ) : null}
        </div>
      </section>

      <FullReportOverlay
        open={showFullReport}
        onClose={() => setShowFullReport(false)}
        reports={fullReports}
        ticker={symbolEntry?.symbol}
        analysisDate={settings.analysis_date}
        loading={reportLoading}
        error={reportError}
      />
    </div>
  );
}
