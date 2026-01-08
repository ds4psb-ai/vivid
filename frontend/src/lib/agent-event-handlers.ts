/**
 * AG-UI Standard Event Handlers
 * 
 * Extracted from AgentChatAccordion.tsx for maintainability.
 * Provides typed handlers for all agent SSE events.
 * 
 * P4: AG-UI 표준 매퍼 - Phase 1
 */

import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";
import type { EventHandlers } from "@/lib/sse-utils";

// =============================================================================
// Types
// =============================================================================

export interface Message {
    id: string;
    role: "user" | "assistant" | "tool";
    content: React.ReactNode;
    timestamp: Date;
    attachments?: { name: string; mime_type: string; file_uri: string }[];
    toolName?: string;
    toolStatus?: "pending" | "complete" | "error";
    toolOutput?: Record<string, unknown>;
    toolError?: string;
}

export interface WorkflowStartEvent {
    topic: string;
    dimensions: string[];
    total_steps: number;
}

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

export interface WorkflowCompleteEvent {
    total_credits: number;
    success_count: number;
}

export interface WorkflowCreatedEvent {
    workflow_id: string;
    topic: string;
    dimensions: string[];
    nodes: Array<{
        id: string;
        dimension: string;
        dimension_name: string;
        tool_name: string;
        status: string;
    }>;
}

export interface ToolResultEvent {
    name: string;
    status: string;
    output: Record<string, unknown>;
    arguments: Record<string, unknown>;
    error?: string;
}

/**
 * Context required by event handlers.
 * Passed from AgentChatAccordion to createEventHandlers.
 */
export interface AgentEventContext {
    // State setters
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;

    // Current assistant message ID
    assistantMessageId: string;

    // Accumulated content ref (for delta events)
    accumulatedContentRef: React.MutableRefObject<string>;

    // Workflow callbacks
    onWorkflowStart?: (data: WorkflowStartEvent) => void;
    onWorkflowStep?: (event: WorkflowStepEvent) => void;
    onWorkflowComplete?: (data: WorkflowCompleteEvent) => void;
    onWorkflowCreated?: (event: WorkflowCreatedEvent) => void;
    onToolResult?: (result: ToolResultEvent) => void;

    // Navigation
    router: AppRouterInstance;
}

// =============================================================================
// Event Handler Factory
// =============================================================================

/**
 * Creates a map of event type -> handler function.
 * Used with SSEEventBuffer for ordered event processing.
 */
export function createEventHandlers(ctx: AgentEventContext): EventHandlers {
    return {
        // ---------------------------------------------------------------------
        // Text Streaming Events
        // ---------------------------------------------------------------------

        "agent.delta": (payload) => handleDelta(ctx, payload),
        "agent.message": (payload) => handleMessage(ctx, payload),

        // ---------------------------------------------------------------------
        // Tool Events
        // ---------------------------------------------------------------------

        "agent.tool_calls": (payload) => handleToolCalls(ctx, payload),
        "agent.tool_result": (payload) => handleToolResult(ctx, payload),

        // ---------------------------------------------------------------------
        // Workflow Events
        // ---------------------------------------------------------------------

        "agent.workflow_start": (payload) => handleWorkflowStart(ctx, payload),
        "agent.workflow_step_start": (payload) => handleWorkflowStep(ctx, payload, "start"),
        "agent.workflow_step_complete": (payload) => handleWorkflowStep(ctx, payload, "complete"),
        "agent.workflow_step_error": (payload) => handleWorkflowStep(ctx, payload, "error"),
        "agent.workflow_complete": (payload) => handleWorkflowComplete(ctx, payload),
        "agent.workflow_created": (payload) => handleWorkflowCreated(ctx, payload),

        // ---------------------------------------------------------------------
        // Navigation Events
        // ---------------------------------------------------------------------

        "agent.navigation": (payload) => handleNavigation(ctx, payload),

        // ---------------------------------------------------------------------
        // Teaching / Dimension Tool Events (Mapped to Workflow UI)
        // ---------------------------------------------------------------------

        "agent.teaching_start": (payload) => handleWorkflowStep(ctx, {
            ...payload,
            step: 1,
            total_steps: 1,
            dimension: "Teaching",
            tool_name: payload.tool_name,
        }, "start"),

        "agent.teaching_complete": (payload) => handleWorkflowStep(ctx, {
            ...payload,
            step: 1,
            total_steps: 1,
            dimension: "Teaching",
            tool_name: payload.tool_name,
            output_preview: "Teaching complete",
        }, "complete"),

        "agent.teaching_error": (payload) => handleWorkflowStep(ctx, {
            ...payload,
            step: 1,
            total_steps: 1,
            dimension: "Teaching",
            tool_name: payload.tool_name,
        }, "error"),

        // ---------------------------------------------------------------------
        // Legacy Support (deprecated)
        // ---------------------------------------------------------------------

        "content": (payload) => handleLegacyContent(ctx, payload),
    };
}

