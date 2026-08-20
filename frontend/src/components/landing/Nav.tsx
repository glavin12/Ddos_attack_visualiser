import Link from "next/link";

export default function Nav() {
  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 landing-nav-blur"
      style={{ height: 64 }}
      aria-label="Site navigation"
    >
      {/* Brand */}
      <Link href="/" className="flex items-center gap-2.5 no-underline" aria-label="AEGIS home">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <polygon
            points="7,0.5 13.5,7 7,13.5 0.5,7"
            fill="none"
            stroke="var(--color-signal-cyan)"
            strokeWidth="1.2"
          />
          <polygon
            points="7,3.5 10.5,7 7,10.5 3.5,7"
            fill="var(--color-signal-cyan)"
            opacity="0.45"
          />
        </svg>
        <span
          className="font-space text-[13px] font-bold tracking-[0.14em] uppercase"
          style={{ color: "#FFFFFF" }}
        >
          AEGIS
        </span>
      </Link>

      {/* Nav links */}
      <div className="hidden md:flex items-center gap-8" role="list">
        <Link
          href="/dashboard"
          role="listitem"
          className="font-mono text-[11px] uppercase tracking-widest no-underline"
          style={{ color: "var(--color-text-muted)" }}
        >
          Dashboard
        </Link>
        <a
          href="#how-it-works"
          role="listitem"
          className="font-mono text-[11px] uppercase tracking-widest no-underline"
          style={{ color: "var(--color-text-muted)" }}
        >
          Methodology
        </a>
        <a
          href="https://github.com"
          role="listitem"
          className="font-mono text-[11px] uppercase tracking-widest no-underline"
          style={{ color: "var(--color-text-muted)" }}
          target="_blank"
          rel="noopener noreferrer"
        >
          Source
        </a>
      </div>

      {/* CTA */}
      <Link href="/dashboard" className="btn-primary text-[11px]">
        Open Dashboard
      </Link>
    </nav>
  );
}
