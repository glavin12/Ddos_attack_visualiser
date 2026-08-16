"use client";

const SEVERITY_LEVELS = [
  { label: "CRITICAL", color: "#FF3B4E", glow: "rgba(255, 59, 78, 0.6)" },
  { label: "HIGH",     color: "#FF7A18", glow: "rgba(255, 122, 24, 0.6)" },
  { label: "MEDIUM",   color: "#FFB52E", glow: "rgba(255, 181, 46, 0.6)" },
  { label: "LOW",      color: "#12C8B0", glow: "rgba(18, 200, 176, 0.6)" },
];

export default function AttackIntensity() {
  return (
    <div
      className="panel-glass rounded-xl p-4 min-w-[170px]"
      style={{
        backgroundColor: "rgba(6, 14, 24, 0.78)",
        border: "1px solid rgba(30, 60, 90, 0.45)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.6)",
      }}
      aria-label="Attack intensity"
    >
      <h2
        className="font-mono text-[10px] font-bold tracking-[0.14em] uppercase mb-3.5"
        style={{ color: "#8EA0AD" }}
      >
        Attack Intensity
      </h2>

      <div className="space-y-2.5">
        {SEVERITY_LEVELS.map(({ label, color, glow }) => (
          <div key={label} className="flex items-center gap-2.5">
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{
                backgroundColor: color,
                boxShadow: `0 0 8px ${glow}`,
              }}
              aria-hidden="true"
            />
            <span
              className="font-mono text-[11px] font-bold tracking-wider"
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
