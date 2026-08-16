/**
 * TypeScript interfaces matching the backend API contracts.
 *
 * WebSocket envelope: IMPLEMENTATION.md §32
 * REST schemas: api/schemas.py
 * Domain enums: domain/enums.py
 */

/* ─── Enums ─── */

export type Layer = "L3" | "L7";
export type Unit = "bytes" | "requests";
export type DistributionRole = "origin" | "target";
export type CharacteristicCategory = "protocol" | "vector" | "http_method";
export type Normalization = "PERCENTAGE" | "MIN_MAX";
export type ConnectionState = "CONNECTED" | "RECONNECTING" | "OFFLINE";
export type Severity = "low" | "medium" | "high" | "critical";

/* ─── WebSocket messages (IMPLEMENTATION.md §32) ─── */

export interface SourceTarget {
  code: string;
  name: string | null;
  lat: number;
  lon: number;
}

export interface AttackEventData {
  event_id: string;
  layer: Layer;
  source: SourceTarget;
  target: SourceTarget;
  intensity: number;
  is_synthetic: boolean;
  data_source: "cloudflare_radar" | "synthetic";
  // Enriched fields (populated in demo mode or when available)
  attackType?: string;
  trafficGbps?: number;
  packetsPerSecond?: number;
}

export interface StatsData {
  active_events: number;
}

export interface SystemData {
  message: string;
}

export type WSMessage =
  | { type: "attack_event"; data: AttackEventData }
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

/* ─── Globe arc data (frontend-only) ─── */

export interface GlobeArc {
  id: string;
  startLat: number;
  startLng: number;
  endLat: number;
  endLng: number;
  color: string;
  stroke: number;
  dashGap: number;
  dashLength: number;
  layer: Layer;
  severity: Severity;
  isSynthetic: boolean;
  intensity: number;
  sourceCode: string;
  targetCode: string;
  attackType: string;
  trafficGbps: number;
  createdAt: number;
  expiresAt: number;
}

export interface GlobeRipple {
  id: string;
  lat: number;
  lng: number;
  color: string;
  maxRadius: number;
  propagationSpeed: number;
  repeatPeriod: number;
  isSynthetic: boolean;
  createdAt: number;
}

/* ─── Demo enrichment data ─── */

export interface DemoMetrics {
  totalTrafficGbps: number;
  targetsUnderAttack: number;
  countriesInvolved: number;
  blockedPct: number;
  lastMinTrafficTb: number;
  uptimeSeconds: number;
}
