"use client";

import { useRadarStore } from "@/store/useRadarStore";
import BarList from "@/components/BarList";

export default function TopSources() {
  const topOrigins = useRadarStore((s) => s.topOrigins);
  const topRoutes = useRadarStore((s) => s.topRoutes);

  // Use top origins if available, otherwise derive from routes
  const entries =
    topOrigins.length > 0
      ? topOrigins.slice(0, 8)
      : deriveFromRoutes(topRoutes);

  return (
    <BarList
      title="Top Sources"
      entries={entries.map((e) => ({
        code: e.country.code,
        name: e.country.name,
        share: e.share,
      }))}
    />
  );
}

function deriveFromRoutes(
  routes: { source: { code: string; name: string | null }; share: number }[]
) {
  const map = new Map<
    string,
    { code: string; name: string | null; total: number }
  >();
  for (const r of routes) {
    const existing = map.get(r.source.code);
    if (existing) {
      existing.total += Number(r.share);
    } else {
      map.set(r.source.code, {
        code: r.source.code,
        name: r.source.name,
        total: Number(r.share),
      });
    }
  }
  return Array.from(map.values())
    .sort((a, b) => b.total - a.total)
    .slice(0, 8)
    .map((e) => ({
      country: { code: e.code, name: e.name },
      share: e.total,
      rank: null,
    }));
}
