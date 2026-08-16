"use client";

import { useMemo } from "react";
import { useRadarStore } from "@/store/useRadarStore";
import { formatNumber } from "@/lib/format";
import { SkeletonRows, PanelError } from "@/components/PanelStates";

const W = 300;
const H = 120;
const PAD = 8;

export default function HistoryChart() {
  const history = useRadarStore((s) => s.history);
  const loadState = useRadarStore((s) => s.loadState);
  const requestReload = useRadarStore((s) => s.requestReload);

  const { line, area, maxValue } = useMemo(() => {
    if (history.length === 0) {
      return { line: "", area: "", maxValue: 0 };
    }
    const vals = history.map((p) => p.value);
    const max = Math.max(...vals, 1e-9);
    const stepX = (W - PAD * 2) / (history.length - 1);
    const y = (v: number) => H - PAD - (v / max) * (H - PAD * 2);

    const pts = history.map((p, i) => {
      const x = PAD + i * stepX;
      return `${x.toFixed(2)},${y(p.value).toFixed(2)}`;
    });

    return {
      line: `M${pts.join(" L")}`,
      area: `M${PAD},${H - PAD} L${pts.join(" L")} L${W - PAD},${H - PAD} Z`,
      maxValue: max,
    };
  }, [history]);

  return (
    <div className="flex flex-col">
      <div
        className="flex items-center justify-between px-3.5 py-2.5 shrink-0 bg-slate-950/70"
        style={{ borderBottom: "1px solid rgba(47, 209, 224, 0.2)" }}
      >
        <span className="type-label font-bold text-cyan-400 tracking-wider">
          7-Day Attack Timeline
        </span>
        <span className="font-mono text-[10px] text-slate-400 uppercase">
          Normalized Min-Max
        </span>
      </div>

      <div className="p-3.5">
        {loadState === "loading" ? (
          <SkeletonRows rows={3} />
        ) : loadState === "error" ? (
          <PanelError message="Unable to reach radar API" onRetry={requestReload} />
        ) : history.length === 0 ? (
          <div
            className="flex items-center justify-center border border-dashed border-slate-800 rounded"
            style={{ height: H }}
          >
            <span className="font-mono text-[11px] text-slate-500 uppercase">
              Synchronizing historical telemetry…
            </span>
          </div>
        ) : (
          <div>
            <div className="rounded-lg p-2 bg-slate-950/50 border border-slate-800/80">
              <svg
                width="100%"
                viewBox={`0 0 ${W} ${H}`}
                preserveAspectRatio="none"
                role="img"
                aria-label="Seven day relative attack activity"
              >
                <defs>
                  <linearGradient id="historyFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-signal-cyan)" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="var(--color-signal-cyan)" stopOpacity="0.0" />
                  </linearGradient>
                </defs>
                <path d={area} fill="url(#historyFill)" />
                <path
                  d={line}
                  fill="none"
                  stroke="var(--color-signal-cyan)"
                  strokeWidth={2}
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                />
                <line
                  x1={PAD}
                  y1={H - PAD}
                  x2={W - PAD}
                  y2={H - PAD}
                  stroke="rgba(47, 209, 224, 0.3)"
                  strokeWidth={1}
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
            </div>
            <div className="flex items-center justify-between mt-2.5 px-1 font-mono text-[10px] text-slate-400 uppercase">
              <span>7 days ago</span>
              <span className="text-cyan-400 font-bold tabular-nums">Peak: {formatNumber(maxValue, 2)}</span>
              <span>Live</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
