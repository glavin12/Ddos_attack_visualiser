/** Application constants. Config values match backend config.py defaults. */

import type { SourceFeed } from "@/lib/types";

/* ─── API ─── */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/api/v1/ws/radar";

/* ─── REST refresh cadence ─── */
/** Radar top-routes refresh — backend polls Cloudflare every 6h; we poll well inside that window. */
export const ROUTES_REFRESH_MS = 30 * 60 * 1000; // 30 min
export const STATUS_POLL_MS = 30 * 1000;

/* ─── Threat indicator feed budget ─── */
export const MAX_INDICATOR_POINTS = 200;
export const MAX_LIVE_FEED_ROWS = 60;

/* ─── Arc rendering (Radar 24h aggregate top routes) ─── */
export const MAX_ARCS = 30;
/** Comet flight duration range — faster for higher-ranked (larger share) routes. */
export const ARC_FLIGHT_MS_FAST = 2500; // top-10 routes
export const ARC_FLIGHT_MS_SLOW = 3500; // remaining routes
export const ARC_BASE_TRAIL_OPACITY = 0.15;
export const ARC_HOVER_DIM_OPACITY = 0.05;
export const ARC_MIN_ALTITUDE = 0.15;
export const ARC_MAX_ALTITUDE = 0.3;

/* ─── Threat indicator birth choreography (ms, from motion spec) ─── */
export const BIRTH_PULSE_START_MS = 800;
export const BIRTH_PULSE_END_MS = 1200;
export const BIRTH_SETTLE_START_MS = 1200;
export const BIRTH_SETTLE_END_MS = 3000;

/* ─── Persistent point life ─── */
export const POINT_SETTLED_OPACITY = 0.55;
export const POINT_BREATHE_MIN_OPACITY = 0.4;
export const POINT_BREATHE_MAX_OPACITY = 0.7;
export const POINT_BREATHE_PERIOD_MS = 4000;
export const POINT_AGING_THRESHOLD_MS = 6 * 60 * 60 * 1000; // 6h since last_seen
export const POINT_AGED_OPACITY = 0.25;

/* ─── Country resonance (dot birth -> border pulse) ─── */
export const RESONANCE_DURATION_MS = 800;

/* ─── Ambient sonar (quiet-globe heartbeat) ─── */
export const SONAR_IDLE_THRESHOLD_MS = 30 * 1000;
export const SONAR_INTERVAL_MS = 8 * 1000;

/* ─── Globe ─── */
export const GLOBE_AUTO_ROTATE_DEG_PER_SEC = 360 / 120; // 1 rev / 120s
export const GLOBE_IDLE_RESUME_MS = 8000;

/* ─── WebSocket reconnect ─── */
export const WS_RECONNECT_BASE_MS = 1000;
export const WS_RECONNECT_MAX_MS = 30000;

/* ─── Colors (mirrored from CSS for JS/Three.js usage) ─── */
export const COLORS = {
  // Backgrounds
  void: "#020408",
  panel: "#0A1017",
  panelRaised: "#0D151D",
  hairline: "#1C2A34",
  hairlineLight: "#253844",

  // Text
  textPrimary: "#E4EDF1",
  textMuted: "#7C939E",
  textFaint: "#48606C",

  // Primary accent — signal cyan (arcs, cool/context)
  signalCyan: "#3FE0D0",
  signalCyanDim: "rgba(63,224,208,0.16)",
  signalCyanBright: "#6FF5E6",

  // Secondary accent — amber (warn/threat)
  amber: "#F5A623",
  amberDim: "rgba(245,166,35,0.16)",

  // Source feed colors (dots) — honest by feed, not arbitrary severity
  feedFeodo: "#FF4D5E", // active botnet C2 — most dangerous class
  feedUrlhaus: "#F5A623", // malware distribution URLs
  feedThreatfox: "#E85DE0", // general IOCs

  // Globe
  globeBase: "#04070C",
  globeOcean: "#081119",
} as const;

export const ALL_SOURCE_FEEDS: SourceFeed[] = ["feodo", "urlhaus", "threatfox"];

export function feedColor(feed: SourceFeed): string {
  switch (feed) {
    case "feodo":
      return COLORS.feedFeodo;
    case "urlhaus":
      return COLORS.feedUrlhaus;
    case "threatfox":
      return COLORS.feedThreatfox;
  }
}

export function feedLabel(feed: SourceFeed): string {
  switch (feed) {
    case "feodo":
      return "Feodo Tracker";
    case "urlhaus":
      return "URLhaus";
    case "threatfox":
      return "ThreatFox";
  }
}

export function feedSourceUrl(feed: SourceFeed): string {
  switch (feed) {
    case "feodo":
      return "https://feodotracker.abuse.ch";
    case "urlhaus":
      return "https://urlhaus.abuse.ch";
    case "threatfox":
      return "https://threatfox.abuse.ch";
  }
}

/** Deterministic [0,1) hash of a string — stable across renders/reloads. */
export function hash01(input: string, salt = 0): number {
  let h = 2166136261 ^ salt;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 10000) / 10000;
}
