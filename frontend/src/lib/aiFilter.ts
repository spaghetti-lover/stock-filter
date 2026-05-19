import { API_BASE } from "./api";
import type {
  AIFilterApplyRequest,
  AIFilterCatalogEntry,
  AIFilterCatalogResponse,
  AIFilterParseRequest,
  AIFilterParseResponse,
} from "./aiFilterTypes";
import type { FilteredStocksResponse } from "./types";

export function renderLabel(
  entry: AIFilterCatalogEntry,
  params: Record<string, unknown>,
): string {
  const merged: Record<string, unknown> = {};
  for (const p of entry.params) merged[p.name] = p.default;
  for (const [k, v] of Object.entries(params ?? {})) merged[k] = v;
  return entry.label_template.replace(/\{(\w+)\}/g, (_match, key) => {
    const v = merged[key];
    if (Array.isArray(v)) return `[${v.map((x) => `'${x}'`).join(", ")}]`;
    return v === undefined ? `{${key}}` : String(v);
  });
}

async function readError(res: Response): Promise<string> {
  let detail = res.statusText;
  try {
    const j = await res.json();
    if (j?.detail) detail = j.detail;
  } catch {
    /* ignore */
  }
  return `${res.status} — ${detail}`;
}

export async function fetchAIFilterCatalog(): Promise<AIFilterCatalogResponse> {
  const res = await fetch(`${API_BASE}/ai-filter/catalog`, { cache: "no-store" });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function parseAIFilter(
  payload: AIFilterParseRequest,
): Promise<AIFilterParseResponse> {
  const res = await fetch(`${API_BASE}/ai-filter/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function applyAIFilter(
  payload: AIFilterApplyRequest,
): Promise<FilteredStocksResponse> {
  const res = await fetch(`${API_BASE}/ai-filter/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}
