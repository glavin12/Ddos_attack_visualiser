const STEPS = [
  {
    n: "01",
    title: "Ingest",
    body: "Cloudflare Radar's aggregate DDoS telemetry is polled on a scheduled cadence, normalized, and stored — top attack routes across 100+ countries, never invented.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5"/>
        <path d="M6 10 L10 6 L14 10 M10 6 L10 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    color: "var(--color-signal-cyan)",
  },
  {
    n: "02",
    title: "Visualize",
    body: "Each top route is drawn as a comet arc on a live 3D globe — brighter arcs carry a larger share of attack traffic — and the backend streams every update to open dashboards.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5"/>
        <circle cx="10" cy="10" r="4" stroke="currentColor" strokeWidth="1" opacity="0.5"/>
        <line x1="2" y1="10" x2="18" y2="10" stroke="currentColor" strokeWidth="1" opacity="0.4"/>
        <line x1="10" y1="2" x2="10" y2="18" stroke="currentColor" strokeWidth="1" opacity="0.4"/>
      </svg>
    ),
    color: "var(--color-severity-medium)",
  },
  {
    n: "03",
    title: "Analyze",
    body: "Side panels break down attack vectors, origin countries, and target distribution from the same rolling aggregates — refreshed automatically as new telemetry lands.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
        <rect x="2" y="14" width="3" height="4" rx="1" fill="currentColor" opacity="0.9"/>
        <rect x="7" y="10" width="3" height="8" rx="1" fill="currentColor" opacity="0.7"/>
        <rect x="12" y="6" width="3" height="12" rx="1" fill="currentColor" opacity="0.5"/>
        <rect x="17" y="2" width="1" height="16" rx="0.5" fill="currentColor" opacity="0.3"/>
      </svg>
    ),
    color: "var(--color-severity-low)",
  },
];

export default function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="relative py-20 px-6 landing-section"
      style={{ borderTop: "1px solid var(--color-hairline)" }}
      aria-labelledby="how-heading"
    >
      <div className="max-w-3xl mx-auto">
        {/* Eyebrow — exactly 2 of 2 allowed on this page */}
        <div className="flex items-center gap-3 mb-4">
          <div
            className="h-px flex-1"
            style={{ backgroundColor: "var(--color-hairline)" }}
            aria-hidden="true"
          />
          <span
            className="font-mono text-[10px] uppercase tracking-[0.18em]"
            style={{ color: "var(--color-text-faint)" }}
          >
            How it works
          </span>
          <div
            className="h-px flex-1"
            style={{ backgroundColor: "var(--color-hairline)" }}
            aria-hidden="true"
          />
        </div>

        <h2
          id="how-heading"
          className="font-space font-bold text-center mb-16"
          style={{
            fontSize: "clamp(22px, 3vw, 32px)",
            color: "#FFFFFF",
            textWrap: "balance",
          }}
        >
          From telemetry to situational awareness
        </h2>

        {/* Vertical step stack — no zigzag */}
        <ol className="space-y-0 list-none" role="list">
          {STEPS.map((step, i) => (
            <li
              key={step.n}
              className="flex gap-8 relative"
              role="listitem"
            >
              {/* Step number + connector line */}
              <div className="flex flex-col items-center shrink-0 w-10">
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center font-mono text-[13px] font-bold shrink-0"
                  style={{
                    backgroundColor: `color-mix(in srgb, ${step.color} 12%, transparent)`,
                    border: `1px solid color-mix(in srgb, ${step.color} 35%, transparent)`,
                    color: step.color,
                  }}
                  aria-hidden="true"
                >
                  {step.n}
                </div>
                {i < STEPS.length - 1 && (
                  <div
                    className="w-px flex-1 mt-2"
                    style={{
                      background: `linear-gradient(to bottom, color-mix(in srgb, ${step.color} 30%, transparent), transparent)`,
                      minHeight: 48,
                    }}
                    aria-hidden="true"
                  />
                )}
              </div>

              {/* Content */}
              <div className="pb-14 min-w-0 flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <span style={{ color: step.color }}>{step.icon}</span>
                  <h3
                    className="font-space text-[17px] font-bold"
                    style={{ color: "#FFFFFF" }}
                  >
                    {step.title}
                  </h3>
                </div>
                <p
                  className="font-plex text-[14px] leading-relaxed"
                  style={{ color: "var(--color-text-muted)", maxWidth: 520 }}
                >
                  {step.body}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
