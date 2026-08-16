"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          backgroundColor: "var(--color-void, #000308)",
          color: "#E8EFF8",
          fontFamily: "system-ui, sans-serif",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100dvh",
        }}
      >
        <div style={{ textAlign: "center", maxWidth: 420, padding: "0 24px" }}>
          <h1
            style={{
              fontSize: 18,
              fontFamily: "'Space Grotesk', sans-serif",
              marginBottom: 8,
            }}
          >
            Radar link lost
          </h1>
          <p style={{ fontSize: 13, opacity: 0.7, marginBottom: 20 }}>
            Something went wrong loading the dashboard. Refreshing usually
            restores the feed.
          </p>
          <button
            onClick={reset}
            style={{
              padding: "8px 16px",
              fontSize: 12,
              fontFamily: "monospace",
              fontWeight: 700,
              cursor: "pointer",
              color: "#2FD1E0",
              backgroundColor: "rgba(47, 209, 224, 0.1)",
              border: "1px solid rgba(47, 209, 224, 0.4)",
              borderRadius: 4,
              textTransform: "uppercase",
            }}
          >
            Retry
          </button>
        </div>
      </body>
    </html>
  );
}
