"use client";

import { create } from "zustand";
import type {
  AttackEventData,
  CharacteristicValue,
  ConnectionState,
  CountryRank,
  AttackRoute,
  GlobeArc,
  GlobeRipple,
  HistoryPoint,
  Layer,
  OverviewResponse,
  StatusResponse,
  DemoMetrics,
} from "@/lib/types";
import {
  MAX_LIVE_EVENTS,
  MAX_ACTIVE_ARCS,
  ARC_EXPIRE_MS,
  deriveSeverity,
  severityColor,
} from "@/lib/constants";

const ATTACK_TYPES = ["UDP FLOOD", "SYN FLOOD", "HTTP FLOOD", "ICMP FLOOD", "DNS AMP", "NTP AMP", "SSDP FLOOD"];

function randomAttackType(): string {
  const weights = [0.35, 0.28, 0.18, 0.08, 0.05, 0.04, 0.02];
  let r = Math.random();
  for (let i = 0; i < weights.length; i++) {
    r -= weights[i];
    if (r <= 0) return ATTACK_TYPES[i];
  }
  return ATTACK_TYPES[0];
}

/* ─── Derived arc from attack event ─── */
function eventToArc(event: AttackEventData): GlobeArc {
  const now = Date.now();
  const intensity = Math.max(0.05, event.intensity);
  const severity = deriveSeverity(intensity);
  const color = severityColor(severity);

  return {
    id: event.event_id,
    startLat: event.source.lat,
    startLng: event.source.lon,
    endLat: event.target.lat,
    endLng: event.target.lon,
    // Thin arcs: 1–3px, never exceed 3px
    stroke: Math.min(3, Math.max(1, 1 + intensity * 2)),
    color,
    severity,
    dashGap: 0.15,
    dashLength: 0.5,
    layer: event.layer,
    isSynthetic: event.is_synthetic,
    intensity,
    sourceCode: event.source.code,
    targetCode: event.target.code,
    attackType: event.attackType ?? randomAttackType(),
    trafficGbps: event.trafficGbps ?? parseFloat((0.1 + intensity * 8).toFixed(2)),
    createdAt: now,
    expiresAt: now + ARC_EXPIRE_MS,
  };
}

function eventToRipple(event: AttackEventData): GlobeRipple {
  const intensity = Math.max(0.3, event.intensity);
  const severity = deriveSeverity(intensity);
  const color = severityColor(severity);

  return {
    id: event.event_id + "-ripple",
    lat: event.target.lat,
    lng: event.target.lon,
    color,
    maxRadius: Math.max(2, intensity * 5.5),
    propagationSpeed: 2.5,
    repeatPeriod: 750,
    isSynthetic: event.is_synthetic,
    createdAt: Date.now(),
  };
}

/* ─── Store shape ─── */
interface RadarStore {
  /* Connection */
  connectionState: ConnectionState;
  reconnectAttempts: number;
  lastConnectedAt: number | null;

  /* Events */
  events: (AttackEventData & { receivedAt: number })[];
  arcs: GlobeArc[];
  ripples: GlobeRipple[];
  activeEventCount: number;
  totalEvents: number;

  /* Overview / REST data */
  overview: OverviewResponse | null;
  topRoutes: AttackRoute[];
  topOrigins: CountryRank[];
  topTargets: CountryRank[];
  protocols: CharacteristicValue[];
  vectors: CharacteristicValue[];
  httpMethods: CharacteristicValue[];
  history: HistoryPoint[];
  status: StatusResponse | null;
  selectedLayer: Layer;

  /* Demo metrics */
  demoMetrics: DemoMetrics | null;

  /* Load status */
  loadState: "loading" | "loaded" | "error";
  reloadToken: number;

  /* Actions */
  setConnectionState: (state: ConnectionState) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;
  addEvent: (event: AttackEventData) => void;
  setActiveEventCount: (count: number) => void;
  pruneExpiredArcs: () => void;
  setOverview: (data: OverviewResponse) => void;
  setTopRoutes: (routes: AttackRoute[]) => void;
  setTopOrigins: (origins: CountryRank[]) => void;
  setTopTargets: (targets: CountryRank[]) => void;
  setProtocols: (values: CharacteristicValue[]) => void;
  setVectors: (values: CharacteristicValue[]) => void;
  setHttpMethods: (values: CharacteristicValue[]) => void;
  setHistory: (points: HistoryPoint[]) => void;
  setStatus: (status: StatusResponse | null) => void;
  setSelectedLayer: (layer: Layer) => void;
  setDemoMetrics: (metrics: DemoMetrics) => void;
  setLoadState: (state: "loading" | "loaded" | "error") => void;
  requestReload: () => void;
}

export const useRadarStore = create<RadarStore>((set) => ({
  connectionState: "OFFLINE",
  reconnectAttempts: 0,
  lastConnectedAt: null,

  events: [],
  arcs: [],
  ripples: [],
  activeEventCount: 0,
  totalEvents: 0,

  overview: null,
  topRoutes: [],
  topOrigins: [],
  topTargets: [],
  protocols: [],
  vectors: [],
  httpMethods: [],
  history: [],
  status: null,
  selectedLayer: "L3",
  demoMetrics: null,
  loadState: "loading",
  reloadToken: 0,

  setConnectionState: (state) =>
    set({
      connectionState: state,
      ...(state === "CONNECTED" ? { lastConnectedAt: Date.now() } : {}),
    }),

  incrementReconnectAttempts: () =>
    set((s) => ({ reconnectAttempts: s.reconnectAttempts + 1 })),

  resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),

  addEvent: (event) =>
    set((s) => {
      const newArc = eventToArc(event);
      const newRipple = eventToRipple(event);
      const receivedAt = Date.now();

      return {
        events: [{ ...event, receivedAt }, ...s.events].slice(0, MAX_LIVE_EVENTS),
        arcs: [newArc, ...s.arcs].slice(0, MAX_ACTIVE_ARCS),
        ripples: [newRipple, ...s.ripples].slice(0, MAX_ACTIVE_ARCS),
        totalEvents: s.totalEvents + 1,
      };
    }),

  setActiveEventCount: (count) => set({ activeEventCount: count }),

  pruneExpiredArcs: () => {
    const now = Date.now();
    set((s) => ({
      arcs: s.arcs.filter((a) => a.expiresAt > now),
      ripples: s.ripples.filter((r) => now - r.createdAt < 2000),
    }));
  },

  setOverview: (data) =>
    set({
      overview: data,
      topRoutes: data.top_routes,
      topOrigins: data.top_origins,
      topTargets: data.top_targets,
    }),

  setTopRoutes: (routes) => set({ topRoutes: routes }),
  setTopOrigins: (origins) => set({ topOrigins: origins }),
  setTopTargets: (targets) => set({ topTargets: targets }),
  setProtocols: (values) => set({ protocols: values }),
  setVectors: (values) => set({ vectors: values }),
  setHttpMethods: (values) => set({ httpMethods: values }),
  setHistory: (points) => set({ history: points }),
  setStatus: (status) => set({ status }),
  setSelectedLayer: (layer) => set({ selectedLayer: layer }),
  setDemoMetrics: (metrics) => set({ demoMetrics: metrics }),
  setLoadState: (loadState) => set({ loadState }),
  requestReload: () =>
    set((s) => ({ reloadToken: s.reloadToken + 1, loadState: "loading" })),
}));
