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
  RadarPulseData,
  StatusResponse,
  ThreatIndicatorData,
} from "@/lib/types";
import { MAX_INDICATOR_POINTS } from "@/lib/constants";

/** Per-layer route store — both layers are kept so the backend's radar_pulse
 * (which always carries L3+L7) serves an instant layer toggle. */
export interface RoutesByLayer {
  L3: AttackRoute[];
  L7: AttackRoute[];
}

/* ─── Store shape ─── */
interface RadarStore {
  /* Connection */
  connectionState: ConnectionState;
  reconnectAttempts: number;
  lastConnectedAt: number | null;

  /* Threat indicators — real IOCs streamed over WebSocket */
  indicators: GlobeIndicatorPoint[];
  activeIndicatorCount: number;
  totalIndicatorsSeen: number;
  /** Client-clock ms of the most recent indicator arrival — drives the ambient-sonar idle check. */
  lastIndicatorAtMs: number | null;

  /* Radar 24h aggregate top routes — REST bootstrap + backend-driven
   * radar_pulse WS push. topRoutes is the selected layer's view of
   * routesByLayer (kept in sync by the actions below). */
  topRoutes: AttackRoute[];
  routesByLayer: RoutesByLayer;
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
  addIndicator: (data: ThreatIndicatorData) => void;
  setActiveIndicatorCount: (count: number) => void;
  setTopRoutes: (routes: AttackRoute[]) => void;
  setRadarPulse: (data: RadarPulseData) => void;
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
  routesByLayer: { L3: [], L7: [] },
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
    set((s) => ({
      connectionState: state,
      ...(state === "CONNECTED" ? { lastConnectedAt: Date.now() } : {}),
      // Leaving a live connection makes every arc/dot on the globe
      // unverifiable — clear them instead of freezing stale data on screen
      // while ConnectionStatus says otherwise. CLAUDE.md: "offline = empty
      // globe + honest ConnectionStatus", never a fabricated/frozen fallback.
      ...(s.connectionState === "CONNECTED" && state !== "CONNECTED"
        ? {
            topRoutes: [],
            routesByLayer: { L3: [], L7: [] } as RoutesByLayer,
            routesUpdatedAtMs: null,
            indicators: [],
            activeIndicatorCount: 0,
          }
        : {}),
    })),

  incrementReconnectAttempts: () =>
    set((s) => ({ reconnectAttempts: s.reconnectAttempts + 1 })),

  resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),

  addIndicator: (data) =>
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

  setTopRoutes: (routes) =>
    set((s) => ({
      topRoutes: routes,
      routesByLayer: { ...s.routesByLayer, [s.selectedLayer]: routes },
      routesUpdatedAtMs: Date.now(),
    })),

  setRadarPulse: (data) =>
    set((s) => {
      const routesByLayer: RoutesByLayer = {
        L3: data.l3?.routes ?? [],
        L7: data.l7?.routes ?? [],
      };
      // An absent layer (null) means the backend has no observation for it
      // yet — keep whatever the last real data for that layer was instead
      // of wiping arcs the moment a pulse omits it.
      if (data.l3 == null) routesByLayer.L3 = s.routesByLayer.L3;
      if (data.l7 == null) routesByLayer.L7 = s.routesByLayer.L7;
      return {
        routesByLayer,
        topRoutes: routesByLayer[s.selectedLayer],
        routesUpdatedAtMs: Date.now(),
      };
    }),

  setOverview: (data) =>
    set((s) => ({
      overview: data,
      topOrigins: data.top_origins,
      topTargets: data.top_targets,
      // Fallback: overview carries the same top_routes Radar returned: if a
      // dedicated /radar/attacks call fails, don't discard equivalent data
      // that arrived here instead.
      ...(data.top_routes.length > 0
        ? {
            topRoutes: data.top_routes,
            routesByLayer: {
              ...s.routesByLayer,
              [data.layer]: data.top_routes,
            },
            routesUpdatedAtMs: Date.now(),
          }
        : {}),
    })),

  setTopOrigins: (origins) => set({ topOrigins: origins }),
  setTopTargets: (targets) => set({ topTargets: targets }),
  setProtocols: (values) => set({ protocols: values }),
  setVectors: (values) => set({ vectors: values }),
  setHttpMethods: (values) => set({ httpMethods: values }),
  setHistory: (points) => set({ history: points }),
  setStatus: (status) => set({ status }),
  setSelectedLayer: (layer) =>
    set((s) => ({
      selectedLayer: layer,
      // Instant switch from the last pulse/REST data for that layer; the
      // REST reload for the new layer overwrites it when it lands.
      topRoutes: s.routesByLayer[layer],
    })),
  setLoadState: (loadState) => set({ loadState }),
  setAnalyticsOpen: (open) => set({ analyticsOpen: open }),
  requestReload: () =>
    set((s) => ({ reloadToken: s.reloadToken + 1, loadState: "loading" })),
}));
