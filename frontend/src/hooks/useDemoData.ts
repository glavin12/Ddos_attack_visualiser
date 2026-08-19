"use client";

import { useEffect, useRef } from "react";
import { useRadarStore } from "@/store/useRadarStore";
import { ALL_SOURCE_FEEDS, DEMO_MODE } from "@/lib/constants";
import { DEMO_CITIES } from "@/lib/demoCities";
import type { AttackRoute, ThreatIndicatorData } from "@/lib/types";

/**
 * Demo data generator — feeds the store synthetic routes + indicators so the
 * dashboard renders meaningfully even without a running backend.
 *
 * Activated only when WS is not CONNECTED and NEXT_PUBLIC_DEMO_MODE=true.
 * Every route/indicator this hook produces is passed to the store with
 * { synthetic: true }, which GlobeIndicatorPoint/GlobeArc carry through as
 * isSynthetic — GlobeCanvas dims/thins them and Legend/AttackIntensity avoid
 * attributing them to Cloudflare Radar or public feeds. The Topbar "Demo
 * Data" banner is a secondary, always-visible signal on top of that
 * (CLAUDE.md §3: real vs synthetic must stay separable).
 */

const THREAT_FAMILIES = ["Emotet", "TrickBot", "QakBot", "Cobalt Strike", "AgentTesla", "Dridex"];

const DEMO_ROUTE_COUNTRIES: { code: string; name: string; lat: number; lon: number }[] = [
  { code: "CN", name: "China", lat: 35.86, lon: 104.2 },
  { code: "US", name: "United States", lat: 37.09, lon: -95.71 },
  { code: "RU", name: "Russia", lat: 61.52, lon: 105.32 },
  { code: "DE", name: "Germany", lat: 51.17, lon: 10.45 },
  { code: "BR", name: "Brazil", lat: -14.24, lon: -51.93 },
  { code: "IN", name: "India", lat: 20.59, lon: 78.96 },
  { code: "SG", name: "Singapore", lat: 1.35, lon: 103.82 },
  { code: "NL", name: "Netherlands", lat: 52.13, lon: 5.29 },
  { code: "GB", name: "United Kingdom", lat: 55.38, lon: -3.44 },
  { code: "UA", name: "Ukraine", lat: 48.38, lon: 31.17 },
  { code: "JP", name: "Japan", lat: 36.2, lon: 138.25 },
  { code: "VN", name: "Vietnam", lat: 14.06, lon: 108.28 },
];

const DEMO_ROUTE_PAIRS: [string, string, number][] = [
  ["CN", "US", 0.18], ["RU", "DE", 0.12], ["BR", "US", 0.09],
  ["IN", "SG", 0.07], ["UA", "GB", 0.06], ["VN", "JP", 0.05],
  ["NL", "US", 0.04], ["DE", "GB", 0.03],
];

function buildDemoRoutes(): AttackRoute[] {
  const byCode = new Map(DEMO_ROUTE_COUNTRIES.map((c) => [c.code, c]));
  return DEMO_ROUTE_PAIRS.map(([srcCode, tgtCode, share], i) => {
    const src = byCode.get(srcCode)!;
    const tgt = byCode.get(tgtCode)!;
    return {
      source: { code: src.code, name: src.name },
      target: { code: tgt.code, name: tgt.name },
      share,
      rank: i + 1,
    };
  });
}

function randomFrom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomIp(): string {
  return `${1 + Math.floor(Math.random() * 223)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${1 + Math.floor(Math.random() * 254)}`;
}

let demoCounter = 0;

function generateDemoIndicator(): ThreatIndicatorData | null {
  const codes = Object.keys(DEMO_CITIES);
  const code = randomFrom(codes);
  const cities = DEMO_CITIES[code];
  if (!cities?.length) return null;
  const city = randomFrom(cities);
  const now = new Date().toISOString();
  demoCounter++;

  return {
    indicator: `demo-${demoCounter}-${randomIp()}`,
    indicator_type: "ip",
    source_feed: randomFrom(ALL_SOURCE_FEEDS),
    resolved_ip: randomIp(),
    country_code: code,
    country_name: null,
    city: city.city,
    lat: city.lat,
    lng: city.lng,
    threat_family: randomFrom(THREAT_FAMILIES),
    first_seen: now,
    last_seen: now,
    greynoise_classification: null,
    greynoise_tags: null,
    source_url: null,
  };
}

export function useDemoData() {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const connectionState = useRadarStore((s) => s.connectionState);
  const topRoutes = useRadarStore((s) => s.topRoutes);
  const addIndicator = useRadarStore((s) => s.addIndicator);
  const setTopRoutes = useRadarStore((s) => s.setTopRoutes);
  const setActiveIndicatorCount = useRadarStore((s) => s.setActiveIndicatorCount);
  const setLoadState = useRadarStore((s) => s.setLoadState);

  useEffect(() => {
    const shouldDemo = DEMO_MODE && connectionState !== "CONNECTED";

    if (shouldDemo && !intervalRef.current) {
      if (topRoutes.length === 0) {
        setTopRoutes(buildDemoRoutes(), { synthetic: true });
      }
      setLoadState("loaded");

      intervalRef.current = setInterval(() => {
        const indicator = generateDemoIndicator();
        if (indicator) addIndicator(indicator, { synthetic: true });
        setActiveIndicatorCount(20 + Math.floor(Math.random() * 40));
      }, 900 + Math.random() * 900);
    }

    if (!shouldDemo && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [connectionState, topRoutes.length, addIndicator, setTopRoutes, setActiveIndicatorCount, setLoadState]);
}
