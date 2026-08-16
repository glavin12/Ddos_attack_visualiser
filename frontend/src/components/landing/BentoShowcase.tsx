import Image from "next/image";

interface BentoCell {
  id: string;
  title: string;
  body: string;
  gradient: string;
  textAccent: string;
  span?: "wide" | "normal";
  stat?: { label: string; value: string };
}

const CELLS: BentoCell[] = [
  {
    id: "globe",
    title: "Real-Time Globe",
    body: "Rotate an interactive 3D globe to trace attack routes as they happen. Severity-graded arcs show threat intensity at a glance.",
    gradient: "radial-gradient(ellipse 80% 70% at 20% 30%, rgba(0,217,255,0.12) 0%, rgba(8,18,28,0.6) 100%)",
    textAccent: "var(--color-signal-cyan)",
    span: "wide",
    stat: { label: "Attack routes visible", value: "Up to 30" },
  },
  {
    id: "analytics",
    title: "Attack Analytics",
    body: "See top attacking countries, severity distribution, and attack type breakdown in live-updating panels.",
    gradient: "linear-gradient(135deg, rgba(255,59,78,0.08) 0%, rgba(8,18,28,0.8) 100%)",
    textAccent: "var(--color-severity-high)",
    stat: { label: "Attack types tracked", value: "7+" },
  },
  {
    id: "metrics",
    title: "Live Metrics Bar",
    body: "Six key network health indicators including total traffic, blocked attacks, and country count with inline sparklines.",
    gradient: "linear-gradient(135deg, rgba(18,200,176,0.08) 0%, rgba(8,18,28,0.8) 100%)",
    textAccent: "var(--color-severity-low)",
    stat: { label: "Metrics tracked", value: "6 live" },
  },
];

export default function BentoShowcase() {
  return (
    <section
      className="relative py-20 px-6"
      style={{ backgroundColor: "var(--color-void)" }}
      aria-labelledby="bento-heading"
    >
      <div className="max-w-6xl mx-auto">
        <h2
          id="bento-heading"
          className="font-space font-bold text-center mb-3"
          style={{
            fontSize: "clamp(24px, 3vw, 36px)",
            color: "#FFFFFF",
            textWrap: "balance",
          }}
        >
          Everything in one view
        </h2>
        <p
          className="font-plex text-center mb-12"
          style={{
            fontSize: 15,
            color: "var(--color-text-muted)",
            maxWidth: 480,
            margin: "0 auto 48px",
            textWrap: "balance",
          }}
        >
          Designed for security engineers who need full situational awareness without tab-switching.
        </p>

        {/* Bento grid: 2-column, first cell spans both on desktop */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Wide cell — spans full width */}
          <div
            className="relative rounded-xl overflow-hidden col-span-1 md:col-span-2"
            style={{
              background: CELLS[0].gradient,
              border: "1px solid rgba(0,217,255,0.2)",
              minHeight: 300,
            }}
          >
            {/* Screenshot fill */}
            <div className="flex flex-col md:flex-row h-full">
              <div className="flex-1 flex flex-col justify-between p-8">
                <div>
                  <h3
                    className="font-space text-[22px] font-bold mb-3"
                    style={{ color: CELLS[0].textAccent }}
                  >
                    {CELLS[0].title}
                  </h3>
                  <p
                    className="font-plex text-[14px] leading-relaxed"
                    style={{ color: "var(--color-text-muted)", maxWidth: 360 }}
                  >
                    {CELLS[0].body}
                  </p>
                </div>
                {CELLS[0].stat && (
                  <div className="mt-6">
                    <span
                      className="font-mono text-[32px] font-bold"
                      style={{ color: CELLS[0].textAccent }}
                    >
                      {CELLS[0].stat.value}
                    </span>
                    <p
                      className="font-mono text-[10px] uppercase tracking-wider mt-1"
                      style={{ color: "var(--color-text-faint)" }}
                    >
                      {CELLS[0].stat.label}
                    </p>
                  </div>
                )}
              </div>
              {/* Dashboard screenshot */}
              <div className="flex-1 relative min-h-48">
                <Image
                  src="/hero-dashboard.jpg"
                  alt="DDoS Sentinel dashboard globe view"
                  fill
                  className="object-cover object-left"
                  style={{ opacity: 0.7 }}
                />
              </div>
            </div>
          </div>

          {/* Normal cells */}
          {CELLS.slice(1).map((cell) => (
            <div
              key={cell.id}
              className="relative rounded-xl p-8 flex flex-col justify-between"
              style={{
                background: cell.gradient,
                border: "1px solid rgba(60, 130, 150, 0.18)",
                minHeight: 220,
              }}
            >
              <div>
                <h3
                  className="font-space text-[18px] font-bold mb-3"
                  style={{ color: cell.textAccent }}
                >
                  {cell.title}
                </h3>
                <p
                  className="font-plex text-[13px] leading-relaxed"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  {cell.body}
                </p>
              </div>
              {cell.stat && (
                <div className="mt-6">
                  <span
                    className="font-mono text-[28px] font-bold"
                    style={{ color: cell.textAccent }}
                  >
                    {cell.stat.value}
                  </span>
                  <p
                    className="font-mono text-[10px] uppercase tracking-wider mt-1"
                    style={{ color: "var(--color-text-faint)" }}
                  >
                    {cell.stat.label}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
