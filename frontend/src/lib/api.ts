import type { ChatMessage, Layer2Response, Provider } from "./types";
import type { SmartMoneyFlowResponse } from "@/components/layer2/smart-money/types";

export const API_BASE = "/api";

export async function fetchLayer2Latest(): Promise<Layer2Response> {
  const res = await fetch(`${API_BASE}/layer2/latest`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Layer 2 fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchSmartMoneyFlow(symbol: string): Promise<SmartMoneyFlowResponse> {
  const res = await fetch(`${API_BASE}/layer2/smart-money/${encodeURIComponent(symbol)}?days=60`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Smart money fetch failed: ${res.status}`);
  return res.json();
}

export async function postChat(payload: {
  messages: ChatMessage[];
  stocks_context: unknown[] | null;
  provider: Provider;
}): Promise<{ response: string; provider: string }> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      if (j?.detail) detail = j.detail;
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status} — ${detail}`);
  }
  return res.json();
}
