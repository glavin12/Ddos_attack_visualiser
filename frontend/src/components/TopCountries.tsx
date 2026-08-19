"use client";

import { useRadarStore } from "@/store/useRadarStore";
import { flagEmoji, formatPercent } from "@/lib/format";

const RANK_COLORS = ["#3FE0D0", "#6FF5E6", "#3FE0D0", "#6FF5E6", "#3FE0D0"];

export default function TopCountries() {
  const topOrigins = useRadarStore((s) => s.topOrigins);

  const displayList = topOrigins.slice(0, 5).map((entry, i) => ({
    code: entry.country.code,
    name: entry.country.name || entry.country.code,
    share: entry.share,
    color: RANK_COLORS[i] || "#3FE0D0",
  }));

  return (
    <div className="panel-glass rounded-xl p-4 min-w-[210px]" aria-label="Top origin countries, 24h aggregate">
      <h2 className="type-label mb-3.5" style={{ color: "var(--color-text-muted)" }}>
        Top Origins (24h)
      </h2>

      {displayList.length === 0 ? (
        <p className="type-body-sm" style={{ color: "var(--color-text-faint)" }}>
          Loading Radar data&hellip;
        </p>
      ) : (
      <div className="space-y-3 font-mono text-[12px]">
        {displayList.map((item) => (
          <div
            key={item.code}
            className="flex items-center justify-between gap-4"
          >
            {/* Flag + Country Name */}
            <div className="flex items-center gap-2.5 min-w-0">
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
      )}
    </div>
  );
}
