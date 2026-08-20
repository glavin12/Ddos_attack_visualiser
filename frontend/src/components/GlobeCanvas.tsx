"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { useRadarStore } from "@/store/useRadarStore";
import { getCountry } from "@/lib/countries";
import { flagEmoji, formatPercent, formatRelativeTime } from "@/lib/format";
import { feedColor, feedLabel } from "@/lib/constants";
import {
  GLOBE_AUTO_ROTATE_DEG_PER_SEC,
  GLOBE_IDLE_RESUME_MS,
  MAX_ARCS,
  ARC_FLIGHT_MS_FAST,
  ARC_FLIGHT_MS_SLOW,
  ARC_BASE_TRAIL_OPACITY,
  ARC_HOVER_DIM_OPACITY,
  ARC_TRAIL_STROKE,
  ARC_HIT_STROKE,
  ARC_MIN_ALTITUDE,
  ARC_MAX_ALTITUDE,
  BIRTH_PULSE_START_MS,
  BIRTH_PULSE_END_MS,
  BIRTH_SETTLE_START_MS,
  BIRTH_SETTLE_END_MS,
  POINT_SETTLED_OPACITY,
  POINT_BREATHE_MIN_OPACITY,
  POINT_BREATHE_MAX_OPACITY,
  POINT_BREATHE_PERIOD_MS,
  POINT_AGING_THRESHOLD_MS,
  POINT_AGED_OPACITY,
  RESONANCE_DURATION_MS,
  SONAR_IDLE_THRESHOLD_MS,
  SONAR_INTERVAL_MS,
  hash01,
} from "@/lib/constants";
import type { AttackRoute, GlobeArc, GlobeIndicatorPoint, Layer } from "@/lib/types";

/* eslint-disable @typescript-eslint/no-explicit-any */

function hexToRgba(hex: string, alpha: number): string {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

/* Radial-gradient sprite textures for glowing indicator dots — built once,
 * tinted per-feed via the sprite material color. Sprites always face the
 * camera, so dots stay crisp and never flatten to a line at the globe's rim. */
let _glowTexture: THREE.Texture | null = null;
let _coreTexture: THREE.Texture | null = null;

function radialTexture(stops: [number, number][]): THREE.Texture {
  const size = 128;
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  const grad = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  for (const [offset, alpha] of stops) grad.addColorStop(offset, `rgba(255,255,255,${alpha})`);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);
  return new THREE.CanvasTexture(canvas);
}

function glowTexture(): THREE.Texture {
  if (!_glowTexture) {
    _glowTexture = radialTexture([
      [0, 1], [0.25, 0.5], [0.5, 0.16], [1, 0],
    ]);
  }
  return _glowTexture;
}

function coreTexture(): THREE.Texture {
  if (!_coreTexture) {
    _coreTexture = radialTexture([
      [0, 1], [0.45, 1], [0.7, 0.5], [1, 0],
    ]);
  }
  return _coreTexture;
}

/** Build one arc per real Radar route — country centroid to country centroid. */
function buildArcs(routes: AttackRoute[], layer: Layer, maxArcs: number = MAX_ARCS): GlobeArc[] {
  const capped = routes.slice(0, maxArcs);
  const maxShare = Math.max(...capped.map((r) => r.share), 0.0001);
  const arcs: GlobeArc[] = [];
  capped.forEach((route, i) => {
    const src = getCountry(route.source.code);
    const tgt = getCountry(route.target.code);
    if (!src || !tgt) return; // unresolvable code — never invent a coordinate
    const id = `${route.source.code}-${route.target.code}`;
    const h1 = hash01(id);
    const h2 = hash01(id, 7);
    const rank = route.rank ?? i + 1;
    arcs.push({
      id,
      startLat: src.lat,
      startLng: src.lng,
      endLat: tgt.lat,
      endLng: tgt.lng,
      sourceCode: route.source.code,
      sourceName: route.source.name || route.source.code,
      targetCode: route.target.code,
      targetName: route.target.name || route.target.code,
      share: route.share,
      rank: route.rank,
      layer,
      normalizedShare: route.share / maxShare,
      altitude: ARC_MIN_ALTITUDE + h2 * (ARC_MAX_ALTITUDE - ARC_MIN_ALTITUDE),
      phaseOffset: h1,
      flightDurationMs: rank <= 10 ? ARC_FLIGHT_MS_FAST : ARC_FLIGHT_MS_SLOW,
    });
  });
  return arcs;
}

