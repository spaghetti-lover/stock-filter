"use client";

import { motion } from "motion/react";

export function KPI({
  label,
  value,
  suffix,
  emphasize = false,
}: {
  label: string;
  value: string | number;
  suffix?: string;
  emphasize?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.2, 0.7, 0.2, 1] }}
      className="border border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-4"
    >
      <div className="tag mb-3">{label}</div>
      <div className="flex items-baseline gap-2">
        <span
          className={`serif-num text-[44px] leading-none ${
            emphasize ? "text-[var(--color-accent)]" : "text-[var(--color-text)]"
          }`}
        >
          {value}
        </span>
        {suffix ? <span className="mono text-[12px] text-[var(--color-text-dim)]">{suffix}</span> : null}
      </div>
    </motion.div>
  );
}
