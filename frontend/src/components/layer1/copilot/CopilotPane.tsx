"use client";

import { ChatThread } from "./ChatThread";
import { ChatComposer } from "./ChatComposer";
import { SuggestedPrompts } from "./SuggestedPrompts";
import { useCopilotStore } from "@/lib/store";
import type { Provider } from "@/lib/types";

interface Props {
  onError: (msg: string) => void;
}

export function CopilotPane({ onError }: Props) {
  const collapsed = useCopilotStore((s) => s.collapsed);
  const toggleCollapsed = useCopilotStore((s) => s.toggleCollapsed);
  const provider = useCopilotStore((s) => s.provider);
  const setProvider = useCopilotStore((s) => s.setProvider);
  const setPendingPrompt = useCopilotStore((s) => s.setPendingPrompt);
  const clear = useCopilotStore((s) => s.clear);

  if (collapsed) {
    return (
      <aside className="sticky top-16 flex h-[calc(100vh-4rem)] w-12 shrink-0 flex-col items-center border-l border-[var(--color-line)] bg-[var(--color-bg)] py-3">
        <button
          type="button"
          onClick={toggleCollapsed}
          aria-label="Open copilot"
          className="tag rotate-90 whitespace-nowrap px-2 py-3 tracking-[0.18em] text-[var(--color-text-dim)] hover:text-[var(--color-accent)]"
        >
          ‹ Copilot
        </button>
      </aside>
    );
  }

  return (
    <aside className="sticky top-16 flex h-[calc(100vh-4rem)] w-[360px] shrink-0 flex-col border-l border-[var(--color-line)] bg-[var(--color-bg)]">
      <header className="flex items-center justify-between border-b border-[var(--color-line)] px-4 py-3">
        <div className="flex flex-col">
          <div className="display text-[16px] tracking-tight">Copilot</div>
          <div className="tag text-[var(--color-text-dim)]">AI filter assistant</div>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as Provider)}
            className="mono border border-[var(--color-line-2)] bg-[var(--color-bg)] px-1.5 py-1 text-[11px] focus:border-[var(--color-accent)] focus:outline-none"
          >
            <option value="claude">claude</option>
            <option value="gemini">gemini</option>
          </select>
          <button
            type="button"
            onClick={clear}
            aria-label="Clear chat"
            className="mono px-1.5 py-1 text-[11px] tracking-[0.16em] uppercase text-[var(--color-text-dim)] hover:text-[var(--color-danger)]"
          >
            clear
          </button>
          <button
            type="button"
            onClick={toggleCollapsed}
            aria-label="Collapse copilot"
            className="mono px-1.5 py-1 text-[14px] text-[var(--color-text-dim)] hover:text-[var(--color-accent)]"
          >
            ›
          </button>
        </div>
      </header>

      <ChatThread onError={onError} />
      <SuggestedPrompts onPick={(s) => setPendingPrompt(s)} />
      <ChatComposer onError={onError} />
    </aside>
  );
}
