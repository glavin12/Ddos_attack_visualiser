import { SkeletonRows } from "@/components/PanelStates";

export default function Loading() {
  return (
    <div
      className="flex flex-col h-screen"
      style={{ backgroundColor: "var(--color-void)" }}
    >
      <div
        className="flex items-center justify-between px-5 shrink-0"
        style={{
          height: 54,
          backgroundColor: "rgba(7, 13, 24, 0.95)",
          borderBottom: "1px solid var(--color-hairline)",
        }}
      >
        <div className="h-4 w-28 rounded bg-[var(--color-hairline)] animate-pulse" />
        <div className="hidden md:block h-4 w-40 rounded bg-[var(--color-hairline)] animate-pulse" />
        <div className="h-4 w-24 rounded bg-[var(--color-hairline)] animate-pulse" />
      </div>
      <div className="flex flex-1 min-h-0">
        <div className="relative flex-1 min-w-0 bg-[var(--color-void)]">
          <div className="absolute inset-0 flex items-center justify-center">
            <span
              className="font-mono text-[13px] tracking-widest uppercase"
              style={{ color: "var(--color-text-faint)" }}
            >
              Initializing telemetry…
            </span>
          </div>
        </div>
        <aside
          className="hidden md:flex flex-col shrink-0"
          style={{ width: 340, backgroundColor: "var(--color-panel)" }}
        >
          <SkeletonRows rows={8} />
        </aside>
      </div>
    </div>
  );
}
