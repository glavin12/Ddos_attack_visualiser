import type { Metadata } from "next";
import Nav from "@/components/landing/Nav";
import Hero from "@/components/landing/Hero";
import TrustStrip from "@/components/landing/TrustStrip";
import BentoShowcase from "@/components/landing/BentoShowcase";
import HowItWorks from "@/components/landing/HowItWorks";
import PullQuote from "@/components/landing/PullQuote";
import Footer from "@/components/landing/Footer";

export const metadata: Metadata = {
  title: "DDoS Sentinel — Real-Time Attack Visualization",
  description:
    "See global DDoS attacks as they happen. Interactive 3D globe with severity-graded attack routes powered by Cloudflare Radar telemetry. Free and open source.",
  openGraph: {
    title: "DDoS Sentinel",
    description: "Real-time global DDoS attack visualization",
    images: [{ url: "/hero-dashboard.jpg", width: 1400, height: 787 }],
    type: "website",
  },
};

export default function LandingPage() {
  return (
    <div
      className="bg-starfield"
      style={{ minHeight: "100dvh", color: "var(--color-text-primary)" }}
    >
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:rounded focus:font-mono focus:text-sm focus:font-bold"
        style={{ backgroundColor: "var(--color-signal-cyan)", color: "var(--color-void)" }}
      >
        Skip to main content
      </a>

      {/* Navigation — fixed 64px */}
      <Nav />

      {/* Main content */}
      <main id="main-content">
        {/* 1. Hero — full viewport, asymmetric split */}
        <Hero />

        {/* 2. Trust strip — immediately below hero */}
        <TrustStrip />

        {/* 3. Bento showcase — "What it shows" */}
        <BentoShowcase />

        {/* 4. How it works — 3-step methodology */}
        <HowItWorks />

        {/* 5. Pull-quote */}
        <PullQuote />
      </main>

      {/* 6. Footer with final CTA */}
      <Footer />
    </div>
  );
}
