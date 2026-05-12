"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { BoxPanel } from "./BoxPanel";

interface Props {
  symbol: string;
  date: string;
  analystCodes: string[];
  locked?: boolean;
  done?: boolean;
  onComplete: () => void;
}

type AgentStatus = "pending" | "in_progress" | "completed";

interface AgentRow {
  team: string;
  agent: string;
  code: string;
  status: AgentStatus;
}

interface ToolRow {
  time: string;
  type: "Tool" | "LLM" | "System";
  content: string;
}

const ANALYST_LABEL: Record<string, { agent: string; team: string }> = {
  market: { agent: "Market Analyst", team: "Analyst Team" },
  social: { agent: "Social Analyst", team: "Analyst Team" },
  news: { agent: "News Analyst", team: "Analyst Team" },
  fundamentals: { agent: "Fundamentals Analyst", team: "Analyst Team" },
};

const RESEARCH_AGENTS: AgentRow[] = [
  { team: "Research Team", agent: "Bull Researcher", code: "bull", status: "pending" },
  { team: "Research Team", agent: "Bear Researcher", code: "bear", status: "pending" },
  { team: "Research Team", agent: "Research Manager", code: "research_mgr", status: "pending" },
];

const TRADER_AGENTS: AgentRow[] = [
  { team: "Trading Team", agent: "Trader", code: "trader", status: "pending" },
];

const RISK_AGENTS: AgentRow[] = [
  { team: "Risk Team", agent: "Risky Analyst", code: "risky", status: "pending" },
  { team: "Risk Team", agent: "Safe Analyst", code: "safe", status: "pending" },
  { team: "Risk Team", agent: "Neutral Analyst", code: "neutral", status: "pending" },
  { team: "Risk Team", agent: "Risk Manager", code: "risk_mgr", status: "pending" },
];

