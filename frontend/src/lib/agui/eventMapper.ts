/**
 * AG-UI Event Mapper (Hardened)
 * 
 * Maps existing SSE events to AG-UI protocol standard events.
 * This adapter allows gradual migration to AG-UI without backend changes.
 * 
 * Hardening includes:
 * - Strict type guards for all payload fields
 * - Null/undefined safety
 * - Error recovery with fallbacks
 * - Payload validation
 * - Event sequence tracking
 * 
 * Reference: https://docs.ag-ui.com/
 */

import type { AgentStreamEnvelope } from '../agentStream';

// =============================================================================
// AG-UI Standard Event Types
// =============================================================================

export enum AguiEventType {
    // Lifecycle events
    RUN_STARTED = 'RUN_STARTED',
    RUN_FINISHED = 'RUN_FINISHED',
    RUN_ERROR = 'RUN_ERROR',

    // Message events
    TEXT_MESSAGE_START = 'TEXT_MESSAGE_START',
    TEXT_MESSAGE_CONTENT = 'TEXT_MESSAGE_CONTENT',
    TEXT_MESSAGE_END = 'TEXT_MESSAGE_END',

    // Tool events
    TOOL_CALL_START = 'TOOL_CALL_START',
    TOOL_CALL_ARGS = 'TOOL_CALL_ARGS',
    TOOL_CALL_END = 'TOOL_CALL_END',

    // State events
    STATE_SNAPSHOT = 'STATE_SNAPSHOT',
    STATE_DELTA = 'STATE_DELTA',

    // Raw/Custom events (passthrough)
    RAW = 'RAW',
    CUSTOM = 'CUSTOM',
}

// =============================================================================
// SSE to AG-UI Event Mapping Table
// =============================================================================

const SSE_TO_AGUI_MAP: Readonly<Record<string, AguiEventType>> = Object.freeze({
    // Core agent events
    'agent.session': AguiEventType.RUN_STARTED,
    'agent.thinking': AguiEventType.TEXT_MESSAGE_START,
    'agent.delta': AguiEventType.TEXT_MESSAGE_CONTENT,
    'agent.message': AguiEventType.TEXT_MESSAGE_END,
    'agent.tool_calls': AguiEventType.TOOL_CALL_START,
    'agent.tool_result': AguiEventType.TOOL_CALL_END,
    'agent.artifact_update': AguiEventType.STATE_DELTA,
    'agent.error': AguiEventType.RUN_ERROR,
    'agent.done': AguiEventType.RUN_FINISHED,

    // Teaching tool events
    'agent.teaching_start': AguiEventType.TOOL_CALL_START,
    'agent.teaching_complete': AguiEventType.TOOL_CALL_END,
    'agent.teaching_error': AguiEventType.RUN_ERROR,

    // Canvas events
    'agent.node_created': AguiEventType.STATE_DELTA,
    'agent.canvas_update': AguiEventType.STATE_DELTA,
});

// =============================================================================
// Type Guards (Hardened)
// =============================================================================

function isString(value: unknown): value is string {
    return typeof value === 'string';
}

