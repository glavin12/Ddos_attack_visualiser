/** Application constants. Config values match backend config.py defaults. */

/* ─── API ─── */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/api/v1/ws/radar";

/* ─── Event budget (matches backend max_active_events) ─── */
export const MAX_LIVE_EVENTS = 100;
export const MAX_ACTIVE_ARCS = 45;

/* ─── Arc timing ─── */
export const ARC_FLIGHT_MS = 2200;
export const ARC_EXPIRE_MS = 10000;
export const RIPPLE_DURATION_MS = 1400;

/* ─── Globe ─── */
export const GLOBE_AUTO_ROTATE_DEG_PER_SEC = 360 / 90; // 1 rev / 90s (slow, readable)
export const GLOBE_IDLE_RESUME_MS = 8000;

/* ─── WebSocket reconnect ─── */
export const WS_RECONNECT_BASE_MS = 1000;
export const WS_RECONNECT_MAX_MS = 30000;

/* ─── Demo mode — synthetic visualization when backend is down ─── */
export const DEMO_MODE =
  (process.env.NEXT_PUBLIC_DEMO_MODE ?? "true").toLowerCase() === "true";

/* ─── Colors (mirrored from CSS for JS usage, e.g. Three.js) ─── */
export const COLORS = {
  // Backgrounds
  void: "#03070B",
  panel: "#08121C",
  panelRaised: "#0A1621",
  hairline: "#142A38",
  hairlineLight: "#193746",

  // Text
  textPrimary: "#D7E5EA",
  textMuted: "#6F8793",
  textFaint: "#3C535F",

  // Primary accent — signal cyan
  signalCyan: "#00D9FF",
  signalCyanDim: "rgba(0,217,255,0.18)",
  signalCyanBright: "#33E5FF",

  // Severity hierarchy
  severityCritical: "#FF3B4E",
  severityHigh: "#FF7A18",
  severityMedium: "#FFB52E",
  severityLow: "#12C8B0",

  // Globe
  globeBase: "#040810",

  // Legacy aliases (for compatibility)
  layer7Amber: "#FF7A18",
  positive: "#12C8B0",
  negative: "#FF3B4E",
} as const;

/* ─── Severity system ─── */
export type Severity = "low" | "medium" | "high" | "critical";

export function deriveSeverity(intensity: number): Severity {
  if (intensity > 0.75) return "critical";
  if (intensity > 0.50) return "high";
  if (intensity > 0.25) return "medium";
  return "low";
}

export function severityColor(severity: Severity): string {
  switch (severity) {
    case "critical": return COLORS.severityCritical;
    case "high":     return COLORS.severityHigh;
    case "medium":   return COLORS.severityMedium;
    case "low":      return COLORS.severityLow;
  }
}

/** Route opacity by display priority tier */
export const ROUTE_OPACITY = {
  primary: 0.65,    // top 5 active routes
  secondary: 0.40,  // next 10 routes
  background: 0.18, // all remaining
} as const;
