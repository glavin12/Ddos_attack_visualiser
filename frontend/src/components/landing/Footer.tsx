import Link from "next/link";

export default function Footer() {
  return (
    <footer
      className="relative landing-section"
      style={{ borderTop: "1px solid var(--color-hairline)" }}
      aria-label="Site footer"
    >
      {/* Final CTA section */}
      <div
        className="py-20 px-6 text-center"
        style={{
          background:
            "radial-gradient(ellipse 50% 80% at 50% 0%, rgba(0,217,255,0.06) 0%, transparent 70%)",
        }}
      >
        <h2
          className="font-space font-bold mb-4"
          style={{
            fontSize: "clamp(22px, 3vw, 36px)",
            color: "#FFFFFF",
            textWrap: "balance",
          }}
        >
          Start monitoring now
        </h2>
        <p
          className="font-plex mb-8"
          style={{
            fontSize: 15,
            color: "var(--color-text-muted)",
            maxWidth: 400,
            margin: "0 auto 32px",
            textWrap: "balance",
          }}
        >
          No account. No signup. Open the dashboard and see the global DDoS landscape in seconds.
        </p>
        <Link
          href="/dashboard"
          className="btn-primary text-[13px]"
          id="footer-cta"
        >
          Open Dashboard
        </Link>
      </div>

      {/* Footer links */}
      <div
        className="px-6 py-8"
        style={{ borderTop: "1px solid var(--color-hairline)" }}
      >
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
              <polygon points="6,0.5 11.5,6 6,11.5 0.5,6" fill="none" stroke="var(--color-signal-cyan)" strokeWidth="1.2"/>
              <polygon points="6,3 9,6 6,9 3,6" fill="var(--color-signal-cyan)" opacity="0.4"/>
            </svg>
            <span
              className="font-mono text-[10px] uppercase tracking-wider"
              style={{ color: "var(--color-text-faint)" }}
            >
              AEGIS
            </span>
          </div>

          {/* Links */}
          <nav aria-label="Footer navigation">
            <ul className="flex items-center gap-6 list-none">
              <li>
                <a
                  href="#how-it-works"
                  className="font-mono text-[10px] uppercase tracking-wider no-underline"
                  style={{ color: "var(--color-text-faint)" }}
                >
                  Methodology
                </a>
              </li>
              <li>
                <Link
                  href="/dashboard"
                  className="font-mono text-[10px] uppercase tracking-wider no-underline"
                  style={{ color: "var(--color-text-faint)" }}
                >
                  Dashboard
                </Link>
              </li>
              <li>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[10px] uppercase tracking-wider no-underline"
                  style={{ color: "var(--color-text-faint)" }}
                >
                  GitHub
                </a>
              </li>
              <li>
                <a
                  href="https://radar.cloudflare.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[10px] uppercase tracking-wider no-underline"
                  style={{ color: "var(--color-text-faint)" }}
                >
                  Data Source
                </a>
              </li>
            </ul>
          </nav>

          {/* Copyright */}
          <p
            className="font-mono text-[10px]"
            style={{ color: "var(--color-text-faint)" }}
          >
            Built with Cloudflare Radar API
          </p>
        </div>
      </div>
    </footer>
  );
}
