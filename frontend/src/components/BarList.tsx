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
    <div className="flex flex-col">
      {/* Header */}
      <div
        className="flex items-center justify-between px-3.5 py-2.5 shrink-0 bg-slate-950/70"
        style={{ borderBottom: "1px solid rgba(47, 209, 224, 0.2)" }}
      >
        <span className="type-label font-bold text-cyan-400 tracking-wider">
          {title}
        </span>
        <span className="font-mono text-[10px] text-slate-500 uppercase">Ranked</span>
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
          <span className="font-mono text-[11px] text-slate-500">
            {emptyLabel}
          </span>
        ) : (
          entries.map((entry, idx) => {
            const barWidth = maxShare > 0 ? (entry.share / maxShare) * 100 : 0;
            const countryName = entry.name || getCountryName(entry.code);
            const isTop3 = idx < 3;

            return (
              <div key={entry.code} className="space-y-1 group">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className="font-mono text-[11px] font-bold w-4 text-center tabular-nums"
                      style={{ color: isTop3 ? "var(--color-signal-cyan)" : "#64748b" }}
                    >
                      {idx + 1}
                    </span>
                    <span className="font-mono text-[12px] font-bold text-white">
                      {entry.code}
                    </span>
                    <span className="font-sans text-[11px] text-slate-400 truncate">
                      {countryName}
                    </span>
                  </div>
                  <span
                    className="font-mono text-[11px] font-bold shrink-0 tabular-nums"
                    style={{ color: isTop3 ? "var(--color-signal-cyan)" : "#94a3b8" }}
                  >
                    {formatPercent(entry.share)}
                  </span>
                </div>
                <div
                  className="w-full rounded-full overflow-hidden"
                  style={{
                    height: 4,
                    backgroundColor: "rgba(30, 41, 59, 0.8)",
                  }}
                >
                  <div
                    className="h-full rounded-full bar-fill-scale"
                    style={{
                      transform: `scaleX(${barWidth / 100})`,
                      backgroundColor: isTop3 ? "var(--color-signal-cyan)" : "#38BDF8",
                      boxShadow: isTop3 ? "0 0 8px rgba(47, 209, 224, 0.5)" : "none",
                    }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
      )}
    </div>
  );
}
