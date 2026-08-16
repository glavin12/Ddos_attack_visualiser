"use client";

import { useCallback, useEffect } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useDemoData } from "@/hooks/useDemoData";
import { useRadarStore } from "@/store/useRadarStore";
import {
  fetchOverview,
  fetchCountries,
  fetchCharacteristics,
  fetchHistory,
  fetchStatus,
} from "@/lib/api";
import Globe from "@/components/Globe";
import Topbar from "@/components/Topbar";
import AttackIntensity from "@/components/AttackIntensity";
import LiveAttacks from "@/components/LiveAttacks";
import TopCountries from "@/components/TopCountries";
import Legend from "@/components/Legend";
import MetricsBar from "@/components/MetricsBar";
import AnalyticsDrawer from "@/components/AnalyticsDrawer";
import type { Layer } from "@/lib/types";

export default function DashboardPage() {
  useWebSocket();
  useDemoData();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const selectedLayer = useRadarStore((s) => s.selectedLayer);
  const setSelectedLayer = useRadarStore((s) => s.setSelectedLayer);
  const setOverview = useRadarStore((s) => s.setOverview);
  const setTopOrigins = useRadarStore((s) => s.setTopOrigins);
  const setTopTargets = useRadarStore((s) => s.setTopTargets);
  const setProtocols = useRadarStore((s) => s.setProtocols);
  const setVectors = useRadarStore((s) => s.setVectors);
  const setHttpMethods = useRadarStore((s) => s.setHttpMethods);
  const setHistory = useRadarStore((s) => s.setHistory);
  const setStatus = useRadarStore((s) => s.setStatus);
  const setLoadState = useRadarStore((s) => s.setLoadState);
  const reloadToken = useRadarStore((s) => s.reloadToken);

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
      setLoadState("loading");
      let failed = false;
      const markError = () => { failed = true; setLoadState("error"); };
      const markDone  = () => { if (!failed) setLoadState("loaded"); };

      fetchOverview(layer).then(setOverview).catch(markError);
      fetchCountries(layer, "origin").then((r) => setTopOrigins(r.entries)).catch(markError);
      fetchCountries(layer, "target").then((r) => setTopTargets(r.entries)).catch(markError);
      fetchCharacteristics(layer, "protocol").then((r) => setProtocols(r.entries)).catch(markError);
      fetchCharacteristics(layer, "vector").then((r) => setVectors(r.entries)).catch(markError);
      if (layer === "L7") {
        fetchCharacteristics(layer, "http_method").then((r) => setHttpMethods(r.entries)).catch(markError);
      } else {
        setHttpMethods([]);
      }
      fetchHistory(layer).then((r) => setHistory(r.points)).catch(markError).finally(markDone);
    },
    [setOverview, setTopOrigins, setTopTargets, setProtocols, setVectors, setHttpMethods, setHistory, setLoadState]
  );

  useEffect(() => { loadLayerData(selectedLayer); }, [selectedLayer, loadLayerData, reloadToken]);

  // Status poll — 30s
  useEffect(() => {
    fetchStatus().then(setStatus).catch(() => {});
    const id = setInterval(() => fetchStatus().then(setStatus).catch(() => {}), 30000);
    return () => clearInterval(id);
  }, [setStatus]);

  return (
    <div
      className="relative w-screen h-screen overflow-hidden bg-[#03070B] select-none"
      style={{ minHeight: "100dvh" }}
    >
      {/* ── Topbar: brand, live status, L3/L7 toggle, analytics control ── */}
      <Topbar />

      {/* ── Background 3D Globe Canvas (Full Viewport) ── */}
      <div className="absolute inset-0 z-0 w-full h-full">
        <Globe />
      </div>

      {/* ── Top-Left Floating HUD Card: ATTACK INTENSITY ── */}
      <div className="absolute top-[64px] left-6 z-20 pointer-events-auto">
        <AttackIntensity />
      </div>

      {/* ── Bottom-Left Floating HUD Card: LIVE ATTACKS ── */}
      <div className="absolute bottom-24 left-6 z-20 pointer-events-auto hidden md:block">
        <LiveAttacks />
      </div>

      {/* ── Top-Right Floating HUD Card: TOP ATTACKING COUNTRIES ── */}
      <div className="absolute top-[64px] right-6 z-20 pointer-events-auto">
        <TopCountries />
      </div>

      {/* ── Bottom-Right Floating HUD Card: LEGEND ── */}
      <div className="absolute bottom-24 right-6 z-20 pointer-events-auto hidden md:block">
        <Legend />
      </div>

      {/* ── Bottom Floating HUD Bar: METRICS TELEMETRY ── */}
      <div className="absolute bottom-5 left-1/2 -translate-x-1/2 z-20 pointer-events-auto px-4 w-full flex justify-center">
        <MetricsBar />
      </div>

      {/* ── Analytics side drawer ── */}
      <AnalyticsDrawer />
    </div>
  );
}
