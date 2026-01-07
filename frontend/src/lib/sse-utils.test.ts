/**
 * P2 Hardening: Unit tests for sse-utils.ts
 */
import { describe, test, expect, beforeEach, vi } from 'vitest';
import {
    SSEEventBuffer,
    SSEConnectionManager,
    parseSSEEvent,
    saveSession,
    loadSession,
    clearSession,
    hasValidSession,
    type SSEEvent,
} from './sse-utils';

describe('SSEEventBuffer', () => {
    let handlers: Record<string, ReturnType<typeof vi.fn>>;
    let buffer: SSEEventBuffer;

    beforeEach(() => {
        handlers = {
            'agent.delta': vi.fn(),
            'agent.message': vi.fn(),
            'agent.tool_result': vi.fn(),
        };
        buffer = new SSEEventBuffer(handlers);
    });

    test('processes events without seq immediately', () => {
        const event: SSEEvent = { type: 'agent.delta', payload: { delta: 'hello' } };
        buffer.push(event);
        expect(handlers['agent.delta']).toHaveBeenCalledWith({ delta: 'hello' });
    });

    test('processes in-order events immediately', () => {
        buffer.push({ type: 'agent.delta', payload: { n: 1 }, seq: 1 });
        buffer.push({ type: 'agent.delta', payload: { n: 2 }, seq: 2 });
        buffer.push({ type: 'agent.delta', payload: { n: 3 }, seq: 3 });

        expect(handlers['agent.delta']).toHaveBeenCalledTimes(3);
    });

    test('buffers out-of-order events and drains correctly', () => {
        // Events arrive: 1, 3, 2
        buffer.push({ type: 'agent.delta', payload: { n: 1 }, seq: 1 });
        expect(handlers['agent.delta']).toHaveBeenCalledTimes(1);

        buffer.push({ type: 'agent.delta', payload: { n: 3 }, seq: 3 });
        expect(handlers['agent.delta']).toHaveBeenCalledTimes(1); // Still 1, seq 3 is buffered

        buffer.push({ type: 'agent.delta', payload: { n: 2 }, seq: 2 });
        expect(handlers['agent.delta']).toHaveBeenCalledTimes(3); // Now 2 and 3 are processed
    });

    test('ignores duplicate sequence numbers', () => {
        buffer.push({ type: 'agent.delta', payload: { n: 1 }, seq: 1 });
        buffer.push({ type: 'agent.delta', payload: { n: 1 }, seq: 1 }); // Duplicate

        expect(handlers['agent.delta']).toHaveBeenCalledTimes(1);
    });

    test('reset clears buffer and resets sequence', () => {
        buffer.push({ type: 'agent.delta', payload: { n: 1 }, seq: 1 });
        buffer.push({ type: 'agent.delta', payload: { n: 3 }, seq: 3 }); // Buffered

        buffer.reset();

        const stats = buffer.getStats();
        expect(stats.bufferedCount).toBe(0);
        expect(stats.nextSeq).toBe(1);
    });

    test('handles missing event handler gracefully', () => {
        const event: SSEEvent = { type: 'unknown.event' as any, payload: {} };
        expect(() => buffer.push(event)).not.toThrow();
    });
});

describe('SSEConnectionManager', () => {
    let manager: SSEConnectionManager;

    beforeEach(() => {
        manager = new SSEConnectionManager({ maxRetries: 3, baseDelay: 100 });
    });

    test('initial state is disconnected', () => {
        expect(manager.getState()).toBe('disconnected');
    });

    test('getRetryDelay returns exponential backoff', () => {
        expect(manager.getRetryDelay()).toBe(100); // 100 * 2^0
        manager.incrementRetry();
        expect(manager.getRetryDelay()).toBe(200); // 100 * 2^1
        manager.incrementRetry();
        expect(manager.getRetryDelay()).toBe(400); // 100 * 2^2
    });

    test('shouldRetry returns true until max retries', () => {
        expect(manager.shouldRetry()).toBe(true);
        manager.incrementRetry();
        expect(manager.shouldRetry()).toBe(true);
        manager.incrementRetry();
        expect(manager.shouldRetry()).toBe(true);
        manager.incrementRetry();
        expect(manager.shouldRetry()).toBe(false); // 3 retries exhausted
    });

    test('resetRetries resets counter', () => {
        manager.incrementRetry();
        manager.incrementRetry();
        manager.resetRetries();
        expect(manager.shouldRetry()).toBe(true);
        expect(manager.getRetryDelay()).toBe(100);
    });

    test('state change callback is called', () => {
        const onStateChange = vi.fn();
        const mgr = new SSEConnectionManager({ onStateChange });

        mgr.setState('connecting');
        expect(onStateChange).toHaveBeenCalledWith('connecting');

        mgr.setState('connected');
        expect(onStateChange).toHaveBeenCalledWith('connected');
    });
});

describe('parseSSEEvent', () => {
    test('parses valid JSON', () => {
        const data = JSON.stringify({ type: 'agent.delta', payload: { text: 'hi' }, seq: 1 });
        const event = parseSSEEvent(data);

        expect(event).not.toBeNull();
        expect(event?.type).toBe('agent.delta');
        expect(event?.payload).toEqual({ text: 'hi' });
        expect(event?.seq).toBe(1);
    });

    test('returns null for [DONE]', () => {
        expect(parseSSEEvent('[DONE]')).toBeNull();
    });

    test('returns null for empty string', () => {
        expect(parseSSEEvent('')).toBeNull();
    });

    test('returns null for invalid JSON', () => {
        expect(parseSSEEvent('not json')).toBeNull();
    });

    test('handles missing payload by using parsed object', () => {
        const data = JSON.stringify({ type: 'agent.message', content: 'hello' });
        const event = parseSSEEvent(data);

        expect(event?.payload).toEqual({ type: 'agent.message', content: 'hello' });
    });
});

describe('Session Storage', () => {
    // Skip these tests in Node.js environment (no localStorage)
    const isBrowser = typeof window !== 'undefined' && typeof localStorage !== 'undefined';

    beforeEach(() => {
        if (isBrowser) clearSession();
    });

    test.skipIf(!isBrowser)('saveSession and loadSession roundtrip', () => {
        const messages = [
            { id: 'msg-1', role: 'user', content: 'Hello', timestamp: new Date() },
            { id: 'msg-2', role: 'assistant', content: 'Hi there!', timestamp: new Date() },
        ];

        saveSession('session-123', messages);
        const loaded = loadSession();

        expect(loaded).not.toBeNull();
        expect(loaded?.sessionId).toBe('session-123');
        expect(loaded?.messages).toHaveLength(2);
    });

    test.skipIf(!isBrowser)('hasValidSession returns true after save', () => {
        saveSession('session-456', []);
        expect(hasValidSession()).toBe(true);
    });

    test.skipIf(!isBrowser)('clearSession removes data', () => {
        saveSession('session-789', []);
        clearSession();
        expect(hasValidSession()).toBe(false);
    });

    test.skipIf(!isBrowser)('loadSession returns null for expired session', () => {
        // Mock old session
        const oldSession = {
            sessionId: 'old-session',
            messages: [],
            lastActive: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(), // 25 hours ago
        };
        localStorage.setItem('vivid_agent_session', JSON.stringify(oldSession));

        expect(loadSession()).toBeNull();
    });
});
