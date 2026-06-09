"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Stock } from "./types";
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