function fmtClock(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function fmtNow(d: Date) {
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(
    2,
    "0",
  )}:${String(d.getSeconds()).padStart(2, "0")}`;
}

function buildToolScript(symbol: string, date: string): Omit<ToolRow, "time">[] {
  return [
    {
      type: "Tool",
      content: `get_ohlcv: {'ticker': '${symbol}', 'start_date': '${shiftDate(date, -60)}', 'end_date': '${date}'}`,
    },
    {
      type: "Tool",
      content: `get_indicators: {'ticker': '${symbol}', 'set': 'core', 'period': 14}`,
    },
    {
      type: "Tool",
      content: `get_news: {'ticker': '${symbol}', 'start_date': '${shiftDate(date, -7)}', 'end_date': '${date}'}`,
    },
    {
      type: "Tool",
      content: `get_global_news: {'curr_date': '${date}', 'look_back_days': 7, 'limit': 10}`,
    },
    {
      type: "Tool",
      content: `get_reddit_sentiment: {'ticker': '${symbol}', 'window': '7d'}`,
    },
    {
      type: "Tool",
      content: `get_fundamentals: {'ticker': '${symbol}', 'period': 'TTM'}`,
    },
    {
      type: "LLM",
      content: `summarize_analyst_report → market analyst draft (1812 tokens)`,
    },
    {
      type: "Tool",
      content: `vector_search: {'index': 'memory', 'query': 'recent macro tailwinds ${symbol}'}`,
    },
  ];
}

function shiftDate(iso: string, days: number) {
  const d = new Date(iso);
  d.setDate(d.getDate() + days);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

const REPORT_CHUNKS = [
  "Excellent! I now have comprehensive data to write a detailed analysis report. Let me compile everything into a thorough report.",
  "\n\n———\n\n## 📊 {SYMBOL} — Weekly Social Media, News & Sentiment Analysis Report\n\nReport Date: {DATE} | Coverage Period: rolling 7 days",
  "\n\n### 1. ⏱ Executive Summary",
  "\n\nThe {SYMBOL} ticker has had a notably bullish week driven by three dominant macro tailwinds: **strong Q1 corporate earnings**, **renewed AI investment optimism**, and **cooling geopolitical tensions** in the Middle East.",
  "\n\nMultiple sources confirmed the S&P 500 and Nasdaq 100 reached **record highs** during this period. The VIX settled at approximately **17.39**, signaling a moderate but not complacent level of investor anxiety.",
  "\n\n### 2. 🌐 Social Sentiment Pulse",
  "\n\n- Reddit r/wallstreetbets mentions: **+38% w/w**, predominantly bullish framing\n- StockTwits sentiment score: **0.62** (bullish) vs. **0.41** prior week\n- Notable retail narratives center on AI-led mega-cap leadership",
];

export function RunningStep({
  symbol,
  date,
  analystCodes,
  locked = false,
  done = false,
  onComplete,
}: Props) {
  const initialAgents = useMemo<AgentRow[]>(() => {
    const analysts: AgentRow[] = analystCodes.map((code) => ({
      code,
      agent: ANALYST_LABEL[code]?.agent ?? code,
      team: ANALYST_LABEL[code]?.team ?? "Analyst Team",
      status: "pending",
    }));
    return [...analysts, ...RESEARCH_AGENTS, ...TRADER_AGENTS, ...RISK_AGENTS];
  }, [analystCodes]);

  const [agents, setAgents] = useState<AgentRow[]>(initialAgents);
  const [tools, setTools] = useState<ToolRow[]>([]);
  const [report, setReport] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [tokensUp, setTokensUp] = useState(0);
  const [tokensDown, setTokensDown] = useState(0);
  const [reports, setReports] = useState(0);
  const [llmCalls, setLlmCalls] = useState(0);
  const completedRef = useRef(false);

  const totalAgents = initialAgents.length;
  const totalReports = 7;
  const toolScript = useMemo(() => buildToolScript(symbol, date), [symbol, date]);

  useEffect(() => {
    if (locked || done) return;

    // Wall-clock ticker
    const tickStart = Date.now();
    const tickHandle = window.setInterval(() => {
      setElapsed(Math.floor((Date.now() - tickStart) / 1000));
      setTokensUp((t) => t + Math.floor(Math.random() * 480) + 220);
      setTokensDown((t) => t + Math.floor(Math.random() * 110) + 40);
    }, 250);

    // Scripted agent + tool timeline
    const timeouts: number[] = [];
    const schedule = (ms: number, fn: () => void) => {
      timeouts.push(window.setTimeout(fn, ms));
    };

    // Stage 1: kick off first three analysts
    schedule(200, () =>
      setAgents((prev) =>
        prev.map((a, i) =>
          i === 0 ? { ...a, status: "in_progress" } : a,
        ),
      ),
    );
    schedule(400, () => pushTool(toolScript[0]));
    schedule(900, () => pushTool(toolScript[1]));
    schedule(1100, () => bumpLlm());
    schedule(1400, () => {
      setAgents((prev) =>
        prev.map((a, i) => {
          if (i === 0) return { ...a, status: "completed" };
          if (i === 1) return { ...a, status: "in_progress" };
          return a;
        }),
      );
      bumpReports();
      appendReportChunk(0);
    });
    schedule(1700, () => pushTool(toolScript[2]));
    schedule(2000, () => pushTool(toolScript[3]));
    schedule(2300, () => appendReportChunk(1));
    schedule(2600, () => bumpLlm());
    schedule(2900, () => {
      setAgents((prev) =>
        prev.map((a, i) => {
          if (i === 1) return { ...a, status: "completed" };
          if (i === 2) return { ...a, status: "in_progress" };
          return a;
        }),
      );
      bumpReports();
      appendReportChunk(2);
    });
    schedule(3200, () => pushTool(toolScript[4]));
    schedule(3500, () => appendReportChunk(3));
    schedule(3900, () => pushTool(toolScript[5]));
    schedule(4200, () => bumpLlm());
    schedule(4400, () => appendReportChunk(4));
    schedule(4800, () => {
      setAgents((prev) =>
        prev.map((a, i) => {
          if (i === 2) return { ...a, status: "completed" };
          if (i < Math.min(4, totalAgents)) return { ...a, status: "in_progress" };
          return a;
        }),
      );
      bumpReports();
    });
    schedule(5100, () => pushTool(toolScript[6]));
    schedule(5400, () => appendReportChunk(5));
    schedule(5800, () => pushTool(toolScript[7]));
    schedule(6100, () => bumpLlm());
    schedule(6300, () => appendReportChunk(6));
    schedule(6700, () => {
      setAgents((prev) =>
        prev.map((a) =>
          a.status === "in_progress" ? { ...a, status: "completed" } : a,
        ),
      );
      bumpReports();
    });
    schedule(7000, () => appendReportChunk(7));
    schedule(7300, () => {
      // Mark the rest as completed so the dashboard reads "done" before exiting
      setAgents((prev) => prev.map((a) => ({ ...a, status: "completed" })));
      setReports(totalReports);
    });
    schedule(7900, () => {
      if (completedRef.current) return;
      completedRef.current = true;
      onComplete();
    });

    function pushTool(entry: Omit<ToolRow, "time">) {
      setTools((prev) => [...prev, { ...entry, time: fmtNow(new Date()) }]);
    }
    function bumpLlm() {
      setLlmCalls((c) => c + 1);
    }
    function bumpReports() {
      setReports((r) => Math.min(totalReports, r + 1));
    }
    function appendReportChunk(idx: number) {
      const raw = REPORT_CHUNKS[idx];
      if (!raw) return;
      const chunk = raw.replace(/{SYMBOL}/g, symbol).replace(/{DATE}/g, date);
      setReport((prev) => prev + chunk);
    }

    return () => {
      window.clearInterval(tickHandle);
      timeouts.forEach((id) => window.clearTimeout(id));
    };
  }, [locked, done, onComplete, symbol, date, toolScript, totalAgents]);

  const tone = done ? "muted" : locked ? "muted" : "accent";
  const completedAgents = agents.filter((a) => a.status === "completed").length;
  const toolsCount = tools.filter((t) => t.type === "Tool").length;

  return (
    <BoxPanel title="Step 09 · Pipeline Runtime" tone={tone}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <p className="display text-[18px] tracking-tight">
            {done ? "Pipeline complete." : "Welcome to TradingAgents."}
          </p>
          <p className="text-[13px] text-[var(--color-text-dim)]">
            {done
              ? "All analyst, research, trader, and risk agents have settled."
              : `Live multi-agent run for ${symbol} · session ${date}. Streams advance automatically.`}
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <ProgressPanel agents={agents} />
          <MessagesPanel rows={tools} />
        </div>

        <CurrentReportPanel report={report} />

        <StatusFooter
          agentsDone={completedAgents}
          agentsTotal={totalAgents}
          llm={llmCalls}
          tools={toolsCount}
          tokensUp={tokensUp}
          tokensDown={tokensDown}
          reports={reports}
          totalReports={totalReports}
          elapsed={elapsed}
          done={done}
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
      <div className="max-h-[260px] overflow-y-auto">
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
                  key={`${a.code}-${i}`}
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
    return (
      <span style={{ color: "var(--color-ok)" }}>completed</span>
    );
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
  return (
    <span style={{ color: "var(--color-text-faint)" }}>pending</span>
  );
}

function MessagesPanel({ rows }: { rows: ToolRow[] }) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [rows]);
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
      <div ref={scrollRef} className="max-h-[260px] overflow-y-auto">
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
                  key={i}
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
                            : r.type === "LLM"
                              ? "var(--color-ok)"
                              : "var(--color-text-dim)",
                      }}
                    >
                      {r.type}
                    </span>
                  </td>
                  <td className="break-words px-3 py-1.5 text-[var(--color-text)]">
                    {r.content}
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

function CurrentReportPanel({ report }: { report: string }) {
  return (
    <div className="border border-[var(--color-line)] bg-[var(--color-bg)]">
      <div className="border-b border-[var(--color-line)] bg-[var(--color-surface-2)] px-3 py-2">
        <span
          className="mono text-[10px] uppercase tracking-[0.24em]"
          style={{ color: "var(--color-accent)" }}
        >
          Current Report
        </span>
      </div>
      <div className="max-h-[320px] overflow-y-auto px-4 py-3">
        {report.length === 0 ? (
          <p className="mono text-[12px] text-[var(--color-text-faint)]">
            · waiting for first analyst draft…
          </p>
        ) : (
          <pre className="whitespace-pre-wrap font-mono text-[12.5px] leading-[1.55] text-[var(--color-text)]">
            {report}
            <span
              aria-hidden
              className="ml-0.5 inline-block h-[1em] w-[0.55ch] -translate-y-[2px] animate-pulse"
              style={{ background: "var(--color-accent)" }}
            />
          </pre>
        )}
      </div>
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
    {
      label: "Tokens",
      value: `${formatTokens(tokensUp)}↑ ${formatTokens(tokensDown)}↓`,
    },
    { label: "Reports", value: `${reports}/${totalReports}` },
    { label: "⏱", value: fmtClock(elapsed) },
  ];
  return (
    <div
      className="mono flex flex-wrap items-center gap-x-4 gap-y-1 border border-dashed border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-2 text-[12px]"
      style={{
        color: done ? "var(--color-ok)" : "var(--color-text-dim)",
      }}
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

function formatTokens(n: number) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}
