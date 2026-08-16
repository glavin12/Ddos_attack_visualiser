"use client";

import { useEffect, useRef } from "react";
import { useRadarStore } from "@/store/useRadarStore";
import { DEMO_MODE } from "@/lib/constants";
import type { AttackEventData, DemoMetrics } from "@/lib/types";

/**
 * Demo data generator — creates synthetic visualization events so the
 * globe renders beautifully even without a running backend.
 *
 * ALL demo events are marked is_synthetic: true, data_source: "synthetic"
 * per AGENTS.md §7. This is visual infrastructure, not real telemetry.
 *
 * Activated only when WebSocket is OFFLINE or RECONNECTING.
 */

const ATTACK_TYPES = [
  { name: "UDP FLOOD",  weight: 0.35 },
  { name: "SYN FLOOD",  weight: 0.28 },
  { name: "HTTP FLOOD", weight: 0.18 },
  { name: "ICMP FLOOD", weight: 0.08 },
  { name: "DNS AMP",    weight: 0.05 },
  { name: "NTP AMP",    weight: 0.04 },
  { name: "SSDP FLOOD", weight: 0.02 },
];

const DEMO_ROUTES = [
  { src: { code: "CN", name: "China",         lat: 35.86,  lon: 104.20  }, tgt: { code: "US", name: "United States", lat: 37.09, lon: -95.71 }, weight: 0.18 },
  { src: { code: "RU", name: "Russia",         lat: 61.52,  lon: 105.32  }, tgt: { code: "DE", name: "Germany",       lat: 51.17, lon:  10.45 }, weight: 0.12 },
  { src: { code: "BR", name: "Brazil",         lat: -14.24, lon: -51.93  }, tgt: { code: "US", name: "United States", lat: 37.09, lon: -95.71 }, weight: 0.09 },
  { src: { code: "IN", name: "India",          lat:  20.59, lon:  78.96  }, tgt: { code: "SG", name: "Singapore",     lat:  1.35, lon: 103.82 }, weight: 0.07 },
  { src: { code: "ID", name: "Indonesia",      lat:  -0.79, lon: 113.92  }, tgt: { code: "AU", name: "Australia",     lat: -25.27,lon: 133.78 }, weight: 0.06 },
  { src: { code: "UA", name: "Ukraine",        lat:  48.38, lon:  31.17  }, tgt: { code: "PL", name: "Poland",        lat: 51.92, lon:  19.15 }, weight: 0.05 },
  { src: { code: "VN", name: "Vietnam",        lat:  14.06, lon: 108.28  }, tgt: { code: "JP", name: "Japan",         lat: 36.20, lon: 138.25 }, weight: 0.05 },
  { src: { code: "NL", name: "Netherlands",    lat:  52.13, lon:   5.29  }, tgt: { code: "US", name: "United States", lat: 37.09, lon: -95.71 }, weight: 0.04 },
  { src: { code: "KR", name: "South Korea",    lat:  35.91, lon: 127.77  }, tgt: { code: "JP", name: "Japan",         lat: 36.20, lon: 138.25 }, weight: 0.04 },
  { src: { code: "FR", name: "France",         lat:  46.23, lon:   2.21  }, tgt: { code: "GB", name: "United Kingdom",lat: 55.38, lon:  -3.44 }, weight: 0.04 },
  { src: { code: "NG", name: "Nigeria",        lat:   9.08, lon:   8.68  }, tgt: { code: "ZA", name: "South Africa",  lat: -30.56,lon:  22.94 }, weight: 0.03 },
  { src: { code: "MX", name: "Mexico",         lat:  23.63, lon: -102.55 }, tgt: { code: "US", name: "United States", lat: 37.09, lon: -95.71 }, weight: 0.03 },
  { src: { code: "TR", name: "Turkey",         lat:  38.96, lon:  35.24  }, tgt: { code: "DE", name: "Germany",       lat: 51.17, lon:  10.45 }, weight: 0.03 },
  { src: { code: "PK", name: "Pakistan",       lat:  30.38, lon:  69.35  }, tgt: { code: "IN", name: "India",         lat: 20.59, lon:  78.96 }, weight: 0.03 },
  { src: { code: "TH", name: "Thailand",       lat:  15.87, lon: 100.99  }, tgt: { code: "SG", name: "Singapore",     lat:  1.35, lon: 103.82 }, weight: 0.02 },
  { src: { code: "US", name: "United States",  lat:  37.09, lon: -95.71  }, tgt: { code: "CN", name: "China",         lat: 35.86, lon: 104.20 }, weight: 0.04 },
  { src: { code: "DE", name: "Germany",        lat:  51.17, lon:  10.45  }, tgt: { code: "US", name: "United States", lat: 37.09, lon: -95.71 }, weight: 0.03 },
  { src: { code: "AR", name: "Argentina",      lat: -38.42, lon: -63.62  }, tgt: { code: "BR", name: "Brazil",        lat:-14.24, lon: -51.93 }, weight: 0.02 },
];

