"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { postChat } from "@/lib/api";
import { useStocksStore } from "@/lib/store";
import { ProviderPicker } from "@/components/chat/ProviderPicker";
import { ChatThread } from "@/components/chat/ChatThread";
import { ChatComposer } from "@/components/chat/ChatComposer";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Banner } from "@/components/ui/Banner";
import type { ChatMessage, Provider } from "@/lib/types";

export default function ChatPage() {
  const [provider, setProvider] = useState<Provider>("claude");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const lastStocks = useStocksStore((s) => s.lastStocks);

  const mutation = useMutation({
    mutationFn: async (next: ChatMessage[]) =>
      postChat({
        messages: next,
        stocks_context: lastStocks.length ? lastStocks : null,
        provider,
      }),
    onError: (e: unknown) => setError(e instanceof Error ? e.message : String(e)),
    onSuccess: (res) => {
      setMessages((m) => [...m, { role: "assistant", content: res.response }]);
    },
  });

  const send = (text: string) => {
    setError(null);
    const next: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    mutation.mutate(next);
  };

  return (
    <div>
      <div className="hairline-grid border-b border-[var(--color-line)]">
        <div className="mx-auto max-w-[920px] px-8 pb-10 pt-12">
          <SectionHeader
            index="ASST"
            eyebrow="Assistant · multi-provider"
            title="Talk to your screen."
            description="A short-context assistant that reads your last Layer 1 result. Switch providers freely — the conversation persists across the swap."
            right={<ProviderPicker value={provider} onChange={setProvider} />}
          />
        </div>
      </div>

      <div className="mx-auto flex max-w-[920px] flex-col gap-6 px-8 py-10">
        <div className="flex items-center justify-between">
          <span className="tag">
            {lastStocks.length
              ? `context · ${lastStocks.length} stocks attached`
              : "context · no stocks attached"}
          </span>
          {messages.length ? (
            <button
              onClick={() => setMessages([])}
              className="mono text-[11px] tracking-[0.18em] uppercase text-[var(--color-text-dim)] hover:text-[var(--color-text)]"
            >
              Clear thread
            </button>
          ) : null}
        </div>

        {error ? (
          <Banner tone="danger" label="error">
            {error}
          </Banner>
        ) : null}

        <ChatThread messages={messages} pending={mutation.isPending} />

        <div className="sticky bottom-4">
          <ChatComposer onSubmit={send} disabled={mutation.isPending} />
        </div>
      </div>
    </div>
  );
}
