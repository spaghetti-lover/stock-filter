import type { ReactNode } from "react";

type Tone = "info" | "warn" | "danger";
const TONE_BORDER: Record<Tone, string> = {
  info: "border-[var(--color-line-2)]",
  warn: "border-[var(--color-warn)]/60",
  danger: "border-[var(--color-danger)]/60",
};
const TONE_RULE: Record<Tone, string> = {
  info: "bg-[var(--color-text-dim)]",
  warn: "bg-[var(--color-warn)]",
  danger: "bg-[var(--color-danger)]",
};
const TONE_LABEL: Record<Tone, string> = {
  info: "text-[var(--color-text-dim)]",
  warn: "text-[var(--color-warn)]",
  danger: "text-[var(--color-danger)]",
};

export function Banner({
  tone = "info",
  label,
  children,
}: {
  tone?: Tone;
  label?: string;
  children: ReactNode;
}) {
  return (
    <div className={`flex border-l-2 ${TONE_BORDER[tone]} ${TONE_RULE[tone]}`}>
      <div className="flex-1 border-y border-r border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-3">
        {label ? (
          <div className={`tag mb-1 ${TONE_LABEL[tone]}`}>{label}</div>
        ) : null}
        <div className="text-[13px] text-[var(--color-text)]">{children}</div>
      </div>
    </div>
  );
}
