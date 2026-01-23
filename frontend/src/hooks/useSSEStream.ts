"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface SSEEvent<T = unknown> {
  type: string;
  data: T;
  timestamp: number;
}

interface UseSSEStreamOptions {
  /** Auto-reconnect on disconnect (default: true) */
  reconnect?: boolean;
  /** Reconnection delay in ms (default: 3000) */
  reconnectDelay?: number;
  /** Max reconnection attempts (default: 5) */
  maxRetries?: number;
  /** Callback when connected */
  onConnect?: () => void;
  /** Callback when disconnected */
  onDisconnect?: () => void;
  /** Callback on error */
  onError?: (error: Error) => void;
}

interface UseSSEStreamReturn<T> {
  /** Latest event data */
  data: T | null;
  /** All events received */
  events: SSEEvent<T>[];
  /** Connection status */
  isConnected: boolean;
  /** Is currently reconnecting */
  isReconnecting: boolean;
  /** Connection error */
  error: Error | null;
  /** Manually connect */
  connect: () => void;
  /** Manually disconnect */
  disconnect: () => void;
}

/**
 * Hook for consuming Server-Sent Events (SSE) streams.
 *
 * @example
 * ```tsx
 * const { data, isConnected } = useSSEStream<KPIUpdate>(
 *   "/api/v1/analytics/stream/kpis",
 *   { reconnect: true }
 * );
 * ```
 */
export function useSSEStream<T = unknown>(
  url: string,
  options: UseSSEStreamOptions = {}
): UseSSEStreamReturn<T> {
  const {
    reconnect = true,
    reconnectDelay = 3000,
    maxRetries = 5,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [events, setEvents] = useState<SSEEvent<T>[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const retriesRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const connectRef = useRef<() => void>(() => {});

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsConnected(false);
    setIsReconnecting(false);
  }, [clearReconnectTimeout]);

  const connect = useCallback(() => {
    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setError(null);

    try {
      const eventSource = new EventSource(url, { withCredentials: true });
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setIsReconnecting(false);
        setError(null);
        retriesRef.current = 0;
        onConnect?.();
      };

      eventSource.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          const sseEvent: SSEEvent<T> = {
            type: parsed.type || "message",
            data: parsed.data ?? parsed,
            timestamp: Date.now(),
          };

          // Skip heartbeats from data updates
          if (parsed.type !== "heartbeat") {
            setData(sseEvent.data);
            setEvents((prev) => [...prev.slice(-99), sseEvent]);
          }
        } catch {
          // Handle non-JSON data
          console.warn("SSE: Failed to parse event data", event.data);
        }
      };

      eventSource.onerror = () => {
        const wasConnected = isConnected;
        setIsConnected(false);
        eventSource.close();
        eventSourceRef.current = null;

        if (wasConnected) {
          onDisconnect?.();
        }

        // Attempt reconnection
        if (reconnect && retriesRef.current < maxRetries) {
          setIsReconnecting(true);
          retriesRef.current += 1;

          const delay = reconnectDelay * Math.pow(2, retriesRef.current - 1);
          reconnectTimeoutRef.current = setTimeout(() => {
            connectRef.current();
          }, delay);
        } else if (retriesRef.current >= maxRetries) {
          const err = new Error(`SSE connection failed after ${maxRetries} retries`);
          setError(err);
          setIsReconnecting(false);
          onError?.(err);
        }
      };
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to create EventSource");
      setError(error);
      onError?.(error);
    }
  }, [url, reconnect, reconnectDelay, maxRetries, isConnected, onConnect, onDisconnect, onError]);

  // Keep ref in sync with latest connect function
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  // Auto-connect on mount
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    connect();
    return () => {
      disconnect();
    };
  }, [url]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    data,
    events,
    isConnected,
    isReconnecting,
    error,
    connect,
    disconnect,
  };
}

export default useSSEStream;
