"use client";

import { useRadarStore } from "@/store/useRadarStore";
import { formatPercent } from "@/lib/format";
import { SkeletonRows } from "@/components/PanelStates";
import type { CharacteristicValue } from "@/lib/types";

function CharList({
  title,
  values,
  accentColor = "var(--color-signal-cyan)",
}: {
  title: string;
  values: CharacteristicValue[];
  accentColor?: string;
}) {
  const maxShare =
    values.length > 0 ? Math.max(...values.map((v) => v.share)) : 1;

  const loadState = useRadarStore((s) => s.loadState);

  return (
    <div className="px-3.5 py-3">
      <div className="type-label mb-2.5 font-bold tracking-wider text-cyan-400">
        {title}
      </div>
      {loadState === "loading" ? (
        <SkeletonRows rows={3} />
      ) : values.length === 0 ? (
        <span className="font-mono text-[11px] text-slate-500">
          No data available
        </span>
      ) : (
        <div className="space-y-2">
          {values.map((v) => {
            const barWidth = maxShare > 0 ? (v.share / maxShare) * 100 : 0;
            return (
              <div key={v.value} className="space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-sans text-[12px] font-medium text-slate-200 truncate uppercase">
                    {v.value}
                  </span>
                  <span className="font-mono text-[11px] font-bold text-slate-400 shrink-0 tabular-nums">
                    {formatPercent(v.share)}
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
                      backgroundColor: accentColor,
                      boxShadow: `0 0 8px ${accentColor}40`,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function AnalyticsPanel() {
  const protocols = useRadarStore((s) => s.protocols);
  const vectors = useRadarStore((s) => s.vectors);
  const httpMethods = useRadarStore((s) => s.httpMethods);

  return (
    <div className="flex flex-col h-full overflow-y-auto divide-y divide-slate-800/40">
      <div
        className="flex items-center justify-between px-3.5 py-2.5 shrink-0 bg-slate-950/70"
        style={{ borderBottom: "1px solid rgba(47, 209, 224, 0.2)" }}
      >
        <span className="type-label font-bold text-cyan-400 tracking-wider">
          Attack Vectors & Protocols
        </span>
      </div>
      <CharList title="Layer 3 Protocols" values={protocols.slice(0, 8)} accentColor="var(--color-signal-cyan)" />
      <CharList title="Attack Vectors" values={vectors.slice(0, 8)} accentColor="#38BDF8" />
      {httpMethods.length > 0 && (
        <CharList title="Layer 7 HTTP Methods" values={httpMethods.slice(0, 8)} accentColor="var(--color-layer7-amber)" />
      )}
    </div>
  );
}
