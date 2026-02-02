/**
 * Analytics utility for tracking user interactions.
 * Sends events to backend /api/v1/analytics/events endpoint.
 * Also sends to PostHog for product analytics (funnels, session replay, etc.)
 */
import { api } from "./api";
import posthog from "posthog-js";

export type AnalyticsEventType =
    | "evidence_ref_opened"
    | "template_seeded"
    | "template_version_swapped"
    | "template_run_started"
    | "template_run_completed"
    // Crebit Apply flow events
    | "crebit_cta_click"
    | "crebit_modal_open"
    | "crebit_form_submit"
    | "crebit_form_error"
    // Prompty Tikitaka events (Phase 6)
    | "tikitaka_start"
    | "tikitaka_step_advance"
    | "tikitaka_complete"
    | "anchor_selected"
    | "tool_prompt_copied"
    | "verdict_action";

export interface TrackEventOptions {
    templateId?: string;
    capsuleId?: string;
    runId?: string;
    evidenceRef?: string;
    location?: string;  // For Crebit CTA tracking
    source?: string;    // For modal/component tracking
    track?: string;     // For Crebit track selection
    applicationId?: string; // For application tracking
    errorMessage?: string;  // For error tracking
    // Tikitaka event options (Phase 6)
    projectId?: string;
    step?: number;
    fromStep?: number;
    toStep?: number;
    sceneId?: string;
    toolId?: string;
    verdict?: "PASS" | "REVISE" | "REJECT";
    clarity?: number;
    meta?: Record<string, unknown>;
    // Allow any additional properties
    [key: string]: unknown;
}

/**
 * Track an analytics event and send to backend + PostHog.
 * In development, also logs to console.
 */
export async function trackEvent(
    eventType: AnalyticsEventType,
    options?: TrackEventOptions
): Promise<void> {
    if (process.env.NODE_ENV === "development") {
        console.log(`[Analytics] ${eventType}`, options || "");
    }

    // Send to PostHog (if initialized)
    try {
        if (typeof window !== "undefined" && posthog.__loaded) {
            posthog.capture(eventType, {
                ...options,
                $set: options?.projectId ? { last_project_id: options.projectId } : undefined,
            });
        }
    } catch (error) {
        console.warn("[Analytics] PostHog capture failed:", error);
    }

    // Send to backend analytics
    try {
        await api.trackAnalyticsEvent({
            event_type: eventType,
            template_id: options?.templateId,
            capsule_id: options?.capsuleId,
            run_id: options?.runId,
            evidence_ref: options?.evidenceRef,
            meta: options?.meta,
        });
    } catch (error) {
        // Silently fail analytics - don't block user experience
        console.warn("[Analytics] Failed to track event:", error);
    }
}

/**
 * Track when user clicks/opens an evidence reference.
 */
export function trackEvidenceClick(
    evidenceRef: string,
    context?: { templateId?: string; capsuleId?: string; runId?: string }
): void {
    void trackEvent("evidence_ref_opened", {
        evidenceRef,
        ...context,
    });
}

/**
 * Track when a template is seeded from evidence.
 */
export function trackTemplateSeed(templateId: string, meta?: Record<string, unknown>): void {
    void trackEvent("template_seeded", { templateId, meta });
}

/**
 * Track when template version is swapped.
 */
export function trackTemplateSwap(
    templateId: string,
    meta?: { fromVersion?: number; toVersion?: number }
): void {
    void trackEvent("template_version_swapped", { templateId, meta });
}

/**
 * Track when a template run starts.
 */
export function trackRunStart(runId: string, capsuleId: string): void {
    void trackEvent("template_run_started", { runId, capsuleId });
}

/**
 * Track when a template run completes.
 */
export function trackRunComplete(runId: string, capsuleId: string, success: boolean): void {
    void trackEvent("template_run_completed", { runId, capsuleId, meta: { success } });
}

// Legacy events for Crebit Apply flow (backward compatible)
export const EVENTS = {
    CTA_CLICK: "crebit_cta_click",
    MODAL_OPEN: "crebit_modal_open",
    FORM_SUBMIT: "crebit_form_submit",
    FORM_ERROR: "crebit_form_error",
} as const;

// Tikitaka event helpers (Phase 6)

/**
 * Track when tikitaka workflow starts
 */
export function trackTikitakaStart(projectId: string, anchorSceneId?: string): void {
    void trackEvent("tikitaka_start", { projectId, sceneId: anchorSceneId });
}

/**
 * Track tikitaka step advancement
 */
export function trackTikitakaStepAdvance(
    projectId: string,
    fromStep: number,
    toStep: number
): void {
    void trackEvent("tikitaka_step_advance", { projectId, fromStep, toStep });
}

/**
 * Track tikitaka workflow completion
 */
export function trackTikitakaComplete(projectId: string): void {
    void trackEvent("tikitaka_complete", { projectId });
}

/**
 * Track ANCHOR scene selection
 */
export function trackAnchorSelected(
    projectId: string,
    sceneId: string,
    clarity?: number
): void {
    void trackEvent("anchor_selected", { projectId, sceneId, clarity });
}

/**
 * Track tool prompt copy
 */
export function trackToolPromptCopy(
    projectId: string,
    toolId: string,
    step: number
): void {
    void trackEvent("tool_prompt_copied", { projectId, toolId, step });
}

/**
 * Track verdict action (PASS/REVISE/REJECT)
 */
export function trackVerdictAction(
    projectId: string,
    verdict: "PASS" | "REVISE" | "REJECT",
    step: number
): void {
    void trackEvent("verdict_action", { projectId, verdict, step });
}
