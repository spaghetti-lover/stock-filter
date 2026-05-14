"use client";

import { useEffect, useRef, useState } from "react";
import { BoxPanel } from "./BoxPanel";

interface Props {
  locked?: boolean;
  value?: string[];
  onSubmit: (urls: string[]) => void;
  onSkip: () => void;
}

export function YoutubeUrlsStep({ locked = false, value, onSubmit, onSkip }: Props) {
  const [draft, setDraft] = useState(() => (value ?? []).join("\n"));
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (!locked) textareaRef.current?.focus();
  }, [locked]);

  const parseUrls = (raw: string): string[] =>
    raw
      .split("\n")
      .map((u) => u.trim())
      .filter((u) => u.startsWith("http"));

  const submit = () => {
    const urls = parseUrls(draft);
    if (urls.length === 0) {
      onSkip();
    } else {
      onSubmit(urls);
    }
  };

  const lockedUrls = value ?? [];
  const urlCount = parseUrls(draft).length;

  return (
    <BoxPanel title="Step 04b · YouTube Videos" tone={locked ? "muted" : "accent"}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <p className="display text-[18px] tracking-tight">YouTube Videos</p>
          <p className="text-[13px] text-[var(--color-text-dim)]">
            Paste one YouTube URL per line. The analyst will fetch and analyze transcripts
            for each video in context of the target stock.
          </p>
          <p className="mono text-[11px] text-[var(--color-text-faint)]">
            leave blank to skip · e.g. https://www.youtube.com/watch?v=…
          </p>
        </div>

        {locked ? (
          <div className="flex items-stretch border border-[var(--color-line)] bg-[var(--color-bg)]">
            <span
              className="mono flex items-center gap-2 border-r border-[var(--color-line)] bg-[var(--color-surface-2)] px-3 text-[12px]"
              style={{ color: "var(--color-accent)" }}
            >
              <span aria-hidden>›</span>
              <span>urls</span>
              <span aria-hidden>:</span>
            </span>
            <div className="flex flex-1 flex-col justify-center gap-0.5 px-3 py-2.5 font-mono text-[12.5px]">
              {lockedUrls.length === 0 ? (
                <span className="text-[var(--color-text-faint)]">skipped</span>
              ) : (
                lockedUrls.map((u, i) => (
                  <span key={i} className="truncate text-[var(--color-text-dim)]">{u}</span>
                ))
              )}
            </div>
            <span
              aria-hidden
              className="mono flex items-center gap-2 border-l border-[var(--color-line)] bg-[var(--color-surface)] px-4 text-[11px] uppercase tracking-[0.18em] text-[var(--color-ok)]"
            >
              <span>✓ confirmed</span>
            </span>
          </div>
        ) : (
          <div
            className="flex flex-col border border-[var(--color-line)] bg-[var(--color-bg)]"
            style={{
              boxShadow: "inset 0 0 0 1px color-mix(in srgb, var(--color-accent) 24%, transparent)",
            }}
          >
            <textarea
              ref={textareaRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  submit();
                }
              }}
              rows={4}
              placeholder={"https://www.youtube.com/watch?v=...\nhttps://youtu.be/..."}
              spellCheck={false}
              autoComplete="off"
              className="flex-1 resize-none bg-transparent px-3 py-3 font-mono text-[13px] text-[var(--color-text)] caret-[var(--color-accent)] outline-none placeholder:text-[var(--color-text-faint)]/60"
            />
            <div className="flex items-center justify-between gap-3 border-t border-[var(--color-line)] px-3 py-2">
              <span className="mono text-[11px] uppercase tracking-[0.2em] text-[var(--color-text-faint)]">
                {urlCount} url{urlCount !== 1 ? "s" : ""} · ctrl+enter to confirm
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={onSkip}
                  className="mono border border-[var(--color-line)] bg-[var(--color-surface)] px-3 py-1.5 text-[11px] uppercase tracking-[0.2em] text-[var(--color-text-faint)] transition-colors hover:border-[var(--color-line-2)] hover:text-[var(--color-text-dim)]"
                >
                  skip
                </button>
                <button
                  onClick={submit}
                  className="group mono flex items-center gap-2 border border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-1.5 text-[11px] uppercase tracking-[0.18em] text-[var(--color-text-dim)] transition-colors hover:bg-[var(--color-accent)] hover:text-black"
                >
                  <span>confirm</span>
                  <span aria-hidden className="transition-transform group-hover:translate-x-0.5">↵</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </BoxPanel>
  );
}
