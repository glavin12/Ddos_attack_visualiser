"use client";

import { useEffect, useRef, useState } from "react";
import { useRadarStore } from "@/store/useRadarStore";
import {
  GLOBE_AUTO_ROTATE_DEG_PER_SEC,
  GLOBE_IDLE_RESUME_MS,
  ROUTE_OPACITY,
  severityColor,
} from "@/lib/constants";
import * as THREE from "three";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * Globe Canvas — DDoS Sentinel visual centerpiece.
 * Full-viewport dark satellite globe with city night lights,
 * luminous severity-coded arcs (Red, Orange, Yellow, Teal),
 * and concentric pulse rings at source (red) and target (cyan) nodes.
 */
export default function GlobeCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<any>(null);
  const idleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isDraggingRef = useRef(false);
  const reducedMotion = useRef(false);
  const [countries, setCountries] = useState<any[]>([]);

  const arcs = useRadarStore((s) => s.arcs);
  const ripples = useRadarStore((s) => s.ripples);
  const pruneExpiredArcs = useRadarStore((s) => s.pruneExpiredArcs);

  // Check reduced motion preference
  useEffect(() => {
    if (typeof window !== "undefined") {
      reducedMotion.current = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches;
    }
  }, []);

  // Fetch country borders GeoJSON
  useEffect(() => {
    const LOCAL_URL = "/globe/countries-110m.geojson";
    const CDN_URL =
      "https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson";

    const load = async (url: string): Promise<any> => {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    };

    load(LOCAL_URL)
      .catch(() => load(CDN_URL))
      .then((data) => {
        if (data?.features) setCountries(data.features);
      })
      .catch(() => {});
  }, []);

  // Periodic arc expiration pruning
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
        .showGlobe(true)
        .showAtmosphere(true)
        .atmosphereColor("#00D9FF")
        .atmosphereAltitude(0.18)
        .globeImageUrl("//unpkg.com/three-globe/example/img/earth-night.jpg")
        .showGraticules(true)
        // Country polygons
        .polygonsData([])
        .polygonCapColor(() => "rgba(10, 25, 45, 0.25)")
        .polygonSideColor(() => "rgba(0, 0, 0, 0)")
        .polygonStrokeColor(() => "rgba(0, 217, 255, 0.35)")
        .polygonAltitude(0.006)
        // Arc layer — curved severity lines
        .arcsData([])
        .arcColor("color")
        .arcStroke("stroke")
        .arcDashLength(0.5)
        .arcDashGap(0.08)
        .arcDashAnimateTime(reducedMotion.current ? 0 : 2200)
        .arcAltitudeAutoScale(0.55)
        // Rings layer — sonar ripple pulses
        .ringsData([])
        .ringColor("color")
        .ringMaxRadius("maxRadius")
        .ringPropagationSpeed(reducedMotion.current ? 0 : 2.4)
        .ringRepeatPeriod(reducedMotion.current ? 0 : 700)
        .ringAltitude(0.02)
        // Points layer — glowing node markers
        .pointsData([])
        .pointAltitude(0.022)
        .pointRadius((d: any) => d.radius ?? 0.3)
        .pointColor((d: any) => d.color ?? "#00D9FF")
        .pointResolution(24);

      globeRef.current = globe;

      // Adjust globe material
      const globeMaterial = globe.globeMaterial() as THREE.MeshPhongMaterial;
      if (globeMaterial) {
        globeMaterial.color = new THREE.Color("#050c18");
        globeMaterial.emissive = new THREE.Color("#020610");
        globeMaterial.emissiveIntensity = 0.25;
        globeMaterial.shininess = 20;
      }

      // Very subtle graticules
      const scene = globe.scene();
      scene.traverse((child: THREE.Object3D) => {
        if (child instanceof THREE.Line || child instanceof THREE.LineSegments) {
          const mat = child.material as THREE.LineBasicMaterial;
          if (mat) {
            mat.color = new THREE.Color("#00D9FF");
            mat.opacity = 0.06;
            mat.transparent = true;
          }
        }
      });

      // Atmospheric & scene lighting
      const ambient = new THREE.AmbientLight(0xd7e5ea, 1.0);
      scene.add(ambient);
      const keyLight = new THREE.DirectionalLight(0x00d9ff, 0.8);
      keyLight.position.set(6, 6, 10);
      scene.add(keyLight);
      const rimLight = new THREE.DirectionalLight(0x1a4570, 0.5);
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

      // Pause rotation during interaction
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

      // Center initial perspective to frame Europe/Africa/Asia/Americas nicely
      globe.pointOfView({ lat: 20, lng: 10, altitude: 2.15 });

      const handleResize = () => {
        if (containerRef.current && globeRef.current) {
          globeRef.current.width(containerRef.current.clientWidth);
          globeRef.current.height(containerRef.current.clientHeight);
        }
      };
      window.addEventListener("resize", handleResize);
      handleResize();

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
    if (!globeRef.current || countries.length === 0) return;
    globeRef.current.polygonsData(countries);
  }, [countries]);

  // Update arcs
  useEffect(() => {
    if (!globeRef.current) return;

    const hexToRgba = (hex: string, alpha: number): string => {
      const cleanHex = hex.replace("#", "");
      const r = parseInt(cleanHex.slice(0, 2), 16);
      const g = parseInt(cleanHex.slice(2, 4), 16);
      const b = parseInt(cleanHex.slice(4, 6), 16);
      return `rgba(${r},${g},${b},${alpha})`;
    };

    const arcData = arcs.map((a, i) => {
      const color = severityColor(a.severity);
      const opacity = i < 5 ? ROUTE_OPACITY.primary : i < 15 ? ROUTE_OPACITY.secondary : ROUTE_OPACITY.background;

      return {
        startLat: a.startLat,
        startLng: a.startLng,
        endLat: a.endLat,
        endLng: a.endLng,
        color: [hexToRgba(color, Math.min(1, opacity * 1.2)), hexToRgba(color, 0.15)],
        stroke: Math.min(2.5, Math.max(1.2, a.stroke)),
        dashLength: a.dashLength,
        dashGap: a.dashGap,
      };
    });

    globeRef.current.arcsData(arcData);

    // Update point markers (red for sources, cyan for targets)
    const pointsMap = new Map<string, any>();
    arcs.forEach((a) => {
      const srcKey = `${a.startLat.toFixed(1)},${a.startLng.toFixed(1)}`;
      if (!pointsMap.has(srcKey)) {
        pointsMap.set(srcKey, {
          lat: a.startLat,
          lng: a.startLng,
          color: "#FF3B4E",
          radius: 0.35,
        });
      }
      const tgtKey = `${a.endLat.toFixed(1)},${a.endLng.toFixed(1)}`;
      pointsMap.set(tgtKey, {
        lat: a.endLat,
        lng: a.endLng,
        color: "#00D9FF",
        radius: 0.42,
      });
    });

    globeRef.current.pointsData(Array.from(pointsMap.values()));
  }, [arcs]);

  // Update ripple rings
  useEffect(() => {
    if (!globeRef.current) return;
    globeRef.current.ringsData(
      ripples.map((r) => ({
        lat: r.lat,
        lng: r.lng,
        color: (t: number) => {
          const alpha = Math.max(0, 0.8 * (1 - t));
          const hex = r.color.replace("#", "");
          const rv = parseInt(hex.slice(0, 2), 16);
          const gv = parseInt(hex.slice(2, 4), 16);
          const bv = parseInt(hex.slice(4, 6), 16);
          return `rgba(${rv},${gv},${bv},${alpha})`;
        },
        maxRadius: r.maxRadius ?? 4.5,
        propagationSpeed: 2.4,
        repeatPeriod: 750,
      }))
    );
  }, [ripples]);

  return (
    <div className="relative w-full h-full">
      {/* Background space glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 65% 65% at 50% 50%, rgba(0, 217, 255, 0.07) 0%, rgba(3, 7, 11, 0.85) 75%, #03070B 100%)",
        }}
        aria-hidden="true"
      />

      <div
        ref={containerRef}
        className="w-full h-full"
        role="img"
        aria-label="3D Globe DDoS attack visualization"
        style={{ cursor: "grab", touchAction: "none" }}
      />
    </div>
  );
}
