"use client";

import { useEffect, useRef, useCallback } from "react";
import { useRadarStore } from "@/store/useRadarStore";
import { WS_URL, WS_RECONNECT_BASE_MS, WS_RECONNECT_MAX_MS } from "@/lib/constants";
import type { WSMessage } from "@/lib/types";

/**
 * Native browser WebSocket hook.
 * Auto-reconnects with exponential backoff.
 * Dispatches parsed messages to the Zustand store.
 */
export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  // Selected individually (not destructured off the whole store) so this
  // hook never subscribes to unrelated state and doesn't force DashboardPage
  // to re-render on every store mutation.
  const setConnectionState = useRadarStore((s) => s.setConnectionState);
  const incrementReconnectAttempts = useRadarStore((s) => s.incrementReconnectAttempts);
  const resetReconnectAttempts = useRadarStore((s) => s.resetReconnectAttempts);
  const addIndicator = useRadarStore((s) => s.addIndicator);
  const setActiveIndicatorCount = useRadarStore((s) => s.setActiveIndicatorCount);

  // scheduleReconnect references connect and connect references
  // scheduleReconnect — resolve the cycle through a ref.
  const connectRef = useRef<() => void>(() => {});

  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current) return;
    setConnectionState("RECONNECTING");
    incrementReconnectAttempts();

    const attempt = useRadarStore.getState().reconnectAttempts;
    const delay = Math.min(
      WS_RECONNECT_BASE_MS * Math.pow(2, attempt),
      WS_RECONNECT_MAX_MS
    );

    reconnectTimerRef.current = setTimeout(() => {
      if (mountedRef.current) connectRef.current();
    }, delay);
  }, [setConnectionState, incrementReconnectAttempts]);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionState("RECONNECTING");

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setConnectionState("CONNECTED");
        resetReconnectAttempts();
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const msg: WSMessage = JSON.parse(event.data);
          switch (msg.type) {
            case "threat_indicator":
              addIndicator(msg.data);
              break;
            case "stats":
              setActiveIndicatorCount(msg.data.active_indicators);
              break;
            case "system":
              console.info("[WS system]", msg.data.message);
              break;
            default:
              // Unknown message types safely ignored.
              break;
          }
        } catch {
          // Malformed JSON — ignore
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        wsRef.current = null;
        scheduleReconnect();
      };

      ws.onerror = () => {
        // The close handler will fire after this
        ws.close();
      };
    } catch {
      scheduleReconnect();
    }
  }, [
    addIndicator,
    resetReconnectAttempts,
    scheduleReconnect,
    setActiveIndicatorCount,
    setConnectionState,
  ]);

  // Keep the ref pointing at the latest connect implementation.
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    mountedRef.current = true;
    connectRef.current();

    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
      setConnectionState("OFFLINE");
    };
  }, [setConnectionState]);
}
