"use client";

const ROWS = [
  "─── ─── ─── ─── ─── ─── ─── ─── ───",
];

export function AsciiBanner() {
  return (
    <div className="flex flex-col items-center gap-5">
      {/* Top ornamental bar */}
      <div className="flex items-center gap-3">
        <span
          aria-hidden
          className="block h-px w-16"
          style={{
            background: "linear-gradient(to right, transparent, var(--color-accent))",
          }}
        />
        <span
          aria-hidden
          className="block h-2 w-2 rotate-45"
          style={{
            background: "var(--color-accent)",
            boxShadow: "0 0 12px var(--color-accent)",
          }}
        />
        <span
          className="mono text-[10px] uppercase tracking-[0.32em]"
          style={{ color: "var(--color-accent)" }}
        >
          Phung Duc Anh
        </span>
        <span
          aria-hidden
          className="block h-2 w-2 rotate-45"
          style={{
            background: "var(--color-accent)",
            boxShadow: "0 0 12px var(--color-accent)",
          }}
        />
        <span
          aria-hidden
          className="block h-px w-16"
          style={{
            background: "linear-gradient(to left, transparent, var(--color-accent))",
          }}
        />
      </div>

      {/* The headline */}
      <h2
        className="display select-none text-center leading-[0.88] tracking-[-0.02em]"
        style={{
          fontVariationSettings: '"opsz" 144, "SOFT" 30',
          fontSize: "clamp(48px, 9vw, 104px)",
          color: "var(--color-text)",
        }}
      >
        Trading
        <span
          className="block italic"
          style={{
            color: "var(--color-accent)",
            textShadow:
              "0 0 18px color-mix(in srgb, var(--color-accent) 32%, transparent)",
          }}
        >
          Agents
        </span>
      </h2>

      {/* Mono caption */}
      <pre
        aria-hidden
        className="mono select-none whitespace-pre text-[9.5px] leading-[1] text-[var(--color-text-faint)] md:text-[11px]"
      >
        {ROWS[0]}
      </pre>
    </div>
  );
}
