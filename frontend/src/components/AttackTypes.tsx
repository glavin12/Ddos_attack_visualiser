"use client";

import { useRadarStore } from "@/store/useRadarStore";
import { formatPercent } from "@/lib/format";

// Fallback display if store has no data yet
const FALLBACK = [
  { value: "UDP FLOOD",  share: 0.452 },
  { value: "SYN FLOOD",  share: 0.287 },
  { value: "HTTP FLOOD", share: 0.153 },
  { value: "ICMP FLOOD", share: 0.061 },
  { value: "OTHER",      share: 0.047 },
];

const BAR_COLORS = [
  "var(--color-signal-cyan)",
  "var(--color-severity-medium)",
  "var(--color-severity-high)",
  "var(--color-severity-low)",
  "var(--color-text-faint)",
];

export default function AttackTypes() {
  const vectors = useRadarStore((s) => s.vectors);
  const entries = vectors.length > 0 ? vectors.slice(0, 5) : FALLBACK;
  const maxShare = Math.max(...entries.map((e) => e.share), 0.001);

  return (
    <section aria-label="Top attack types">
      <div
        className="flex items-center justify-between px-3.5 py-2.5 shrink-0"
        style={{ borderBottom: "1px solid rgba(0, 217, 255, 0.15)" }}
      >
        <h3
          className="font-mono text-[10px] font-bold tracking-[0.14em] uppercase"
          style={{ color: "#8EA0AD" }}
        >
          Top Attack Types
        </h3>
        <span
          className="font-mono text-[9px] uppercase tracking-wider"
          style={{ color: "var(--color-text-faint)" }}
        >
          Vectors
        </span>
      </div>

      <div className="px-3.5 py-3 space-y-2.5">
        {entries.map((entry, i) => {
          const barWidth = (entry.share / maxShare) * 100;
          const color = BAR_COLORS[i % BAR_COLORS.length];
          return (
            <div key={entry.value} className="space-y-1">
              <div className="flex items-center justify-between gap-2">
                <span
                  className="font-mono text-[11px] font-medium truncate"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  {entry.value}
                </span>
                <span
                  className="font-mono text-[11px] font-bold tabular-nums shrink-0"
                  style={{ color }}
                >
                  {formatPercent(entry.share)}
                </span>
              </div>
              <div
                className="w-full rounded-full overflow-hidden"
                style={{ height: 3, backgroundColor: "rgba(20, 42, 56, 0.8)" }}
              >
                <div
                  className="h-full rounded-full bar-fill-scale"
                  style={{
                    transform: `scaleX(${barWidth / 100})`,
                    backgroundColor: color,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