function arcTooltipHtml(arc: GlobeArc, totalArcs: number): string {
  return `
    <div style="font-family:var(--font-geist-sans),sans-serif;background:rgba(10,16,23,0.96);border:1px solid rgba(63,224,208,0.3);border-radius:8px;padding:10px 12px;min-width:200px;box-shadow:0 8px 24px rgba(0,0,0,0.5);">
      <div style="font-size:13px;font-weight:600;color:#E4EDF1;margin-bottom:4px;">
        ${flagEmoji(arc.sourceCode)} ${arc.sourceName} &rarr; ${flagEmoji(arc.targetCode)} ${arc.targetName}
      </div>
      <div style="font-family:var(--font-geist-mono),monospace;font-size:11px;color:#7C939E;line-height:1.6;">
        ${arc.layer} &middot; share ${formatPercent(arc.share, 1)}${arc.rank ? ` &middot; rank #${arc.rank} of ${totalArcs}` : ""}<br/>
        24h aggregate &middot; Cloudflare Radar
      </div>
    </div>`;
}

function indicatorTooltipHtml(point: GlobeIndicatorPoint): string {
  const location = [point.city, point.countryName].filter(Boolean).join(", ") || "Unknown location";
  return `
    <div style="font-family:var(--font-geist-sans),sans-serif;background:rgba(10,16,23,0.96);border:1px solid ${hexToRgba(feedColor(point.sourceFeed), 0.4)};border-radius:8px;padding:10px 12px;min-width:220px;box-shadow:0 8px 24px rgba(0,0,0,0.5);">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
        <span style="width:7px;height:7px;border-radius:50%;background:${feedColor(point.sourceFeed)};box-shadow:0 0 6px ${feedColor(point.sourceFeed)};"></span>
        <span style="font-family:var(--font-geist-mono),monospace;font-size:10px;font-weight:600;letter-spacing:0.04em;color:${feedColor(point.sourceFeed)};text-transform:uppercase;">${feedLabel(point.sourceFeed)}</span>
        ${point.threatFamily ? `<span style="font-size:11px;color:#E4EDF1;margin-left:auto;">${point.threatFamily}</span>` : ""}
      </div>
      <div style="font-family:var(--font-geist-mono),monospace;font-size:12px;color:#E4EDF1;margin-bottom:2px;">${point.resolvedIp}</div>
      <div style="font-size:11px;color:#7C939E;margin-bottom:4px;">${flagEmoji(point.countryCode)} ${location}</div>
      <div style="font-family:var(--font-geist-mono),monospace;font-size:10px;color:#48606C;">
        First seen ${formatRelativeTime(new Date(point.firstSeen).getTime())} &middot; Last seen ${formatRelativeTime(new Date(point.lastSeen).getTime())}
      </div>
      ${point.greynoiseClassification ? `<div style="font-family:var(--font-geist-mono),monospace;font-size:10px;color:#48606C;margin-top:2px;">GreyNoise: ${point.greynoiseClassification}</div>` : ""}
    </div>`;
}

interface RippleDatum {
  id: string;
  lat: number;
  lng: number;
  color: string;
  maxRadius: number;
  propagationSpeed: number;
  alt: number;
}

/** Indicator sprite sizes, in globe world units (globe radius = 100). */
const CORE_SIZE = 3.4;
const HALO_SIZE = 11;
/** Newest N indicators emit continuous sonar pulses; older ones stay calm. */
const CONTINUOUS_PULSE_LIMIT = 22;

/**
 * Globe Canvas — AEGIS globe.
 *
 * Two independent, honestly-separated layers:
 * - Arcs: Cloudflare Radar 24h aggregate top routes. Bootstrapped from REST,
 *   then kept current by the backend's radar_pulse WebSocket push. Static
 *   per refresh — globe.gl's own dash animation loops the comet motion with
 *   zero per-frame data churn.
 * - Points: real threat indicators streamed over WebSocket, each with a
 *   choreographed birth (double ripple + pulse + settle), a breathing idle
 *   state, and visible aging when not re-observed.
 */
export default function GlobeCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<any>(null);
  const countriesRef = useRef<any[]>([]);
  const idleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reducedMotion = useRef(false);
  /* Mobile / low-power gate: caps pixel ratio, arc + pulse budgets, and skips
   * the ambient-sonar decoration so the WebGL globe stays smooth on phones.
   * Rendered client-only (GlobeCanvas is dynamic, ssr:false), so reading
   * matchMedia in a lazy initializer is safe and stays constant per session. */
  const [isMobile] = useState<boolean>(
    () =>
      typeof window !== "undefined" &&
      (window.matchMedia("(max-width: 767px)").matches ||
        window.matchMedia("(pointer: coarse)").matches)
  );
  const [globeReady, setGlobeReady] = useState(false);
  const [countries, setCountries] = useState<any[]>([]);

  const topRoutes = useRadarStore((s) => s.topRoutes);
  const selectedLayer = useRadarStore((s) => s.selectedLayer);
  const indicators = useRadarStore((s) => s.indicators);
  const lastIndicatorAtMs = useRadarStore((s) => s.lastIndicatorAtMs);

  const hoveredArcIdRef = useRef<string | null>(null);
  const hoveredIndicatorIdRef = useRef<string | null>(null);
  const seenIndicatorIdsRef = useRef<Set<string>>(new Set());
  const ripplesRef = useRef<RippleDatum[]>([]);
  const resonanceRef = useRef<Map<string, number>>(new Map()); // countryCode -> startMs
  const resonanceRafRef = useRef<number | null>(null);
  /* Every ripple/sonar cleanup setTimeout, tracked so unmount can cancel them all. */
  const pendingTimersRef = useRef<Set<ReturnType<typeof setTimeout>>>(new Set());

  function scheduleCleanup(fn: () => void, ms: number) {
    const t = setTimeout(() => {
      pendingTimersRef.current.delete(t);
      fn();
    }, ms);
    pendingTimersRef.current.add(t);
  }

  // Each arc renders 4 line meshes (hit/trail/tail/head), two of them animated
  // additive comets. On mobile we render the top ~16 routes so the globe stays
  // smooth; desktop keeps the full arc budget.
  const arcs = useMemo(
    () => buildArcs(topRoutes, selectedLayer, isMobile ? 16 : MAX_ARCS),
    [topRoutes, selectedLayer, isMobile]
  );
  const totalArcs = arcs.length;

  /* Reduced motion preference */
  useEffect(() => {
    if (typeof window !== "undefined") {
      reducedMotion.current = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }
  }, []);

  /* Fetch GeoJSON country borders */
  useEffect(() => {
    // On mobile prefer the lighter 110m borders (~480KB vs ~3MB) — far fewer
    // vertices to upload and stroke each frame. Desktop keeps the crisp 50m set.
    const URLS = isMobile
      ? [
          "/globe/countries-110m.geojson",
          "/globe/countries-50m.geojson",
        ]
      : [
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
  }, [isMobile]);

  /* Initialize Globe */
  useEffect(() => {
    if (!containerRef.current) return;
    let mounted = true;
    const pendingTimers = pendingTimersRef.current;

    const initGlobe = async () => {
      const GlobeModule = await import("globe.gl");
      const Globe = GlobeModule.default;
      if (!mounted || !containerRef.current) return;

      const globe = new Globe(containerRef.current)
        .backgroundColor("rgba(0,0,0,0)")
        .showAtmosphere(true)
        .atmosphereColor("#3FE0D0")
        .atmosphereAltitude(0.13)
        .showGraticules(false)
        // Country borders — outline only, dynamic stroke color for resonance
        .polygonsData([])
        .polygonCapColor(() => "rgba(0,0,0,0)")
        .polygonSideColor(() => "rgba(0,0,0,0)")
        .polygonStrokeColor((d: any) => {
          const code = d?.properties?.ISO_A2;
          const startMs = code ? resonanceRef.current.get(code) : undefined;
          if (startMs !== undefined) {
            const age = Date.now() - startMs;
            if (age < RESONANCE_DURATION_MS) {
              const t = age / RESONANCE_DURATION_MS;
              const feed = resonanceColorRef.current.get(code!) ?? "#3FE0D0";
              return hexToRgba(feed, 0.9 * (1 - t) + 0.15);
            }
          }
          return "rgba(140,190,210,0.35)";
        })
        .polygonAltitude(0.004)
        // Arcs — real Radar routes only, rebuilt when topRoutes refreshes.
        // The dash accessors below are what make the comet actually travel:
        // globe.gl animates the lit dash segment from source to target and
        // loops it, driven per-arc by the dashAnimateTime property.
        .arcsData([])
        .arcColor("color")
        .arcAltitude("alt")
        .arcStroke("stroke")
        .arcDashLength("dashLength")
        .arcDashGap("dashGap")
        .arcDashInitialGap("dashInitialGap")
        .arcDashAnimateTime("dashAnimateTime")
        .arcsTransitionDuration(0)
        // Rings — birth choreography, continuous per-dot pulses, ambient sonar
        .ringsData([])
        .ringColor("colorFn")
        .ringMaxRadius("maxRadius")
        .ringPropagationSpeed("propagationSpeed")
        .ringRepeatPeriod("repeatPeriod")
        .ringAltitude("alt")
        // Threat indicator points — custom layer for birth/breathe/age choreography
        .customLayerData([])
        .customThreeObjectUpdate((obj: any, d: any) => {
          // A dot never moves relative to the globe, so its world position is a
          // pure function of lat/lng — recompute (trig) only when those change,
          // not every frame. Meaningful with up to ~200 dots at 60fps.
          const ud = obj.userData;
          if (ud._lat !== d.lat || ud._lng !== d.lng) {
            const coords = globe.getCoords(d.lat, d.lng, 0.012);
            obj.position.set(coords.x, coords.y, coords.z);
            ud._lat = d.lat;
            ud._lng = d.lng;
          }

          const { halo, core } = obj.userData;
          const now = Date.now();
          const age = now - d.bornAtMs;
          const isHovered = hoveredIndicatorIdRef.current === d.id;
          let opacityMul = 1;
          let scale = 1;

          if (age < BIRTH_PULSE_END_MS) {
            if (age >= BIRTH_PULSE_START_MS) {
              const p = (age - BIRTH_PULSE_START_MS) / (BIRTH_PULSE_END_MS - BIRTH_PULSE_START_MS);
              scale = 1 + 0.55 * Math.sin(p * Math.PI);
            }
          } else if (age < BIRTH_SETTLE_END_MS) {
            const p = (age - BIRTH_SETTLE_START_MS) / (BIRTH_SETTLE_END_MS - BIRTH_SETTLE_START_MS);
            opacityMul = 1 - p * (1 - POINT_SETTLED_OPACITY);
          } else {
            const phase = (now % POINT_BREATHE_PERIOD_MS) / POINT_BREATHE_PERIOD_MS;
            opacityMul =
              POINT_BREATHE_MIN_OPACITY +
              (POINT_BREATHE_MAX_OPACITY - POINT_BREATHE_MIN_OPACITY) * (0.5 + 0.5 * Math.sin(phase * 2 * Math.PI));
          }

          const lastSeenMs = Date.parse(d.lastSeen);
          if (Number.isFinite(lastSeenMs) && now - lastSeenMs > POINT_AGING_THRESHOLD_MS) {
            opacityMul = Math.min(opacityMul, POINT_AGED_OPACITY);
          }

          if (isHovered) {
            opacityMul = 1;
            scale = 1.7;
          }
          if (reducedMotion.current) scale = 1;

          core.scale.setScalar(CORE_SIZE * scale);
          halo.scale.setScalar(HALO_SIZE * (0.85 + 0.15 * scale));
          core.material.opacity = Math.min(1, opacityMul + 0.2);
          halo.material.opacity = 0.42 * opacityMul;
        })
        .customThreeObject((d: any) => {
          const group = new THREE.Group();
          const color = new THREE.Color(feedColor(d.sourceFeed));

          const halo = new THREE.Sprite(
            new THREE.SpriteMaterial({
              map: glowTexture(),
              color,
              transparent: true,
              opacity: 0.42,
              depthWrite: false,
              blending: THREE.AdditiveBlending,
            })
          );
          halo.scale.setScalar(HALO_SIZE);

          const core = new THREE.Sprite(
            new THREE.SpriteMaterial({
              map: coreTexture(),
              color: color.clone().lerp(new THREE.Color("#ffffff"), 0.35),
              transparent: true,
              opacity: 1,
              depthWrite: false,
            })
          );
          core.scale.setScalar(CORE_SIZE);

          group.add(halo, core);
          group.userData = { halo, core };
          group.renderOrder = 3;
          return group;
        })
        .customLayerLabel((d: any) => indicatorTooltipHtml(d))
        .onCustomLayerHover((obj: any) => {
          hoveredIndicatorIdRef.current = obj ? (obj as GlobeIndicatorPoint).id : null;
        })
        .onCustomLayerClick((obj: any) => {
          const point = obj as GlobeIndicatorPoint;
          if (point?.sourceUrl && typeof window !== "undefined") {
            window.open(point.sourceUrl, "_blank", "noopener,noreferrer");
          }
        });

      globeRef.current = globe;

      // Cap the renderer pixel ratio. Phones report DPR 2–3, so the fill-heavy
      // additive glow sprites would otherwise shade 4–9x the pixels — the single
      // biggest cause of mobile lag. 1.5 on mobile stays crisp; desktop caps at 2.
      const renderer = globe.renderer?.();
      if (renderer) {
        const cap = isMobile ? 1.5 : 2;
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, cap));
      }

      if (countriesRef.current.length > 0) {
        globe.polygonsData(countriesRef.current);
      }

      const globeMaterial = globe.globeMaterial() as THREE.MeshPhongMaterial;
      if (globeMaterial) {
        globeMaterial.color = new THREE.Color("#081119");
        globeMaterial.emissive = new THREE.Color("#000000");
        globeMaterial.emissiveIntensity = 0;
        globeMaterial.shininess = 4;
      }

      const scene = globe.scene();
      scene.add(new THREE.AmbientLight(0xc9d6df, 0.8));
      const keyLight = new THREE.DirectionalLight(0xbfd3e0, 0.5);
      keyLight.position.set(6, 8, 10);
      scene.add(keyLight);
      const rimLight = new THREE.DirectionalLight(0x0b1b2e, 0.4);
      rimLight.position.set(-8, -6, -8);
      scene.add(rimLight);

      const controls = globe.controls();
      if (!reducedMotion.current) {
        controls.autoRotate = true;
        controls.autoRotateSpeed = GLOBE_AUTO_ROTATE_DEG_PER_SEC / 5;
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
      }
      controls.addEventListener("start", () => {
        controls.autoRotate = false;
        if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      });
      controls.addEventListener("end", () => {
        idleTimerRef.current = setTimeout(() => {
          if (!reducedMotion.current) controls.autoRotate = true;
        }, GLOBE_IDLE_RESUME_MS);
      });

      globe.pointOfView({ lat: 18, lng: 10, altitude: 2.15 });

      const handleResize = () => {
        if (containerRef.current && globeRef.current) {
          globeRef.current.width(containerRef.current.clientWidth);
          globeRef.current.height(containerRef.current.clientHeight);
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
      if (resonanceRafRef.current) cancelAnimationFrame(resonanceRafRef.current);
      // Cancel every pending ripple/sonar cleanup timer so none of them fire
      // against a torn-down globe instance after unmount.
      pendingTimers.forEach((t) => clearTimeout(t));
      pendingTimers.clear();
      // Sprite materials are created fresh per indicator (customThreeObject)
      // and are never disposed elsewhere; the shared glow/core textures are
      // module-level singletons and must NOT be disposed here since they're
      // reused across mounts.
      globeRef.current?.scene()?.traverse((obj: any) => {
        if (obj instanceof THREE.Sprite) obj.material?.dispose();
      });
      globeRef.current?._destructor?.();
      globeRef.current = null;
    };
  }, [isMobile]);

  /* Country resonance colors keyed alongside resonanceRef (feed color per pulse) */
  const resonanceColorRef = useRef<Map<string, string>>(new Map());
  /* Continuous sonar pulses for the newest indicators (persist until they age out) */
  const continuousPulsesRef = useRef<any[]>([]);

  /* Merge the always-on per-dot pulses with any transient birth/sonar ripples
   * and push the combined set to globe.gl in one call. */
  function refreshRings() {
    const transient = ripplesRef.current.map((r) => ({
      lat: r.lat,
      lng: r.lng,
      alt: r.alt,
      maxRadius: r.maxRadius,
      propagationSpeed: r.propagationSpeed,
      repeatPeriod: 100000, // effectively one-shot; removed via setTimeout
      colorFn: (t: number) => hexToRgba(r.color, Math.max(0, 1 - t)),
    }));
    globeRef.current?.ringsData([...continuousPulsesRef.current, ...transient]);
  }

  /* Rebuild the continuous-pulse set from the newest live indicators. */
  function refreshContinuousPulses(points: GlobeIndicatorPoint[]) {
    if (reducedMotion.current) {
      continuousPulsesRef.current = [];
      return;
    }
    const now = Date.now();
    const pulseLimit = isMobile ? 8 : CONTINUOUS_PULSE_LIMIT;
    continuousPulsesRef.current = points
      .slice(0, pulseLimit)
      .filter((p) => {
        const ls = Date.parse(p.lastSeen);
        return !(Number.isFinite(ls) && now - ls > POINT_AGING_THRESHOLD_MS);
      })
      .map((p) => {
        const color = feedColor(p.sourceFeed);
        return {
          lat: p.lat,
          lng: p.lng,
          alt: 0.01,
          maxRadius: 3,
          propagationSpeed: 1.5, // ~2s to full radius
          repeatPeriod: 2400,
          colorFn: (t: number) => hexToRgba(color, 0.45 * (1 - t)),
        };
      });
  }

  function spawnBirthRipples(point: GlobeIndicatorPoint) {
    if (reducedMotion.current) return;
    const color = feedColor(point.sourceFeed);
    const r1: RippleDatum = {
      id: `${point.id}-r1`,
      lat: point.lat,
      lng: point.lng,
      color,
      maxRadius: 3.5,
      propagationSpeed: 4.375, // 3.5deg / 0.8s
      alt: 0.015,
    };
    const r2: RippleDatum = {
      id: `${point.id}-r2`,
      lat: point.lat,
      lng: point.lng,
      color,
      maxRadius: 5,
      propagationSpeed: 3.33, // 5deg / 1.5s
      alt: 0.012,
    };
    // Pushed here without a refreshRings() call — the caller (the indicator
    // effect) issues one combined refresh after processing every new point
    // in the batch, so a burst of arrivals doesn't push ringsData() N times.
    ripplesRef.current = [...ripplesRef.current, r2, r1];
    scheduleCleanup(() => {
      ripplesRef.current = ripplesRef.current.filter((r) => r.id !== r1.id);
      refreshRings();
    }, 820);
    scheduleCleanup(() => {
      ripplesRef.current = ripplesRef.current.filter((r) => r.id !== r2.id);
      refreshRings();
    }, 1520);
  }

  function runResonanceLoop() {
    if (resonanceRafRef.current) return; // already running
    const tick = () => {
      const globe = globeRef.current;
      if (!globe) {
        resonanceRafRef.current = null;
        return;
      }
      const now = Date.now();
      let anyActive = false;
      for (const [code, startMs] of resonanceRef.current) {
        if (now - startMs < RESONANCE_DURATION_MS) anyActive = true;
        else resonanceRef.current.delete(code);
      }
      globe.polygonStrokeColor(globe.polygonStrokeColor());
      if (anyActive) {
        resonanceRafRef.current = requestAnimationFrame(tick);
      } else {
        resonanceRafRef.current = null;
      }
    };
    resonanceRafRef.current = requestAnimationFrame(tick);
  }

  /* Update country polygons once loaded */
  useEffect(() => {
    if (!globeRef.current || !globeReady || countries.length === 0) return;
    globeRef.current.polygonsData(countries);
  }, [countries, globeReady]);

  /* Update arcs — only touches globe.gl when topRoutes actually refreshes
   * (backend radar_pulse push + periodic REST re-poll). */
  useEffect(() => {
    if (!globeRef.current || !globeReady) return;

    const TAIL_LEN = 0.32;
    const TAIL_GAP = 1.7;
    const HEAD_LEN = 0.09;
    const period = TAIL_LEN + TAIL_GAP;

    const entries: any[] = [];
    arcs.forEach((arc) => {
      const brightness = 0.55 + 0.45 * Math.sqrt(arc.normalizedShare);
      const geo = {
        startLat: arc.startLat,
        startLng: arc.startLng,
        endLat: arc.endLat,
        endLng: arc.endLng,
        alt: arc.altitude,
        __arc: arc,
      };
      const dimmed = () => hoveredArcIdRef.current !== null && hoveredArcIdRef.current !== arc.id;

      // 0. Invisible wide hit-tube — the reliable hover target. Spans the full
      // path as a fat tube so the tooltip fires anywhere along the arc,
      // including short/self routes where the visible comet is tiny. A
      // zero-width line (the old trail) was essentially un-raycastable, which
      // is why tooltips only appeared over the thin lit comet before.
      entries.push({
        ...geo,
        id: `${arc.id}-hit`,
        stroke: ARC_HIT_STROKE,
        // Near-zero alpha: imperceptible, but keeps the mesh raycastable
        // (a fully culled 0-opacity material could stop receiving hovers).
        color: () => hexToRgba("#3FE0D0", 0.001),
        dashLength: 1,
        dashGap: 0,
        dashInitialGap: 0,
        dashAnimateTime: 0,
      });

      // 1. Static trail — a thin, brighter tube (not a zero-width line) that
      // always shows where the route goes even between comet passes.
      entries.push({
        ...geo,
        id: `${arc.id}-trail`,
        stroke: ARC_TRAIL_STROKE,
        color: () =>
          hexToRgba("#4FE8D8", dimmed() ? ARC_HOVER_DIM_OPACITY : ARC_BASE_TRAIL_OPACITY),
        dashLength: 1,
        dashGap: 0,
        dashInitialGap: 0,
        dashAnimateTime: 0,
      });

      // 2. Comet tail — a glowing streak that travels source -> target and loops.
      entries.push({
        ...geo,
        id: `${arc.id}-tail`,
        stroke: 0.5,
        color: (t: number) =>
          hexToRgba("#4FE8D8", (dimmed() ? 0.12 : 1) * brightness * (0.6 - 0.28 * t)),
        dashLength: TAIL_LEN,
        dashGap: TAIL_GAP,
        dashInitialGap: arc.phaseOffset * period,
        dashAnimateTime: reducedMotion.current ? 0 : arc.flightDurationMs,
      });

      // 3. Comet head — short bright leading node riding the front of the tail.
      entries.push({
        ...geo,
        id: `${arc.id}-head`,
        stroke: 0.75,
        color: (t: number) =>
          hexToRgba("#DFFFFA", (dimmed() ? 0.18 : 1) * brightness * Math.max(0.15, 1 - 0.55 * t)),
        dashLength: HEAD_LEN,
        dashGap: period - HEAD_LEN,
        dashInitialGap: arc.phaseOffset * period + (TAIL_LEN - HEAD_LEN),
        dashAnimateTime: reducedMotion.current ? 0 : arc.flightDurationMs,
      });
    });

    globeRef.current.arcsData(entries);
    globeRef.current
      .arcColor((d: any) => d.color)
      .arcStroke((d: any) => d.stroke)
      .arcLabel((d: any) => (d.__arc ? arcTooltipHtml(d.__arc, totalArcs) : ""))
      .onArcHover((d: any) => {
        hoveredArcIdRef.current = d?.__arc?.id ?? null;
        // Re-apply the color accessor so dimming refreshes without touching
        // arcsData (which would reset every comet's dash phase to zero).
        globeRef.current?.arcColor((dd: any) => dd.color);
      });
  }, [arcs, globeReady, totalArcs]);

  /* Update indicator custom layer + trigger birth choreography (ripples + resonance) */
  useEffect(() => {
    if (!globeRef.current || !globeReady) return;
    globeRef.current.customLayerData(indicators);

    const seen = seenIndicatorIdsRef.current;
    for (const point of indicators) {
      if (seen.has(point.id)) continue;
      seen.add(point.id);
      if (Date.now() - point.bornAtMs > 500) continue; // skip choreography on initial page load burst

      spawnBirthRipples(point);
      if (point.countryCode) {
        resonanceRef.current.set(point.countryCode, Date.now());
        resonanceColorRef.current.set(point.countryCode, feedColor(point.sourceFeed));
        runResonanceLoop();
      }
    }

    // Keep the continuous per-dot pulses in sync with the newest indicators.
    refreshContinuousPulses(indicators);
    refreshRings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [indicators, globeReady]);

  /* Ambient sonar — quiet-globe heartbeat when no indicators have arrived recently.
   * Skipped on mobile (pure decoration) to keep the render loop light. */
  useEffect(() => {
    if (reducedMotion.current || isMobile) return;
    const interval = setInterval(() => {
      const idleFor = lastIndicatorAtMs ? Date.now() - lastIndicatorAtMs : Infinity;
      if (idleFor < SONAR_IDLE_THRESHOLD_MS) return;
      const lat = (Math.asin(2 * Math.random() - 1) * 180) / Math.PI;
      const lng = 360 * Math.random() - 180;
      const id = `sonar-${Date.now()}`;
      ripplesRef.current = [
        ...ripplesRef.current,
        { id, lat, lng, color: "#8FA6B0", maxRadius: 5, propagationSpeed: 2, alt: 0.01 },
      ];
      refreshRings();
      scheduleCleanup(() => {
        ripplesRef.current = ripplesRef.current.filter((r) => r.id !== id);
        refreshRings();
      }, 2600);
    }, SONAR_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [lastIndicatorAtMs, isMobile]);

  return (
    <div className="relative w-full h-full">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 65% 65% at 50% 50%, rgba(63,224,208,0.05) 0%, rgba(2,4,8,0.85) 75%, #020408 100%)",
        }}
        aria-hidden="true"
      />
      <div
        ref={containerRef}
        className="w-full h-full"
        role="img"
        aria-label="AEGIS globe — Cloudflare Radar routes and live threat indicators"
        style={{ cursor: "grab", touchAction: "none" }}
      />
    </div>
  );
}