// =============================================================================
// Handler Implementations
// =============================================================================

function handleDelta(ctx: AgentEventContext, payload: Record<string, unknown>): void {
    const delta = String(payload.delta || '');
    ctx.accumulatedContentRef.current += delta;

    ctx.setMessages(prev => prev.map(m =>
        m.id === ctx.assistantMessageId
            ? { ...m, content: ctx.accumulatedContentRef.current }
            : m
    ));
}

function handleMessage(ctx: AgentEventContext, payload: Record<string, unknown>): void {
    const content = String(payload.content || '');
    ctx.accumulatedContentRef.current = content;

    ctx.setMessages(prev => prev.map(m =>
        m.id === ctx.assistantMessageId
            ? { ...m, content }
            : m
    ));
}

function handleToolCalls(ctx: AgentEventContext, payload: Record<string, unknown>): void {
    const toolCalls = Array.isArray(payload.tool_calls) ? payload.tool_calls : [];

    // Timeout for pending tools (30 seconds)
    const TOOL_TIMEOUT_MS = 30_000;

    toolCalls.forEach((call: { id?: string; name?: string }) => {
        if (!call.name) return;

        const messageId = `tool-pending-${call.id || Date.now()}`;
        const toolName = call.name;

        const pendingMessage: Message = {
            id: messageId,
            role: "tool",
            content: "",
            timestamp: new Date(),
            toolName,
            toolStatus: "pending",
        };

        ctx.setMessages(prev => [...prev, pendingMessage]);

        // Set timeout to auto-fail if no result received
        setTimeout(() => {
            ctx.setMessages(prev => {
                const pendingIdx = prev.findIndex(
                    m => m.id === messageId && m.toolStatus === "pending"
                );

                if (pendingIdx !== -1) {
                    // Still pending after timeout - mark as error
                    return prev.map((m, i) =>
                        i === pendingIdx
                            ? {
                                ...m,
                                toolStatus: "error" as const,
                                toolError: "⏱️ 응답 시간 초과 (30초)"
                            }
                            : m
                    );
                }
                return prev;
            });
        }, TOOL_TIMEOUT_MS);
    });
}

function handleToolResult(ctx: AgentEventContext, payload: Record<string, unknown>): void {
    const toolName = String(payload.name || 'tool');
    const status = String(payload.status || 'complete');
    const output = (payload.output as Record<string, unknown>) || {};
    const error = payload.error ? String(payload.error) : undefined;
    const finalStatus: "complete" | "error" = status === "error" ? "error" : "complete";

    ctx.setMessages(prev => {
        // Find pending tool message
        const pendingIdx = prev.findIndex(
            m => m.role === "tool" &&
                m.toolName === toolName &&
                m.toolStatus === "pending"
        );

        if (pendingIdx !== -1) {
            // Update existing pending message
            return prev.map((m, i) =>
                i === pendingIdx
                    ? { ...m, toolStatus: finalStatus, toolOutput: output, toolError: error }
                    : m
            );
        } else {
            // Create new tool message if no pending found
            const newMessage: Message = {
                id: `tool-${Date.now()}-${toolName}`,
                role: "tool",
                content: "",
                timestamp: new Date(),
                toolName,
                toolStatus: finalStatus,
                toolOutput: output,
                toolError: error,
            };
            return [...prev, newMessage];
        }
    });

    // Callback for external handlers
    ctx.onToolResult?.({
        name: toolName,
        status,
        output,
        arguments: (payload.arguments as Record<string, unknown>) || {},
        error,
    });
}

