"use client";

import { useMemo, useState } from "react";
import type { AgentEntry, CatalogResponse, ModelWithEffort } from "@/lib/tradingAgent";

export interface AgentSettings {
  trading_style: "day" | "swing";
  analysis_date: string;
  output_language: string;
  analysts: string[];
  youtube_urls: string;
  research_depth: 1 | 3 | 5;
  llm_provider: string;
  shallow_thinker: string;
  deep_thinker: string;
  agent_models: Record<string, { model: string; effort: string | null }>;
}

interface Props {
  settings: AgentSettings;
  onChange: (next: AgentSettings) => void;
  onRun: () => void;
  running: boolean;
  catalog: CatalogResponse | null;
  catalogError: string | null;
  canRun: boolean;
}

const ANALYST_LABELS: Record<string, string> = {
  market: "Market",
  social: "Social",
  news: "News",
  fundamentals: "Fundamentals",
  youtube: "YouTube",
};

export function SettingsSidebar({
  settings,
  onChange,
  onRun,
  running,
  catalog,
  catalogError,
  canRun,
}: Props) {
  const [agentsOpen, setAgentsOpen] = useState(false);
  const set = <K extends keyof AgentSettings>(k: K, v: AgentSettings[K]) =>
    onChange({ ...settings, [k]: v });

  const providers = catalog?.providers ?? [];
  const modelsForProvider: ModelWithEffort[] = useMemo(
    () => catalog?.models_with_effort?.[settings.llm_provider] ?? [],
    [catalog, settings.llm_provider],
  );
  const agents: AgentEntry[] = catalog?.agents ?? [];

  const handleProviderChange = (key: string) => {
    const next: AgentSettings = { ...settings, llm_provider: key, agent_models: {} };
    const quickList = catalog?.models?.[key]?.quick ?? [];
    const deepList = catalog?.models?.[key]?.deep ?? [];
    if (quickList[0]) next.shallow_thinker = quickList[0].value;
    if (deepList[0]) next.deep_thinker = deepList[0].value;
    onChange(next);
  };

  const toggleAnalyst = (code: string) => {
    const has = settings.analysts.includes(code);
    set("analysts", has ? settings.analysts.filter((a) => a !== code) : [...settings.analysts, code]);
  };

  const setAgentModel = (key: string, raw: string) => {
    const next = { ...settings.agent_models };
    if (!raw) {
      delete next[key];
    } else {
      const [model, effort] = raw.split("|");
      next[key] = { model, effort: effort || null };
    }
    set("agent_models", next);
  };

  const applyToAll = (raw: string) => {
    if (!raw) {
      set("agent_models", {});
      return;
    }
    const [model, effort] = raw.split("|");
    const next: Record<string, { model: string; effort: string | null }> = {};
    for (const agent of agents) {
      next[agent.key] = { model, effort: effort || null };
    }
    set("agent_models", next);
  };

  const resetAll = () => set("agent_models", {});

  const analystOptions = catalog?.analysts ?? ["market", "social", "news", "fundamentals", "youtube"];

  return (
    <aside className="sidebar-scroll sticky top-16 flex h-[calc(100vh-4rem)] w-[340px] shrink-0 flex-col border-r border-[var(--color-line)] bg-[var(--color-bg)]">
      <div className="border-b border-[var(--color-line)] px-5 py-5">
        <div className="tag">AGNT · Settings</div>
        <h2 className="display mt-1 text-[22px] tracking-tight">Trading session</h2>
        {catalogError ? (
          <p className="mono mt-1 text-[10px] uppercase tracking-[0.18em]" style={{ color: "var(--color-warn)" }}>
            ! catalog unreachable
          </p>
        ) : !catalog ? (
          <p className="mono mt-1 text-[10px] uppercase tracking-[0.18em] text-[var(--color-text-faint)]">· fetching catalog…</p>
        ) : null}
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        <Block label="Trading style" hint={settings.trading_style === "day" ? "intraday · hour unit" : "multi-day · day unit"}>
          <Segmented
            options={[
              { code: "day", label: "Day" },
              { code: "swing", label: "Swing" },
            ]}
            value={settings.trading_style}
            onChange={(v) => set("trading_style", v as "day" | "swing")}
          />
        </Block>

        <Block label="Analysis date" hint="calendar picker · no typing">
          <input
            type="date"
            value={settings.analysis_date}
            onChange={(e) => set("analysis_date", e.target.value)}
            className="w-full border border-[var(--color-line)] bg-[var(--color-bg)] px-3 py-2 font-mono text-[13px] text-[var(--color-text)] outline-none focus:border-[var(--color-accent)]"
          />
        </Block>

        <Block label="Output language">
          <Select
            value={settings.output_language}
            options={(catalog?.languages ?? ["English"]).map((l) => ({ code: l, label: l }))}
            onChange={(v) => set("output_language", v)}
          />
        </Block>

        <Block label="Analysts" hint="pick at least one">
          <div className="grid grid-cols-2 gap-1.5">
            {analystOptions.map((code) => {
              const checked = settings.analysts.includes(code);
              return (
                <button
                  key={code}
                  type="button"
                  onClick={() => toggleAnalyst(code)}
                  className="mono flex items-center gap-2 border px-2 py-1.5 text-[11px] uppercase tracking-[0.16em] transition-colors"
                  style={{
                    background: checked ? "color-mix(in srgb, var(--color-accent) 16%, transparent)" : "transparent",
                    borderColor: checked ? "var(--color-accent)" : "var(--color-line)",
                    color: checked ? "var(--color-text)" : "var(--color-text-dim)",
                  }}
                >
                  <span style={{ color: checked ? "var(--color-accent)" : "var(--color-text-faint)" }}>{checked ? "■" : "□"}</span>
                  <span>{ANALYST_LABELS[code] ?? code}</span>
                </button>
              );
            })}
          </div>
        </Block>

        {settings.analysts.includes("youtube") ? (
          <Block label="YouTube URLs" hint="one per line">
            <textarea
              value={settings.youtube_urls}
              onChange={(e) => set("youtube_urls", e.target.value)}
              rows={3}
              placeholder="https://www.youtube.com/watch?v=…"
              className="w-full resize-none border border-[var(--color-line)] bg-[var(--color-bg)] px-3 py-2 font-mono text-[12px] text-[var(--color-text)] outline-none focus:border-[var(--color-accent)]"
            />
          </Block>
        ) : null}

        <Block label="Research depth" hint="controls debate + risk rounds">
          <Select
            value={String(settings.research_depth)}
            options={(catalog?.depths ?? [
              { label: "Shallow", value: 1, hint: "" },
              { label: "Medium", value: 3, hint: "" },
              { label: "Deep", value: 5, hint: "" },
            ]).map((d) => ({ code: String(d.value), label: d.label }))}
            onChange={(v) => set("research_depth", Number(v) as 1 | 3 | 5)}
          />
        </Block>

        <Block label="LLM provider">
          <Select
            value={settings.llm_provider}
            options={providers.map((p) => ({ code: p.key, label: p.label }))}
            onChange={handleProviderChange}
          />
        </Block>

        <Block label="Per-agent models" hint={agentsOpen ? "click to collapse" : "click to expand"}>
          <button
            type="button"
            onClick={() => setAgentsOpen((v) => !v)}
            className="mono flex w-full items-center justify-between border border-[var(--color-line)] px-3 py-2 text-[11px] uppercase tracking-[0.18em] text-[var(--color-text-dim)] transition-colors hover:bg-[var(--color-surface)]"
          >
            <span>{agentsOpen ? "Hide overrides" : "Show overrides"}</span>
            <span aria-hidden>{agentsOpen ? "▾" : "▸"}</span>
          </button>
          {agentsOpen ? (
            <div className="mt-3 flex flex-col gap-2">
              {agents.length === 0 ? (
                <p className="mono text-[10px] text-[var(--color-text-faint)]">awaiting catalog…</p>
              ) : modelsForProvider.length === 0 ? (
                <p className="mono text-[10px] text-[var(--color-text-faint)]">
                  no static model list for {settings.llm_provider} — leave as default
                </p>
              ) : (
                <>
                  <div className="flex flex-col gap-1 border-b border-dashed border-[var(--color-line)] pb-3">
                    <label className="mono text-[10px] uppercase tracking-[0.18em]" style={{ color: "var(--color-accent)" }}>
                      Apply to all agents
                    </label>
                    <select
                      defaultValue=""
                      onChange={(e) => { applyToAll(e.target.value); e.currentTarget.value = ""; }}
                      className="w-full border border-[var(--color-accent)] bg-[var(--color-bg)] px-2 py-1.5 font-mono text-[11px] text-[var(--color-text)] outline-none"
                    >
                      <option value="">— pick a model to broadcast —</option>
                      {modelsForProvider.map((m) => {
                        const v = `${m.model}|${m.effort ?? ""}`;
                        return <option key={v} value={v}>{m.label}</option>;
                      })}
                    </select>
                    <button
                      type="button"
                      onClick={resetAll}
                      className="mono mt-1 self-start text-[10px] uppercase tracking-[0.18em] text-[var(--color-text-dim)] underline-offset-2 hover:text-[var(--color-accent)] hover:underline"
                    >
                      reset all to defaults
                    </button>
                  </div>
                  {agents.map((agent) => {
                  const current = settings.agent_models[agent.key];
                  const currentValue = current ? `${current.model}|${current.effort ?? ""}` : "";
                  return (
                    <div key={agent.key} className="flex flex-col gap-1">
                      <label className="mono text-[10px] uppercase tracking-[0.18em] text-[var(--color-text-faint)]">
                        {agent.label}
                        <span className="ml-2 text-[var(--color-text-faint)]/60">{agent.default_tier === "deep" ? "deep" : "quick"}</span>
                      </label>
                      <select
                        value={currentValue}
                        onChange={(e) => setAgentModel(agent.key, e.target.value)}
                        className="w-full border border-[var(--color-line)] bg-[var(--color-bg)] px-2 py-1.5 font-mono text-[11px] text-[var(--color-text)] outline-none focus:border-[var(--color-accent)]"
                      >
                        <option value="">— default ({agent.default_tier}) —</option>
                        {modelsForProvider.map((m) => {
                          const v = `${m.model}|${m.effort ?? ""}`;
                          return (
                            <option key={v} value={v}>{m.label}</option>
                          );
                        })}
                      </select>
                    </div>
                  );
                })}
                </>
              )}
            </div>
          ) : null}
        </Block>
      </div>

      <div className="border-t border-[var(--color-line)] px-5 py-4">
        <button
          onClick={onRun}
          disabled={running || !canRun}
          className="group relative w-full overflow-hidden border border-[var(--color-accent)] bg-[var(--color-accent)] py-3 text-center text-[12px] font-medium uppercase tracking-[0.22em] text-black transition-colors hover:bg-[var(--color-accent-dim)] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {running ? "Running…" : "Run pipeline"}
        </button>
        {!canRun && !running ? (
          <p className="mono mt-2 text-[10px] uppercase tracking-[0.18em] text-[var(--color-text-faint)]">
            pick symbol + ≥1 analyst
          </p>
        ) : null}
      </div>
    </aside>
  );
}

