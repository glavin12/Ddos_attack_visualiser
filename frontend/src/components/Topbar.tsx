"use client";

import { useEffect, useState } from "react";
import { useRadarStore } from "@/store/useRadarStore";
import ConnectionStatus from "@/components/ConnectionStatus";
import type { Layer } from "@/lib/types";

const LAYERS: { key: Layer; label: string }[] = [
  { key: "L3", label: "L3 Network" },
  { key: "L7", label: "L7 App" },
];

export default function Topbar() {
  const selectedLayer = useRadarStore((s) => s.selectedLayer);
  const setSelectedLayer = useRadarStore((s) => s.setSelectedLayer);
  const status = useRadarStore((s) => s.status);
  const activeEventCount = useRadarStore((s) => s.activeEventCount);
  const analyticsOpen = useRadarStore((s) => s.analyticsOpen);
  const setAnalyticsOpen = useRadarStore((s) => s.setAnalyticsOpen);

  // Live UTC clock — SSR safe (starts empty, fills on mount)
  const [utcTime, setUtcTime] = useState<string>("");
  useEffect(() => {
    const tick = () =>
      setUtcTime(
        new Intl.DateTimeFormat("en-GB", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
          timeZone: "UTC",
        }).format(new Date())
      );
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const isStale = status?.status === "degraded";

  return (
    <header
      className="flex items-center justify-between px-5 shrink-0 z-50 relative"
      style={{
        height: 48,
        backgroundColor: "rgba(8, 18, 28, 0.97)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(0, 217, 255, 0.15)",
        boxShadow: "0 2px 16px rgba(0, 0, 0, 0.5)",
      }}
    >
      {/* ── Left: Brand ── */}
      <div className="flex items-center gap-3">
        {/* Diamond logo mark */}
        <svg
          width="16"
          height="16"
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

        <div className="flex flex-col">
          <h1
            className="font-space text-[13px] font-bold tracking-[0.12em] leading-none uppercase"
            style={{ color: "#FFFFFF" }}
            translate="no"
          >
            DDoS{" "}
            <span style={{ color: "var(--color-signal-cyan)" }}>Sentinel</span>
          </h1>
          <span
            className="font-mono text-[8px] tracking-[0.14em] leading-none mt-0.5 uppercase hidden md:block"
            style={{ color: "var(--color-text-faint)" }}
          >
            Network Security Operations
          </span>
        </div>

        {/* Stale data warning */}
        {isStale && (
          <span
            className="hidden lg:inline-flex items-center gap-1 font-mono text-[10px] px-2 py-0.5 rounded uppercase tracking-wider"
            style={{
              backgroundColor: "rgba(255, 181, 46, 0.15)",
              color: "var(--color-severity-medium)",
              border: "1px solid rgba(255, 181, 46, 0.35)",
            }}
            aria-live="polite"
          >
            Data Degraded
          </span>
        )}
      </div>

      {/* ── Center: LIVE indicator ── */}
      <div className="hidden md:flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full live-pulse"
            style={{
              backgroundColor: "var(--color-severity-low)",
              boxShadow: "0 0 6px var(--color-severity-low)",
            }}
            aria-hidden="true"
          />
          <span
            className="font-mono text-[11px] font-bold tracking-widest uppercase"
            style={{ color: "var(--color-severity-low)" }}
          >
            Live
          </span>
        </div>

        <span style={{ color: "var(--color-hairline-light)" }} aria-hidden="true">|</span>

        {/* Active event count */}
        {activeEventCount > 0 && (
          <div
            className="flex items-center gap-1.5 px-2 py-0.5 rounded"
            style={{
              backgroundColor: "rgba(255, 59, 78, 0.12)",
              border: "1px solid rgba(255, 59, 78, 0.3)",
            }}
            aria-live="polite"
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: "var(--color-severity-critical)" }}
              aria-hidden="true"
            />
            <span
              className="font-mono text-[10px] font-bold uppercase tabular-nums"
              style={{ color: "var(--color-severity-critical)" }}
            >
              {activeEventCount} active
            </span>
          </div>
        )}
      </div>

      {/* ── Right: Controls ── */}
      <div className="flex items-center gap-3">
        {/* Analytics drawer toggle */}
        <button
          onClick={() => setAnalyticsOpen(!analyticsOpen)}
          aria-expanded={analyticsOpen}
          aria-controls="analytics-drawer"
          className="px-2.5 py-1 rounded text-[10px] font-mono font-bold tracking-wider cursor-pointer uppercase transition-colors"
          style={{
            backgroundColor: analyticsOpen
              ? "rgba(0, 217, 255, 0.18)"
              : "rgba(4, 8, 16, 0.8)",
            color: analyticsOpen
              ? "var(--color-signal-cyan)"
              : "var(--color-text-faint)",
            border: analyticsOpen
              ? "1px solid rgba(0, 217, 255, 0.4)"
              : "1px solid var(--color-hairline-light)",
          }}
        >
          Analytics
        </button>

        {/* Environment labels */}
        <div className="hidden lg:flex items-center gap-3 font-mono text-[10px]">
          <span style={{ color: "var(--color-text-faint)" }}>
            Simulation:{" "}
            <span style={{ color: "var(--color-severity-low)" }}>ACTIVE</span>
          </span>
          <span style={{ color: "var(--color-text-faint)" }}>
            Env:{" "}
            <span style={{ color: "var(--color-text-muted)" }}>DEMO</span>
          </span>
          <span
            className="tabular-nums"
            style={{ color: "var(--color-text-muted)" }}
          >
            {utcTime || "--:--:--"} UTC
          </span>
        </div>

        {/* L3 / L7 layer toggle */}
        <div
          className="flex p-0.5 rounded"
          role="group"
          aria-label="Attack layer selector"
          style={{
            backgroundColor: "rgba(4, 8, 16, 0.8)",
            border: "1px solid var(--color-hairline-light)",
          }}
        >
          {LAYERS.map((layer) => {
            const isActive = selectedLayer === layer.key;
            return (
              <button
                key={layer.key}
                onClick={() => setSelectedLayer(layer.key)}
                aria-pressed={isActive}
                className="px-2.5 py-1 rounded text-[10px] font-mono font-bold tracking-wider cursor-pointer uppercase"
                style={{
                  backgroundColor: isActive
                    ? "rgba(0, 217, 255, 0.18)"
                    : "transparent",
                  color: isActive
                    ? "var(--color-signal-cyan)"
                    : "var(--color-text-faint)",
                  border: isActive
                    ? "1px solid rgba(0, 217, 255, 0.4)"
                    : "1px solid transparent",
                  transition: "color 150ms ease, background-color 150ms ease",
                }}
              >
                {layer.label}
              </button>
            );
          })}
        </div>

        <ConnectionStatus />
      </div>
    </header>
  );
}
