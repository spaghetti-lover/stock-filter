"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Provider, Stock } from "./types";
import type { AIFilterCondition } from "./aiFilterTypes";
import { DEFAULT_WEIGHTS, type Weights } from "./scoring";

// ── Cross-page stock context (used by /chat) ──────────────────────────
interface StocksState {
  lastStocks: Stock[];
  passedStocks: Stock[];
  setStocks: (passed: Stock[], rejected: Stock[]) => void;
  clear: () => void;
}

export const useStocksStore = create<StocksState>()(
  persist(
    (set) => ({
      lastStocks: [],
      passedStocks: [],
      setStocks: (passed, rejected) =>
        set({ lastStocks: [...passed, ...rejected], passedStocks: passed }),
      clear: () => set({ lastStocks: [], passedStocks: [] }),
    }),
    { name: "stock-filter:last-stocks" },
  ),
);

// ── Layer 2 weights ────────────────────────────────────────────────────
interface WeightsState {
  weights: Weights;
  setWeight: (key: string, value: number) => void;
  reset: () => void;
}

export const useWeightsStore = create<WeightsState>()(
  persist(
    (set) => ({
      weights: { ...DEFAULT_WEIGHTS },
      setWeight: (key, value) =>
        set((s) => ({ weights: { ...s.weights, [key]: value } })),
      reset: () => set({ weights: { ...DEFAULT_WEIGHTS } }),
    }),
    { name: "stock-filter:weights" },
  ),
);

// ── Copilot (Layer 1 AI Filter side pane) ──────────────────────────────
export type CopilotMessage =
  | { id: string; kind: "text"; role: "user" | "assistant"; content: string }
  | {
      id: string;
      kind: "filter_card";
      role: "assistant";
      summary: string;
      conditions: AIFilterCondition[];
      unsupported: string[];
      applied?: boolean;
    }
  | { id: string; kind: "filter_applied"; role: "assistant"; count: number; summary: string };

interface CopilotState {
  messages: CopilotMessage[];
  provider: Provider;
  pendingPrompt: string;
  collapsed: boolean;
  activeConditions: AIFilterCondition[];

  appendMessage: (m: CopilotMessage) => void;
  markCardApplied: (id: string) => void;
  setProvider: (p: Provider) => void;
  setPendingPrompt: (s: string) => void;
  toggleCollapsed: () => void;
  setActiveConditions: (cs: AIFilterCondition[]) => void;
  updateConditionParams: (index: number, params: Record<string, unknown>) => void;
  removeCondition: (index: number) => void;
  clear: () => void;
}

const INTRO_MESSAGE: CopilotMessage = {
  id: "intro",
  kind: "text",
  role: "assistant",
  content:
    "Xin chào, tôi là Stock Copilot. Mô tả bộ lọc bạn muốn (VD: \"Lọc cổ phiếu thanh khoản cao\") và tôi sẽ chuyển nó thành điều kiện cụ thể.",
};

export const useCopilotStore = create<CopilotState>()(
  persist(
    (set) => ({
      messages: [INTRO_MESSAGE],
      provider: "claude",
      pendingPrompt: "",
      collapsed: false,
      activeConditions: [],

      appendMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
      markCardApplied: (id) =>
        set((s) => ({
          messages: s.messages.map((m) =>
            m.id === id && m.kind === "filter_card" ? { ...m, applied: true } : m,
          ),
        })),
      setProvider: (provider) => set({ provider }),
      setPendingPrompt: (pendingPrompt) => set({ pendingPrompt }),
      toggleCollapsed: () => set((s) => ({ collapsed: !s.collapsed })),
      setActiveConditions: (activeConditions) => set({ activeConditions }),
      updateConditionParams: (index, params) =>
        set((s) => ({
          activeConditions: s.activeConditions.map((c, i) =>
            i === index ? { ...c, params: { ...c.params, ...params } } : c,
          ),
        })),
      removeCondition: (index) =>
        set((s) => ({
          activeConditions: s.activeConditions.filter((_, i) => i !== index),
        })),
      clear: () =>
        set({
          messages: [INTRO_MESSAGE],
          pendingPrompt: "",
          activeConditions: [],
        }),
    }),
    { name: "stock-filter:copilot", version: 2 },
  ),
);
