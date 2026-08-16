"use client";

import { getCountryName } from "@/lib/countries";
import { formatPercent } from "@/lib/format";
import { useRadarStore } from "@/store/useRadarStore";
import { SkeletonRows, PanelError } from "@/components/PanelStates";

export interface BarEntry {
  code: string;
  name: string | null;
  share: number;
}

export default function BarList({
  title,
  entries,
  emptyLabel = "No data available",
}: {
  title: string;
  entries: BarEntry[];
  emptyLabel?: string;
}) {
  const maxShare =
    entries.length > 0 ? Math.max(...entries.map((e) => e.share)) : 1;

  const loadState = useRadarStore((s) => s.loadState);
  const requestReload = useRadarStore((s) => s.requestReload);

  return (
    <section aria-label={title}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-3.5 py-2.5 shrink-0"
        style={{ borderBottom: "1px solid rgba(0, 217, 255, 0.15)" }}
      >
        <h3
          className="font-mono text-[10px] font-bold tracking-[0.14em] uppercase"
          style={{ color: "#8EA0AD" }}
        >
          {title}
        </h3>
        <span
          className="font-mono text-[9px] uppercase tracking-wider"
          style={{ color: "var(--color-text-faint)" }}
        >
          Ranked
        </span>
      </div>

      {/* Bar list */}
      {loadState === "loading" ? (
        <SkeletonRows rows={5} />
      ) : loadState === "error" ? (
        <PanelError
          message="Unable to reach radar API"
          onRetry={requestReload}
        />
      ) : (
      <div className="px-3.5 py-3 space-y-2.5">
        {entries.length === 0 ? (
          <span className="font-mono text-[11px]" style={{ color: "var(--color-text-faint)" }}>
            {emptyLabel}
          </span>
        ) : (
          entries.map((entry, idx) => {
            const barWidth = maxShare > 0 ? (entry.share / maxShare) * 100 : 0;
            const countryName = entry.name || getCountryName(entry.code);
            const isTop3 = idx < 3;

            return (
              <div key={entry.code} className="space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="font-mono text-[11px] font-bold w-4 text-center tabular-nums"
                      style={{ color: isTop3 ? "var(--color-signal-cyan)" : "var(--color-text-faint)" }}
                    >
                      {idx + 1}
                    </span>
                    <span
                      className="font-mono text-[12px] font-bold"
                      style={{ color: "var(--color-text-primary)" }}
                    >
                      {entry.code}
                    </span>
                    <span
                      className="font-sans text-[11px] truncate"
                      style={{ color: "var(--color-text-muted)" }}
                    >
                      {countryName}
                    </span>
                  </div>
                  <span
                    className="font-mono text-[11px] font-bold shrink-0 tabular-nums"
                    style={{ color: isTop3 ? "var(--color-signal-cyan)" : "var(--color-text-muted)" }}
                  >
                    {formatPercent(entry.share)}
                  </span>
                </div>
                <div
                  className="w-full rounded-full overflow-hidden"
                  style={{
                    height: 4,
                    backgroundColor: "rgba(20, 42, 56, 0.8)",
                  }}
                >
                  <div
                    className="h-full rounded-full bar-fill-scale"
                    style={{
                      transform: `scaleX(${barWidth / 100})`,
                      backgroundColor: isTop3 ? "var(--color-signal-cyan)" : "var(--color-hairline-light)",
                      boxShadow: isTop3 ? "0 0 8px rgba(0, 217, 255, 0.5)" : "none",
                    }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
      )}
    </section>
  );
}
