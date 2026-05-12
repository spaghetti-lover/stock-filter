import { SectionHeader } from "@/components/ui/SectionHeader";

export default function AgentPage() {
  return (
    <div>
      <div className="hairline-grid border-b border-[var(--color-line)]">
        <div className="mx-auto max-w-[920px] px-8 pb-10 pt-12">
          <SectionHeader
            index="AGNT"
            eyebrow="Trading agent · WIP"
            title="Pipeline orchestrator — coming soon."
            description="This surface will host the automated screening + ranking pipeline. Nothing is wired up here yet."
          />
        </div>
      </div>

      <div className="mx-auto max-w-[920px] px-8 py-12">
        <div className="flex items-start gap-6 border border-dashed border-[var(--color-line-2)] px-6 py-10">
          <div
            aria-hidden
            className="mt-1 h-3 w-3 rotate-45 bg-[var(--color-warn)]"
            style={{ boxShadow: "0 0 12px var(--color-warn)" }}
          />
          <div className="flex flex-col gap-2">
            <span className="tag">under construction</span>
            <p className="display text-[24px] tracking-tight">
              No pipeline UI in this build.
            </p>
            <p className="max-w-[58ch] text-[13px] text-[var(--color-text-dim)]">
              The backend stub exists. The orchestrator UI will land once the
              flow specification is finalized.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
