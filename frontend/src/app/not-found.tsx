import Link from "next/link";

export default function NotFound() {
  return (
    <div
      className="flex flex-col items-center justify-center min-h-[100dvh] px-6 text-center"
      style={{ backgroundColor: "var(--color-void)" }}
    >
      <p
        className="font-mono text-[12px] tracking-widest uppercase mb-3"
        style={{ color: "var(--color-signal-cyan)" }}
      >
        404 / Signal lost
      </p>
      <h1
        className="font-space text-3xl font-semibold mb-3"
        style={{ color: "var(--color-text-primary)" }}
      >
        This route is not in the observation window
      </h1>
      <p
        className="font-sans text-[14px] max-w-md leading-relaxed mb-6"
        style={{ color: "var(--color-text-muted)" }}
      >
        The page you are looking for does not exist or has been moved. Return
        to the dashboard to resume telemetry.
      </p>
      <Link
        href="/"
        className="px-4 py-2 font-mono text-[12px] font-bold uppercase rounded transition-colors"
        style={{
          color: "var(--color-signal-cyan)",
          backgroundColor: "rgba(47, 209, 224, 0.1)",
          border: "1px solid rgba(47, 209, 224, 0.4)",
        }}
      >
        Return to dashboard
      </Link>
    </div>
  );
}