function jitter(v: number, range = 0.4): number {
  return v + (Math.random() - 0.5) * range;
}

function weightedSampleRoute() {
  const total = DEMO_ROUTES.reduce((s, r) => s + r.weight, 0);
  let r = Math.random() * total;
  for (const route of DEMO_ROUTES) {
    r -= route.weight;
    if (r <= 0) return route;
  }
  return DEMO_ROUTES[0];
}

function weightedSampleAttackType(): string {
  const total = ATTACK_TYPES.reduce((s, t) => s + t.weight, 0);
  let r = Math.random() * total;
  for (const t of ATTACK_TYPES) {
    r -= t.weight;
    if (r <= 0) return t.name;
  }
  return ATTACK_TYPES[0].name;
}

let demoCounter = 0;

// Intensity distribution: skewed toward LOW/MEDIUM with occasional spikes
function randomIntensity(): number {
  const r = Math.random();
  if (r > 0.92) return 0.76 + Math.random() * 0.24; // CRITICAL ~8%
  if (r > 0.75) return 0.51 + Math.random() * 0.24; // HIGH ~17%
  if (r > 0.45) return 0.26 + Math.random() * 0.24; // MEDIUM ~30%
  return 0.05 + Math.random() * 0.19;               // LOW ~45%
}

function generateDemoEvent(): AttackEventData {
  const route = weightedSampleRoute();
  const layer = Math.random() > 0.72 ? "L7" as const : "L3" as const;
  const intensity = randomIntensity();
  const trafficGbps = parseFloat((0.05 + intensity * 9.5).toFixed(2));
  const packetsPerSecond = Math.round(intensity * 2_800_000);
  demoCounter++;

  return {
    event_id: `demo-${demoCounter}-${Date.now()}`,
    layer,
    source: {
      code: route.src.code,
      name: route.src.name,
      lat: jitter(route.src.lat),
      lon: jitter(route.src.lon),
    },
    target: {
      code: route.tgt.code,
      name: route.tgt.name,
      lat: jitter(route.tgt.lat),
      lon: jitter(route.tgt.lon),
    },
    intensity,
    is_synthetic: true,
    data_source: "synthetic",
    attackType: weightedSampleAttackType(),
    trafficGbps,
    packetsPerSecond,
  };
}

function buildDemoMetrics(): DemoMetrics {
  return {
    totalTrafficGbps: parseFloat((5.8 + Math.random() * 4.2).toFixed(2)),
    targetsUnderAttack: Math.floor(18 + Math.random() * 12),
    countriesInvolved: Math.floor(58 + Math.random() * 18),
    blockedPct: parseFloat((97.2 + Math.random() * 2.5).toFixed(1)),
    lastMinTrafficTb: parseFloat((4.8 + Math.random() * 2.8).toFixed(2)),
    uptimeSeconds: Date.now() / 1000 - 1_700_000_000,
  };
}

