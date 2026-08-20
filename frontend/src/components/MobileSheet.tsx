"use client";

import { useState } from "react";
import { useRadarStore } from "@/store/useRadarStore";
import AttackIntensity from "@/components/AttackIntensity";
import TopCountries from "@/components/TopCountries";
import ThreatFeed from "@/components/ThreatFeed";
import Legend from "@/components/Legend";

/**
 * Mobile-only slide-up data sheet (md:hidden). The globe stays the full-screen
 * hero; the corner HUD cards — which overlap on a phone — are stacked here
 * behind a tappable peek header. Desktop keeps the floating corner cards.
 */
export default function MobileSheet() {
  const [open, setOpen] = useState(false);
  const activeIndicatorCount = useRadarStore((s) => s.indicators.length);
  const routeCount = useRadarStore((s) => s.topRoutes.length);
  const connectionState = useRadarStore((s) => s.connectionState);
  const isLive = connectionState === "CONNECTED";

  return (
    <div className="md:hidden">
      {/* Backdrop — tap to close */}
      <div
        className="fixed inset-0 z-30 transition-opacity duration-200"
        style={{
          backgroundColor: "rgba(2, 5, 9, 0.5)",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
        }}
        onClick={() => setOpen(false)}
        aria-hidden="true"
      />

      {/* Sheet */}
      <div
        className="fixed left-0 right-0 bottom-0 z-40 flex flex-col"
        style={{
          maxHeight: open ? "82vh" : "auto",
          backgroundColor: "rgba(5, 13, 21, 0.97)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          borderTop: "1px solid rgba(0, 217, 255, 0.18)",
          boxShadow: "0 -12px 40px rgba(0, 0, 0, 0.6)",
          transition: "max-height 220ms ease",
          paddingBottom: "env(safe-area-inset-bottom)",
        }}
      >
        {/* Grab handle */}
        <div className="flex justify-center pt-2" aria-hidden="true">
          <span
            className="block rounded-full"
            style={{ width: 36, height: 4, backgroundColor: "var(--color-hairline-light)" }}
          />
        </div>

        {/* Peek header — tap to toggle */}
        <button
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-controls="mobile-data-sheet"
          className="flex items-center justify-between px-4 py-3 w-full cursor-pointer"
        >
          <div className="flex items-center gap-3 min-w-0">
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{
                backgroundColor: isLive
                  ? "var(--color-severity-low)"
                  : "var(--color-text-faint)",
                boxShadow: isLive ? "0 0 6px var(--color-severity-low)" : "none",
              }}
              aria-hidden="true"
            />
            <span
              className="font-mono text-[11px] font-bold tracking-widest uppercase shrink-0"
              style={{ color: "var(--color-text-primary)" }}
            >
              Live Data
            </span>
            <span
              className="font-mono text-[10px] uppercase tabular-nums truncate"
              style={{ color: "var(--color-text-muted)" }}
            >
              {activeIndicatorCount} dots &middot; {routeCount} routes
            </span>
          </div>
          <svg
            width="16"
            height="16"
            viewBox="0 0 14 14"
            className="shrink-0"
            style={{ transform: open ? "rotate(180deg)" : "none", transition: "transform 200ms ease" }}
            aria-hidden="true"
          >
            <path
              d="M3 5 L7 9 L11 5"
              stroke="var(--color-text-muted)"
              strokeWidth="1.5"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>

        {/* Scrollable panel stack */}
        <div
          id="mobile-data-sheet"
          className="overflow-y-auto overscroll-contain px-4 pb-4 flex-col gap-3"
          style={{ display: open ? "flex" : "none" }}
        >
          <AttackIntensity />
          <TopCountries />
          <ThreatFeed />
          <Legend />
        </div>
      </div>
    </div>
  );
}
