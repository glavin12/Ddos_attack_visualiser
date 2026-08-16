"use client";

import { useRadarStore } from "@/store/useRadarStore";
import { formatPercent } from "@/lib/format";

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

// Fallback matching the screenshot values if store not loaded yet
const DEFAULT_ORIGINS = [
  { code: "CN", name: "China",     share: 0.284, color: "#FF3B4E" },
  { code: "RU", name: "Russia",    share: 0.187, color: "#FF7A18" },
  { code: "BR", name: "Brazil",    share: 0.128, color: "#FFB52E" },
  { code: "IN", name: "India",     share: 0.096, color: "#12C8B0" },
  { code: "ID", name: "Indonesia", share: 0.063, color: "#12C8B0" },
];

const RANK_COLORS = ["#FF3B4E", "#FF7A18", "#FFB52E", "#12C8B0", "#12C8B0"];

export default function TopCountries() {
  const topOrigins = useRadarStore((s) => s.topOrigins);

  const displayList =
    topOrigins.length >= 3
      ? topOrigins.slice(0, 5).map((entry, i) => ({
          code: entry.country.code,
          name: entry.country.name || entry.country.code,
          share: entry.share,
          color: RANK_COLORS[i] || "#12C8B0",
        }))
      : DEFAULT_ORIGINS;

  return (
    <div
      className="panel-glass rounded-xl p-4 min-w-[210px]"
      style={{
        backgroundColor: "rgba(6, 14, 24, 0.78)",
        border: "1px solid rgba(30, 60, 90, 0.45)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.6)",
      }}
      aria-label="Top attacking countries"
    >
      <h2
        className="font-mono text-[10px] font-bold tracking-[0.14em] uppercase mb-3.5"
        style={{ color: "#8EA0AD" }}
      >
        Top Attacking Countries
      </h2>

      <div className="space-y-2.5">
        {displayList.map((item) => (
          <div
            key={item.code}
            className="flex items-center justify-between gap-4 font-mono text-[12px]"
          >
            {/* Flag + Name */}
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-[14px] leading-none shrink-0" aria-hidden="true">
                {flagEmoji(item.code)}
              </span>
              <span className="font-medium text-[#D7E5EA] truncate">
                {item.name}
              </span>
            </div>

            {/* Percentage colored by rank */}
            <span
              className="font-mono text-[12px] font-bold tabular-nums shrink-0"
              style={{ color: item.color }}
            >
              {formatPercent(item.share, 1)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
