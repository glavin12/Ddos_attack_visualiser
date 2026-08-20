export default function PullQuote() {
  return (
    <section
      className="relative py-20 px-6 landing-section"
      style={{
        background:
          "radial-gradient(ellipse 60% 80% at 50% 50%, rgba(0,217,255,0.04) 0%, transparent 70%)",
        borderTop: "1px solid var(--color-hairline)",
      }}
      aria-label="Design philosophy"
    >
      <div className="max-w-3xl mx-auto text-center">
        {/* Typographic open-quote mark */}
        <p
          className="font-space font-bold mb-6 leading-none"
          style={{ fontSize: 64, color: "var(--color-signal-cyan)", opacity: 0.25, lineHeight: 1 }}
          aria-hidden="true"
        >
          &quot;
        </p>

        <blockquote>
          <p
            className="font-space font-medium"
            style={{
              fontSize: "clamp(18px, 2.5vw, 26px)",
              lineHeight: 1.45,
              color: "var(--color-text-primary)",
              textWrap: "balance",
              letterSpacing: "-0.01em",
            }}
          >
            Honest data, honestly visualized.
            <br />
            <span style={{ color: "var(--color-text-muted)" }}>
              Cloudflare Radar sees it. We show it.
            </span>
          </p>

          <footer className="mt-8">
            <cite
              className="font-mono text-[11px] uppercase tracking-[0.16em] not-italic"
              style={{ color: "var(--color-text-faint)" }}
            >
              AEGIS project
            </cite>
          </footer>
        </blockquote>
      </div>
    </section>
  );
}
