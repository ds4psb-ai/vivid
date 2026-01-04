"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

// =============================================================================
// Types
// =============================================================================

export interface WorkflowStepEvent {
    step: number;
    total_steps: number;
    dimension: string;
    dimension_name: string;
    tool_name: string;
    status: "start" | "complete" | "error";
    output_preview?: string;
    credit_cost?: number;
}

interface WorkflowStartEvent {
    topic: string;
    dimensions: string[];
    total_steps: number;
}

interface WorkflowCompleteEvent {
    total_credits: number;
    success_count: number;
}

type WorkflowEventListener = {
    onStart?: (data: WorkflowStartEvent) => void;
    onStep?: (event: WorkflowStepEvent) => void;
    onComplete?: (data: WorkflowCompleteEvent) => void;
};

interface WorkflowEventContextType {
    // For AgentChatAccordion to emit events
    emitStart: (data: WorkflowStartEvent) => void;
    emitStep: (event: WorkflowStepEvent) => void;
    emitComplete: (data: WorkflowCompleteEvent) => void;

    // For consumers (like /flow page) to subscribe
    subscribe: (listener: WorkflowEventListener) => () => void;
}

// =============================================================================
// Context
// =============================================================================

const WorkflowEventContext = createContext<WorkflowEventContextType | null>(null);

export function WorkflowEventProvider({ children }: { children: ReactNode }) {
    const [listeners] = useState<Set<WorkflowEventListener>>(() => new Set());

    const subscribe = useCallback((listener: WorkflowEventListener) => {
        listeners.add(listener);
        return () => {
            listeners.delete(listener);
        };
    }, [listeners]);

    const emitStart = useCallback((data: WorkflowStartEvent) => {
        listeners.forEach((l) => l.onStart?.(data));
    }, [listeners]);

    const emitStep = useCallback((event: WorkflowStepEvent) => {
        listeners.forEach((l) => l.onStep?.(event));
    }, [listeners]);

    const emitComplete = useCallback((data: WorkflowCompleteEvent) => {
        listeners.forEach((l) => l.onComplete?.(data));
    }, [listeners]);

    return (
        <WorkflowEventContext.Provider
            value={{ emitStart, emitStep, emitComplete, subscribe }}
        >
            {children}
        </WorkflowEventContext.Provider>
    );
}

export function useWorkflowEvents() {
    const context = useContext(WorkflowEventContext);
    if (!context) {
        throw new Error("useWorkflowEvents must be used within WorkflowEventProvider");
    }
    return context;
}

// Optional hook for consuming workflow events
export function useWorkflowEventListener(listener: WorkflowEventListener) {
    const { subscribe } = useWorkflowEvents();

    // Subscribe on mount, unsubscribe on unmount
    // Using a pattern that works with React's lifecycle
    const [subscribed, setSubscribed] = useState(false);

    if (!subscribed) {
        subscribe(listener);
        setSubscribed(true);
    }
}
