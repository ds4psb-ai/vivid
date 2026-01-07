/**
 * P2-1: SSE Event Buffer and Parser Utilities
 * 
 * Provides robust SSE event handling with:
 * - Event buffering for sequence ordering
 * - Retry logic with exponential backoff
 * - Connection state management
 * - Error recovery
 */

// SSE Event Types (matching backend)
export type SSEEventType =
    | "agent.delta"
    | "agent.message"
    | "agent.tool_calls"
    | "agent.tool_result"
    | "agent.workflow_start"
    | "agent.workflow_step_start"
    | "agent.workflow_step_complete"
    | "agent.workflow_step_error"
    | "agent.workflow_complete"
    | "agent.workflow_created"
    | "agent.navigation"
    | "agent.error"
    | "content"  // Legacy format
    | "done";

export interface SSEEvent {
    type: SSEEventType;
    payload: Record<string, unknown>;
    seq?: number;
    timestamp?: number;
}

export interface EventHandlers {
    [key: string]: (payload: Record<string, unknown>) => void;
}

/**
 * SSE Event Buffer for ordered event processing
 * Ensures events are processed in sequence order even if they arrive out of order.
 */
export class SSEEventBuffer {
    private buffer: Map<number, SSEEvent> = new Map();
    private nextSeq: number = 1;
    private handlers: EventHandlers;
    private maxBufferSize: number = 100;
    private debug: boolean = false;

    constructor(handlers: EventHandlers, options?: { debug?: boolean; maxBufferSize?: number }) {
        this.handlers = handlers;
        if (options?.debug) this.debug = options.debug;
        if (options?.maxBufferSize) this.maxBufferSize = options.maxBufferSize;
    }

    /**
     * Push an event to the buffer
     * Processes immediately if in sequence, buffers otherwise
     */
    push(event: SSEEvent): void {
        const seq = event.seq;

        // If no sequence number, process immediately
        if (seq === undefined || seq === null) {
            this.process(event);
            return;
        }

        if (seq === this.nextSeq) {
            // Event is in sequence - process immediately
            this.process(event);
            this.nextSeq++;

            // Process any buffered events that are now in sequence
            this.drainBuffer();
        } else if (seq > this.nextSeq) {
            // Event is out of order - buffer it
            if (this.buffer.size < this.maxBufferSize) {
                this.buffer.set(seq, event);
                if (this.debug) {
                    console.debug(`[SSEBuffer] Buffered event seq=${seq}, expecting=${this.nextSeq}`);
                }
            } else {
                console.warn(`[SSEBuffer] Buffer full, dropping event seq=${seq}`);
            }
        }
        // seq < nextSeq: Duplicate event, ignore silently
    }

    /**
     * Drain buffered events in sequence order
     */
    private drainBuffer(): void {
        while (this.buffer.has(this.nextSeq)) {
            const buffered = this.buffer.get(this.nextSeq)!;
            this.buffer.delete(this.nextSeq);
            this.process(buffered);
            this.nextSeq++;
        }
    }

    /**
     * Process a single event by calling its handler
     */
    private process(event: SSEEvent): void {
        const handler = this.handlers[event.type];
        if (handler) {
            try {
                handler(event.payload);
            } catch (error) {
                console.error(`[SSEBuffer] Handler error for ${event.type}:`, error);
            }
        } else if (this.debug) {
            console.debug(`[SSEBuffer] No handler for event type: ${event.type}`);
        }
    }

    /**
     * Reset the buffer (for new connections)
     */
    reset(): void {
        this.buffer.clear();
        this.nextSeq = 1;
    }

    /**
     * Get buffer stats for debugging
     */
    getStats(): { bufferedCount: number; nextSeq: number } {
        return {
            bufferedCount: this.buffer.size,
            nextSeq: this.nextSeq,
        };
    }
}

/**
 * Parse SSE data line into typed event
 */
export function parseSSEEvent(data: string): SSEEvent | null {
    if (!data || data === '[DONE]') return null;

    try {
        const parsed = JSON.parse(data);
        if (!parsed || typeof parsed !== 'object') return null;

        return {
            type: parsed.type || 'unknown',
            payload: parsed.payload || parsed,
            seq: parsed.seq,
            timestamp: parsed.timestamp || Date.now(),
        };
    } catch (error) {
        console.debug('[SSE] Parse error:', error);
        return null;
    }
}

