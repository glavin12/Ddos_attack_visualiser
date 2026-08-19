"use client";

import { create } from "zustand";
import type {
  AttackRoute,
  CharacteristicValue,
  ConnectionState,
  CountryRank,
  GlobeIndicatorPoint,
  HistoryPoint,
  Layer,
  OverviewResponse,
  StatusResponse,
  ThreatIndicatorData,
} from "@/lib/types";
import { MAX_INDICATOR_POINTS } from "@/lib/constants";

/* ─── Store shape ─── */
interface RadarStore {
  /* Connection */
  connectionState: ConnectionState;
  reconnectAttempts: number;
  lastConnectedAt: number | null;

  /* Threat indicators — real IOCs streamed over WebSocket (or demo-mode
   * synthetic ones, marked via GlobeIndicatorPoint.isSynthetic) */
  indicators: GlobeIndicatorPoint[];
  activeIndicatorCount: number;
  totalIndicatorsSeen: number;
  /** Client-clock ms of the most recent indicator arrival — drives the ambient-sonar idle check. */
  lastIndicatorAtMs: number | null;

  /* Radar 24h aggregate top routes — REST-driven, refreshed periodically.
   * topRoutesSynthetic marks the whole batch as demo-mode data (per
   * CLAUDE.md §3: real vs synthetic must stay visually separable). */
  topRoutes: AttackRoute[];
  topRoutesSynthetic: boolean;
  routesUpdatedAtMs: number | null;

  /* Overview / REST data */
  overview: OverviewResponse | null;
  topOrigins: CountryRank[];
  topTargets: CountryRank[];
  protocols: CharacteristicValue[];
  vectors: CharacteristicValue[];
  httpMethods: CharacteristicValue[];
  history: HistoryPoint[];
  status: StatusResponse | null;
  selectedLayer: Layer;

  /* Load status */
  loadState: "loading" | "loaded" | "error";
  reloadToken: number;

  /* Analytics drawer */
  analyticsOpen: boolean;

  /* Actions */
  setConnectionState: (state: ConnectionState) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;
  addIndicator: (data: ThreatIndicatorData, opts?: { synthetic?: boolean }) => void;
  setActiveIndicatorCount: (count: number) => void;
  setTopRoutes: (routes: AttackRoute[], opts?: { synthetic?: boolean }) => void;
  setOverview: (data: OverviewResponse) => void;
  setTopOrigins: (origins: CountryRank[]) => void;
  setTopTargets: (targets: CountryRank[]) => void;
  setProtocols: (values: CharacteristicValue[]) => void;
  setVectors: (values: CharacteristicValue[]) => void;
  setHttpMethods: (values: CharacteristicValue[]) => void;
  setHistory: (points: HistoryPoint[]) => void;
  setStatus: (status: StatusResponse | null) => void;
  setSelectedLayer: (layer: Layer) => void;
  setLoadState: (state: "loading" | "loaded" | "error") => void;
  setAnalyticsOpen: (open: boolean) => void;
  requestReload: () => void;
}

export const useRadarStore = create<RadarStore>((set) => ({
  connectionState: "OFFLINE",
  reconnectAttempts: 0,
  lastConnectedAt: null,

  indicators: [],
  activeIndicatorCount: 0,
  totalIndicatorsSeen: 0,
  lastIndicatorAtMs: null,

  topRoutes: [],
  topRoutesSynthetic: false,
  routesUpdatedAtMs: null,

  overview: null,
  topOrigins: [],
  topTargets: [],
  protocols: [],
  vectors: [],
  httpMethods: [],
  history: [],
  status: null,
  selectedLayer: "L3",
  loadState: "loading",
  reloadToken: 0,
  analyticsOpen: false,

  setConnectionState: (state) =>
    set({
      connectionState: state,
      ...(state === "CONNECTED" ? { lastConnectedAt: Date.now() } : {}),
    }),

  incrementReconnectAttempts: () =>
    set((s) => ({ reconnectAttempts: s.reconnectAttempts + 1 })),

  resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),

  addIndicator: (data, opts) =>
    set((s) => {
      // Never fabricate a globe position — an indicator without GeoIP
      // resolution simply isn't placed. See CLAUDE.md transparency rules.
      if (data.lat == null || data.lng == null) return {};

      const now = Date.now();
      const id = `${data.source_feed}:${data.indicator}`;
      const existingIdx = s.indicators.findIndex((p) => p.id === id);

      const point: GlobeIndicatorPoint = {
        id,
        indicator: data.indicator,
        indicatorType: data.indicator_type,
        sourceFeed: data.source_feed,
        resolvedIp: data.resolved_ip,
        countryCode: data.country_code,
        countryName: data.country_name,
        city: data.city,
        lat: data.lat,
        lng: data.lng,
        threatFamily: data.threat_family,
        firstSeen: data.first_seen,
        lastSeen: data.last_seen,
        greynoiseClassification: data.greynoise_classification,
        greynoiseTags: data.greynoise_tags,
        sourceUrl: data.source_url,
        // Re-observations keep their original birth timestamp so the
        // choreographed entrance animation never replays for known IOCs.
        bornAtMs: existingIdx >= 0 ? s.indicators[existingIdx].bornAtMs : now,
        lastRefreshedMs: now,
        isSynthetic: opts?.synthetic ?? false,
      };

      // Re-observed indicators move to the front so array position always
      // reflects recency — the feed and continuous-pulse layer both render
      // only the first N entries.
      let indicators: GlobeIndicatorPoint[];
      if (existingIdx >= 0) {
        const rest = s.indicators.filter((_, i) => i !== existingIdx);
        indicators = [point, ...rest];
      } else {
        indicators = [point, ...s.indicators].slice(0, MAX_INDICATOR_POINTS);
      }

      return {
        indicators,
        totalIndicatorsSeen:
          existingIdx >= 0 ? s.totalIndicatorsSeen : s.totalIndicatorsSeen + 1,
        lastIndicatorAtMs: now,
      };
    }),

  setActiveIndicatorCount: (count) => set({ activeIndicatorCount: count }),

  setTopRoutes: (routes, opts) =>
    set({
      topRoutes: routes,
      topRoutesSynthetic: opts?.synthetic ?? false,
      routesUpdatedAtMs: Date.now(),
    }),

  setOverview: (data) =>
    set({
      overview: data,
      topOrigins: data.top_origins,
      topTargets: data.top_targets,
      // Fallback: overview carries the same top_routes Radar returned: if a
      // dedicated /radar/attacks call fails, don't discard equivalent data
      // that arrived here instead. Only real (non-demo) callers reach this
      // action, so topRoutesSynthetic is never set true here.
      ...(data.top_routes.length > 0
        ? {
            topRoutes: data.top_routes,
            topRoutesSynthetic: false,
            routesUpdatedAtMs: Date.now(),
          }
        : {}),
    }),

  setTopOrigins: (origins) => set({ topOrigins: origins }),
  setTopTargets: (targets) => set({ topTargets: targets }),
  setProtocols: (values) => set({ protocols: values }),
  setVectors: (values) => set({ vectors: values }),
  setHttpMethods: (values) => set({ httpMethods: values }),
  setHistory: (points) => set({ history: points }),
  setStatus: (status) => set({ status }),
  setSelectedLayer: (layer) => set({ selectedLayer: layer }),
  setLoadState: (loadState) => set({ loadState }),
  setAnalyticsOpen: (open) => set({ analyticsOpen: open }),
  requestReload: () =>
    set((s) => ({ reloadToken: s.reloadToken + 1, loadState: "loading" })),
}));
