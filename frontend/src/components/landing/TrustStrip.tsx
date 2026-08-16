/**
 * TrustStrip — technology logos UNDER the hero, NOT inside it.
 * Logo-only, no category labels (taste-skill rule: "Logo wall = logo only").
 * Using inline SVG marks to avoid external image requests and ensure accuracy.
 */

// Clean wordmark-style SVG logos using text elements for accuracy
function CloudflareLogo() {
  return (
    <svg viewBox="0 0 130 30" fill="none" className="h-6 w-auto" aria-label="Cloudflare">
      <rect x="0" y="8" width="20" height="14" rx="7" fill="#F48120" opacity="0.9"/>
      <rect x="6" y="4" width="20" height="14" rx="7" fill="#F48120" opacity="0.6"/>
      <text x="28" y="21" fontFamily="system-ui, sans-serif" fontSize="13" fontWeight="700" fill="#F48120" letterSpacing="0.5">Cloudflare</text>
    </svg>
  );
}

function NextjsLogo() {
  return (
    <svg viewBox="0 0 80 24" fill="none" className="h-5 w-auto" aria-label="Next.js">
      <circle cx="12" cy="12" r="11" fill="#000" stroke="#fff" strokeWidth="1.5" opacity="0.7"/>
      <path d="M8 16V8l8 10" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
      <path d="M14 8h2" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
      <text x="28" y="17" fontFamily="system-ui, sans-serif" fontSize="13" fontWeight="700" fill="white" opacity="0.7">Next.js</text>
    </svg>
  );
}

function ThreeLogo() {
  return (
    <svg viewBox="0 0 80 24" fill="none" className="h-5 w-auto" aria-label="Three.js">
      <path d="M6 4 L18 20 L6 20 Z" fill="none" stroke="white" strokeWidth="1.5" opacity="0.65"/>
      <text x="26" y="17" fontFamily="system-ui, sans-serif" fontSize="13" fontWeight="700" fill="white" opacity="0.65">Three.js</text>
    </svg>
  );
}

function FastAPILogo() {
  return (
    <svg viewBox="0 0 85 24" fill="none" className="h-5 w-auto" aria-label="FastAPI">
      <circle cx="12" cy="12" r="10" fill="#009485" opacity="0.85"/>
      <path d="M12 5 L7 13 L11.5 13 L10 19 L16 11 L11.5 11 Z" fill="white"/>
      <text x="27" y="17" fontFamily="system-ui, sans-serif" fontSize="13" fontWeight="700" fill="#009485" opacity="0.9">FastAPI</text>
    </svg>
  );
}

function TypeScriptLogo() {
  return (
    <svg viewBox="0 0 100 24" fill="none" className="h-5 w-auto" aria-label="TypeScript">
      <rect x="1" y="2" width="20" height="20" rx="3" fill="#3178C6" opacity="0.85"/>
      <text x="5" y="17" fontFamily="system-ui, sans-serif" fontSize="11" fontWeight="900" fill="white">TS</text>
      <text x="27" y="17" fontFamily="system-ui, sans-serif" fontSize="13" fontWeight="700" fill="#3178C6" opacity="0.85">TypeScript</text>
    </svg>
  );
}

function ZustandLogo() {
  return (
    <svg viewBox="0 0 85 24" fill="none" className="h-5 w-auto" aria-label="Zustand">
      <circle cx="12" cy="12" r="9" fill="none" stroke="rgba(215,229,234,0.5)" strokeWidth="1.5"/>
      <circle cx="12" cy="9" r="3" fill="rgba(215,229,234,0.5)"/>
      <path d="M5 18 Q12 14 19 18" stroke="rgba(215,229,234,0.5)" strokeWidth="1.5" fill="none"/>
      <text x="26" y="17" fontFamily="system-ui, sans-serif" fontSize="13" fontWeight="600" fill="rgba(215,229,234,0.65)">Zustand</text>
    </svg>
  );
}

export default function TrustStrip() {
  return (
    <section
      className="relative py-10"
      style={{ borderTop: "1px solid var(--color-hairline)" }}
      aria-label="Built with"
    >
      <div className="max-w-5xl mx-auto px-6">
        <p
          className="font-mono text-[10px] uppercase tracking-[0.18em] text-center mb-8"
          style={{ color: "var(--color-text-faint)" }}
        >
          Built on
        </p>

        <div className="flex flex-wrap items-center justify-center gap-10 md:gap-14">
          <CloudflareLogo />
          <NextjsLogo />
          <ThreeLogo />
          <FastAPILogo />
          <TypeScriptLogo />
          <ZustandLogo />
        </div>
      </div>
    </section>
  );
}
