"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/layer1", label: "Layer 01", title: "Hard filters" },
  { href: "/layer2", label: "Layer 02", title: "BUY score" },
  { href: "/agent", label: "Agent", title: "Trading Agent" },
  { href: "/chat", label: "Assistant", title: "Stock chat" },
];

export function TopNav() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--color-line)] bg-[var(--color-bg)]/95 backdrop-blur">
      <div className="flex h-16 items-stretch">
        {/* Brand block */}
        <Link
          href="/layer1"
          className="flex items-center gap-3 border-r border-[var(--color-line)] px-5 transition-colors hover:bg-[var(--color-surface)]"
        >
          <span
            aria-hidden
            className="block h-3 w-3 rotate-45 bg-[var(--color-accent)]"
            style={{ boxShadow: "0 0 12px var(--color-accent)" }}
          />
          <div className="flex flex-col leading-none">
            <span className="mono text-[11px] tracking-[0.22em] text-[var(--color-text-dim)]">
              VN/STOCK
            </span>
            <span className="display text-[15px] tracking-tight">AgentTrader</span>
          </div>
        </Link>
        {/* Routes */}
        <nav className="flex items-stretch">
          {NAV.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex flex-col justify-center gap-0.5 border-r border-[var(--color-line)] px-5 transition-colors ${
                  active
                    ? "bg-[var(--color-surface)] text-[var(--color-text)]"
                    : "text-[var(--color-text-dim)] hover:bg-[var(--color-surface)]/60 hover:text-[var(--color-text)]"
                }`}
              >
                <span className="mono text-[10px] tracking-[0.2em] uppercase opacity-90">
                  {item.label}
                </span>
                <span className="text-[14px] leading-none">{item.title}</span>
                {active ? (
                  <span
                    aria-hidden
                    className="absolute bottom-[-1px] left-0 h-[2px] w-full bg-[var(--color-accent)]"
                    style={{ boxShadow: "0 0 10px var(--color-accent)" }}
                  />
                ) : null}
              </Link>
            );
          })}
        </nav>
        <div className="flex-1" />
        {/* Status block */}
        <div className="hidden md:flex items-center gap-4 px-5">
          <span className="flex items-center gap-2">
            <span className="block h-1.5 w-1.5 bg-[var(--color-ok)]" />
            <span className="mono text-[11px] text-[var(--color-text-dim)]">live</span>
          </span>
        </div>
      </div>
    </header>
  );
}
