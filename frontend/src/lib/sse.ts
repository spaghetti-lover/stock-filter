// Native EventSource doesn't expose response status cleanly, but it auto-reconnects
// on transient drops. We disable reconnection by closing on error/result.

import type { SSEEvent } from "./types";

export function openSSE(
  url: string,
  onEvent: (e: SSEEvent) => void,
  onClose?: () => void,
): { close: () => void } {
  const source = new EventSource(url);
  let finished = false;

  const finish = () => {
    if (finished) return;
    finished = true;
    source.close();
    onClose?.();
  };

  source.onmessage = (ev) => {
    if (finished) return;
    try {
      const payload = JSON.parse(ev.data) as SSEEvent;
      onEvent(payload);
      if (payload.type === "result" || payload.type === "error") finish();
    } catch (err) {
      console.error("SSE parse error", err);
    }
  };

  source.onerror = () => {
    // EventSource fires onerror on normal close too; ignore if we've already
    // received a terminal event so we don't surface a phantom "Connection lost".
    if (finished) return;
    onEvent({ type: "error", detail: "Connection lost" });
    finish();
  };

  return {
    close: () => {
      finished = true;
      source.close();
    },
  };
}
