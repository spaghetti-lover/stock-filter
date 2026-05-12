interface Props {
  value: number; // 0..100
  label: string;
  tone?: "accent" | "warn" | "danger" | "neutral";
}

const COLOR: Record<NonNullable<Props["tone"]>, string> = {
  accent: "var(--color-accent)",
  warn: "var(--color-warn)",
  danger: "var(--color-danger)",
  neutral: "var(--color-text-dim)",
};

export function PillarGauge({ value, label, tone = "neutral" }: Props) {
  const clamped = Math.max(0, Math.min(100, value));
  const SIZE = 80;
  const R = 32;
  const C = 2 * Math.PI * R;
  const arc = (clamped / 100) * C;
  const color = COLOR[tone];

  // 8 tick marks (4 strong, 4 minor)
  const ticks = Array.from({ length: 8 }, (_, i) => i);

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
        <g transform={`translate(${SIZE / 2} ${SIZE / 2}) rotate(-90)`}>
          <circle r={R} fill="none" stroke="var(--color-line-2)" strokeWidth={1} />
          <circle
            r={R}
            fill="none"
            stroke={color}
            strokeWidth={2}
            strokeDasharray={`${arc} ${C - arc}`}
            style={{ filter: `drop-shadow(0 0 6px ${color})` }}
          />
          {ticks.map((i) => {
            const angle = (i / 8) * Math.PI * 2;
            const x1 = Math.cos(angle) * (R + 4);
            const y1 = Math.sin(angle) * (R + 4);
            const x2 = Math.cos(angle) * (R + 8);
            const y2 = Math.sin(angle) * (R + 8);
            return (
              <line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={i % 2 === 0 ? "var(--color-line-2)" : "var(--color-line)"}
                strokeWidth={1}
              />
            );
          })}
        </g>
        <text
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="central"
          fontFamily="var(--font-display)"
          fontSize="22"
          fill="var(--color-text)"
          style={{ fontVariationSettings: '"opsz" 144' }}
        >
          {fmt(clamped)}
        </text>
      </svg>
      <span className="tag" style={{ color }}>
        {label}
      </span>
    </div>
  );
}

function fmt(v: number): string {
  return Number.isInteger(v) ? String(v) : v.toFixed(1);
}
