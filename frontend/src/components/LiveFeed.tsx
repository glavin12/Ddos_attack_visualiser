"use client";

import { useRadarStore } from "@/store/useRadarStore";
import { getCountryName } from "@/lib/countries";
import { formatTime } from "@/lib/format";
import type { AttackEventData } from "@/lib/types";

function FeedRow({
  event,
  index,
}: {
  event: AttackEventData & { receivedAt: number };
  index: number;
}) {
  const isL7 = event.layer === "L7";
  const ts = formatTime(event.receivedAt);
  const intensityPct = Math.round(event.intensity * 100);
  const isHighIntensity = intensityPct >= 75;

  const srcName = getCountryName(event.source.code);
  const dstName = getCountryName(event.target.code);

  return (
    <div
      className={`feed-enter flex flex-col gap-1 px-3.5 py-2.5 transition-colors duration-150 ${
        index === 0 ? "bg-slate-900/60" : ""
      }`}
      style={{
        contentVisibility: "auto",
        containIntrinsicSize: "auto 64px",
        borderLeft: isHighIntensity
          ? "3px solid var(--color-negative)"
          : isL7
          ? "3px solid var(--color-layer7-amber)"
          : "3px solid var(--color-signal-cyan)",
        borderBottom: "1px solid rgba(29, 42, 61, 0.4)",
      }}
    >
      {/* Top line: Time + Layer + Source -> Target */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-mono text-[11px] text-slate-400 shrink-0 tabular-nums">
            {ts}
          </span>
          <span
            className="px-1.5 py-0.2 text-[10px] font-mono font-bold rounded shrink-0 uppercase"
            style={{
              backgroundColor: isL7
                ? "rgba(217, 164, 65, 0.15)"
                : "rgba(47, 209, 224, 0.15)",
              color: isL7 ? "#FFB800" : "var(--color-signal-cyan)",
              border: isL7
                ? "1px solid rgba(217, 164, 65, 0.4)"
                : "1px solid rgba(47, 209, 224, 0.4)",
            }}
          >
            {event.layer}
          </span>
          <div className="font-mono text-[13px] font-bold text-white truncate">
            <span style={{ color: "var(--color-signal-cyan)" }}>{event.source.code}</span>
            <span className="text-slate-500 mx-1.5" aria-hidden="true">➔</span>
            <span style={{ color: isHighIntensity ? "var(--color-negative)" : isL7 ? "var(--color-layer7-amber)" : "#38BDF8" }}>
              {event.target.code}
            </span>
          </div>
        </div>

        {/* Intensity share badge */}
        <span
          className="font-mono text-[11px] font-bold shrink-0 tabular-nums"
          style={{
            color: isHighIntensity ? "var(--color-negative)" : isL7 ? "#FFB800" : "#38BDF8",
          }}
        >
          {intensityPct}%
        </span>
      </div>

      {/* Bottom line: Full Country Names & Intensity bar */}
      <div className="flex items-center justify-between gap-3 text-[11px] text-slate-400">
        <span className="truncate text-slate-300">
          {srcName} <span className="text-slate-600">to</span> {dstName}
        </span>
        <div className="w-16 h-1.5 rounded-full bg-slate-800 shrink-0 overflow-hidden">
          <div
            className="h-full rounded-full bar-fill-scale"
            style={{
              transform: `scaleX(${intensityPct / 100})`,
              backgroundColor: isHighIntensity
                ? "var(--color-negative)"
                : isL7
                ? "var(--color-layer7-amber)"
                : "var(--color-signal-cyan)",
              boxShadow: isHighIntensity
                ? "0 0 8px var(--color-negative)"
                : isL7
                ? "0 0 8px var(--color-layer7-amber)"
                : "0 0 8px var(--color-signal-cyan)",
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default function LiveFeed() {
  const events = useRadarStore((s) => s.events);
  const connectionState = useRadarStore((s) => s.connectionState);
  const lastConnectedAt = useRadarStore((s) => s.lastConnectedAt);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div
        className="flex items-center justify-between px-3.5 py-2.5 shrink-0 bg-slate-950/80"
        style={{ borderBottom: "1px solid rgba(47, 209, 224, 0.2)" }}
      >
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" aria-hidden="true" />
          <span className="type-label font-bold tracking-wider text-cyan-400">
            Real-Time Attack Intercept
          </span>
        </div>
        <span
          className="font-mono text-[11px] px-2 py-0.5 rounded font-bold tabular-nums uppercase"
          aria-live="polite"
          style={{
            backgroundColor: "rgba(47, 209, 224, 0.15)",
            color: "var(--color-signal-cyan)",
          }}
        >
          {events.length} Captured
        </span>
      </div>

      {/* Feed list */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden divide-y divide-slate-800/30">
        {connectionState === "OFFLINE" ? (
          <div className="flex flex-col items-center justify-center h-full px-4 text-center">
            <span className="w-3 h-3 rounded-full bg-rose-500 animate-ping mb-3" aria-hidden="true" />
            <span className="font-space text-[14px] text-white font-bold mb-1">
              Disconnected from Radar
            </span>
            <span className="font-mono text-[12px] text-slate-400">
              {lastConnectedAt
                ? `Last packet at ${formatTime(lastConnectedAt)}`
                : "Re-establishing socket connection…"}
            </span>
          </div>
        ) : events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-center p-4">
            <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" aria-hidden="true" />
            <span className="font-mono text-[12px] text-cyan-400 font-bold tracking-wider uppercase">
              Scanning global traffic…
            </span>
          </div>
        ) : (
          events.map((event, i) => (
            <FeedRow key={event.event_id} event={event} index={i} />
          ))
        )}
      </div>
    </div>
  );
}
