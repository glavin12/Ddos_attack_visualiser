"use client";

import { useRadarStore } from "@/store/useRadarStore";
import { formatPercent } from "@/lib/format";

export default function AttackIntensity() {
  const topRoutes = useRadarStore((s) => s.topRoutes);
  const routesUpdatedAtMs = useRadarStore((s) => s.routesUpdatedAtMs);
  const top5 = topRoutes.slice(0, 5);

  return (
    <div className="panel-glass rounded-xl p-3.5 min-w-[200px]" aria-label="Top 24h attack routes">
      <h2 className="type-label mb-3" style={{ color: "var(--color-text-muted)" }}>
        Top Routes (24h)
      </h2>

      {top5.length === 0 ? (
        <p className="type-body-sm" style={{ color: "var(--color-text-faint)" }}>
          Loading Radar data&hellip;
        </p>
      ) : (
        <div className="space-y-2.5">
          {top5.map((route, i) => (
            <div key={`${route.source.code}-${route.target.code}`} className="flex items-center gap-2.5">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{
                  backgroundColor: "var(--color-signal-cyan)",
                  opacity: 1 - i * 0.15,
                }}
                aria-hidden="true"
              />
              <span className="type-data flex-1 truncate" style={{ color: "var(--color-text-primary)" }}>
                {route.source.code} &rarr; {route.target.code}
              </span>
              <span className="type-data tabular-nums" style={{ color: "var(--color-text-muted)" }}>
                {formatPercent(route.share, 1)}
              </span>
            </div>
          ))}
        </div>
      )}

      {routesUpdatedAtMs && (
        <p className="type-label mt-3 pt-2" style={{ color: "var(--color-text-faint)", fontWeight: 400, textTransform: "none", letterSpacing: "normal", borderTop: "1px solid var(--color-hairline)" }}>
          Cloudflare Radar · 24h aggregate
        </p>
      )}
    </div>
  );
}