export function useDemoData() {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const metricsRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const connectionState = useRadarStore((s) => s.connectionState);
  const addEvent = useRadarStore((s) => s.addEvent);
  const setActiveEventCount = useRadarStore((s) => s.setActiveEventCount);
  const setTopOrigins = useRadarStore((s) => s.setTopOrigins);
  const setTopTargets = useRadarStore((s) => s.setTopTargets);
  const setVectors = useRadarStore((s) => s.setVectors);
  const setProtocols = useRadarStore((s) => s.setProtocols);
  const setDemoMetrics = useRadarStore((s) => s.setDemoMetrics);
  const setLoadState = useRadarStore((s) => s.setLoadState);

  useEffect(() => {
    const shouldDemo = DEMO_MODE && connectionState !== "CONNECTED";

    if (shouldDemo && !intervalRef.current) {
      // Seed store with demo reference data
      setTopOrigins([
        { country: { code: "CN", name: "China"          }, share: 0.284, rank: 1 },
        { country: { code: "RU", name: "Russia"         }, share: 0.187, rank: 2 },
        { country: { code: "BR", name: "Brazil"         }, share: 0.128, rank: 3 },
        { country: { code: "IN", name: "India"          }, share: 0.096, rank: 4 },
        { country: { code: "ID", name: "Indonesia"      }, share: 0.063, rank: 5 },
        { country: { code: "UA", name: "Ukraine"        }, share: 0.054, rank: 6 },
        { country: { code: "VN", name: "Vietnam"        }, share: 0.048, rank: 7 },
        { country: { code: "NL", name: "Netherlands"    }, share: 0.042, rank: 8 },
      ]);

      setTopTargets([
        { country: { code: "US", name: "United States"  }, share: 0.312, rank: 1 },
        { country: { code: "DE", name: "Germany"        }, share: 0.148, rank: 2 },
        { country: { code: "SG", name: "Singapore"      }, share: 0.112, rank: 3 },
        { country: { code: "GB", name: "United Kingdom" }, share: 0.098, rank: 4 },
        { country: { code: "JP", name: "Japan"          }, share: 0.087, rank: 5 },
        { country: { code: "AU", name: "Australia"      }, share: 0.072, rank: 6 },
        { country: { code: "FR", name: "France"         }, share: 0.061, rank: 7 },
        { country: { code: "IN", name: "India"          }, share: 0.054, rank: 8 },
      ]);

      setVectors([
        { value: "UDP FLOOD",  share: 0.452 },
        { value: "SYN FLOOD",  share: 0.287 },
        { value: "HTTP FLOOD", share: 0.153 },
        { value: "ICMP FLOOD", share: 0.061 },
        { value: "OTHER",      share: 0.047 },
      ]);

      setProtocols([
        { value: "UDP",  share: 0.614 },
        { value: "TCP",  share: 0.298 },
        { value: "ICMP", share: 0.061 },
        { value: "HTTP", share: 0.027 },
      ]);

      setDemoMetrics(buildDemoMetrics());
      setLoadState("loaded");

      // Attack event stream: ~1 event / 600-1200ms
      intervalRef.current = setInterval(() => {
        addEvent(generateDemoEvent());
        setActiveEventCount(Math.floor(22 + Math.random() * 18));
      }, 600 + Math.random() * 600);

      // Metrics ticker: refresh every 5s
      metricsRef.current = setInterval(() => {
        setDemoMetrics(buildDemoMetrics());
      }, 5000);
    }

    if (!shouldDemo) {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      if (metricsRef.current)  { clearInterval(metricsRef.current);  metricsRef.current = null; }
    }

    return () => {
      if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      if (metricsRef.current)  { clearInterval(metricsRef.current);  metricsRef.current = null; }
    };
  }, [connectionState, addEvent, setActiveEventCount, setTopOrigins, setTopTargets,
      setVectors, setProtocols, setDemoMetrics, setLoadState]);
}
