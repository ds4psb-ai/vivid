"use client";

import { useCallback, useReducer } from "react";
import type { Node } from "@xyflow/react";
import type { CanvasNodeData } from "@/components/canvas/CustomNodes";
import { useNodeLifecycle } from "./useNodeLifecycle";
import { normalizeApiError } from "@/lib/errors";

/**
 * Virlo-aligned 5-State FSM for Capsule Nodes
 * 
 * States:
 * - idle: Ready for input, parameters editable
 * - loading: Waiting for server response (optimistic)
 * - streaming: Receiving chunked output (SSE/WebSocket)
 * - complete: Full result received, summary displayed
 * - error: Operation failed, retry available
 */
export type CapsuleNodeState =
    | "idle"
    | "loading"
    | "streaming"
    | "complete"
    | "error"
    | "cancelled";

type FSMAction =
    | { type: "RUN" }
    | { type: "FIRST_CHUNK"; partialText: string }
    | { type: "STREAM_CHUNK"; partialText: string; progress?: number }
    | { type: "STREAM_END"; finalResult: unknown }
    | { type: "ERROR"; message: string }
    | { type: "CANCEL"; message: string }
    | { type: "RETRY" }
    | { type: "RESET" };

interface FSMContext {
    state: CapsuleNodeState;
    partialText: string;
    progress: number;
    errorMessage: string | null;
    finalResult: unknown | null;
}

const initialContext: FSMContext = {
    state: "idle",
    partialText: "",
    progress: 0,
    errorMessage: null,
    finalResult: null,
};

function fsmReducer(context: FSMContext, action: FSMAction): FSMContext {
    switch (action.type) {
        case "RUN":
            if (context.state !== "idle" && context.state !== "error" && context.state !== "cancelled") {
                return context;
            }
            return {
                ...initialContext,
                state: "loading",
            };

        case "FIRST_CHUNK":
            if (context.state !== "loading") return context;
            return {
                ...context,
                state: "streaming",
                partialText: action.partialText,
                progress: 10,
            };

        case "STREAM_CHUNK":
            if (context.state !== "streaming") return context;
            return {
                ...context,
                partialText: action.partialText,
                progress: action.progress ?? Math.min(context.progress + 10, 90),
            };

        case "STREAM_END":
            if (context.state !== "streaming" && context.state !== "loading") return context;
            return {
                ...context,
                state: "complete",
                progress: 100,
                finalResult: action.finalResult,
                partialText: "",
            };

        case "ERROR":
            return {
                ...context,
                state: "error",
                errorMessage: action.message,
                progress: 0,
            };

        case "CANCEL":
            return {
                ...context,
                state: "cancelled",
                errorMessage: action.message,
                progress: 0,
                partialText: "",
            };

        case "RETRY":
        case "RESET":
            return initialContext;

        default:
            return context;
    }
}

type SetNodes = React.Dispatch<React.SetStateAction<Node<CanvasNodeData>[]>>;
type UpdateNodeData = (nodeId: string, data: Partial<CanvasNodeData>) => void;

interface UseCapsuleNodeFSMOptions {
    nodeId: string;
    setNodes?: SetNodes;
    updateNodeData?: UpdateNodeData;
    onRun?: (
        params: Record<string, unknown>,
        helpers: {
            receiveChunk: (text: string, isFirst: boolean, progress?: number) => void;
            complete: (result: unknown) => void;
            error: (message: string) => void;
            cancel: (message: string) => void;
        }
    ) => Promise<unknown | void>;
}