function Block({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 border-b border-dashed border-[var(--color-line)] py-3 last:border-b-0">
      <div className="flex items-baseline justify-between gap-2">
        <span className="mono text-[10px] uppercase tracking-[0.18em] text-[var(--color-text-dim)]">{label}</span>
        {hint ? <span className="mono text-[10px] text-[var(--color-text-faint)]">{hint}</span> : null}
      </div>
      {children}
    </div>
  );
}

function Select({ value, options, onChange }: { value: string; options: { code: string; label: string }[]; onChange: (v: string) => void }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full border border-[var(--color-line)] bg-[var(--color-bg)] px-3 py-2 font-mono text-[12px] text-[var(--color-text)] outline-none focus:border-[var(--color-accent)]"
    >
      {options.map((o) => (
        <option key={o.code} value={o.code}>{o.label}</option>
      ))}
    </select>
  );
}

function Segmented({ options, value, onChange }: { options: { code: string; label: string }[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="mono flex overflow-hidden border border-[var(--color-line)] text-[11px] uppercase tracking-[0.18em]">
      {options.map((o) => {
        const active = o.code === value;
        return (
          <button
            key={o.code}
            type="button"
            onClick={() => onChange(o.code)}
            className="flex-1 px-3 py-2 transition-colors"
            style={{
              background: active ? "var(--color-accent)" : "transparent",
              color: active ? "var(--color-bg)" : "var(--color-text-dim)",
            }}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
