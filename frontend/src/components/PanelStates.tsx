"use client";

/**
 * Shared loading / error UI states for REST-driven panels.
 * Vercel parity: skeleton matches the final layout shape; errors
 * include a fix/next-step message and a retry affordance.
 */

export function SkeletonRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="px-3.5 py-3 space-y-3" aria-hidden="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="space-y-1.5">
          <div className="flex items-center justify-between gap-2">
            <div className="h-3 w-24 rounded bg-[var(--color-hairline)] animate-pulse" />
            <div className="h-3 w-10 rounded bg-[var(--color-hairline)] animate-pulse" />
          </div>
          <div className="h-1 w-full rounded bg-[var(--color-hairline)] animate-pulse" />
        </div>
      ))}
    </div>
  );
}

export function PanelError({
  message = "Failed to load data",
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2.5 px-4 py-6 text-center" role="alert">
      <span className="font-mono text-[11px]" style={{ color: "var(--color-text-muted)" }}>{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3 py-1 font-mono text-[11px] font-bold rounded cursor-pointer uppercase transition-colors"
          style={{
            color: "var(--color-signal-cyan)",
            border: "1px solid rgba(0, 217, 255, 0.4)",
            backgroundColor: "rgba(0, 217, 255, 0.1)",
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
