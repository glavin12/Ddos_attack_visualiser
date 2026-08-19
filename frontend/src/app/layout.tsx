import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

/* ─── Typography — Geist Sans (UI) + Geist Mono (data/IPs/timestamps) ─── */
const geistSans = Geist({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-geist-sans",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-geist-mono",
  display: "swap",
});

/* ─── SEO metadata ─── */
export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: "Threat Observatory — Real-Time Global Threat Intelligence",
  description:
    "A live global threat-intelligence dashboard combining Cloudflare Radar's 24-hour DDoS attack aggregates with real malicious-infrastructure indicators from URLhaus, Feodo Tracker, and ThreatFox.",
  keywords: [
    "threat intelligence",
    "cybersecurity",
    "network security",
    "DDoS",
    "Cloudflare Radar",
    "URLhaus",
    "Feodo Tracker",
    "ThreatFox",
    "threat map",
    "security dashboard",
  ],
  robots: "index, follow",
  openGraph: {
    title: "Threat Observatory",
    description: "Real-time global threat intelligence, sourced honestly.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable}`}
    >
      <head>
        <meta name="theme-color" content="#020408" />
      </head>
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:rounded focus:font-mono focus:text-sm focus:font-bold"
          style={{ backgroundColor: "var(--color-signal-cyan)", color: "var(--color-void)" }}
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
