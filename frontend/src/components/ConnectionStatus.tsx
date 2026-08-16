"use client";

import { useRadarStore } from "@/store/useRadarStore";
import type { ConnectionState } from "@/lib/types";

const LABELS: Record<ConnectionState, string> = {
  CONNECTED: "Connected",
  RECONNECTING: "Reconnecting",
  OFFLINE: "Offline",
};

export default function ConnectionStatus() {
  const connectionState = useRadarStore((s) => s.connectionState);
  const reconnectAttempts = useRadarStore((s) => s.reconnectAttempts);
  const lastConnectedAt = useRadarStore((s) => s.lastConnectedAt);

  const dotClass =
    connectionState === "CONNECTED"
      ? "status-dot status-dot--connected"
      : connectionState === "RECONNECTING"
        ? "status-dot status-dot--reconnecting"
        : "status-dot status-dot--offline";

  let label = LABELS[connectionState];
  if (connectionState === "RECONNECTING" && reconnectAttempts > 0) {
    label += ` (${reconnectAttempts})`;
  }

  return (
    <div className="flex items-center gap-2" role="status" aria-live="polite">
      <span className={dotClass} aria-hidden="true" />
      <span className="font-mono text-[11px] tracking-wider uppercase" style={{
        color: connectionState === "CONNECTED"
          ? "var(--color-severity-low)"
          : connectionState === "OFFLINE"
            ? "var(--color-severity-critical)"
            : "var(--color-text-muted)",
      }}>
        {label}
      </span>
      {connectionState === "OFFLINE" && lastConnectedAt && (
        <span className="font-mono text-[10px]" style={{ color: "var(--color-text-faint)" }}>
          Last: {new Date(lastConnectedAt).toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}
