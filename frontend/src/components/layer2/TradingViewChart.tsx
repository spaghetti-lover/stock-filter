"use client";

import { useEffect, useRef } from "react";

const CHART_HEIGHT = 460;

export function TradingViewChart({ symbol, exchange }: { symbol: string; exchange: string }) {
  const widgetRef = useRef<HTMLDivElement>(null);
  const tvSymbol = `${exchange}:${symbol}`;

  useEffect(() => {
    const widget = widgetRef.current;
    if (!widget) return;

    // Build a fresh wrapper the TradingView loader owns, leaving the React-managed
    // widgetRef div untouched so the loader's async callbacks never hit a null node.
    const mount = document.createElement("div");
    mount.style.height = `${CHART_HEIGHT}px`;
    mount.style.width = "100%";
    widget.appendChild(mount);

    const script = document.createElement("script");
    script.src =
      "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      symbol: tvSymbol,
      interval: "D",
      timezone: "Asia/Ho_Chi_Minh",
      theme: "dark",
      style: "1",
      locale: "en",
      hide_side_toolbar: false,
      allow_symbol_change: false,
      backgroundColor: "rgba(0, 0, 0, 0)",
      support_host: "https://www.tradingview.com",
      width: "100%",
      height: CHART_HEIGHT,
    });
    mount.appendChild(script);

    return () => {
      // Remove only the TradingView-owned subtree; React keeps owning widgetRef.
      mount.remove();
    };
  }, [tvSymbol]);

  return (
    <div
      ref={widgetRef}
      className="overflow-hidden rounded-sm border border-[var(--color-line)]"
      style={{ height: CHART_HEIGHT }}
    />
  );
}
