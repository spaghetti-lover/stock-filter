"use client";

import { useEffect, useRef } from "react";
import { FilterCard } from "./FilterCard";
import { applyAIFilter } from "@/lib/aiFilter";
import { useCopilotStore, useStocksStore } from "@/lib/store";
import type { CopilotMessage } from "@/lib/store";

interface Props {
  onError: (msg: string) => void;
}

export function ChatThread({ onError }: Props) {
  const messages = useCopilotStore((s) => s.messages);
  const setActiveConditions = useCopilotStore((s) => s.setActiveConditions);
  const appendMessage = useCopilotStore((s) => s.appendMessage);
  const markCardApplied = useCopilotStore((s) => s.markCardApplied);
  const setStocks = useStocksStore((s) => s.setStocks);

  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleApply = async (m: Extract<CopilotMessage, { kind: "filter_card" }>) => {
    setActiveConditions(m.conditions);
    try {
      const data = await applyAIFilter({ conditions: m.conditions });
      setStocks(data.passed, data.rejected);
      markCardApplied(m.id);
      appendMessage({
        id: `applied-${Date.now()}`,
        kind: "filter_applied",
        role: "assistant",
        count: data.passed.length,
        summary: m.summary,
      });
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto px-4 py-4"
    >
      <div className="flex flex-col gap-3">
        {messages.map((m) => (
          <MessageRow key={m.id} message={m} onApply={handleApply} />
        ))}
      </div>
    </div>
  );
}

function MessageRow({
  message,
  onApply,
}: {
  message: CopilotMessage;
  onApply: (m: Extract<CopilotMessage, { kind: "filter_card" }>) => void;
}) {
  if (message.kind === "text") {
    if (message.role === "user") {
      return (
        <div className="flex justify-end">
          <div className="max-w-[85%] border border-[var(--color-accent)]/40 bg-[var(--color-accent)]/10 px-3 py-2 text-[13px] text-[var(--color-text)]">
            {message.content}
          </div>
        </div>
      );
    }
    return (
      <div className="flex justify-start">
        <div className="max-w-[85%] text-[13px] text-[var(--color-text-dim)]">
          {message.content}
        </div>
      </div>
    );
  }
  if (message.kind === "filter_card") {
    return (
      <FilterCard
        summary={message.summary}
        conditions={message.conditions}
        unsupported={message.unsupported}
        applied={message.applied}
        onApply={() => onApply(message)}
      />
    );
  }
  // filter_applied
  return (
    <div className="border-l-2 border-[var(--color-ok)] bg-[var(--color-surface)] px-3 py-2 text-[12px] text-[var(--color-text-dim)]">
      <span className="text-[var(--color-ok)]">●</span> Applied: {message.count} stocks match —{" "}
      {message.summary}
    </div>
  );
}
