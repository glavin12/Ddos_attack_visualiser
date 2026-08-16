"use client";

import { useRadarStore } from "@/store/useRadarStore";
import { deriveSeverity, severityColor } from "@/lib/constants";

// Country code to flag emoji
function flagEmoji(code: string): string {
  if (!code || code.length < 2) return "🌐";
  return code
    .toUpperCase()
    .slice(0, 2)
    .split("")
    .map((c) => String.fromCodePoint(0x1f1e6 + c.charCodeAt(0) - 65))
    .join("");
}

// Fallback matching exact reference screenshot values
const DEFAULT_ATTACKS = [
  { id: "1", srcCode: "CN", srcName: "China",     tgtName: "USA",       rate: "2.34 Mpps", severity: "critical" as const },
  { id: "2", srcCode: "RU", srcName: "Russia",    tgtName: "Germany",   rate: "1.21 Mpps", severity: "high" as const },
  { id: "3", srcCode: "BR", srcName: "Brazil",    tgtName: "USA",       rate: "870 Kpps",  severity: "medium" as const },
  { id: "4", srcCode: "IN", srcName: "India",     tgtName: "Singapore", rate: "654 Kpps",  severity: "low" as const },
  { id: "5", srcCode: "ID", srcName: "Indonesia", tgtName: "Australia", rate: "512 Kpps",  severity: "critical" as const },
];

function formatRate(intensity: number, packetsPerSecond?: number): string {
  if (packetsPerSecond) {
    if (packetsPerSecond >= 1_000_000) {
      return `${(packetsPerSecond / 1_000_000).toFixed(2)} Mpps`;
    }
    return `${Math.round(packetsPerSecond / 1000)} Kpps`;
  }
  const pps = intensity * 2_800_000;
  if (pps >= 1_000_000) {
    return `${(pps / 1_000_000).toFixed(2)} Mpps`;
  }
  return `${Math.round(pps / 1000)} Kpps`;
}

export default function LiveAttacks() {
  const events = useRadarStore((s) => s.events);

  const displayAttacks =
    events.length >= 3
      ? events.slice(0, 5).map((e) => {
          const severity = deriveSeverity(e.intensity);
          return {
            id: e.event_id,
            srcCode: e.source.code,
            srcName: e.source.name || e.source.code,
            tgtName: e.target.name || e.target.code,
            rate: formatRate(e.intensity, e.packetsPerSecond),
            severity,
          };
        })
      : DEFAULT_ATTACKS;

  return (
    <div
      className="panel-glass rounded-xl p-4 min-w-[280px] max-w-[340px]"
      style={{
        backgroundColor: "rgba(6, 14, 24, 0.78)",
        border: "1px solid rgba(30, 60, 90, 0.45)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.6)",
      }}
      aria-label="Live attacks feed"
    >
      <h2
        className="font-mono text-[10px] font-bold tracking-[0.14em] uppercase mb-3.5"
        style={{ color: "#8EA0AD" }}
      >
        Live Attacks
      </h2>

      <div className="space-y-3 font-mono text-[12px]">
        {displayAttacks.map((atk) => {
          const dotColor = severityColor(atk.severity);
          return (
            <div
              key={atk.id}
              className="flex items-center justify-between gap-3"
            >
              {/* Left: Dot + Flag + Source -> Target */}
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{
                    backgroundColor: dotColor,
                    boxShadow: `0 0 6px ${dotColor}`,
                  }}
                  aria-hidden="true"
                />
                <span className="text-[13px] leading-none shrink-0" aria-hidden="true">
                  {flagEmoji(atk.srcCode)}
                </span>
                <span
                  className="font-medium text-[#D7E5EA] truncate max-w-[70px]"
                  title={atk.srcName}
                >
                  {atk.srcName}
                </span>
                <span className="text-[#4A6372] text-[11px] shrink-0" aria-hidden="true">
                  →
                </span>
                <span
                  className="font-medium text-[#8EA0AD] truncate max-w-[75px]"
                  title={atk.tgtName}
                >
                  {atk.tgtName}
                </span>
              </div>

              {/* Right: Rate in Mpps / Kpps */}
              <span className="font-mono text-[11px] text-[#A0B3C2] tabular-nums font-semibold shrink-0">
                {atk.rate}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
