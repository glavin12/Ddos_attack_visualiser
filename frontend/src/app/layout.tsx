import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";

/* ─── Typography — technical SOC font stack ─── */
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600"],
  variable: "--font-space",
  display: "swap",
});

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

/* ─── SEO metadata ─── */
export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: "DDoS Sentinel — Network Security Operations",
  description:
    "Real-time global DDoS attack visualization powered by Cloudflare Radar telemetry. Interactive 3D globe with live attack routes, severity analysis, and network security analytics.",
  keywords: [
    "DDoS",
    "cybersecurity",
    "network security",
    "SOC",
    "attack visualization",
    "Cloudflare Radar",
    "security operations",
    "attack map",
  ],
  robots: "index, follow",
  openGraph: {
    title: "DDoS Sentinel",
    description: "Real-time global DDoS attack visualization",
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
      className={`${spaceGrotesk.variable} ${ibmPlexSans.variable} ${jetbrainsMono.variable}`}
    >
      <head>
        <meta name="theme-color" content="#03070B" />
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
