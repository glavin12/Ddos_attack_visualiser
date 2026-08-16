"use client";

import { useEffect, useState } from "react";
import { useRadarStore } from "@/store/useRadarStore";

export default function MetricsBar() {
  const demoMetrics = useRadarStore((s) => s.demoMetrics);
  const activeEventCount = useRadarStore((s) => s.activeEventCount);
  const events = useRadarStore((s) => s.events);
  const topTargets = useRadarStore((s) => s.topTargets);

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

  const totalAttacks = demoMetrics ? `${demoMetrics.totalTrafficGbps.toFixed(2)} Mpps` : "8.72 Mpps";
  const targets = demoMetrics?.targetsUnderAttack || activeEventCount || (topTargets.length ? topTargets.length : 23);
  const countries = demoMetrics?.countriesInvolved || (events.length > 0 ? 68 : 68);
  const lastMin = demoMetrics?.lastMinTrafficTb ? `${demoMetrics.lastMinTrafficTb.toFixed(2)} TB` : "6.21 TB";
  const blocked = demoMetrics?.blockedPct ? `${demoMetrics.blockedPct.toFixed(1)}%` : "98.7%";

  return (
    <div
      className="panel-glass rounded-xl px-2 py-2 flex items-center shadow-2xl max-w-5xl w-full justify-between overflow-x-auto"
      style={{
        backgroundColor: "rgba(6, 14, 24, 0.85)",
        border: "1px solid rgba(30, 60, 90, 0.45)",
        boxShadow: "0 12px 40px rgba(0, 0, 0, 0.75)",
      }}
      role="region"
      aria-label="Network telemetry metrics"
    >
      {/* 1. TOTAL ATTACKS */}
      <div className="flex-1 min-w-[130px] px-4 py-1 text-center border-r border-[rgba(30,60,90,0.35)]">
        <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
          Total Attacks
        </div>
        <div className="font-mono text-[20px] font-bold tabular-nums text-[#FF5566]">
          {totalAttacks}
        </div>
      </div>

      {/* 2. TARGETS UNDER ATTACK */}
      <div className="flex-1 min-w-[140px] px-4 py-1 text-center border-r border-[rgba(30,60,90,0.35)]">
        <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
          Targets Under Attack
        </div>
        <div className="font-mono text-[20px] font-bold tabular-nums text-[#FF8833]">
          {targets}
        </div>
      </div>

      {/* 3. COUNTRIES INVOLVED */}
      <div className="flex-1 min-w-[130px] px-4 py-1 text-center border-r border-[rgba(30,60,90,0.35)]">
        <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
          Countries Involved
        </div>
        <div className="font-mono text-[20px] font-bold tabular-nums text-[#00D9FF]">
          {countries}
        </div>
      </div>

      {/* 4. LAST 1 MIN TRAFFIC */}
      <div className="flex-1 min-w-[130px] px-4 py-1 text-center border-r border-[rgba(30,60,90,0.35)]">
        <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
          Last 1 Min Traffic
        </div>
        <div className="font-mono text-[20px] font-bold tabular-nums text-[#12C8B0]">
          {lastMin}
        </div>
      </div>

      {/* 5. BLOCKED ATTACKS */}
      <div className="flex-1 min-w-[130px] px-4 py-1 text-center border-r border-[rgba(30,60,90,0.35)]">
        <div className="font-mono text-[9px] font-bold uppercase tracking-[0.14em] text-[#8EA0AD] mb-1">
          Blocked Attacks
        </div>
        <div className="font-mono text-[20px] font-bold tabular-nums text-[#38BDF8]">
          {blocked}
        </div>
      </div>

      {/* 6. LIVE TIME */}
      <div className="flex-1 min-w-[130px] px-4 py-1 text-center">
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
