"use client";

/**
 * useFeedback - Hook for P6 RAG Feedback API integration
 *
 * Features:
 * - Submit explicit feedback (rating, thumbs up/down, comment)
 * - Track implicit feedback (source clicks, text copy, query reformulation)
 * - Error handling with retry
 * - Submission state management
 */

import { useState, useCallback, useRef } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

// =============================================================================
// Types
// =============================================================================

export type FeedbackType = "thumbs_up" | "thumbs_down" | "report";

export type ImplicitEventType =
    | "source_click"
    | "text_copy"
    | "query_reformulate"
    | "session_end";

export interface ExplicitFeedbackPayload {
    response_id: string;
    rating?: number;
    feedback_type?: FeedbackType;
    comment?: string;
}

export interface ImplicitFeedbackPayload {
    response_id: string;
    event_type: ImplicitEventType;
    source_id?: string;
    source_index?: number;
    duration_ms?: number;
    new_query?: string;
    copied_length?: number;
}

export interface UseFeedbackOptions {
    /** RAG Response ID to associate feedback with */
    responseId: string;
    /** Callback on successful submission */
    onSuccess?: () => void;
    /** Callback on error */
    onError?: (error: Error) => void;
    /** Custom API base URL */
    apiBase?: string;
}

export interface UseFeedbackReturn {
    /** Submit explicit feedback (rating, thumbs, comment) */
    submitExplicit: (
        type: "positive" | "negative",
        rating?: number,
        comment?: string
    ) => Promise<void>;
    /** Track implicit feedback events */
    trackImplicit: (
        eventType: ImplicitEventType,
        metadata?: Partial<Omit<ImplicitFeedbackPayload, "response_id" | "event_type">>
    ) => Promise<void>;
    /** Whether a submission is in progress */
    isSubmitting: boolean;
    /** Whether feedback has been submitted */
    hasSubmitted: boolean;
    /** Current error */
    error: Error | null;
    /** Clear error state */
    clearError: () => void;
    /** Reset all state */
    reset: () => void;
}

// =============================================================================
// Hook
// =============================================================================

export function useFeedback({
    responseId,
    onSuccess,
    onError,
    apiBase = API_BASE,
}: UseFeedbackOptions): UseFeedbackReturn {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [hasSubmitted, setHasSubmitted] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    // Track implicit events to prevent duplicates
    const trackedEventsRef = useRef<Set<string>>(new Set());

    /**
     * Submit explicit feedback
     */
    const submitExplicit = useCallback(
        async (
            type: "positive" | "negative",
            rating?: number,
            comment?: string
        ): Promise<void> => {
            if (isSubmitting || hasSubmitted) return;

            setIsSubmitting(true);
            setError(null);

            const feedbackType: FeedbackType =
                type === "positive" ? "thumbs_up" : "thumbs_down";

            const payload: ExplicitFeedbackPayload = {
                response_id: responseId,
                feedback_type: feedbackType,
            };

            if (rating !== undefined && rating >= 1 && rating <= 5) {
                payload.rating = rating;
            }

            if (comment?.trim()) {
                payload.comment = comment.trim();
            }

            try {
                const response = await fetch(`${apiBase}/api/v1/rag/feedback/explicit`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(
                        errorData.detail || `Feedback submission failed: ${response.status}`
                    );
                }

                setHasSubmitted(true);
                onSuccess?.();
            } catch (err) {
                const error = err instanceof Error ? err : new Error(String(err));
                setError(error);
                onError?.(error);
                throw error;
            } finally {
                setIsSubmitting(false);
            }
        },
        [responseId, apiBase, isSubmitting, hasSubmitted, onSuccess, onError]
    );

    /**
     * Track implicit feedback events
     * These are fire-and-forget - we don't block on them
     */
    const trackImplicit = useCallback(
        async (
            eventType: ImplicitEventType,
            metadata?: Partial<Omit<ImplicitFeedbackPayload, "response_id" | "event_type">>
        ): Promise<void> => {
            // Generate a unique key for this event to prevent duplicates
            const eventKey = `${eventType}-${metadata?.source_id || ""}-${metadata?.source_index ?? ""}`;

            // Skip if already tracked (except session_end which can happen multiple times)
            if (eventType !== "session_end" && trackedEventsRef.current.has(eventKey)) {
                return;
            }

            trackedEventsRef.current.add(eventKey);

            const payload: ImplicitFeedbackPayload = {
                response_id: responseId,
                event_type: eventType,
                ...metadata,
            };

            try {
                // Fire and forget - don't await in a blocking way
                const response = await fetch(`${apiBase}/api/v1/rag/feedback/implicit`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) {
                    console.warn(
                        `[useFeedback] Implicit tracking failed: ${response.status}`,
                        eventType
                    );
                }
            } catch (err) {
                // Don't throw - implicit tracking should not block the user
                console.warn("[useFeedback] Implicit tracking error:", err);
            }
        },
        [responseId, apiBase]
    );

    /**
     * Clear error state
     */
    const clearError = useCallback(() => {
        setError(null);
    }, []);

    /**
     * Reset all state
     */
    const reset = useCallback(() => {
        setIsSubmitting(false);
        setHasSubmitted(false);
        setError(null);
        trackedEventsRef.current.clear();
    }, []);

    return {
        submitExplicit,
        trackImplicit,
        isSubmitting,
        hasSubmitted,
        error,
        clearError,
        reset,
    };
}

// =============================================================================
// Utility Functions for Implicit Tracking
// =============================================================================

/**
 * Create a source click tracker
 * Usage: onClick={trackSourceClick("source_id", 0)}
 */
export function createSourceClickHandler(
    trackImplicit: UseFeedbackReturn["trackImplicit"],
    sourceId: string,
    sourceIndex: number
) {
    return () => {
        trackImplicit("source_click", {
            source_id: sourceId,
            source_index: sourceIndex,
        });
    };
}

/**
 * Create a text copy tracker
 * Usage: onCopy={trackTextCopy(selectedText.length)}
 */
export function createTextCopyHandler(
    trackImplicit: UseFeedbackReturn["trackImplicit"],
    copiedLength: number
) {
    return () => {
        trackImplicit("text_copy", {
            copied_length: copiedLength,
        });
    };
}

/**
 * Track session end with duration
 * Usage: useEffect cleanup or beforeunload
 */
export function trackSessionEnd(
    trackImplicit: UseFeedbackReturn["trackImplicit"],
    startTime: number
) {
    const durationMs = Date.now() - startTime;
    trackImplicit("session_end", {
        duration_ms: durationMs,
    });
}

// =============================================================================
// Export default
// =============================================================================

export default useFeedback;