export function useCapsuleNodeFSM({
    nodeId,
    setNodes,
    updateNodeData,
    onRun,
}: UseCapsuleNodeFSMOptions) {
    const [context, dispatch] = useReducer(fsmReducer, initialContext);
    const noopSetNodes: SetNodes = () => undefined;
    const { updateNodeData: updateNodeDataFromLifecycle } = useNodeLifecycle(
        setNodes ?? noopSetNodes
    );
    const applyNodeUpdate = updateNodeData ?? updateNodeDataFromLifecycle;

    // Sync FSM state to node data
    const syncToNode = useCallback(
        (ctx: FSMContext) => {
            if (!applyNodeUpdate) return;
            applyNodeUpdate(nodeId, {
                status: ctx.state as CanvasNodeData["status"],
                streamingData:
                    ctx.state === "streaming"
                        ? { partialText: ctx.partialText, progress: ctx.progress }
                        : undefined,
            });
        },
        [nodeId, applyNodeUpdate]
    );

    const receiveChunk = useCallback(
        (text: string, isFirst: boolean, progress?: number) => {
            if (isFirst) {
                dispatch({ type: "FIRST_CHUNK", partialText: text });
            } else {
                dispatch({ type: "STREAM_CHUNK", partialText: text, progress });
            }
            syncToNode({
                state: "streaming",
                partialText: text,
                progress: progress ?? (isFirst ? 10 : 0),
                errorMessage: null,
                finalResult: null,
            });
        },
        [syncToNode]
    );

    const complete = useCallback(
        (result: unknown) => {
            dispatch({ type: "STREAM_END", finalResult: result });
            syncToNode({
                state: "complete",
                progress: 100,
                finalResult: result,
                partialText: "",
                errorMessage: null,
            });
        },
        [syncToNode]
    );

    const setError = useCallback(
        (message: string) => {
            dispatch({ type: "ERROR", message });
            syncToNode({
                state: "error",
                partialText: "",
                progress: 0,
                errorMessage: message,
                finalResult: null,
            });
        },
        [syncToNode]
    );

    const cancel = useCallback(
        (message: string) => {
            dispatch({ type: "CANCEL", message });
            syncToNode({
                state: "cancelled",
                partialText: "",
                progress: 0,
                errorMessage: message,
                finalResult: null,
            });
        },
        [syncToNode]
    );

    const run = useCallback(
        async (params: Record<string, unknown> = {}) => {
            dispatch({ type: "RUN" });
            syncToNode({ ...initialContext, state: "loading" });

            try {
                if (onRun) {
                    const result = await onRun(params, {
                        receiveChunk,
                        complete,
                        error: setError,
                        cancel,
                    });
                    if (result !== undefined) {
                        complete(result);
                    }
                } else {
                    // Mock streaming for demo
                    await mockStreamingDemo(dispatch, syncToNode);
                }
            } catch (err) {
                const message = normalizeApiError(err, "Unknown error");
                setError(message);
            }
        },
        [onRun, syncToNode, receiveChunk, complete, setError, cancel]
    );

    const retry = useCallback(() => {
        dispatch({ type: "RETRY" });
        syncToNode(initialContext);
    }, [syncToNode]);

    const reset = useCallback(() => {
        dispatch({ type: "RESET" });
        syncToNode(initialContext);
    }, [syncToNode]);

    return {
        state: context.state,
        partialText: context.partialText,
        progress: context.progress,
        errorMessage: context.errorMessage,
        finalResult: context.finalResult,
        run,
        receiveChunk,
        complete,
        cancel,
        retry,
        reset,
    };
}

// Mock streaming for demo/testing
async function mockStreamingDemo(
    dispatch: React.Dispatch<FSMAction>,
    syncToNode: (ctx: FSMContext) => void
) {
    const chunks = [
        "Analyzing input...",
        "Processing patterns...",
        "Generating output...",
        "Finalizing...",
    ];

    for (let i = 0; i < chunks.length; i++) {
        await new Promise((r) => setTimeout(r, 500));
        const isFirst = i === 0;
        const progress = ((i + 1) / chunks.length) * 90;

        if (isFirst) {
            dispatch({ type: "FIRST_CHUNK", partialText: chunks[i] });
        } else {
            dispatch({ type: "STREAM_CHUNK", partialText: chunks[i], progress });
        }

        syncToNode({
            state: "streaming",
            partialText: chunks[i],
            progress,
            errorMessage: null,
            finalResult: null,
        });
    }

    await new Promise((r) => setTimeout(r, 300));
    dispatch({ type: "STREAM_END", finalResult: { summary: "Generation complete!" } });
    syncToNode({
        state: "complete",
        partialText: "",
        progress: 100,
        errorMessage: null,
        finalResult: { summary: "Generation complete!" },
    });
}
