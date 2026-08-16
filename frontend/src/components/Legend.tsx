"use client";

export default function Legend() {
  return (
    <div
      className="panel-glass rounded-xl p-4 min-w-[200px]"
      style={{
        backgroundColor: "rgba(6, 14, 24, 0.78)",
        border: "1px solid rgba(30, 60, 90, 0.45)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.6)",
      }}
      aria-label="Visualization legend"
    >
      <h2
        className="font-mono text-[10px] font-bold tracking-[0.14em] uppercase mb-3.5"
        style={{ color: "#8EA0AD" }}
      >
        Legend
      </h2>

      <div className="space-y-3 font-mono text-[12px]">
        {/* 1. Source: Concentric Red Ring with solid core */}
        <div className="flex items-center gap-3">
          <span className="relative flex items-center justify-center w-4 h-4 shrink-0" aria-hidden="true">
            <span className="absolute w-3.5 h-3.5 rounded-full border border-[#FF3B4E] opacity-75" />
            <span className="w-1.5 h-1.5 rounded-full bg-[#FF3B4E]" />
          </span>
          <span className="text-[#D7E5EA]">Source</span>
        </div>

        {/* 2. Target: Concentric Cyan Ring with hollow core */}
        <div className="flex items-center gap-3">
          <span className="relative flex items-center justify-center w-4 h-4 shrink-0" aria-hidden="true">
            <span className="absolute w-3.5 h-3.5 rounded-full border border-[#00D9FF] opacity-75" />
            <span className="w-1.5 h-1.5 rounded-full border border-[#00D9FF] bg-transparent" />
          </span>
          <span className="text-[#D7E5EA]">Target</span>
        </div>

        {/* 3. Attack Route: Solid line */}
        <div className="flex items-center gap-3">
          <span className="w-4 flex items-center justify-center shrink-0" aria-hidden="true">
            <span className="w-full h-[1.5px] bg-[#6F8793] opacity-80" />
          </span>
          <span className="text-[#D7E5EA]">Attack Route</span>
        </div>

        {/* 4. Low Intensity: Dotted Cyan */}
        <div className="flex items-center gap-3">
          <span className="w-4 flex items-center justify-center shrink-0" aria-hidden="true">
            <span
              className="w-full h-0 border-t-2 border-dotted"
              style={{ borderColor: "#12C8B0" }}
            />
          </span>
          <span className="text-[#D7E5EA]">Low Intensity</span>
        </div>

        {/* 5. Medium Intensity: Dotted Yellow */}
        <div className="flex items-center gap-3">
          <span className="w-4 flex items-center justify-center shrink-0" aria-hidden="true">
            <span
              className="w-full h-0 border-t-2 border-dotted"
              style={{ borderColor: "#FFB52E" }}
            />
          </span>
          <span className="text-[#D7E5EA]">Medium Intensity</span>
        </div>

        {/* 6. High Intensity: Dotted Red */}
        <div className="flex items-center gap-3">
          <span className="w-4 flex items-center justify-center shrink-0" aria-hidden="true">
            <span
              className="w-full h-0 border-t-2 border-dotted"
              style={{ borderColor: "#FF3B4E" }}
            />
          </span>
          <span className="text-[#D7E5EA]">High Intensity</span>
        </div>
      </div>
    </div>
  );
}
