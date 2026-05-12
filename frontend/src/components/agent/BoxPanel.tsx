import type { ReactNode } from "react";

interface Props {
  title?: string;
  tone?: "accent" | "muted" | "warn";
  children: ReactNode;
  className?: string;
}

const TONE: Record<NonNullable<Props["tone"]>, string> = {
  accent: "var(--color-accent)",
  muted: "var(--color-line-2)",
  warn: "var(--color-warn)",
};

export function BoxPanel({ title, tone = "muted", children, className = "" }: Props) {
  const color = TONE[tone];
  return (
    <section
      className={`relative ${className}`}
      style={{
        border: `1px solid ${color}`,
        background:
          "linear-gradient(180deg, color-mix(in srgb, var(--color-surface) 60%, transparent), transparent)",
      }}
    >
      {title ? (
        <div
          className="pointer-events-none absolute left-6 top-0 -translate-y-1/2 px-2"
          style={{ background: "var(--color-bg)" }}
        >
          <span
            className="mono text-[10.5px] uppercase tracking-[0.24em]"
            style={{ color }}
          >
            {title}
          </span>
        </div>
      ) : null}
      <div className="px-6 py-6">{children}</div>
    </section>
  );
}
