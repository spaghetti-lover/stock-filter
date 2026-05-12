import type { ReactNode } from "react";

type Tone = "neutral" | "accent" | "warn" | "danger" | "ok";

const TONE: Record<Tone, string> = {
  neutral: "text-[var(--color-text-dim)] border-[var(--color-line-2)]",
  accent: "text-[var(--color-accent)] border-[var(--color-accent)]/60 bg-[var(--color-accent)]/5",
  warn: "text-[var(--color-warn)] border-[var(--color-warn)]/60",
  danger: "text-[var(--color-danger)] border-[var(--color-danger)]/60",
  ok: "text-[var(--color-ok)] border-[var(--color-ok)]/60",
};

export function Pill({ children, tone = "neutral" }: { children: ReactNode; tone?: Tone }) {
  return (
    <span
      className={`mono inline-flex items-center border px-1.5 py-[2px] text-[10px] tracking-[0.16em] uppercase ${TONE[tone]}`}
    >
      {children}
    </span>
  );
}
