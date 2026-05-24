"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { EditableChip } from "./EditableChip";
import { applyAIFilter, fetchAIFilterCatalog, renderLabel } from "@/lib/aiFilter";
import type {
  AIFilterCatalogEntry,
  AIFilterCondition,
} from "@/lib/aiFilterTypes";
import { NumberField } from "@/components/ui/NumberField";
import { useCopilotStore } from "@/lib/store";
import { useStocksStore } from "@/lib/store";

interface Props {
  onError: (msg: string) => void;
}

export function AIFilterStrip({ onError }: Props) {
  const activeConditions = useCopilotStore((s) => s.activeConditions);
  const updateConditionParams = useCopilotStore((s) => s.updateConditionParams);
  const removeCondition = useCopilotStore((s) => s.removeCondition);
  const setActiveConditions = useCopilotStore((s) => s.setActiveConditions);
  const setStocks = useStocksStore((s) => s.setStocks);

  const [catalog, setCatalog] = useState<AIFilterCatalogEntry[]>([]);
  const [addOpen, setAddOpen] = useState(false);
  const [applying, setApplying] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastAppliedRef = useRef<string>("");

  useEffect(() => {
    fetchAIFilterCatalog()
      .then((r) => setCatalog(r.entries))
      .catch((e) => onError(e instanceof Error ? e.message : String(e)));
  }, [onError]);

  const entriesByKey = useMemo(() => {
    const m: Record<string, AIFilterCatalogEntry> = {};
    for (const e of catalog) m[e.key] = e;
    return m;
  }, [catalog]);

  useEffect(() => {
    if (catalog.length === 0) return;
    const fingerprint = JSON.stringify(activeConditions);
    if (fingerprint === lastAppliedRef.current) return;

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setApplying(true);
      try {
        const refreshed = activeConditions.map((c) => {
          const e = entriesByKey[c.key];
          return e ? { ...c, label: renderLabel(e, c.params) } : c;
        });
        const data = await applyAIFilter({ conditions: refreshed });
        setStocks(data.passed, data.rejected);
        lastAppliedRef.current = fingerprint;
      } catch (e) {
        onError(e instanceof Error ? e.message : String(e));
      } finally {
        setApplying(false);
      }
    }, 350);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [activeConditions, catalog.length, entriesByKey, onError, setStocks]);

  const addCondition = (entry: AIFilterCatalogEntry) => {
    const params: Record<string, unknown> = {};
    for (const p of entry.params) params[p.name] = p.default;
    const next: AIFilterCondition = {
      key: entry.key,
      label: renderLabel(entry, params),
      params,
    };
    setActiveConditions([...activeConditions, next]);
    setAddOpen(false);
  };

  return (
    <div className="flex flex-wrap items-center gap-3 border-b border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-3">
      <span className="tag text-[var(--color-text-dim)]">Active conditions</span>

      {activeConditions.length === 0 ? (
        <span className="mono text-[12px] text-[var(--color-text-dim)]">
          No filter applied — ask copilot or add one →
        </span>
      ) : (
        activeConditions.map((c, i) => {
          const entry = entriesByKey[c.key];
          const popover = entry && entry.params.length > 0 ? (
            <div className="flex flex-col gap-2">
              <div className="tag text-[var(--color-text-dim)]">{entry.description}</div>
              {entry.params.map((p) => (
                <ParamEditor
                  key={p.name}
                  paramName={p.name}
                  type={p.type}
                  value={(c.params[p.name] ?? p.default) as never}
                  onChange={(v) => updateConditionParams(i, { [p.name]: v })}
                />
              ))}
            </div>
          ) : null;
          return (
            <EditableChip
              key={`${c.key}-${i}`}
              label={c.label}
              onRemove={() => removeCondition(i)}
              popover={popover}
            />
          );
        })
      )}

      <div className="relative">
        <button
          type="button"
          onClick={() => setAddOpen((v) => !v)}
          className="mono border border-dashed border-[var(--color-line-2)] px-3 py-1.5 text-[11px] tracking-[0.16em] uppercase text-[var(--color-text-dim)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
        >
          + Add condition
        </button>
        {addOpen ? (
          <AddMenu
            entries={catalog}
            activeKeys={new Set(activeConditions.map((c) => c.key))}
            onPick={addCondition}
            onClose={() => setAddOpen(false)}
          />
        ) : null}
      </div>

      {applying ? (
        <span className="mono ml-auto text-[11px] tracking-[0.16em] uppercase text-[var(--color-accent)]">
          applying…
        </span>
      ) : null}
    </div>
  );
}

function ParamEditor({
  paramName,
  type,
  value,
  onChange,
}: {
  paramName: string;
  type: string;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  if (type === "float" || type === "int") {
    return (
      <label className="flex items-center gap-2">
        <span className="mono w-24 text-[11px] tracking-[0.06em] text-[var(--color-text-dim)]">
          {paramName}
        </span>
        <NumberField
          value={Number(value ?? 0)}
          onChange={(v) => onChange(type === "int" ? Math.round(v) : v)}
          step={type === "int" ? 1 : 0.5}
        />
      </label>
    );
  }
  if (type === "list[str]") {
    const arr = Array.isArray(value) ? value : [];
    return (
      <label className="flex flex-col gap-1">
        <span className="mono text-[11px] tracking-[0.06em] text-[var(--color-text-dim)]">
          {paramName} (comma-separated)
        </span>
        <input
          type="text"
          value={arr.join(", ")}
          onChange={(e) =>
            onChange(
              e.target.value
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
            )
          }
          className="mono border border-[var(--color-line-2)] bg-[var(--color-bg)] px-2 py-1 text-[12px] focus:border-[var(--color-accent)] focus:outline-none"
        />
      </label>
    );
  }
  return (
    <label className="flex items-center gap-2">
      <span className="mono w-24 text-[11px] text-[var(--color-text-dim)]">{paramName}</span>
      <input
        type="text"
        value={String(value ?? "")}
        onChange={(e) => onChange(e.target.value)}
        className="mono flex-1 border border-[var(--color-line-2)] bg-[var(--color-bg)] px-2 py-1 text-[12px] focus:border-[var(--color-accent)] focus:outline-none"
      />
    </label>
  );
}

function AddMenu({
  entries,
  activeKeys,
  onPick,
  onClose,
}: {
  entries: AIFilterCatalogEntry[];
  activeKeys: Set<string>;
  onPick: (e: AIFilterCatalogEntry) => void;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [onClose]);

  return (
    <div
      ref={ref}
      className="absolute right-0 top-full z-30 mt-2 w-[320px] border border-[var(--color-line-2)] bg-[var(--color-surface)] py-1 shadow-lg"
    >
      {entries.map((e) => {
        const taken = activeKeys.has(e.key);
        return (
          <button
            key={e.key}
            type="button"
            disabled={taken}
            onClick={() => onPick(e)}
            className="flex w-full flex-col gap-0.5 px-3 py-2 text-left transition-colors hover:bg-[var(--color-bg)] disabled:cursor-not-allowed disabled:opacity-40"
          >
            <span className="mono text-[12px] text-[var(--color-text)]">{e.label_template}</span>
            <span className="text-[11px] text-[var(--color-text-dim)]">{e.description}</span>
          </button>
        );
      })}
    </div>
  );
}