function isNonEmptyString(value: unknown): value is string {
    return typeof value === 'string' && value.length > 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function safeString(value: unknown, fallback = ''): string {
    return isString(value) ? value : fallback;
}

function safeRecord(value: unknown): Record<string, unknown> {
    return isRecord(value) ? value : {};
}

// =============================================================================
// AG-UI Event Interface
// =============================================================================

export interface AguiEvent {
    /** Original SSE event (preserved for debugging) */
    readonly original: AgentStreamEnvelope;

    /** AG-UI mapped event type */
    readonly aguiType: AguiEventType;

    /** Original SSE event type (for custom handling) */
    readonly sseType: string;

    /** Session ID from envelope */
    readonly sessionId: string;

    /** Sequence number from envelope */
    readonly seq: number;

    /** Timestamp from envelope */
    readonly timestamp: string;

    // AG-UI standard fields (optional based on event type)
    readonly messageId?: string;
    readonly toolCallId?: string;
    readonly toolName?: string;
    readonly delta?: string;
    readonly content?: string;
    readonly error?: string;
    readonly state?: Record<string, unknown>;
    readonly toolCalls?: unknown[];

    /** Whether this event was successfully mapped */
    readonly mapped: boolean;

    /** Validation errors if any */
    readonly validationErrors: readonly string[];
}

// =============================================================================
// Event Mapper (Hardened)
// =============================================================================

/**
 * Maps an SSE event to AG-UI format with validation and error recovery
 */
export function mapToAgui(event: AgentStreamEnvelope | null | undefined): AguiEvent {
    // Handle null/undefined input
    if (!event) {
        return createErrorEvent('Null or undefined event received');
    }

    // Validate envelope structure
    const validationErrors: string[] = [];

    if (!isNonEmptyString(event.type)) {
        validationErrors.push('Missing or invalid event type');
    }

    if (!isNonEmptyString(event.session_id)) {
        validationErrors.push('Missing session_id');
    }

    const sseType = safeString(event.type, 'unknown');
    const aguiType = SSE_TO_AGUI_MAP[sseType] ?? AguiEventType.CUSTOM;
    const payload = safeRecord(event.payload);

    const result: AguiEvent = {
        original: event,
        aguiType,
        sseType,
        sessionId: safeString(event.session_id),
        seq: typeof event.seq === 'number' ? event.seq : 0,
        timestamp: safeString(event.ts, new Date().toISOString()),
        mapped: aguiType !== AguiEventType.CUSTOM,
        validationErrors: Object.freeze(validationErrors),
    };

    // Extract fields based on event type with strict validation
    return enrichEventFields(result, aguiType, payload);
}

/**
 * Enrich event with type-specific fields
 */
function enrichEventFields(
    base: AguiEvent,
    aguiType: AguiEventType,
    payload: Record<string, unknown>
): AguiEvent {
    switch (aguiType) {
        case AguiEventType.RUN_STARTED:
            return {
                ...base,
                state: payload,
            };

        case AguiEventType.TEXT_MESSAGE_START:
            return {
                ...base,
                messageId: safeString(payload.message_id),
            };

        case AguiEventType.TEXT_MESSAGE_CONTENT:
            return {
                ...base,
                messageId: safeString(payload.message_id),
                delta: safeString(payload.delta),
            };

        case AguiEventType.TEXT_MESSAGE_END:
            return {
                ...base,
                messageId: safeString(payload.message_id),
                content: safeString(payload.content),
                toolCalls: Array.isArray(payload.tool_calls) ? payload.tool_calls : undefined,
            };

        case AguiEventType.TOOL_CALL_START:
            return {
                ...base,
                messageId: safeString(payload.message_id),
                toolCalls: Array.isArray(payload.tool_calls) ? payload.tool_calls : undefined,
                toolName: safeString(payload.tool_name) || safeString(payload.name),
            };

        case AguiEventType.TOOL_CALL_END:
            return {
                ...base,
                toolCallId: safeString(payload.tool_call_id),
                toolName: safeString(payload.name),
                state: payload, // Full result as state
            };

        case AguiEventType.STATE_DELTA:
            return {
                ...base,
                state: payload,
            };

        case AguiEventType.RUN_ERROR:
            return {
                ...base,
                error: safeString(payload.error, 'Unknown error'),
            };

        case AguiEventType.RUN_FINISHED:
            return {
                ...base,
                state: payload,
            };

        default:
            return {
                ...base,
                state: payload,
            };
    }
}

/**
 * Create an error event for invalid input
 */
function createErrorEvent(errorMessage: string): AguiEvent {
    const now = new Date().toISOString();
    return {
        original: {
            event_id: `error-${Date.now()}`,
            session_id: '',
            type: 'error',
            seq: 0,
            ts: now,
            payload: { error: errorMessage },
        },
        aguiType: AguiEventType.RUN_ERROR,
        sseType: 'error',
        sessionId: '',
        seq: 0,
        timestamp: now,
        error: errorMessage,
        mapped: false,
        validationErrors: Object.freeze([errorMessage]),
    };
}

// =============================================================================
// Type Guard Functions (Exported)
// =============================================================================

const LIFECYCLE_EVENTS = Object.freeze([
    AguiEventType.RUN_STARTED,
    AguiEventType.RUN_FINISHED,
    AguiEventType.RUN_ERROR,
]);

const MESSAGE_EVENTS = Object.freeze([
    AguiEventType.TEXT_MESSAGE_START,
    AguiEventType.TEXT_MESSAGE_CONTENT,
    AguiEventType.TEXT_MESSAGE_END,
]);

const TOOL_EVENTS = Object.freeze([
    AguiEventType.TOOL_CALL_START,
    AguiEventType.TOOL_CALL_ARGS,
    AguiEventType.TOOL_CALL_END,
]);

const STATE_EVENTS = Object.freeze([
    AguiEventType.STATE_SNAPSHOT,
    AguiEventType.STATE_DELTA,
]);

/**
 * Check if event is an AG-UI lifecycle event
 */
export function isLifecycleEvent(event: AguiEvent): boolean {
    return LIFECYCLE_EVENTS.includes(event.aguiType);
}

/**
 * Check if event is an AG-UI message event
 */
export function isMessageEvent(event: AguiEvent): boolean {
    return MESSAGE_EVENTS.includes(event.aguiType);
}

/**
 * Check if event is an AG-UI tool event
 */
export function isToolEvent(event: AguiEvent): boolean {
    return TOOL_EVENTS.includes(event.aguiType);
}

/**
 * Check if event is an AG-UI state event
 */
export function isStateEvent(event: AguiEvent): boolean {
    return STATE_EVENTS.includes(event.aguiType);
}

/**
 * Check if event is a custom/unmapped event
 */
export function isCustomEvent(event: AguiEvent): boolean {
    return event.aguiType === AguiEventType.CUSTOM || event.aguiType === AguiEventType.RAW;
}

/**
 * Check if event has validation errors
 */
export function hasValidationErrors(event: AguiEvent): boolean {
    return event.validationErrors.length > 0;
}

/**
 * Check if event was successfully mapped to AG-UI
 */
export function isMappedEvent(event: AguiEvent): boolean {
    return event.mapped && !hasValidationErrors(event);
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Get SSE event type from AG-UI event
 */
export function getOriginalSseType(event: AguiEvent): string {
    return event.sseType;
}

/**
 * Check if SSE event type is known/mapped
 */
export function isKnownSseType(sseType: string): boolean {
    return sseType in SSE_TO_AGUI_MAP;
}

/**
 * Get all supported SSE event types
 */
export function getSupportedSseTypes(): readonly string[] {
    return Object.freeze(Object.keys(SSE_TO_AGUI_MAP));
}

/**
 * Get AG-UI type for SSE type (without creating full event)
 */
export function getAguiTypeForSse(sseType: string): AguiEventType {
    return SSE_TO_AGUI_MAP[sseType] ?? AguiEventType.CUSTOM;
}
