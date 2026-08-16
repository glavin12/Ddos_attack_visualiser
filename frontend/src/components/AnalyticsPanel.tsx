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
      <h4
        className="font-mono text-[10px] font-bold tracking-[0.14em] uppercase mb-2.5"
        style={{ color: "var(--color-text-muted)" }}
      >
        {title}
      </h4>
      {loadState === "loading" ? (
        <SkeletonRows rows={3} />
      ) : values.length === 0 ? (
        <span className="font-mono text-[11px]" style={{ color: "var(--color-text-faint)" }}>
          No data available
        </span>
      ) : (
        <div className="space-y-2">
          {values.map((v) => {
            const barWidth = maxShare > 0 ? (v.share / maxShare) * 100 : 0;
            return (
              <div key={v.value} className="space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span
                    className="font-mono text-[11px] font-medium truncate uppercase"
                    style={{ color: "var(--color-text-primary)" }}
                  >
                    {v.value}
                  </span>
                  <span
                    className="font-mono text-[11px] font-bold shrink-0 tabular-nums"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    {formatPercent(v.share)}
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
  const selectedLayer = useRadarStore((s) => s.selectedLayer);

  return (
    <section aria-label="Attack vectors and protocols">
      <div
        className="flex items-center justify-between px-3.5 py-2.5 shrink-0"
        style={{ borderBottom: "1px solid rgba(0, 217, 255, 0.15)" }}
      >
        <h3
          className="font-mono text-[10px] font-bold tracking-[0.14em] uppercase"
          style={{ color: "#8EA0AD" }}
        >
          Vectors &amp; Protocols
        </h3>
        <span
          className="font-mono text-[9px] uppercase tracking-wider"
          style={{ color: "var(--color-text-faint)" }}
        >
          {selectedLayer}
        </span>
      </div>
      {selectedLayer === "L7" ? (
        <CharList
          title="HTTP Methods"
          values={httpMethods.slice(0, 8)}
          accentColor="#FF7A18"
        />
      ) : (
        <>
          <CharList
            title="Layer 3 Protocols"
            values={protocols.slice(0, 8)}
            accentColor="var(--color-signal-cyan)"
          />
          <CharList
            title="Attack Vectors"
            values={vectors.slice(0, 8)}
            accentColor="#33E5FF"
          />
        </>
      )}
    </section>
  );
}