/**
 * Connection state for SSE streams
 */
export type SSEConnectionState =
    | "disconnected"
    | "connecting"
    | "connected"
    | "reconnecting"
    | "error";

/**
 * SSE Connection Manager with retry logic
 */
export class SSEConnectionManager {
    private state: SSEConnectionState = "disconnected";
    private retryCount: number = 0;
    private maxRetries: number = 3;
    private baseDelay: number = 1000;
    private controller: AbortController | null = null;
    private onStateChange?: (state: SSEConnectionState) => void;

    constructor(options?: {
        maxRetries?: number;
        baseDelay?: number;
        onStateChange?: (state: SSEConnectionState) => void;
    }) {
        if (options?.maxRetries) this.maxRetries = options.maxRetries;
        if (options?.baseDelay) this.baseDelay = options.baseDelay;
        this.onStateChange = options?.onStateChange;
    }

    /**
     * Get exponential backoff delay
     */
    getRetryDelay(): number {
        return this.baseDelay * Math.pow(2, this.retryCount);
    }

    /**
     * Check if should retry
     */
    shouldRetry(): boolean {
        return this.retryCount < this.maxRetries;
    }

    /**
     * Increment retry count and update state
     */
    incrementRetry(): void {
        this.retryCount++;
        this.setState("reconnecting");
    }

    /**
     * Reset retry count on successful connection
     */
    resetRetries(): void {
        this.retryCount = 0;
    }

    /**
     * Set connection state
     */
    setState(state: SSEConnectionState): void {
        this.state = state;
        this.onStateChange?.(state);
    }

    /**
     * Get current state
     */
    getState(): SSEConnectionState {
        return this.state;
    }

    /**
     * Get abort controller for current request
     */
    getAbortController(): AbortController {
        this.controller = new AbortController();
        return this.controller;
    }

    /**
     * Abort current connection
     */
    abort(): void {
        this.controller?.abort();
        this.controller = null;
        this.setState("disconnected");
    }

    /**
     * Check if connection is active
     */
    isConnected(): boolean {
        return this.state === "connected";
    }
}

/**
 * Session restoration utilities
 */
export interface StoredSession {
    sessionId: string;
    messages: Array<{
        id: string;
        role: string;
        content: string;
        timestamp: string;
        toolName?: string;
        toolStatus?: string;
    }>;
    lastActive: string;
}

const SESSION_STORAGE_KEY = "vivid_agent_session";
const SESSION_MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Save session to localStorage
 */
export function saveSession(sessionId: string, messages: unknown[]): void {
    try {
        const session: StoredSession = {
            sessionId,
            messages: messages.map((m: unknown) => {
                const msg = m as Record<string, unknown>;
                return {
                    id: String(msg.id || ''),
                    role: String(msg.role || ''),
                    content: typeof msg.content === 'string' ? msg.content : '',
                    timestamp: msg.timestamp instanceof Date
                        ? msg.timestamp.toISOString()
                        : String(msg.timestamp || ''),
                    toolName: msg.toolName ? String(msg.toolName) : undefined,
                    toolStatus: msg.toolStatus ? String(msg.toolStatus) : undefined,
                };
            }),
            lastActive: new Date().toISOString(),
        };
        localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
    } catch (error) {
        console.warn('[Session] Failed to save:', error);
    }
}

/**
 * Load session from localStorage
 */
export function loadSession(): StoredSession | null {
    try {
        const stored = localStorage.getItem(SESSION_STORAGE_KEY);
        if (!stored) return null;

        const session: StoredSession = JSON.parse(stored);

        // Check if session is too old
        const lastActive = new Date(session.lastActive).getTime();
        const now = Date.now();
        if (now - lastActive > SESSION_MAX_AGE_MS) {
            clearSession();
            return null;
        }

        return session;
    } catch (error) {
        console.warn('[Session] Failed to load:', error);
        return null;
    }
}

/**
 * Clear stored session
 */
export function clearSession(): void {
    try {
        localStorage.removeItem(SESSION_STORAGE_KEY);
    } catch (error) {
        console.warn('[Session] Failed to clear:', error);
    }
}

/**
 * Check if session exists and is valid
 */
export function hasValidSession(): boolean {
    return loadSession() !== null;
}
