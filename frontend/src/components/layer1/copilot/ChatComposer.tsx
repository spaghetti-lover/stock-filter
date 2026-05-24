"use client";

import { useEffect, useRef, useState } from "react";
import { parseAIFilter } from "@/lib/aiFilter";
import { useCopilotStore } from "@/lib/store";

interface Props {
  onError: (msg: string) => void;
}

export function ChatComposer({ onError }: Props) {
  const provider = useCopilotStore((s) => s.provider);
  const pendingPrompt = useCopilotStore((s) => s.pendingPrompt);
  const setPendingPrompt = useCopilotStore((s) => s.setPendingPrompt);
  const appendMessage = useCopilotStore((s) => s.appendMessage);
  const [busy, setBusy] = useState(false);
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (pendingPrompt && ref.current) ref.current.focus();
  }, [pendingPrompt]);

  const send = async () => {
    const text = pendingPrompt.trim();
    if (!text || busy) return;
    setBusy(true);

    const userId = `u-${Date.now()}`;
    appendMessage({ id: userId, kind: "text", role: "user", content: text });
    setPendingPrompt("");

    try {
      const res = await parseAIFilter({ prompt: text, provider });
      appendMessage({
        id: `card-${Date.now()}`,
        kind: "filter_card",
        role: "assistant",
        summary: res.summary,
        conditions: res.conditions,
        unsupported: res.unsupported,
      });
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
      appendMessage({
        id: `err-${Date.now()}`,
        kind: "text",
        role: "assistant",
        content: "Sorry, parsing failed.",
      });
    } finally {
      setBusy(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="flex flex-col gap-2 border-t border-[var(--color-line)] px-4 py-3">
      <textarea
        ref={ref}
        value={pendingPrompt}
        onChange={(e) => setPendingPrompt(e.target.value)}
        onKeyDown={onKeyDown}
        rows={2}
        placeholder="Hỗ trợ lọc cổ phiếu… (Enter to send)"
        className="w-full resize-none border border-[var(--color-line-2)] bg-[var(--color-bg)] p-2.5 font-mono text-[12px] text-[var(--color-text)] placeholder:text-[var(--color-text-dim)] focus:border-[var(--color-accent)] focus:outline-none"
      />
      <button
        type="button"
        onClick={send}
        disabled={busy || !pendingPrompt.trim()}
        className="mono w-full border border-[var(--color-accent)] bg-[var(--color-accent)] py-1.5 text-center text-[11px] tracking-[0.18em] uppercase text-black transition-colors hover:bg-[var(--color-accent-dim)] disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "Parsing…" : "Send"}
      </button>
    </div>
  );
}
