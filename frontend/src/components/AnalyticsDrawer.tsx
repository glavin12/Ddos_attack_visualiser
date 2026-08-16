"use client";

import { useEffect, useCallback } from "react";
import { useRadarStore } from "@/store/useRadarStore";
import HistoryChart from "@/components/HistoryChart";
import TopTargets from "@/components/TopTargets";
import TargetDistribution from "@/components/TargetDistribution";
import AttackTypes from "@/components/AttackTypes";
import AnalyticsPanel from "@/components/AnalyticsPanel";

/**
 * Right-side analytics drawer — holds the REST-driven deep-dive panels
 * (history, attacked countries, distribution, attack types, vectors).
 * Toggle state lives in the store so the Topbar button can control it.
 */
export default function AnalyticsDrawer() {
  const open = useRadarStore((s) => s.analyticsOpen);
  const setAnalyticsOpen = useRadarStore((s) => s.setAnalyticsOpen);

  const close = useCallback(() => setAnalyticsOpen(false), [setAnalyticsOpen]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, close]);

  return (
    <>
      {/* Backdrop (click to close) */}
      <div
        className="fixed inset-0 z-30 transition-opacity duration-200"
        style={{
          backgroundColor: "rgba(2, 5, 9, 0.45)",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
          backdropFilter: "blur(1px)",
          WebkitBackdropFilter: "blur(1px)",
        }}
        onClick={close}
        aria-hidden="true"
      />

      {/* Drawer */}
      <aside
        id="analytics-drawer"
        role="dialog"
        aria-label="Attack analytics"
        aria-hidden={!open}
        className="fixed top-12 right-0 bottom-0 z-40 w-[360px] max-w-[92vw] flex flex-col overflow-hidden transition-transform duration-200 ease-out"
        style={{
          backgroundColor: "rgba(5, 13, 21, 0.94)",
          borderLeft: "1px solid rgba(0, 217, 255, 0.18)",
          boxShadow: "-12px 0 40px rgba(0, 0, 0, 0.6)",
          transform: open ? "translateX(0)" : "translateX(100%)",
          visibility: open ? "visible" : "hidden",
        }}
      >
        {/* Drawer header */}
        <div
          className="flex items-center justify-between px-4 py-3 shrink-0"
          style={{ borderBottom: "1px solid rgba(0, 217, 255, 0.18)" }}
        >
          <div className="flex items-center gap-2.5">
            <svg
              width="14"
              height="14"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <polygon
                points="8,1 15,8 8,15 1,8"
                fill="none"
                stroke="var(--color-signal-cyan)"
                strokeWidth="1.5"
              />
              <polygon
                points="8,4 12,8 8,12 4,8"
                fill="var(--color-signal-cyan)"
                opacity="0.4"
              />
            </svg>
            <span
              className="font-mono text-[11px] font-bold tracking-[0.16em] uppercase"
              style={{ color: "var(--color-text-primary)" }}
            >
              Threat Analytics
            </span>
          </div>
          <button
            onClick={close}
            aria-label="Close analytics panel"
            className="w-6 h-6 flex items-center justify-center rounded cursor-pointer transition-colors"
            style={{
              color: "var(--color-text-muted)",
              border: "1px solid var(--color-hairline)",
            }}
          >
            <svg
              width="10"
              height="10"
              viewBox="0 0 10 10"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M1 1 L9 9 M9 1 L1 9"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        {/* Sections */}
        <div className="flex-1 overflow-y-auto overscroll-contain divide-y divide-[rgba(0,217,255,0.08)]">
          <HistoryChart />
          <TopTargets />
          <TargetDistribution />
          <AttackTypes />
          <AnalyticsPanel />

          {/* Footer methodology note */}
          <div className="px-3.5 py-3">
            <p
              className="font-mono text-[9px] uppercase leading-relaxed tracking-wider"
              style={{ color: "var(--color-text-faint)" }}
            >
              Source: Cloudflare Radar telemetry · L3 (network layer) / L7
              (application layer) · Global sample, last 7 days · Synthetic
              visualization only — not real attack telemetry.
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
