"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { BoxPanel } from "./BoxPanel";
import { Markdown } from "@/components/chat/Markdown";
import {
  openAgentStream,
  type AgentSseEvent,
  type AgentRunStatus,
  type RunReports,
} from "@/lib/tradingAgent";

type ReportRenderMode = "markdown" | "raw";

interface Props {
  runId: string | null;
  symbol: string;
  date: string;
  analystCodes: string[];
  locked?: boolean;
  done?: boolean;
  onComplete: (result: { error: string | null }) => void;
}

type AgentStatus = "pending" | "in_progress" | "completed" | "error";

interface AgentRow {
  team: string;
  agent: string;
  status: AgentStatus;
}

interface MsgRow {
  time: string;
  type: string;
  content: string;
}

const ANALYST_LABEL: Record<string, string> = {
  market: "Market Analyst",
  social: "Social Analyst",
  news: "News Analyst",
  fundamentals: "Fundamentals Analyst",
  youtube: "Youtube Analyst",
};

const FIXED_TEAMS: Record<string, string[]> = {
  "Research Team": ["Bull Researcher", "Bear Researcher", "Research Manager"],
  "Trading Team": ["Trader"],
  "Risk Management": ["Aggressive Analyst", "Neutral Analyst", "Conservative Analyst"],
  "Portfolio Management": ["Portfolio Manager"],
};

const SECTION_TITLE: Record<string, string> = {
  market_report: "Market Analysis",
  sentiment_report: "Social Sentiment",
  news_report: "News Analysis",
  fundamentals_report: "Fundamentals Analysis",
  youtube_report: "YouTube Analysis",
  investment_plan: "Research Team Decision",
  trader_investment_plan: "Trading Team Plan",
  final_trade_decision: "Portfolio Management Decision",
};

const SECTION_ANALYST_GATE: Record<string, string> = {
  market_report: "market",
  sentiment_report: "social",
  news_report: "news",
  fundamentals_report: "fundamentals",
  youtube_report: "youtube",
};

function buildInitialAgents(analystCodes: string[]): AgentRow[] {
  const analysts: AgentRow[] = analystCodes
    .map((code) => ({
      team: "Analyst Team",
      agent: ANALYST_LABEL[code] ?? code,
      status: "pending" as AgentStatus,
    }));
  const fixed: AgentRow[] = [];
  for (const [team, members] of Object.entries(FIXED_TEAMS)) {
    for (const agent of members) {
      fixed.push({ team, agent, status: "pending" });
    }
  }
  return [...analysts, ...fixed];
}

function expectedReportSections(analystCodes: string[]): string[] {
  const out: string[] = [];
  for (const section of Object.keys(SECTION_TITLE)) {
    const analyst = SECTION_ANALYST_GATE[section];
    if (analyst === undefined || analystCodes.includes(analyst)) {
      out.push(section);
    }
  }
  return out;
}

