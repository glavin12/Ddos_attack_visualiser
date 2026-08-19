"use client";

import { useRadarStore } from "@/store/useRadarStore";
import { ALL_SOURCE_FEEDS, DEMO_MODE, feedColor, feedLabel } from "@/lib/constants";

export default function Legend() {
  const connectionState = useRadarStore((s) => s.connectionState);
  const isDemo = DEMO_MODE && connectionState !== "CONNECTED";

  return (
    <div className="panel-glass rounded-xl p-4 min-w-[210px]" aria-label="Visualization legend">
      <h2 className="type-label mb-3.5" style={{ color: "var(--color-text-muted)" }}>
        How to Read This
      </h2>

      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <span className="w-4 flex items-center justify-center shrink-0" aria-hidden="true">
            <span
              className="w-full h-[1.5px]"
              style={{ backgroundColor: "var(--color-signal-cyan)", opacity: 0.7 }}
            />
          </span>
          <div>
            <div className="type-body-sm" style={{ color: "var(--color-text-primary)" }}>
              Arc
            </div>
            <div className="type-label" style={{ color: "var(--color-text-faint)", fontWeight: 400 }}>
              24h aggregate route (Cloudflare Radar)
            </div>
          </div>
        </div>

        {ALL_SOURCE_FEEDS.map((feed) => (
          <div key={feed} className="flex items-center gap-3">
            <span
              className="w-2.5 h-2.5 rounded-full shrink-0"
              style={{ backgroundColor: feedColor(feed), boxShadow: `0 0 6px ${feedColor(feed)}` }}
              aria-hidden="true"
            />
            <div>
              <div className="type-body-sm" style={{ color: "var(--color-text-primary)" }}>
                {feedLabel(feed)}
              </div>
              <div className="type-label" style={{ color: "var(--color-text-faint)", fontWeight: 400 }}>
                Live indicator
              </div>
            </div>
          </div>
        ))}
      </div>

      <p
        className="type-label mt-3.5 pt-3 leading-relaxed"
        style={{
          color: "var(--color-text-faint)",
          fontWeight: 400,
          textTransform: "none",
          letterSpacing: "normal",
          borderTop: "1px solid var(--color-hairline)",
        }}
      >
        {isDemo
          ? "Backend offline — arcs and dots below are simulated demo data, dimmed and thinned on the globe to stay visually distinct from real telemetry."
          : "Arcs are a rolling 24h snapshot, not live incidents. Dots are real indicators reported by public feeds — not confirmed DDoS attacks."}
      </p>
    </div>
  );
}
