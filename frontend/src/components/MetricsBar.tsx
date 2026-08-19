"use client";

import { useEffect, useState } from "react";
import { useRadarStore } from "@/store/useRadarStore";

export default function MetricsBar() {
  const activeIndicatorCount = useRadarStore((s) => s.activeIndicatorCount);
  const totalIndicatorsSeen = useRadarStore((s) => s.totalIndicatorsSeen);
  const topTargets = useRadarStore((s) => s.topTargets);
  const topRoutes = useRadarStore((s) => s.topRoutes);

  const [utcTime, setUtcTime] = useState<string>("");
  useEffect(() => {
    const tick = () => {
      const d = new Date();
      const h = String(d.getUTCHours()).padStart(2, "0");
      const m = String(d.getUTCMinutes()).padStart(2, "0");
      const s = String(d.getUTCSeconds()).padStart(2, "0");
      setUtcTime(`${h}:${m}:${s} UTC`);
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      className="flex items-center gap-4 max-w-5xl w-full justify-center"
      role="region"
      aria-label="Network telemetry metrics"
    >
      <div className="panel-glass rounded-xl px-2 py-2.5 flex items-center flex-1 justify-between">
        <div className="flex-1 px-4 py-1 text-center border-r border-[rgba(30,60,90,0.35)]">
          <div className="type-label mb-1" style={{ color: "var(--color-text-muted)" }}>
            Indicators Tracked
          </div>
          <div className="type-metric tabular-nums" style={{ color: "var(--color-feed-feodo)" }}>
            {totalIndicatorsSeen > 0 ? totalIndicatorsSeen : "—"}
          </div>
        </div>

        <div className="flex-1 px-4 py-1 text-center border-r border-[rgba(30,60,90,0.35)]">
          <div className="type-label mb-1" style={{ color: "var(--color-text-muted)" }}>
            Active on Globe
          </div>
          <div className="type-metric tabular-nums" style={{ color: "var(--color-amber)" }}>
            {activeIndicatorCount > 0 ? activeIndicatorCount : "—"}
          </div>
        </div>

        <div className="flex-1 px-4 py-1 text-center border-r border-[rgba(30,60,90,0.35)]">
          <div className="type-label mb-1" style={{ color: "var(--color-text-muted)" }}>
            24h Attack Routes
          </div>
          <div className="type-metric tabular-nums" style={{ color: "var(--color-signal-cyan)" }}>
            {topRoutes.length > 0 ? topRoutes.length : "—"}
          </div>
        </div>

        <div className="flex-1 px-4 py-1 text-center">
          <div className="type-label mb-1" style={{ color: "var(--color-text-muted)" }}>
            Countries Targeted
          </div>
          <div className="type-metric tabular-nums" style={{ color: "var(--color-signal-cyan-bright)" }}>
            {topTargets.length > 0 ? topTargets.length : "—"}
          </div>
        </div>
      </div>

      <div className="panel-glass rounded-xl px-5 py-2.5 text-center shrink-0 min-w-[150px]">
        <div className="type-label mb-1" style={{ color: "var(--color-text-muted)" }}>
          Live Time
        </div>
        <div className="type-data-lg tabular-nums" style={{ color: "var(--color-signal-cyan)" }}>
          {utcTime || "--:--:-- UTC"}
        </div>
      </div>
    </div>
  );
}
