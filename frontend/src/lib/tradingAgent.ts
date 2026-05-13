// Thin client around the trading-agent endpoints, served by the main backend.

export const TRADING_AGENT_BASE = "/api";

export interface CatalogChoice {
  label: string;
  value: string;
}

export interface CatalogResponse {
  analysts: string[];
  languages: string[];
  depths: { label: string; hint: string; value: number }[];
  providers: { label: string; key: string; backend_url: string | null }[];
  models: Record<string, { quick: CatalogChoice[]; deep: CatalogChoice[] }>;
}

export interface AnnouncementsResponse {
  announcements: string[];
  require_attention: boolean;
}

export interface StartRunPayload {
  ticker: string;
  analysis_date: string;
  output_language: string;
  analysts: string[];
  research_depth: 1 | 3 | 5;
  llm_provider: string;
  shallow_thinker: string;
  deep_thinker: string;
  google_thinking_level?: string | null;
  openai_reasoning_effort?: string | null;
  anthropic_effort?: string | null;
  backend_url?: string | null;
}

export interface StartRunResponse {
  run_id: string;
}

export interface RunReports {
  market_report?: string;
  sentiment_report?: string;
  news_report?: string;
  fundamentals_report?: string;
  investment_plan?: string;
  trader_investment_plan?: string;
  final_trade_decision?: string;
  [key: string]: string | undefined;
}

export interface RunReportResponse {
  run_id: string;
  status: string;
  ticker: string;
  analysis_date: string;
  reports: RunReports;
  final_state: Record<string, unknown> | null;
}

export type AgentRunStatus = "pending" | "running" | "done" | "error";

export interface RunSnapshot {
  run_id: string;
  status: AgentRunStatus;
  agents: Record<string, "pending" | "in_progress" | "completed" | "error">;
  reports: RunReports;
  stats: { llm_calls: number; tool_calls: number; tokens_in: number; tokens_out: number };
  messages: { time: string; type: string; content: string }[];
  tool_calls: { time: string; name: string; args: string }[];
  error: string | null;
  elapsed_seconds: number;
}

// ── SSE event shapes ──────────────────────────────────────────────────

export type AgentSseEvent =
  | { type: "snapshot"; agents: RunSnapshot["agents"]; reports: RunReports; stats: RunSnapshot["stats"]; messages: RunSnapshot["messages"]; tool_calls: RunSnapshot["tool_calls"]; status: AgentRunStatus; time?: string }
  | { type: "agent_status"; agent: string; status: "pending" | "in_progress" | "completed" | "error"; time?: string }
  | { type: "report"; section: string; title: string; content: string; time?: string }
  | { type: "message"; msg_type: string; content: string; time?: string }
  | { type: "tool_call"; name: string; args: string; time?: string }
  | { type: "stats"; stats: RunSnapshot["stats"]; time?: string }
  | { type: "complete_report"; content: string; time?: string }
  | { type: "final_state"; state: Record<string, unknown>; time?: string }
  | { type: "status"; status: AgentRunStatus; error?: string | null; traceback?: string; time?: string };

// ── HTTP helpers ───────────────────────────────────────────────────────

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${TRADING_AGENT_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

export function fetchCatalog(): Promise<CatalogResponse> {
  return getJson<CatalogResponse>("/trading-agent/catalog");
}

export function fetchAnnouncements(): Promise<AnnouncementsResponse> {
  return getJson<AnnouncementsResponse>("/trading-agent/announcements");
}

export async function startRun(payload: StartRunPayload): Promise<StartRunResponse> {
  const res = await fetch(`${TRADING_AGENT_BASE}/trading-agent/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      if (j?.detail) detail = j.detail;
    } catch { /* ignore */ }
    throw new Error(`start run: ${res.status} — ${detail}`);
  }
  return res.json();
}

export function fetchRunReport(runId: string): Promise<RunReportResponse> {
  return getJson<RunReportResponse>(`/trading-agent/run/${runId}/report`);
}

export async function saveRunReport(runId: string, savePath?: string): Promise<{ saved_to: string; save_path: string }> {
  const res = await fetch(`${TRADING_AGENT_BASE}/trading-agent/run/${runId}/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(savePath ? { save_path: savePath } : {}),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      if (j?.detail) detail = j.detail;
    } catch { /* ignore */ }
    throw new Error(`save report: ${res.status} — ${detail}`);
  }
  return res.json();
}

// ── SSE ────────────────────────────────────────────────────────────────

export function openAgentStream(
  runId: string,
  onEvent: (e: AgentSseEvent) => void,
  onClose?: () => void,
): { close: () => void } {
  const source = new EventSource(
    `${TRADING_AGENT_BASE}/trading-agent/stream/${runId}`,
  );
  let finished = false;

  const finish = () => {
    if (finished) return;
    finished = true;
    source.close();
    onClose?.();
  };

  source.onmessage = (ev) => {
    if (finished) return;
    try {
      const payload = JSON.parse(ev.data) as AgentSseEvent;
      onEvent(payload);
      if (payload.type === "status" && (payload.status === "done" || payload.status === "error")) {
        finish();
      }
    } catch (err) {
      console.error("agent SSE parse error", err);
    }
  };

  source.onerror = () => {
    if (finished) return;
    onEvent({ type: "status", status: "error", error: "Connection lost" });
    finish();
  };

  return {
    close: () => {
      finished = true;
      source.close();
    },
  };
}
