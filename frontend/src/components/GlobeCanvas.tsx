"use client";

import { useEffect, useRef, useState } from "react";
import { useRadarStore } from "@/store/useRadarStore";
import {
  GLOBE_AUTO_ROTATE_DEG_PER_SEC,
  GLOBE_IDLE_RESUME_MS,
  severityColor,
} from "@/lib/constants";
import * as THREE from "three";

/* eslint-disable @typescript-eslint/no-explicit-any */

/** Hex color to rgba string helper */
function hexToRgba(hex: string, alpha: number): string {
  const cleanHex = hex.replace("#", "");
  const r = parseInt(cleanHex.slice(0, 2), 16);
  const g = parseInt(cleanHex.slice(2, 4), 16);
  const b = parseInt(cleanHex.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

/** Deterministic [0,1) hash of a string */
function hash01(input: string, salt = 0): number {
  let h = 2166136261 ^ salt;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 10000) / 10000;
}

/** Mix a hex color toward white (0 = none, 1 = full white) */
function tintWhite(hex: string, amount: number): string {
  const color = new THREE.Color(hex);
  color.lerp(new THREE.Color("#FFFFFF"), amount);
  return `#${color.getHexString()}`;
}

/**
 * Globe Canvas — Kaspersky-style navy threat globe:
 * - Solid deep-navy sphere with outline-only country borders (Natural Earth
 *   50m boundaries, no city lights, no graticules, no land fill).
 * - Dim steel-blue atmosphere rim.
 * - Attack arcs as beams of light: a faint full trail plus a bright comet
 *   pulse that travels source→target and fades out on arrival, colored by
 *   severity (red/orange/amber/teal).
 * - Source nodes: pulsing severity-colored rings with glowing core.
 * - Target nodes: hollow cyan rings.
 * - Droplet-wave radar ripples emanating from both source and target points.
 */
export default function GlobeCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<any>(null);
  const arcEntriesRef = useRef<Map<string, any[]>>(new Map());
  const markerMapRef = useRef<Map<string, any>>(new Map());
  const countriesRef = useRef<any[]>([]);
  const idleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isDraggingRef = useRef(false);
  const reducedMotion = useRef(false);
  const [globeReady, setGlobeReady] = useState(false);
  const [countries, setCountries] = useState<any[]>([]);

  const arcs = useRadarStore((s) => s.arcs);
  const ripples = useRadarStore((s) => s.ripples);
  const pruneExpiredArcs = useRadarStore((s) => s.pruneExpiredArcs);

  // Reduced motion preference
  useEffect(() => {
    if (typeof window !== "undefined") {
      reducedMotion.current = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches;
    }
  }, []);

  // Fetch GeoJSON country borders (50m accurate boundaries, fallback chain)
  useEffect(() => {
    const URLS = [
      "/globe/countries-50m.geojson",
      "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson",
      "/globe/countries-110m.geojson",
    ];

    const load = async (url: string): Promise<any> => {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    };

    (async () => {
      for (const url of URLS) {
        try {
          const data = await load(url);
          if (data?.features) {
            countriesRef.current = data.features;
            setCountries(data.features);
            return;
          }
        } catch {
          /* try next source */
        }
      }
    })();
  }, []);

  // Periodic arc expiration
  useEffect(() => {
    const interval = setInterval(pruneExpiredArcs, 1000);
    return () => clearInterval(interval);
  }, [pruneExpiredArcs]);

  // Initialize Globe
  useEffect(() => {
    if (!containerRef.current) return;
    let mounted = true;

    const initGlobe = async () => {
      const GlobeModule = await import("globe.gl");
      const Globe = GlobeModule.default;
      if (!mounted || !containerRef.current) return;

      const globe = new Globe(containerRef.current)
        .backgroundColor("rgba(0,0,0,0)")
        // ── 1. Solid navy sphere (no NASA night-lights texture) ──
        .showAtmosphere(true)
        .atmosphereColor("#4A7A9C")
        .atmosphereAltitude(0.12)
        .showGraticules(false)
        // ── 2. Outline-only country borders on the navy sphere ──
        .polygonsData([])
        .polygonCapColor(() => "rgba(0, 0, 0, 0)")
        .polygonSideColor(() => "rgba(0, 0, 0, 0)")
        .polygonStrokeColor(() => "rgba(150, 200, 240, 0.55)")
        .polygonAltitude(0.004)
        // ── 3. Beam arcs: faint trail + traveling comet pulse ──
        .arcsData([])
        .arcColor("color")
        .arcStroke(null) // Native thin line rendering — never tubes (ribbons)
        .arcDashLength("dashLength")
        .arcDashGap("dashGap")
        .arcDashInitialGap("initialGap")
        .arcDashAnimateTime("animateTime")
        .arcAltitude("alt")
        .arcsTransitionDuration(0)
        // ── 4. Radar-Ping concentric rings (droplet waves) ──
        .ringsData([])
        .ringColor("color")
        .ringMaxRadius("maxRadius")
        .ringPropagationSpeed("propagationSpeed")
        .ringRepeatPeriod("repeatPeriod")
        .ringAltitude(0.02)
        // ── 5. Custom Layer: Concentric Source & Target Markers ──
        .customLayerData([])
        .customThreeObject((d: any) => {
          const group = new THREE.Group();

          if (d.type === "source") {
            // Source: Solid glowing center dot + outer glowing rings
            const coreGeo = new THREE.CircleGeometry(0.7, 24);
            const coreMat = new THREE.MeshBasicMaterial({
              color: new THREE.Color(d.color || "#FF3B4E"),
              side: THREE.DoubleSide,
              transparent: true,
              opacity: 0.98,
            });
            group.add(new THREE.Mesh(coreGeo, coreMat));

            // Outer ring 1
            const ring1Geo = new THREE.RingGeometry(1.0, 1.25, 24);
            const ring1Mat = new THREE.MeshBasicMaterial({
              color: new THREE.Color(d.color || "#FF3B4E"),
              side: THREE.DoubleSide,
              transparent: true,
              opacity: 0.75,
            });
            group.add(new THREE.Mesh(ring1Geo, ring1Mat));

            // Outer ring 2
            const ring2Geo = new THREE.RingGeometry(1.55, 1.8, 24);
            const ring2Mat = new THREE.MeshBasicMaterial({
              color: new THREE.Color(d.color || "#FF3B4E"),
              side: THREE.DoubleSide,
              transparent: true,
              opacity: 0.45,
            });
            group.add(new THREE.Mesh(ring2Geo, ring2Mat));
          } else {
            // Target: Hollow cyan circle + outer cyan halo ring
            const ring1Geo = new THREE.RingGeometry(0.45, 0.9, 24);
            const ring1Mat = new THREE.MeshBasicMaterial({
              color: new THREE.Color("#00D9FF"),
              side: THREE.DoubleSide,
              transparent: true,
              opacity: 0.98,
            });
            group.add(new THREE.Mesh(ring1Geo, ring1Mat));

            // Outer cyan ring
            const ring2Geo = new THREE.RingGeometry(1.25, 1.6, 24);
            const ring2Mat = new THREE.MeshBasicMaterial({
              color: new THREE.Color("#00D9FF"),
              side: THREE.DoubleSide,
              transparent: true,
              opacity: 0.55,
            });
            group.add(new THREE.Mesh(ring2Geo, ring2Mat));
          }

          return group;
        });

      globeRef.current = globe;

      // Polygons may have loaded before the globe finished initializing —
      // apply them immediately if so (the [countries] effect handles the
      // reverse order).
      if (countriesRef.current.length > 0) {
        globe.polygonsData(countriesRef.current);
      }

      // Deep navy sphere material (ocean)
      const globeMaterial = globe.globeMaterial() as THREE.MeshPhongMaterial;
      if (globeMaterial) {
        globeMaterial.color = new THREE.Color("#081322");
        globeMaterial.emissive = new THREE.Color("#000000");
        globeMaterial.emissiveIntensity = 0;
        globeMaterial.shininess = 6;
      }

      // Even, neutral lighting for a flat readable navy map
      const scene = globe.scene();
      const ambient = new THREE.AmbientLight(0xc9d6df, 0.85);
      scene.add(ambient);
      const keyLight = new THREE.DirectionalLight(0xbfd3e0, 0.55);
      keyLight.position.set(6, 8, 10);
      scene.add(keyLight);
      const rimLight = new THREE.DirectionalLight(0x0b1b2e, 0.45);
      rimLight.position.set(-8, -6, -8);
      scene.add(rimLight);

      // Auto rotation
      const controls = globe.controls();
      if (!reducedMotion.current) {
        controls.autoRotate = true;
        controls.autoRotateSpeed = GLOBE_AUTO_ROTATE_DEG_PER_SEC / 5;
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
      }

      controls.addEventListener("start", () => {
        isDraggingRef.current = true;
        controls.autoRotate = false;
        if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      });
      controls.addEventListener("end", () => {
        isDraggingRef.current = false;
        idleTimerRef.current = setTimeout(() => {
          if (!reducedMotion.current) controls.autoRotate = true;
        }, GLOBE_IDLE_RESUME_MS);
      });

      // Framing perspective: framed on the Atlantic, most traffic visible
      globe.pointOfView({ lat: 18, lng: 10, altitude: 2.15 });

      const handleResize = () => {
        if (containerRef.current && globeRef.current) {
          const w = containerRef.current.clientWidth;
          const h = containerRef.current.clientHeight;
          globeRef.current.width(w);
          globeRef.current.height(h);
        }
      };
      window.addEventListener("resize", handleResize);
      handleResize();

      setGlobeReady(true);

      return () => window.removeEventListener("resize", handleResize);
    };

    initGlobe();

    return () => {
      mounted = false;
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      globeRef.current?._destructor?.();
    };
  }, []);

  // Update country polygons
  useEffect(() => {
    if (!globeRef.current || !globeReady || countries.length === 0) return;
    globeRef.current.polygonsData(countries);
  }, [countries, globeReady]);

  // Build the two arc entries (trail + comet) for one route
  const buildArcEntries = (a: any) => {
    const srcColor = severityColor(a.severity);
    const headColor = tintWhite(srcColor, 0.5);
    const h1 = hash01(a.id);
    const h2 = hash01(a.id, 7);
    const isFast = a.severity === "high" || a.severity === "critical";

    const base = {
      startLat: a.startLat,
      startLng: a.startLng,
      endLat: a.endLat,
      endLng: a.endLng,
      alt: 0.22 + h2 * 0.12,
      severity: a.severity,
      intensity: a.intensity,
    };

    // Faint full trail so the route is always readable
    const trail = {
      ...base,
      id: `${a.id}-trail`,
      color: (t: number) => hexToRgba(srcColor, 0.45 - 0.15 * t),
      dashLength: 1,
      dashGap: 0,
      initialGap: 0,
      animateTime: 0,
    };

    // Bright comet pulse: one lit segment traveling source→target,
    // fading slightly as it arrives (energy absorbed by the target)
    const comet = {
      ...base,
      id: `${a.id}-comet`,
      color: (t: number) => hexToRgba(headColor, Math.max(0, 1 - 0.7 * t)),
      dashLength: 0.25,
      dashGap: 1.05,
      initialGap: h1 * 0.95,
      animateTime: reducedMotion.current ? 0 : isFast ? 1600 : 2400,
    };

    return [trail, comet];
  };

  // Update Great-Circle Arcs & Markers
  useEffect(() => {
    if (!globeRef.current || !globeReady) return;

    const map = arcEntriesRef.current;
    const seen = new Set<string>();

    arcs.forEach((a) => {
      seen.add(a.id);
      if (!map.has(a.id)) {
        map.set(a.id, buildArcEntries(a));
      }
    });

    // Drop entries for expired arcs
    for (const key of Array.from(map.keys())) {
      if (!seen.has(key)) map.delete(key);
    }

    globeRef.current.arcsData(Array.from(map.values()).flat());

    // Custom Layer: Concentric Source and Target markers.
    // Memoized by location key so globe.gl never rebuilds existing THREE
    // objects when the arc list refreshes.
    const markerMap = markerMapRef.current;
    const seenMarkers = new Set<string>();
    arcs.forEach((a) => {
      const srcKey = `src-${a.startLat.toFixed(2)},${a.startLng.toFixed(2)}`;
      seenMarkers.add(srcKey);
      if (!markerMap.has(srcKey)) {
        markerMap.set(srcKey, {
          lat: a.startLat,
          lng: a.startLng,
          alt: 0.015,
          type: "source",
          color: severityColor(a.severity),
          severity: a.severity,
        });
      }
      const tgtKey = `tgt-${a.endLat.toFixed(2)},${a.endLng.toFixed(2)}`;
      seenMarkers.add(tgtKey);
      if (!markerMap.has(tgtKey)) {
        markerMap.set(tgtKey, {
          lat: a.endLat,
          lng: a.endLng,
          alt: 0.015,
          type: "target",
          color: "#00D9FF",
          severity: a.severity,
        });
      }
    });

    for (const key of Array.from(markerMap.keys())) {
      if (!seenMarkers.has(key)) markerMap.delete(key);
    }

    globeRef.current.customLayerData(Array.from(markerMap.values()));
  }, [arcs, globeReady]);

  // Update Radar-Ping Pulse Rings
  useEffect(() => {
    if (!globeRef.current || !globeReady) return;

    const allRipples = ripples.map((r) => ({
      lat: r.lat,
      lng: r.lng,
      color: (t: number) => {
        const alpha = Math.max(0, 0.9 * (1 - t));
        return hexToRgba(r.color || "#00D9FF", alpha);
      },
      maxRadius: r.maxRadius ?? 5.5,
      propagationSpeed: reducedMotion.current ? 0 : r.propagationSpeed ?? 2.5,
      repeatPeriod: reducedMotion.current ? 0 : r.repeatPeriod ?? 750,
    }));

    globeRef.current.ringsData(allRipples);
  }, [ripples, globeReady]);

  return (
    <div className="relative w-full h-full">
      {/* Ambient space backdrop */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 65% 65% at 50% 50%, rgba(74, 122, 156, 0.06) 0%, rgba(3, 7, 11, 0.85) 75%, #03070B 100%)",
        }}
        aria-hidden="true"
      />

      <div
        ref={containerRef}
        className="w-full h-full"
        role="img"
        aria-label="3D Globe Threat Intelligence Visualization"
        style={{ cursor: "grab", touchAction: "none" }}
      />
    </div>
  );
}
