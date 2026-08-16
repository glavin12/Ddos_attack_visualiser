"use client";

import { useRadarStore } from "@/store/useRadarStore";
import BarList from "@/components/BarList";

export default function TopTargets() {
  const topTargets = useRadarStore((s) => s.topTargets);

  return (
    <BarList
      title="Top Attacked Countries"
      entries={topTargets.slice(0, 8).map((e) => ({
        code: e.country.code,
        name: e.country.name,
        share: e.share,
      }))}
    />
  );
}
