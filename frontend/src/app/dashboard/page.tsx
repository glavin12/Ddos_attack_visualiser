"use client";

import { useCallback, useEffect, useRef } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useRadarStore } from "@/store/useRadarStore";
import {
  fetchOverview,
  fetchAttacks,
  fetchCountries,
  fetchCharacteristics,
  fetchHistory,
  fetchStatus,
} from "@/lib/api";
import { ROUTES_REFRESH_MS, STATUS_POLL_MS } from "@/lib/constants";
import Globe from "@/components/Globe";
import Topbar from "@/components/Topbar";
import AttackIntensity from "@/components/AttackIntensity";
import ThreatFeed from "@/components/ThreatFeed";
import TopCountries from "@/components/TopCountries";
import Legend from "@/components/Legend";
import MetricsBar from "@/components/MetricsBar";
import AnalyticsDrawer from "@/components/AnalyticsDrawer";
import MobileSheet from "@/components/MobileSheet";
import type { Layer } from "@/lib/types";

export default function DashboardPage() {
  useWebSocket();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const selectedLayer = useRadarStore((s) => s.selectedLayer);
  const setSelectedLayer = useRadarStore((s) => s.setSelectedLayer);
  const setOverview = useRadarStore((s) => s.setOverview);
  const setTopRoutes = useRadarStore((s) => s.setTopRoutes);
  const setTopOrigins = useRadarStore((s) => s.setTopOrigins);
  const setTopTargets = useRadarStore((s) => s.setTopTargets);
  const setProtocols = useRadarStore((s) => s.setProtocols);
  const setVectors = useRadarStore((s) => s.setVectors);
  const setHttpMethods = useRadarStore((s) => s.setHttpMethods);
  const setHistory = useRadarStore((s) => s.setHistory);
  const setStatus = useRadarStore((s) => s.setStatus);
  const setLoadState = useRadarStore((s) => s.setLoadState);
  const reloadToken = useRadarStore((s) => s.reloadToken);

  // Guards against out-of-order responses when the user toggles L3/L7
  // rapidly: each loadLayerData call claims a request id, and every
  // resolved fetch checks it's still the latest before applying its result.
  const requestIdRef = useRef(0);

  // Sync layer from URL on mount
  useEffect(() => {
    const urlLayer = searchParams.get("layer") as Layer | null;
    if (urlLayer && urlLayer !== selectedLayer) setSelectedLayer(urlLayer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Mirror layer selection to URL
  useEffect(() => {
    const params = new URLSearchParams(searchParams.toString());
    if (params.get("layer") !== selectedLayer) {
      params.set("layer", selectedLayer);
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedLayer]);

  const loadLayerData = useCallback(
    (layer: Layer) => {
      const requestId = ++requestIdRef.current;
      const isStale = () => requestIdRef.current !== requestId;

      setLoadState("loading");
      let failed = false;
      const markError = () => { if (isStale()) return; failed = true; setLoadState("error"); };
      const markDone  = () => { if (isStale() || failed) return; setLoadState("loaded"); };

      fetchOverview(layer).then((r) => { if (!isStale()) setOverview(r); }).catch(markError);
      fetchAttacks(layer).then((r) => { if (!isStale()) setTopRoutes(r.entries); }).catch(markError);
      fetchCountries(layer, "origin").then((r) => { if (!isStale()) setTopOrigins(r.entries); }).catch(markError);
      fetchCountries(layer, "target").then((r) => { if (!isStale()) setTopTargets(r.entries); }).catch(markError);
      fetchCharacteristics(layer, "protocol").then((r) => { if (!isStale()) setProtocols(r.entries); }).catch(markError);
      fetchCharacteristics(layer, "vector").then((r) => { if (!isStale()) setVectors(r.entries); }).catch(markError);
      if (layer === "L7") {
        fetchCharacteristics(layer, "http_method").then((r) => { if (!isStale()) setHttpMethods(r.entries); }).catch(markError);
      } else if (!isStale()) {
        setHttpMethods([]);
      }
      fetchHistory(layer).then((r) => { if (!isStale()) setHistory(r.points); }).catch(markError).finally(markDone);
    },
    [setOverview, setTopRoutes, setTopOrigins, setTopTargets, setProtocols, setVectors, setHttpMethods, setHistory, setLoadState]
  );

  useEffect(() => { loadLayerData(selectedLayer); }, [selectedLayer, loadLayerData, reloadToken]);

  // Routes refresh — Radar's 24h window shifts continuously; re-poll well
  // inside the backend's 6h ingest cadence so arcs stay reasonably current.
  // Guarded the same way as loadLayerData: skip applying the result if the
  // user has since switched layers.
  useEffect(() => {
    const id = setInterval(() => {
      const layerAtFetch = selectedLayer;
      fetchAttacks(layerAtFetch)
        .then((r) => {
          if (useRadarStore.getState().selectedLayer === layerAtFetch) setTopRoutes(r.entries);
        })
        .catch(() => {});
    }, ROUTES_REFRESH_MS);
    return () => clearInterval(id);
  }, [selectedLayer, setTopRoutes]);

  // Status poll
  useEffect(() => {
    fetchStatus().then(setStatus).catch(() => {});
    const id = setInterval(() => fetchStatus().then(setStatus).catch(() => {}), STATUS_POLL_MS);
    return () => clearInterval(id);
  }, [setStatus]);

  return (
    <div
      className="relative w-screen h-screen overflow-hidden bg-[var(--color-void)] select-none"
      style={{ minHeight: "100dvh" }}
    >
      {/* ── Topbar: brand, live status, L3/L7 toggle, analytics control ── */}
      <Topbar />

      {/* ── Background 3D Globe Canvas (Full Viewport) ── */}
      <div className="absolute inset-0 z-0 w-full h-full">
        <Globe />
      </div>

      {/* ── Top-Left Floating HUD Card: TOP ROUTES (24h) — desktop only ── */}
      <div className="absolute top-[64px] left-6 z-20 pointer-events-auto hidden md:block">
        <AttackIntensity />
      </div>

      {/* ── Bottom-Left Floating HUD Card: LIVE THREAT FEED ── */}
      <div className="absolute bottom-24 left-6 z-20 pointer-events-auto hidden md:block">
        <ThreatFeed />
      </div>

      {/* ── Top-Right Floating HUD Card: TOP ORIGIN COUNTRIES — desktop only ── */}
      <div className="absolute top-[64px] right-6 z-20 pointer-events-auto hidden md:block">
        <TopCountries />
      </div>

      {/* ── Bottom-Right Floating HUD Card: LEGEND ── */}
      <div className="absolute bottom-24 right-6 z-20 pointer-events-auto hidden md:block">
        <Legend />
      </div>

      {/* ── Bottom Floating HUD Bar: METRICS TELEMETRY — desktop only ── */}
      <div className="absolute bottom-5 left-1/2 -translate-x-1/2 z-20 pointer-events-auto px-4 w-full hidden md:flex justify-center">
        <MetricsBar />
      </div>

      {/* ── Mobile-only slide-up data sheet (globe stays the hero) ── */}
      <MobileSheet />

      {/* ── Analytics side drawer ── */}
      <AnalyticsDrawer />
    </div>
  );
}
