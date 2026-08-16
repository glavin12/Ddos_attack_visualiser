"use client";

const SEVERITY_LEVELS = [
  { label: "CRITICAL", color: "#FF3B4E", glow: "rgba(255, 59, 78, 0.75)", desc: "High volume / multi-vector" },
  { label: "HIGH",     color: "#FF7A18", glow: "rgba(255, 122, 24, 0.75)", desc: "Volumetric floods" },
  { label: "MEDIUM",   color: "#FFB52E", glow: "rgba(255, 181, 46, 0.75)", desc: "Protocol anomalies" },
  { label: "LOW",      color: "#12C8B0", glow: "rgba(18, 200, 176, 0.75)", desc: "Ambient probes" },
];

export default function AttackIntensity() {
  return (
    <div
      className="panel-glass rounded-xl p-3.5 min-w-[190px]"
      style={{
        backgroundColor: "rgba(4, 10, 20, 0.82)",
        border: "1px solid rgba(0, 217, 255, 0.22)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.7)",
      }}
      aria-label="Attack intensity"
    >
      <h2
        className="font-mono text-[10px] font-bold tracking-[0.14em] uppercase mb-3"
        style={{ color: "#8EA0AD" }}
      >
        Attack Intensity
      </h2>

      <div className="space-y-2.5">
        {SEVERITY_LEVELS.map(({ label, color, glow }) => (
          <div key={label} className="flex items-center gap-2.5">
            <span
              className="w-2.5 h-2.5 rounded-full shrink-0"
              style={{
                backgroundColor: color,
                boxShadow: `0 0 8px ${glow}`,
              }}
              aria-hidden="true"
            />
            <span
              className="font-mono text-[11.5px] font-bold tracking-wider"
              style={{ color: "#D7E5EA" }}
            >
              {label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
