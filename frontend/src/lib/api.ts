/**
 * REST API client for the FastAPI backend.
 * The frontend never calls Cloudflare directly (IMPLEMENTATION.md §50).
 */

import { API_BASE_URL } from "@/lib/constants";
import type {
  OverviewResponse,
  CountriesResponse,
  CharacteristicsResponse,
  HistoryResponse,
  StatusResponse,
  Layer,
  DistributionRole,
  CharacteristicCategory,
} from "@/lib/types";

const REQUEST_TIMEOUT_MS = 10000;

async function apiFetch<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(url.toString(), { signal: controller.signal });
    if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}

export async function fetchOverview(layer: Layer): Promise<OverviewResponse> {
  return apiFetch<OverviewResponse>("/radar/overview", { layer });
}

export async function fetchCountries(
  layer: Layer,
  role: DistributionRole,
  limit = 50
): Promise<CountriesResponse> {
  return apiFetch<CountriesResponse>("/radar/countries", {
    layer,
    role,
    limit: String(limit),
  });
}

export async function fetchCharacteristics(
  layer: Layer,
  type: CharacteristicCategory,
  limit = 50
): Promise<CharacteristicsResponse> {
  return apiFetch<CharacteristicsResponse>("/radar/characteristics", {
    layer,
    type,
    limit: String(limit),
  });
}

export async function fetchHistory(layer: Layer, limit = 200): Promise<HistoryResponse> {
  return apiFetch<HistoryResponse>("/radar/history", { layer, limit: String(limit) });
}

export async function fetchStatus(): Promise<StatusResponse> {
  return apiFetch<StatusResponse>("/radar/status");
}
