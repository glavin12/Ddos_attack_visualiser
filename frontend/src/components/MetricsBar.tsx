"use client";

import { useEffect, useState } from "react";
import { useRadarStore } from "@/store/useRadarStore";

export default function MetricsBar() {
  const demoMetrics = useRadarStore((s) => s.demoMetrics);
  const activeEventCount = useRadarStore((s) => s.activeEventCount);
  const totalEvents = useRadarStore((s) => s.totalEvents);
  const topTargets = useRadarStore((s) => s.topTargets);
  const connectionState = useRadarStore((s) => s.connectionState);
  const useDemo = connectionState !== "CONNECTED" && demoMetrics !== null;

  // Live UTC clock ticking in real-time
  const [utcTime, setUtcTime] = useState<string>("");
  useEffect(() => {
    const tick = () => {
      const d = new Date();
      const h = String(d.getUTCHours()).padStart(2, "0");
      const m = String(d.getUTCMinutes()).padStart(2, "0");
      const s = String(d.getUTCSeconds()).padStart(2, "0");
      setUtcTime(`${h}:${m}:${s} UTC`);
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, []);

  const totalAttacks = totalEvents > 0 ? totalEvents : "—";
  const targets = useDemo
    ? demoMetrics.targetsUnderAttack
    : activeEventCount > 0
      ? activeEventCount
      : "—";
  const countries = useDemo
    ? demoMetrics.countriesInvolved
    : topTargets.length > 0
      ? topTargets.length
      : "—";
  const lastMin = useDemo && demoMetrics.lastMinTrafficTb
    ? `${demoMetrics.lastMinTrafficTb.toFixed(2)} TB`
    : "—";
  const blocked = useDemo && demoMetrics.blockedPct
    ? `${demoMetrics.blockedPct.toFixed(1)}%`
    : "—";

  return (
    <div
      className="flex items-center gap-4 max-w-5xl w-full justify-center"
      role="region"
      aria-label="Network telemetry metrics"
    >
      {/* ── Left Main Metric Strip (5 metrics) ── */}
      <div
        className="panel-glass rounded-xl px-2 py-2.5 flex items-center shadow-2xl flex-1 justify-between"
        style={{
          backgroundColor: "rgba(6, 14, 24, 0.78)",
          border: "1px solid rgba(30, 60, 90, 0.45)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.6)",
        }}
      >
        {/* 1. TOTAL ATTACKS */}
        <div className="flex-1 px-4 py-1 text-center border-r border-[rgba(30,60,90,0.45)]">
          <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
            Total Attacks
          </div>
          <div className="font-mono text-[20px] font-bold tabular-nums text-[#FF3B4E]">
            {totalAttacks}
          </div>
        </div>

        {/* 2. TARGETS UNDER ATTACK */}
        <div className="flex-1 px-4 py-1 text-center border-r border-[rgba(30,60,90,0.45)]">
          <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
            Targets Under Attack
          </div>
          <div className="font-mono text-[20px] font-bold tabular-nums text-[#FF7A18]">
            {targets}
          </div>
        </div>

        {/* 3. COUNTRIES INVOLVED */}
        <div className="flex-1 px-4 py-1 text-center border-r border-[rgba(30,60,90,0.45)]">
          <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
            Countries Involved
          </div>
          <div className="font-mono text-[20px] font-bold tabular-nums text-[#00D9FF]">
            {countries}
          </div>
        </div>

        {/* 4. LAST 1 MIN TRAFFIC */}
        <div className="flex-1 px-4 py-1 text-center border-r border-[rgba(30,60,90,0.45)]">
          <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
            Last 1 Min Traffic
          </div>
          <div className="font-mono text-[20px] font-bold tabular-nums text-[#12C8B0]">
            {lastMin}
          </div>
        </div>

        {/* 5. BLOCKED ATTACKS */}
        <div className="flex-1 px-4 py-1 text-center">
          <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
            Blocked Attacks
          </div>
          <div className="font-mono text-[20px] font-bold tabular-nums text-[#38BDF8]">
            {blocked}
          </div>
        </div>
      </div>

      {/* ── Right Separate LIVE TIME Box ── */}
      <div
        className="panel-glass rounded-xl px-5 py-2.5 text-center shrink-0 min-w-[150px]"
        style={{
          backgroundColor: "rgba(6, 14, 24, 0.78)",
          border: "1px solid rgba(30, 60, 90, 0.45)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.6)",
        }}
      >
        <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
          Live Time
        </div>
        <div className="font-mono text-[18px] font-bold tabular-nums text-[#10B981]">
          {utcTime || "14:32:18 UTC"}
        </div>
      </div>
    </div>
  );
}
