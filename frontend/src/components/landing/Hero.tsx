import Image from "next/image";
import Link from "next/link";

export default function Hero() {
  return (
    <section
      className="landing-section relative flex items-center"
      style={{
        minHeight: "100dvh",
        paddingTop: 96,
        paddingBottom: 64,
        paddingLeft: 24,
        paddingRight: 24,
      }}
      aria-labelledby="hero-heading"
    >
      {/* Radial glow background */}
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 80% 60% at 70% 50%, rgba(0,217,255,0.05) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div className="w-full max-w-7xl mx-auto flex flex-col lg:flex-row items-center gap-12 lg:gap-16">
        {/* ── Left: Text column (45%) ── */}
        <div className="flex-1 max-w-xl">
          {/* Eyebrow — exactly 1 of 2 allowed */}
          <div
            className="inline-flex items-center gap-2 mb-6 px-3 py-1.5 rounded-full"
            style={{
              backgroundColor: "rgba(0, 217, 255, 0.08)",
              border: "1px solid rgba(0, 217, 255, 0.25)",
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full live-pulse"
              style={{ backgroundColor: "var(--color-severity-low)" }}
              aria-hidden="true"
            />
            <span
              className="font-mono text-[10px] font-bold uppercase tracking-[0.14em]"
              style={{ color: "var(--color-signal-cyan)" }}
            >
              Network Security Operations
            </span>
          </div>

          {/* Headline — max 2 lines */}
          <h1
            id="hero-heading"
            className="font-space font-bold"
            style={{
              fontSize: "clamp(32px, 4vw, 52px)",
              lineHeight: 1.08,
              letterSpacing: "-0.02em",
              color: "#FFFFFF",
              textWrap: "balance",
            }}
          >
            See global threats.{" "}
            <br />
            <span style={{ color: "var(--color-signal-cyan)" }}>
              As they surface.
            </span>
          </h1>

          {/* Subtext — max 20 words, max 4 lines */}
          <p
            className="font-plex mt-5"
            style={{
              fontSize: 16,
              lineHeight: 1.6,
              color: "var(--color-text-muted)",
              maxWidth: 420,
              textWrap: "balance",
            }}
          >
            Global threat observatory built on Cloudflare Radar&apos;s 24-hour
            DDoS aggregates and live indicators from public threat feeds.
          </p>

          {/* CTAs — single intent: open dashboard */}
          <div className="flex items-center gap-4 mt-8">
            <Link
              href="/dashboard"
              className="btn-primary"
              id="hero-cta"
            >
              Open Dashboard
            </Link>
            <a
              href="#how-it-works"
              className="btn-ghost"
            >
              How it works
            </a>
          </div>

          {/* Trust signal — small, beneath CTA */}
          <p
            className="font-mono mt-5 text-[11px]"
            style={{ color: "var(--color-text-faint)" }}
          >
            Built on Cloudflare Radar API. No account needed. 100% open source.
          </p>
        </div>

        {/* ── Right: Dashboard visual (55%) ── */}
        <div className="flex-1 w-full relative">
          <div
            className="relative rounded-xl overflow-hidden"
            style={{
              border: "1px solid rgba(0, 217, 255, 0.2)",
              boxShadow: "0 0 80px -20px rgba(0, 217, 255, 0.15), 0 24px 64px rgba(0,0,0,0.6)",
            }}
          >
            <Image
              src="/hero-dashboard.jpg"
              alt="Threat Observatory dashboard showing a dark 3D globe with aggregate attack routes, threat feed panels, and live metrics"
              width={1400}
              height={787}
              priority
              className="w-full h-auto block"
              style={{ display: "block" }}
            />
            {/* Subtle top fade for depth */}
            <div
              aria-hidden="true"
              style={{
                position: "absolute",
                inset: 0,
                background: "linear-gradient(to bottom, rgba(3,7,11,0.08) 0%, transparent 30%)",
                pointerEvents: "none",
              }}
            />
          </div>

          {/* Floating metric badge */}
          <div
            className="absolute -left-4 bottom-8 hidden lg:flex items-center gap-3 px-4 py-3 rounded-lg"
            style={{
              backgroundColor: "rgba(8, 18, 28, 0.95)",
              border: "1px solid rgba(0, 217, 255, 0.3)",
              backdropFilter: "blur(12px)",
              WebkitBackdropFilter: "blur(12px)",
              boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
            }}
            aria-hidden="true"
          >
            <span
              className="w-2 h-2 rounded-full live-pulse"
              style={{ backgroundColor: "var(--color-severity-critical)" }}
            />
            <div>
              <div className="font-mono text-[18px] font-bold" style={{ color: "var(--color-severity-critical)" }}>
                24h
              </div>
              <div className="font-mono text-[9px] uppercase tracking-wider" style={{ color: "var(--color-text-faint)" }}>
                rolling attack window
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