function fmtClock(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function formatTokens(n: number) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

export function RunningStep({
  runId,
  symbol,
  date,
  analystCodes,
  locked = false,
  done = false,
  onComplete,
}: Props) {
  const initialAgents = useMemo(() => buildInitialAgents(analystCodes), [analystCodes]);
  const expectedSections = useMemo(
    () => expectedReportSections(analystCodes),
    [analystCodes],
  );

  const [agents, setAgents] = useState<AgentRow[]>(initialAgents);
  const [messages, setMessages] = useState<MsgRow[]>([]);
  const [reports, setReports] = useState<RunReports>({});
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [stats, setStats] = useState({ llm_calls: 0, tool_calls: 0, tokens_in: 0, tokens_out: 0 });
  const [elapsed, setElapsed] = useState(0);
  const [runStatus, setRunStatus] = useState<AgentRunStatus>("pending");
  const [error, setError] = useState<string | null>(null);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  // Reset transient state when a new run is started so a re-run after restart
  // doesn't display stale agents or messages.
  useEffect(() => {
    setAgents(initialAgents);
    setMessages([]);
    setReports({});
    setActiveSection(null);
    setStats({ llm_calls: 0, tool_calls: 0, tokens_in: 0, tokens_out: 0 });
    setElapsed(0);
    setRunStatus("pending");
    setError(null);
  }, [runId, initialAgents]);

  // Wall-clock ticker
  useEffect(() => {
    if (locked || done || runStatus === "done" || runStatus === "error") return;
    const started = Date.now();
    const handle = window.setInterval(() => {
      setElapsed(Math.floor((Date.now() - started) / 1000));
    }, 1000);
    return () => window.clearInterval(handle);
  }, [locked, done, runStatus]);

  // SSE stream
  useEffect(() => {
    if (!runId || locked) return;

    const handler = (e: AgentSseEvent) => {
      switch (e.type) {
        case "snapshot": {
          if (e.agents && Object.keys(e.agents).length) {
            setAgents((prev) =>
              prev.map((row) => ({
                ...row,
                status: (e.agents[row.agent] as AgentStatus | undefined) ?? row.status,
              })),
            );
          }
          if (e.reports) setReports(e.reports);
          if (e.stats) setStats(e.stats);
          if (e.messages?.length) {
            setMessages(
              e.messages.map((m) => ({ time: m.time, type: m.type, content: m.content })),
            );
          }
          if (e.tool_calls?.length) {
            setMessages((prev) => [
              ...e.tool_calls.map((t) => ({ time: t.time, type: "Tool", content: `${t.name}: ${t.args}` })),
              ...prev,
            ]);
          }
          if (e.status) setRunStatus(e.status);
          break;
        }
        case "agent_status": {
          setAgents((prev) =>
            prev.map((row) =>
              row.agent === e.agent ? { ...row, status: e.status as AgentStatus } : row,
            ),
          );
          break;
        }
        case "report": {
          setReports((prev) => ({ ...prev, [e.section]: e.content }));
          setActiveSection(e.section);
          break;
        }
        case "message": {
          setMessages((prev) =>
            [{ time: e.time ?? "", type: e.msg_type, content: e.content }, ...prev].slice(0, 200),
          );
          break;
        }
        case "tool_call": {
          setMessages((prev) =>
            [
              { time: e.time ?? "", type: "Tool", content: `${e.name}: ${e.args}` },
              ...prev,
            ].slice(0, 200),
          );
          break;
        }
        case "stats": {
          setStats(e.stats);
          break;
        }
        case "complete_report": {
          // The full report is also available via the run report endpoint.
          break;
        }
        case "final_state": {
          break;
        }
        case "status": {
          setRunStatus(e.status);
          if (e.error) setError(e.error);
          if (e.status === "done" || e.status === "error") {
            onCompleteRef.current({ error: e.error ?? null });
          }
          break;
        }
      }
    };

    const handle = openAgentStream(runId, handler);
    return () => handle.close();
  }, [runId, locked]);

  const completedAgents = agents.filter((a) => a.status === "completed").length;
  const reportEntries = Object.entries(reports).filter(
    ([k, v]) => expectedSections.includes(k) && v && v.trim(),
  );
  const reportsDone = reportEntries.length;

  const activeReport = activeSection
    ? reports[activeSection]
    : reportEntries.at(-1)?.[1];
  const activeTitle = activeSection
    ? SECTION_TITLE[activeSection] ?? activeSection
    : reportEntries.at(-1)?.[0];

  const tone = done ? "muted" : locked ? "muted" : error ? "warn" : "accent";

  return (
    <BoxPanel title="Step 09 · Pipeline Runtime" tone={tone}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <p className="display text-[18px] tracking-tight">
            {runStatus === "done"
              ? "Pipeline complete."
              : runStatus === "error"
                ? "Pipeline failed."
                : "Welcome to TradingAgents."}
          </p>
          <p className="text-[13px] text-[var(--color-text-dim)]">
            {runId
              ? `Live multi-agent run for ${symbol} · session ${date}. Run ${runId}.`
              : "Awaiting run handshake…"}
          </p>
          {error ? (
            <p
              className="mono mt-2 text-[12px]"
              style={{ color: "var(--color-warn)" }}
            >
              ! {error}
            </p>
          ) : null}
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <ProgressPanel agents={agents} />
          <MessagesPanel rows={messages} />
        </div>

        <CurrentReportPanel report={activeReport ?? ""} title={activeTitle} />

        <StatusFooter
          agentsDone={completedAgents}
          agentsTotal={agents.length}
          llm={stats.llm_calls}
          tools={stats.tool_calls}
          tokensUp={stats.tokens_in}
          tokensDown={stats.tokens_out}
          reports={reportsDone}
          totalReports={expectedSections.length}
          elapsed={elapsed}
          done={runStatus === "done"}
        />
      </div>
    </BoxPanel>
  );
}

function ProgressPanel({ agents }: { agents: AgentRow[] }) {
  return (
    <div className="border border-[var(--color-line)] bg-[var(--color-bg)]">
      <div className="border-b border-[var(--color-line)] bg-[var(--color-surface-2)] px-3 py-2">
        <span
          className="mono text-[10px] uppercase tracking-[0.24em]"
          style={{ color: "var(--color-accent)" }}
        >
          Progress
        </span>
      </div>
      <div className="max-h-[420px] overflow-y-auto">
        <table className="mono w-full table-fixed text-[12px]">
          <thead className="text-[var(--color-text-faint)]">
            <tr>
              <th className="w-[34%] px-3 py-2 text-left font-normal uppercase tracking-[0.18em]">
                Team
              </th>
              <th className="w-[40%] px-3 py-2 text-left font-normal uppercase tracking-[0.18em]">
                Agent
              </th>
              <th className="w-[26%] px-3 py-2 text-left font-normal uppercase tracking-[0.18em]">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {agents.map((a, i) => {
              const teamLabel =
                i === 0 || a.team !== agents[i - 1]?.team ? a.team : "";
              return (
                <tr
                  key={`${a.agent}-${i}`}
                  className="border-t border-dashed border-[var(--color-line)] align-top"
                >
                  <td className="px-3 py-1.5 text-[var(--color-text-dim)]">
                    {teamLabel}
                  </td>
                  <td className="px-3 py-1.5 text-[var(--color-text)]">
                    {a.agent}
                  </td>
                  <td className="px-3 py-1.5">
                    <StatusPill status={a.status} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: AgentStatus }) {
  if (status === "completed") {
    return <span style={{ color: "var(--color-ok)" }}>completed</span>;
  }
  if (status === "error") {
    return <span style={{ color: "var(--color-warn)" }}>error</span>;
  }
  if (status === "in_progress") {
    return (
      <span
        className="inline-flex items-center gap-1.5"
        style={{ color: "var(--color-accent)" }}
      >
        <span
          aria-hidden
          className="inline-block h-1.5 w-1.5 animate-pulse"
          style={{ background: "var(--color-accent)" }}
        />
        in_progress
      </span>
    );
  }
  return <span style={{ color: "var(--color-text-faint)" }}>pending</span>;
}

function MessagesPanel({ rows }: { rows: MsgRow[] }) {
  return (
    <div className="border border-[var(--color-line)] bg-[var(--color-bg)]">
      <div className="border-b border-[var(--color-line)] bg-[var(--color-surface-2)] px-3 py-2">
        <span
          className="mono text-[10px] uppercase tracking-[0.24em]"
          style={{ color: "var(--color-accent)" }}
        >
          Messages & Tools
        </span>
      </div>
      <div className="max-h-[420px] overflow-y-auto">
        {rows.length === 0 ? (
          <div className="mono px-3 py-4 text-[12px] text-[var(--color-text-faint)]">
            · awaiting first tool dispatch…
          </div>
        ) : (
          <table className="mono w-full table-fixed text-[12px]">
            <thead className="text-[var(--color-text-faint)]">
              <tr>
                <th className="w-[22%] px-3 py-2 text-left font-normal uppercase tracking-[0.18em]">
                  Time
                </th>
                <th className="w-[16%] px-3 py-2 text-left font-normal uppercase tracking-[0.18em]">
                  Type
                </th>
                <th className="w-[62%] px-3 py-2 text-left font-normal uppercase tracking-[0.18em]">
                  Content
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr
                  key={`${r.time}-${i}`}
                  className="border-t border-dashed border-[var(--color-line)] align-top"
                >
                  <td className="px-3 py-1.5 text-[var(--color-text-dim)]">
                    {r.time}
                  </td>
                  <td className="px-3 py-1.5">
                    <span
                      style={{
                        color:
                          r.type === "Tool"
                            ? "var(--color-accent)"
                            : r.type === "Agent" || r.type === "LLM"
                              ? "var(--color-ok)"
                              : "var(--color-text-dim)",
                      }}
                    >
                      {r.type}
                    </span>
                  </td>
                  <td className="break-words px-3 py-1.5 text-[var(--color-text)]">
                    {r.content.length > 220
                      ? r.content.slice(0, 217) + "…"
                      : r.content}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function CurrentReportPanel({ report, title }: { report: string; title?: string }) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [mode, setMode] = useState<ReportRenderMode>("markdown");
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [report]);
  return (
    <div className="border border-[var(--color-line)] bg-[var(--color-bg)]">
      <div className="flex items-center justify-between gap-3 border-b border-[var(--color-line)] bg-[var(--color-surface-2)] px-3 py-2">
        <div className="flex items-center gap-3">
          <span
            className="mono text-[10px] uppercase tracking-[0.24em]"
            style={{ color: "var(--color-accent)" }}
          >
            Current Report
          </span>
          {title ? (
            <span
              className="mono text-[10px] uppercase tracking-[0.2em] text-[var(--color-text-dim)]"
            >
              {title}
            </span>
          ) : null}
        </div>
        <RenderModeToggle mode={mode} onChange={setMode} />
      </div>
      <div ref={scrollRef} className="max-h-[560px] overflow-y-auto px-4 py-3">
        {!report ? (
          <p className="mono text-[12px] text-[var(--color-text-faint)]">
            · waiting for first analyst draft…
          </p>
        ) : mode === "markdown" ? (
          <Markdown>{report}</Markdown>
        ) : (
          <pre className="whitespace-pre-wrap font-mono text-[12.5px] leading-[1.55] text-[var(--color-text)]">
            {report}
          </pre>
        )}
      </div>
    </div>
  );
}

function RenderModeToggle({
  mode,
  onChange,
}: {
  mode: ReportRenderMode;
  onChange: (mode: ReportRenderMode) => void;
}) {
  return (
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
            onClick={() => onChange(m)}
            aria-pressed={active}
            className="px-2 py-1 transition-colors"
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
  );
}

function StatusFooter({
  agentsDone,
  agentsTotal,
  llm,
  tools,
  tokensUp,
  tokensDown,
  reports,
  totalReports,
  elapsed,
  done,
}: {
  agentsDone: number;
  agentsTotal: number;
  llm: number;
  tools: number;
  tokensUp: number;
  tokensDown: number;
  reports: number;
  totalReports: number;
  elapsed: number;
  done: boolean;
}) {
  const segments = [
    { label: "Agents", value: `${agentsDone}/${agentsTotal}` },
    { label: "LLM", value: String(llm) },
    { label: "Tools", value: String(tools) },
    { label: "Tokens", value: `${formatTokens(tokensUp)}↑ ${formatTokens(tokensDown)}↓` },
    { label: "Reports", value: `${reports}/${totalReports}` },
    { label: "⏱", value: fmtClock(elapsed) },
  ];
  return (
    <div
      className="mono flex flex-wrap items-center gap-x-4 gap-y-1 border border-dashed border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-2 text-[12px]"
      style={{ color: done ? "var(--color-ok)" : "var(--color-text-dim)" }}
    >
      {segments.map((s, i) => (
        <span key={s.label} className="inline-flex items-center gap-2">
          <span className="text-[var(--color-text-faint)]">{s.label}:</span>
          <span className="text-[var(--color-text)]">{s.value}</span>
          {i < segments.length - 1 ? (
            <span aria-hidden className="text-[var(--color-text-faint)]">
              |
            </span>
          ) : null}
        </span>
      ))}
    </div>
  );
}
