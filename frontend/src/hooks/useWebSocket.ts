"use client";

/**
 * useWebSocket Hook with Automatic Reconnection
 * 
 * Provides WebSocket connection with:
 * - Automatic reconnection with exponential backoff
 * - Connection state tracking
 * - TypeScript-safe message handling
 * 
 * @example
 * const { send, status, disconnect } = useWebSocket(
 *   `${WS_BASE}/ws/runs/${runId}`,
 *   {
 *     onMessage: (event) => console.log(event.data),
 *     onError: (error) => console.error(error),
 *     maxRetries: 3,
 *   }
 * );
 */

import { useEffect, useRef, useState, useCallback } from "react";

export type WebSocketStatus = "connecting" | "connected" | "disconnected" | "reconnecting" | "failed";

export interface UseWebSocketOptions {
    /** Callback when message is received */
    onMessage?: (event: MessageEvent) => void;
    /** Callback when connection opens */
    onOpen?: () => void;
    /** Callback when connection closes */
    onClose?: (event: CloseEvent) => void;
    /** Callback when error occurs */
    onError?: (error: Event) => void;
    /** Maximum number of reconnection attempts (default: 5) */
    maxRetries?: number;
    /** Initial retry delay in ms (default: 1000) */
    retryDelay?: number;
    /** Maximum retry delay in ms (default: 30000) */
    maxRetryDelay?: number;
    /** Whether to connect immediately (default: true) */
    autoConnect?: boolean;
}

export interface UseWebSocketReturn {
    /** Send a message through the WebSocket */
    send: (data: string | object) => void;
    /** Current connection status */
    status: WebSocketStatus;
    /** Disconnect the WebSocket */
    disconnect: () => void;
    /** Manually reconnect */
    reconnect: () => void;
    /** Number of retry attempts made */
    retryCount: number;
}

export function useWebSocket(
    url: string | null,
    options: UseWebSocketOptions = {}
): UseWebSocketReturn {
    const {
        onMessage,
        onOpen,
        onClose,
        onError,
        maxRetries = 5,
        retryDelay = 1000,
        maxRetryDelay = 30000,
        autoConnect = true,
    } = options;

    const [status, setStatus] = useState<WebSocketStatus>("disconnected");
    const [retryCount, setRetryCount] = useState(0);

    const wsRef = useRef<WebSocket | null>(null);
    const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
    const shouldReconnectRef = useRef(true);
    const connectRef = useRef<(() => void) | null>(null);

    const cleanup = useCallback(() => {
        if (retryTimeoutRef.current) {
            clearTimeout(retryTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    }, []);

    const connect = useCallback(() => {
        if (!url) return;

        cleanup();
        setStatus("connecting");

        try {
            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => {
                setStatus("connected");
                setRetryCount(0);
                onOpen?.();
            };

            ws.onmessage = (event) => {
                onMessage?.(event);
            };

            ws.onerror = (error) => {
                onError?.(error);
            };

            ws.onclose = (event) => {
                onClose?.(event);

                // Don't reconnect if it was a normal closure or we've exceeded retries
                if (!shouldReconnectRef.current || event.code === 1000) {
                    setStatus("disconnected");
                    return;
                }

                if (retryCount < maxRetries) {
                    setStatus("reconnecting");
                    const delay = Math.min(retryDelay * Math.pow(2, retryCount), maxRetryDelay);

                    retryTimeoutRef.current = setTimeout(() => {
                        setRetryCount((prev) => prev + 1);
                        connectRef.current?.();
                    }, delay);
                } else {
                    setStatus("failed");
                }
            };
        } catch (error) {
            console.error("WebSocket connection error:", error);
            setStatus("failed");
        }
    }, [url, cleanup, onOpen, onMessage, onClose, onError, retryCount, maxRetries, retryDelay, maxRetryDelay]);

    useEffect(() => {
        connectRef.current = connect;
    }, [connect]);

    const disconnect = useCallback(() => {
        shouldReconnectRef.current = false;
        cleanup();
        setStatus("disconnected");
        setRetryCount(0);
    }, [cleanup]);

    const reconnect = useCallback(() => {
        shouldReconnectRef.current = true;
        setRetryCount(0);
        connect();
    }, [connect]);

    const send = useCallback((data: string | object) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            const message = typeof data === "string" ? data : JSON.stringify(data);
            wsRef.current.send(message);
        } else {
            console.warn("WebSocket is not connected. Cannot send message.");
        }
    }, []);

    // Auto-connect on mount
    useEffect(() => {
        if (!autoConnect || !url) return;
        shouldReconnectRef.current = true;
        const timeout = setTimeout(() => {
            connectRef.current?.();
        }, 0);

        return () => {
            clearTimeout(timeout);
            shouldReconnectRef.current = false;
            cleanup();
        };
    }, [url, autoConnect, cleanup]);

    return {
        send,
        status,
        disconnect,
        reconnect,
        retryCount,
    };
}

export default useWebSocket;
