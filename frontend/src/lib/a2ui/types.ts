/**
 * A2UI Type definitions
 * Based on Google A2UI specification
 */

export interface A2UIMessage {
    /** Unique identifier for this UI element */
    id: string;

    /** Widget type from the catalog */
    type: string;

    /** Properties passed to the widget */
    props?: Record<string, unknown>;

    /** Data model bindings (e.g., "$state.items") */
    dataModel?: {
        contents?: Record<string, unknown>;
        bindings?: Record<string, string>;
    };

    /** Child element IDs */
    children?: string[];

    /** Actions this element can trigger */
    actions?: A2UIAction[];
}

export interface A2UIAction {
    /** Action identifier */
    id: string;

    /** Action type */
    type: 'submit' | 'navigate' | 'callback' | 'agent';

    /** Action payload */
    payload?: Record<string, unknown>;
}

export interface A2UIPayload {
    /** List of UI messages */
    messages: A2UIMessage[];

    /** Optional metadata */
    meta?: {
        version?: string;
        generatedBy?: string;
        timestamp?: string;
    };
}

// ============================================
// AG-UI Related Types
// ============================================

export type AGUIEventType =
    | 'message'
    | 'tool_call'
    | 'state_patch'
    | 'lifecycle'
    | 'a2ui';

export interface AGUIEvent {
    type: AGUIEventType;
    timestamp: string;
    payload: unknown;
}

export interface AGUIMessageEvent extends AGUIEvent {
    type: 'message';
    payload: {
        role: 'user' | 'assistant' | 'system';
        content: string;
    };
}

export interface AGUIA2UIEvent extends AGUIEvent {
    type: 'a2ui';
    payload: A2UIPayload;
}

// ============================================
// Vivid-specific Widget Types
// ============================================

export interface DimensionCardProps {
    dimensionLabel: string;
    title: string;
    description: string;
    essence: string;
    href: string;
    iconName: string;
    borderColor: string;
    activeBg: string;
}

export interface StoryboardSceneProps {
    sceneNumber: number;
    imageUrl?: string;
    prompt: string;
    duration: number;
    status: 'pending' | 'generating' | 'complete' | 'error';
}

export interface ProgressTrackerProps {
    steps: Array<{
        id: string;
        label: string;
        status: 'pending' | 'active' | 'complete';
    }>;
    currentStep: string;
}
