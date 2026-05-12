import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
  bordered = true,
}: {
  children: ReactNode;
  className?: string;
  bordered?: boolean;
}) {
  return (
    <div
      className={`${bordered ? "border border-[var(--color-line)]" : ""} bg-[var(--color-surface)] ${className}`}
    >
      {children}
    </div>
  );
}
