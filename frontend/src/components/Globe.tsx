"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";

/**
 * Globe wrapper with dynamic import (ssr: false).
 * globe.gl uses WebGL and cannot render server-side.
 * Shows "INITIALIZING TELEMETRY…" loading state per design spec §4.7.
 */
const GlobeCanvas = dynamic(() => import("@/components/GlobeCanvas"), {
  ssr: false,
  loading: () => <GlobeLoader />,
});

function GlobeLoader() {
  return (
    <div
      className="flex items-center justify-center w-full h-full"
      style={{ backgroundColor: "var(--color-void)" }}
    >
      <span
        className="font-mono text-[13px] tracking-widest uppercase"
        style={{ color: "var(--color-text-faint)" }}
      >
        Initializing telemetry…
      </span>
    </div>
  );
}

export default function Globe() {
  return (
    <Suspense fallback={<GlobeLoader />}>
      <GlobeCanvas />
    </Suspense>
  );
}
