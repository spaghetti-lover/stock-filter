interface Props {
  index?: string;
  eyebrow?: string;
  title: string;
  description?: string;
  right?: React.ReactNode;
}

export function SectionHeader({ index, eyebrow, title, description, right }: Props) {
  return (
    <header className="flex flex-col gap-2 pb-6">
      <div className="flex items-center gap-3 text-[var(--color-text-dim)]">
        {index ? <span className="mono text-[10px]">{index}</span> : null}
        {eyebrow ? <span className="tag">{eyebrow}</span> : null}
      </div>
      <div className="flex items-end justify-between gap-6">
        <h1 className="display text-[44px] leading-[0.95] tracking-tight text-[var(--color-text)]"
            style={{ fontVariationSettings: '"opsz" 144, "SOFT" 30' }}>
          {title}
        </h1>
        {right}
      </div>
      {description ? (
        <p className="max-w-[60ch] text-[13px] text-[var(--color-text-dim)]">{description}</p>
      ) : null}
    </header>
  );
}
