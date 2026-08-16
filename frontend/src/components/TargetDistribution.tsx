"use client";

import { useRadarStore } from "@/store/useRadarStore";
import { formatPercent } from "@/lib/format";

// Map country codes to continents for distribution
const CONTINENT_MAP: Record<string, string> = {
  US: "North America", CA: "North America", MX: "North America",
  BR: "South America", AR: "South America", CO: "South America",
  GB: "Europe", DE: "Europe", FR: "Europe", NL: "Europe",
  PL: "Europe", UA: "Europe", TR: "Europe", IT: "Europe", ES: "Europe",
  CN: "Asia", JP: "Asia", KR: "Asia", IN: "Asia", SG: "Asia",
  ID: "Asia", VN: "Asia", TH: "Asia", PK: "Asia",
  AU: "Oceania", NZ: "Oceania",
  ZA: "Africa", NG: "Africa", EG: "Africa",
};

const CONTINENT_COLORS: Record<string, string> = {
  "Asia":          "var(--color-signal-cyan)",
  "North America": "var(--color-severity-medium)",
  "Europe":        "var(--color-severity-low)",
  "South America": "var(--color-severity-high)",
  "Africa":        "var(--color-text-muted)",
  "Oceania":       "var(--color-text-faint)",
};

// Build continent distribution from topTargets
function buildContinentDist(
  targets: { country: { code: string }; share: number }[]
): { name: string; share: number; color: string }[] {
  const map: Record<string, number> = {};
  for (const t of targets) {
    const continent = CONTINENT_MAP[t.country.code] ?? "Other";
    map[continent] = (map[continent] ?? 0) + t.share;
  }
  const total = Object.values(map).reduce((s, v) => s + v, 0) || 1;
  return Object.entries(map)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name, share]) => ({
      name,
      share: share / total,
      color: CONTINENT_COLORS[name] ?? "var(--color-text-faint)",
    }));
}

// Minimal SVG donut chart — no external deps
function DonutChart({
  segments,
  size = 72,
}: {
  segments: { share: number; color: string }[];
  size?: number;
}) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.35;
  const strokeW = size * 0.14;
  const circ = 2 * Math.PI * r;

  // Pre-compute cumulative offsets to avoid mutation during render
  const segData = segments.map((seg) => ({ ...seg, dash: seg.share * circ }));
  const offsets = segData.reduce<number[]>((acc) => {
    acc.push(acc.length === 0 ? 0 : acc[acc.length - 1] + segData[acc.length - 1].dash);
    return acc;
  }, []);

  const paths = segData.map((seg, i) => {
    const gap = circ - seg.dash;
    return (
      <circle
        key={i}
        cx={cx}
        cy={cy}
        r={r}
        fill="none"
        stroke={seg.color}
        strokeWidth={strokeW}
        strokeDasharray={`${seg.dash} ${gap}`}
        strokeDashoffset={-offsets[i]}
        strokeLinecap="butt"
        style={{ opacity: 0.85 }}
      />
    );
  });

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      style={{ transform: "rotate(-90deg)" }}
      aria-hidden="true"
    >
      {/* Track */}
      <circle
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke="rgba(20,42,56,0.6)"
        strokeWidth={strokeW}
      />
      {paths}
    </svg>
  );
}

export default function TargetDistribution() {
  const topTargets = useRadarStore((s) => s.topTargets);
  const continents = buildContinentDist(topTargets);
  const countryCount = topTargets.length > 0 ? 68 : 0;

  return (
    <section aria-label="Target distribution by region">
      <div
        className="px-3.5 py-2"
        style={{ borderBottom: "1px solid var(--color-hairline)" }}
      >
        <span className="type-label" style={{ color: "var(--color-text-muted)" }}>
          Target Distribution
        </span>
      </div>

      <div className="px-3.5 py-3">
        {/* Donut + center stat */}
        <div className="flex items-center gap-4 mb-3">
          <div className="relative shrink-0">
            <DonutChart segments={continents} size={80} />
            <div
              className="absolute inset-0 flex flex-col items-center justify-center"
              aria-hidden="true"
            >
              <span
                className="font-mono text-[18px] font-bold tabular-nums leading-none"
                style={{ color: "var(--color-signal-cyan)" }}
              >
                {countryCount}
              </span>
              <span
                className="type-label leading-none mt-0.5"
                style={{ color: "var(--color-text-faint)", fontSize: 8 }}
              >
                countries
              </span>
            </div>
          </div>

          {/* Legend */}
          <div className="space-y-1.5 min-w-0">
            {continents.slice(0, 4).map((c) => (
              <div key={c.name} className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  <span
                    className="w-1.5 h-1.5 rounded-full shrink-0"
                    style={{ backgroundColor: c.color }}
                    aria-hidden="true"
                  />
                  <span
                    className="font-mono text-[10px] truncate"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    {c.name}
                  </span>
                </div>
                <span
                  className="font-mono text-[10px] font-bold tabular-nums shrink-0"
                  style={{ color: c.color }}
                >
                  {formatPercent(c.share)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Remaining continents */}
        {continents.slice(4).map((c) => (
          <div key={c.name} className="flex items-center justify-between gap-2 mb-1">
            <div className="flex items-center gap-1.5">
              <span
                className="w-1.5 h-1.5 rounded-full shrink-0"
                style={{ backgroundColor: c.color }}
                aria-hidden="true"
              />
              <span
                className="font-mono text-[10px]"
                style={{ color: "var(--color-text-muted)" }}
              >
                {c.name}
              </span>
            </div>
            <span
              className="font-mono text-[10px] font-bold tabular-nums"
              style={{ color: c.color }}
            >
              {formatPercent(c.share)}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
