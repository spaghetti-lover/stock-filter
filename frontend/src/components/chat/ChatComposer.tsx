"use client";

import { useRef, useState } from "react";

export function ChatComposer({
  onSubmit,
  disabled,
}: {
  onSubmit: (text: string) => void;
  disabled?: boolean;
}) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement | null>(null);

  const send = () => {
    const t = text.trim();
    if (!t || disabled) return;
    onSubmit(t);
    setText("");
    ref.current?.focus();
  };

  return (
    <div className="border border-[var(--color-line-2)] bg-[var(--color-surface)] p-3">
      <textarea
        ref={ref}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            send();
          }
        }}
        placeholder="Ask about stocks…"
        rows={2}
        className="w-full resize-none bg-transparent text-[14px] outline-none placeholder:text-[var(--color-text-faint)]"
      />
      <div className="mt-2 flex items-center justify-between">
        <span className="tag">⏎ send · ⇧⏎ newline</span>
        <button
          onClick={send}
          disabled={disabled || !text.trim()}
          className="border border-[var(--color-accent)] bg-[var(--color-accent)] px-4 py-1 text-[11px] tracking-[0.2em] uppercase text-black disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  );
}
