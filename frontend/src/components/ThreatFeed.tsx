"use client";

import { useRadarStore } from "@/store/useRadarStore";
import { feedColor, feedLabel } from "@/lib/constants";
import { flagEmoji, formatRelativeTime } from "@/lib/format";
import { MAX_LIVE_FEED_ROWS } from "@/lib/constants";

export default function ThreatFeed() {
  const indicators = useRadarStore((s) => s.indicators);
  const rows = indicators.slice(0, MAX_LIVE_FEED_ROWS);

  return (
    <div
      className="panel-glass rounded-xl p-4 min-w-[280px] max-w-[340px]"
      aria-label="Live threat indicator feed"
    >
      <div className="flex items-center justify-between mb-3.5">
        <h2 className="type-label" style={{ color: "var(--color-text-muted)" }}>
          Live Threat Feed
        </h2>
        {rows.length > 0 && (
          <span className="type-label" style={{ color: "var(--color-text-faint)" }}>
            {rows.length}
          </span>
        )}
      </div>

      {rows.length === 0 ? (
        <p className="type-body-sm" style={{ color: "var(--color-text-faint)" }}>
          Waiting for the first indicator&hellip;
        </p>
      ) : (
        <div className="space-y-2.5 max-h-[280px] overflow-y-auto overscroll-contain">
          {rows.map((point) => (
            <div key={point.id} className="feed-enter flex items-start justify-between gap-2">
              <div className="flex items-start gap-2 min-w-0">
                <span
                  className="w-2 h-2 rounded-full shrink-0 mt-1"
                  style={{
                    backgroundColor: feedColor(point.sourceFeed),
                    boxShadow: `0 0 6px ${feedColor(point.sourceFeed)}`,
                  }}
                  aria-hidden="true"
                />
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[13px] leading-none" aria-hidden="true">
                      {flagEmoji(point.countryCode)}
                    </span>
                    <span className="type-data truncate" style={{ color: "var(--color-text-primary)" }}>
                      {point.resolvedIp}
                    </span>
                  </div>
                  <div className="type-label mt-0.5" style={{ color: "var(--color-text-faint)", letterSpacing: "0.04em" }}>
                    {feedLabel(point.sourceFeed)}
                    {point.threatFamily ? ` · ${point.threatFamily}` : ""}
                  </div>
                </div>
              </div>
              <span className="type-data shrink-0" style={{ color: "var(--color-text-faint)", fontSize: 10 }}>
                {formatRelativeTime(new Date(point.lastSeen).getTime())}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
