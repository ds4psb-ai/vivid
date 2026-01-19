/**
 * Unit tests for AG-UI Event Handlers
 * 
 * P4: AG-UI 표준 매퍼 - Phase 3
 */
import { describe, test, expect, vi, beforeEach } from 'vitest';
import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";
import { createEventHandlers, type AgentEventContext, type Message } from './agent-event-handlers';

describe('createEventHandlers', () => {
    let mockContext: AgentEventContext;
    let messagesState: Message[];

    beforeEach(() => {
        messagesState = [
            { id: 'msg-1', role: 'assistant', content: '', timestamp: new Date() }
        ];

        mockContext = {
            setMessages: vi.fn(updater => {
                if (typeof updater === 'function') {
                    messagesState = updater(messagesState);
                }
                return messagesState;
            }),
            assistantMessageId: 'msg-1',
            accumulatedContentRef: { current: '' },
            router: { push: vi.fn() } as AppRouterInstance,
        };
    });

    describe('agent.delta', () => {
        test('accumulates text content', () => {
            const handlers = createEventHandlers(mockContext);

            handlers["agent.delta"]({ delta: "Hello" });
            handlers["agent.delta"]({ delta: " World" });

            expect(mockContext.accumulatedContentRef.current).toBe("Hello World");
            expect(mockContext.setMessages).toHaveBeenCalledTimes(2);
        });

        test('handles empty delta gracefully', () => {
            const handlers = createEventHandlers(mockContext);

            handlers["agent.delta"]({ delta: "" });
            handlers["agent.delta"]({});

            expect(mockContext.accumulatedContentRef.current).toBe("");
        });
    });

    describe('agent.message', () => {
        test('replaces accumulated content', () => {
            const handlers = createEventHandlers(mockContext);
            mockContext.accumulatedContentRef.current = "old content";

            handlers["agent.message"]({ content: "new content" });

            expect(mockContext.accumulatedContentRef.current).toBe("new content");
        });
    });

    describe('agent.tool_calls', () => {
        test('adds pending tool messages', () => {
            const handlers = createEventHandlers(mockContext);

            handlers["agent.tool_calls"]({
                tool_calls: [
                    { id: 'call-1', name: 'generate_prompt' },
                    { id: 'call-2', name: 'generate_image' },
                ]
            });

            expect(mockContext.setMessages).toHaveBeenCalled();
        });

        test('skips tools without name', () => {
            const handlers = createEventHandlers(mockContext);

            handlers["agent.tool_calls"]({
                tool_calls: [{ id: 'call-1' }]  // No name
            });

            // setMessages should NOT be called when all tools are skipped
            expect(mockContext.setMessages).not.toHaveBeenCalled();
        });
    });

    describe('agent.tool_result', () => {
        test('updates pending tool to complete', () => {
            // Add pending tool message
            messagesState.push({
                id: 'tool-pending-1',
                role: 'tool',
                content: '',
                timestamp: new Date(),
                toolName: 'test_tool',
                toolStatus: 'pending',
            });

            const handlers = createEventHandlers(mockContext);

            handlers["agent.tool_result"]({
                name: 'test_tool',
                status: 'complete',
                output: { result: 'success' },
            });

            expect(mockContext.setMessages).toHaveBeenCalled();
        });

        test('creates new tool message if no pending found', () => {
            const handlers = createEventHandlers(mockContext);

            handlers["agent.tool_result"]({
                name: 'new_tool',
                status: 'complete',
                output: { data: 123 },
            });

            expect(mockContext.setMessages).toHaveBeenCalled();
        });

        test('handles error status', () => {
            const handlers = createEventHandlers(mockContext);

            handlers["agent.tool_result"]({
                name: 'failing_tool',
                status: 'error',
                error: 'Something went wrong',
            });

            expect(mockContext.setMessages).toHaveBeenCalled();
        });

        test('calls onToolResult callback', () => {
            const onToolResult = vi.fn();
            mockContext.onToolResult = onToolResult;

            const handlers = createEventHandlers(mockContext);

            handlers["agent.tool_result"]({
                name: 'test_tool',
                status: 'complete',
                output: { key: 'value' },
                arguments: { arg1: 'val1' },
            });

            expect(onToolResult).toHaveBeenCalledWith({
                name: 'test_tool',
                status: 'complete',
                output: { key: 'value' },
                arguments: { arg1: 'val1' },
                error: undefined,
            });
        });
    });

    describe('agent.workflow_*', () => {
        test('workflow_start calls callback', () => {
            const onWorkflowStart = vi.fn();
            mockContext.onWorkflowStart = onWorkflowStart;

            const handlers = createEventHandlers(mockContext);

            handlers["agent.workflow_start"]({
                topic: 'Video creation',
                dimensions: ['1D', '2D'],
                total_steps: 3,
            });

            expect(onWorkflowStart).toHaveBeenCalledWith({
                topic: 'Video creation',
                dimensions: ['1D', '2D'],
                total_steps: 3,
            });
        });

        test('workflow_complete calls callback', () => {
            const onWorkflowComplete = vi.fn();
            mockContext.onWorkflowComplete = onWorkflowComplete;

            const handlers = createEventHandlers(mockContext);

            handlers["agent.workflow_complete"]({
                total_credits: 50,
                success_count: 3,
            });

            expect(onWorkflowComplete).toHaveBeenCalledWith({
                total_credits: 50,
                success_count: 3,
            });
        });

        test('workflow_step handlers set correct status', () => {
            const onWorkflowStep = vi.fn();
            mockContext.onWorkflowStep = onWorkflowStep;

            const handlers = createEventHandlers(mockContext);
            const basePayload = {
                step: 1,
                total_steps: 3,
                dimension: '1D',
                dimension_name: 'Prompt',
                tool_name: 'generate_prompt',
            };

            handlers["agent.workflow_step_start"](basePayload);
            expect(onWorkflowStep).toHaveBeenCalledWith(expect.objectContaining({ status: 'start' }));

            handlers["agent.workflow_step_complete"]({
                ...basePayload,
                output_preview: 'Generated...',
                credit_cost: 10,
            });
            expect(onWorkflowStep).toHaveBeenCalledWith(expect.objectContaining({ status: 'complete' }));

            handlers["agent.workflow_step_error"](basePayload);
            expect(onWorkflowStep).toHaveBeenCalledWith(expect.objectContaining({ status: 'error' }));
        });
    });

    describe('agent.teaching_* (Dimension Tools)', () => {
        test('teaching events map to workflow_step handler', () => {
            const onWorkflowStep = vi.fn();
            mockContext.onWorkflowStep = onWorkflowStep;

            const handlers = createEventHandlers(mockContext);
            const basePayload = {
                tool_name: 'generate_veo_prompt',
                capsule_key: 'teaching.prompt.generate',
            };

            // Test teaching_start -> workflow_step start
            handlers["agent.teaching_start"](basePayload);
            expect(onWorkflowStep).toHaveBeenCalledWith(expect.objectContaining({
                status: 'start',
                dimension: 'Teaching',
                step: 1,
            }));

            // Test teaching_complete -> workflow_step complete
            handlers["agent.teaching_complete"]({
                ...basePayload,
                latency_ms: 1500,
            });
            expect(onWorkflowStep).toHaveBeenCalledWith(expect.objectContaining({
                status: 'complete',
                output_preview: 'Teaching complete',
            }));

            // Test teaching_error -> workflow_step error
            handlers["agent.teaching_error"]({
                ...basePayload,
                error: 'Failed',
            });
            expect(onWorkflowStep).toHaveBeenCalledWith(expect.objectContaining({
                status: 'error',
            }));
        });
    });

    describe('agent.navigation', () => {
        test('appends navigation message and routes', () => {
            vi.useFakeTimers();
            const handlers = createEventHandlers(mockContext);

            handlers["agent.navigation"]({ path: '/dimension/prompt-alchemy' });

            expect(mockContext.accumulatedContentRef.current).toContain('/dimension/prompt-alchemy');
            expect(mockContext.setMessages).toHaveBeenCalled();

            vi.advanceTimersByTime(500);
            expect(mockContext.router.push).toHaveBeenCalledWith('/dimension/prompt-alchemy');

            vi.useRealTimers();
        });

        test('does nothing for empty path', () => {
            const handlers = createEventHandlers(mockContext);

            handlers["agent.navigation"]({ path: '' });

            expect(mockContext.router.push).not.toHaveBeenCalled();
        });
    });

    describe('legacy content event', () => {
        test('logs deprecation warning', () => {
            const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => { });
            const handlers = createEventHandlers(mockContext);

            handlers["content"]({ delta: "legacy text" });

            expect(warnSpy).toHaveBeenCalledWith(
                expect.stringContaining("Legacy 'content' event")
            );
            expect(mockContext.accumulatedContentRef.current).toBe("legacy text");

            warnSpy.mockRestore();
        });
    });
});
