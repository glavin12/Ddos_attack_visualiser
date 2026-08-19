/**
 * TypeScript interfaces matching the backend API contracts.
 *
 * WebSocket envelope: websocket/envelopes.py
 * REST schemas: api/schemas.py
 * Domain enums: domain/enums.py
 */

/* ─── Enums ─── */

export type Layer = "L3" | "L7";
export type Unit = "bytes" | "requests";
export type DistributionRole = "origin" | "target";
export type CharacteristicCategory = "protocol" | "vector" | "http_method";
export type Normalization = "PERCENTAGE" | "MIN0_MAX";
export type ConnectionState = "CONNECTED" | "RECONNECTING" | "OFFLINE";
export type SourceFeed = "urlhaus" | "feodo" | "threatfox";
export type IndicatorType = "url" | "ip" | "domain";

/* ─── WebSocket messages (websocket/envelopes.py) ─── */

export interface ThreatIndicatorData {
  indicator: string;
  indicator_type: IndicatorType;
  source_feed: SourceFeed;
  resolved_ip: string;
  country_code: string | null;
  country_name: string | null;
  city: string | null;
  lat: number | null;
  lng: number | null;
  threat_family: string | null;
  first_seen: string;
  last_seen: string;
  greynoise_classification: string | null;
  greynoise_tags: string | null;
  source_url: string | null;
}

export interface StatsData {
  active_indicators: number;
}

export interface SystemData {
  message: string;
}

export type WSMessage =
  | { type: "threat_indicator"; data: ThreatIndicatorData }
  | { type: "stats"; data: StatsData }
  | { type: "system"; data: SystemData };

/* ─── REST API responses (api/schemas.py) ─── */

export interface ObservationMeta {
  start: string | null;
  end: string | null;
  last_updated: string | null;
  collected_at: string | null;
}

export interface CountryRef {
  code: string;
  name: string | null;
}

export interface AttackRoute {
  source: CountryRef;
  target: CountryRef;
  share: number;
  rank: number | null;
}

export interface CountryRank {
  country: CountryRef;
  share: number;
  rank: number | null;
}

export interface CharacteristicValue {
  value: string;
  share: number;
}

export interface HistoryPoint {
  timestamp: string;
  value: number;
}

export interface OverviewResponse {
  observation: ObservationMeta;
  layer: Layer;
  top_routes: AttackRoute[];
  top_origins: CountryRank[];
  top_targets: CountryRank[];
}

export interface AttacksResponse {
  layer: Layer;
  unit: Unit;
  entries: AttackRoute[];
}

export interface CountriesResponse {
  layer: Layer;
  role: DistributionRole;
  unit: Unit;
  entries: CountryRank[];
}

export interface CharacteristicsResponse {
  layer: Layer;
  type: CharacteristicCategory;
  unit: Unit;
  entries: CharacteristicValue[];
}

export interface HistoryResponse {
  layer: Layer;
  unit: Unit;
  normalization: Normalization;
  aggregation: string;
  points: HistoryPoint[];
}

export interface StatusResponse {
  status: string;
  observation_start: string | null;
  observation_end: string | null;
  last_updated: string | null;
  collected_at: string | null;
}

export interface HealthResponse {
  status: string;
}

/* ─── Globe arc data (frontend-only) ───
 * Built from AttackRoute (REST, 24h aggregate). One arc per route; country
 * centroid to country centroid. Real routes' share/rank come straight from
 * Cloudflare Radar; demo-mode routes are clearly marked via isSynthetic.
 */

export interface GlobeArc {
  id: string;
  startLat: number;
  startLng: number;
  endLat: number;
  endLng: number;
  sourceCode: string;
  sourceName: string;
  targetCode: string;
  targetName: string;
  share: number;
  rank: number | null;
  layer: Layer;
  /** [0,1] normalized against the current top-route max share — brightness only, never shown as a raw number. */
  normalizedShare: number;
  /** Deterministic hash-derived altitude so the same route always arcs the same way. */
  altitude: number;
  /** Deterministic hash-derived [0,1) start-position fraction along the arc, so comets don't move in lockstep. */
  phaseOffset: number;
  /** Comet flight duration — faster for higher-ranked routes. */
  flightDurationMs: number;
  /** True only for demo-mode routes. Real Radar routes are always false. Per CLAUDE.md §3: real vs synthetic must stay visually separable (bright/thick = real; dim/thin = synthetic). */
  isSynthetic: boolean;
}

/* ─── Globe threat-indicator points (frontend-only) ───
 * One point per real IOC streamed over WebSocket. Birth lifecycle drives the
 * ripple/pulse/settle/breathe/age choreography — see Docs/Frontend-Motion-Spec.md.
 */

export type IndicatorLifecycleStage = "birth" | "settled" | "aging";

export interface GlobeIndicatorPoint {
  id: string;
  indicator: string;
  indicatorType: IndicatorType;
  sourceFeed: SourceFeed;
  resolvedIp: string;
  countryCode: string | null;
  countryName: string | null;
  city: string | null;
  lat: number;
  lng: number;
  threatFamily: string | null;
  firstSeen: string;
  lastSeen: string;
  greynoiseClassification: string | null;
  greynoiseTags: string | null;
  sourceUrl: string | null;
  /** ms timestamp (client clock) this point entered the store — drives birth choreography. */
  bornAtMs: number;
  /** ms timestamp of the most recent re-observation (dedupe update, not a new point). */
  lastRefreshedMs: number;
  /** True only for demo-mode indicators. Real WS indicators are always false. Per CLAUDE.md §3: real vs synthetic must stay visually separable (bright/thick = real; dim/thin = synthetic). */
  isSynthetic: boolean;
}