function handleWorkflowStart(ctx: AgentEventContext, payload: Record<string, unknown>): void {
    ctx.onWorkflowStart?.({
        topic: String(payload.topic || ''),
        dimensions: Array.isArray(payload.dimensions) ? payload.dimensions : [],
        total_steps: Number(payload.total_steps) || 0,
    });
}

function handleWorkflowStep(
    ctx: AgentEventContext,
    payload: Record<string, unknown>,
    status: "start" | "complete" | "error"
): void {
    ctx.onWorkflowStep?.({
        step: Number(payload.step) || 0,
        total_steps: Number(payload.total_steps) || 0,
        dimension: String(payload.dimension || ''),
        dimension_name: String(payload.dimension_name || ''),
        tool_name: String(payload.tool_name || ''),
        status,
        output_preview: status === "complete" && payload.output_preview
            ? String(payload.output_preview)
            : undefined,
        credit_cost: status === "complete" && typeof payload.credit_cost === 'number'
            ? payload.credit_cost
            : undefined,
    });
}

function handleWorkflowComplete(ctx: AgentEventContext, payload: Record<string, unknown>): void {
    ctx.onWorkflowComplete?.({
        total_credits: Number(payload.total_credits) || 0,
        success_count: Number(payload.success_count) || 0,
    });
}

function handleWorkflowCreated(ctx: AgentEventContext, payload: Record<string, unknown>): void {
    const workflowSpec = (payload.workflow_spec as Record<string, unknown>) || payload;
    const nodes = Array.isArray(workflowSpec.nodes) ? workflowSpec.nodes : [];

    ctx.onWorkflowCreated?.({
        workflow_id: String(payload.workflow_id || ''),
        topic: String(payload.topic || ''),
        dimensions: Array.isArray(payload.dimensions) ? payload.dimensions : [],
        nodes: nodes.map((n: Record<string, unknown>) => ({
            id: String(n.id || ''),
            dimension: String(n.dimension || ''),
            dimension_name: String(n.dimension_name || ''),
            tool_name: String(n.tool_name || ''),
            status: String(n.status || 'pending'),
        })),
    });
}

function handleNavigation(ctx: AgentEventContext, payload: Record<string, unknown>): void {
    const targetPath = String(payload.path || '');
    if (!targetPath) return;

    // Add navigation message to chat
    ctx.accumulatedContentRef.current += `\n\n🧭 ${targetPath} 페이지로 이동합니다...`;
    ctx.setMessages(prev => prev.map(m =>
        m.id === ctx.assistantMessageId
            ? { ...m, content: ctx.accumulatedContentRef.current }
            : m
    ));

    // Navigate after short delay for UX
    setTimeout(() => {
        ctx.router.push(targetPath);
    }, 500);
}

function handleLegacyContent(ctx: AgentEventContext, payload: Record<string, unknown>): void {
    // DEPRECATED: Legacy 'content' event type
    console.warn("[AgentChat] Legacy 'content' event detected - please update backend to use 'agent.delta'");

    const delta = String(payload.delta || '');
    ctx.accumulatedContentRef.current += delta;

    ctx.setMessages(prev => prev.map(m =>
        m.id === ctx.assistantMessageId
            ? { ...m, content: ctx.accumulatedContentRef.current }
            : m
    ));
}
