"use client";

import { motion } from "motion/react";
import type { ChatMessage } from "@/lib/types";
import { Markdown } from "./Markdown";

export function ChatThread({ messages, pending }: { messages: ChatMessage[]; pending: boolean }) {
  if (!messages.length && !pending) {
    return (
      <div className="flex flex-col items-start gap-3 border border-dashed border-[var(--color-line-2)] px-6 py-10">
        <span className="tag">empty thread</span>
        <p className="display text-[26px] tracking-tight">Ask about the passing set.</p>
        <p className="max-w-[60ch] text-[13px] text-[var(--color-text-dim)]">
          The assistant receives the stocks from your last Layer 1 scan as context. Try
          <span className="mono text-[var(--color-accent)]"> "summarize the strongest names"</span>.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {messages.map((m, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="flex gap-4"
        >
          <div className="w-[64px] shrink-0 pt-1">
            <span className="tag" style={{ color: m.role === "user" ? "var(--color-accent)" : "var(--color-text-dim)" }}>
              {m.role === "user" ? "You" : "Asst"}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            {m.role === "assistant" ? (
              <Markdown>{m.content}</Markdown>
            ) : (
              <div className="whitespace-pre-wrap text-[14px] leading-relaxed text-[var(--color-text)]">
                {m.content}
              </div>
            )}
          </div>
        </motion.div>
      ))}
      {pending ? (
        <div className="flex gap-4">
          <div className="w-[64px] shrink-0">
            <span className="tag">Asst</span>
          </div>
          <div className="mono flex items-center gap-1 text-[12px] text-[var(--color-text-dim)]">
            <Dot delay={0} />
            <Dot delay={120} />
            <Dot delay={240} />
            <span className="pl-2">thinking</span>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Dot({ delay }: { delay: number }) {
  return (
    <motion.span
      animate={{ opacity: [0.2, 1, 0.2] }}
      transition={{ duration: 1.1, repeat: Infinity, delay: delay / 1000 }}
      className="h-1.5 w-1.5 bg-[var(--color-accent)]"
    />
  );
}
