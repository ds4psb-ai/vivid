"use client";

import { useCallback, useRef, useState } from "react";
import { useReactFlow, type Edge, type Node } from "@xyflow/react";

// ============================================================================
// Types
// ============================================================================

// Node data interface - extends Record for @xyflow/react compatibility
interface NodeData extends Record<string, unknown> {
    capsule_id?: string;
    capsule_key?: string;
    display_name?: string;
    inputs?: Record<string, unknown>;
    output?: Record<string, unknown>;
    executed?: boolean;
}

// Type alias for our nodes
type PipelineNode = Node<NodeData, string>;

interface ExecutionResult {
    nodeId: string;
    success: boolean;
    output: Record<string, unknown>;
    error?: string;
}

interface PipelineResult {
    success: boolean;
    executedCount: number;
    results: ExecutionResult[];
    context: Record<string, unknown>;
}

// ============================================================================
// Topological Sort
// ============================================================================

function topologicalSort(
    nodes: PipelineNode[],
    edges: Edge[],
    startNodeId?: string
): string[] {
    const graph = new Map<string, string[]>();
    const inDegree = new Map<string, number>();

    // Initialize
    nodes.forEach((node) => {
        graph.set(node.id, []);
        inDegree.set(node.id, 0);
    });

    // Build graph
    edges.forEach((edge) => {
        const sources = graph.get(edge.source) || [];
        sources.push(edge.target);
        graph.set(edge.source, sources);
        inDegree.set(edge.target, (inDegree.get(edge.target) || 0) + 1);
    });

    // Find nodes with in-degree 0
    const queue: string[] = [];
    inDegree.forEach((degree, nodeId) => {
        if (degree === 0) {
            if (startNodeId) {
                if (nodeId === startNodeId) queue.push(nodeId);
            } else {
                queue.push(nodeId);
            }
        }
    });

    const result: string[] = [];

    while (queue.length > 0) {
        const current = queue.shift()!;
        result.push(current);

        const neighbors = graph.get(current) || [];
        neighbors.forEach((neighbor) => {
            const newDegree = (inDegree.get(neighbor) || 0) - 1;
            inDegree.set(neighbor, newDegree);
            if (newDegree === 0) {
                queue.push(neighbor);
            }
        });
    }

    return result;
}

// ============================================================================
// Get Upstream Outputs
// ============================================================================

function getUpstreamOutputs(
    nodeId: string,
    edges: Edge[],
    nodes: PipelineNode[]
): Record<string, unknown> {
    const upstreamData: Record<string, unknown> = {};

    edges
        .filter((edge) => edge.target === nodeId)
        .forEach((edge) => {
            const sourceNode = nodes.find((n) => n.id === edge.source);
            if (sourceNode?.data?.output) {
                // Flatten upstream output into inputs
                const output = sourceNode.data.output as Record<string, unknown>;
                Object.entries(output).forEach(([key, value]) => {
                    upstreamData[`upstream_${key}`] = value;
                });
                // Also set primary output
                upstreamData["upstream_output"] = output;
            }
        });

    return upstreamData;
}

// ============================================================================
// Execute Node
// ============================================================================

async function executeNode(
    node: PipelineNode,
    mergedInputs: Record<string, unknown>,
    byokKey?: string
): Promise<{ success: boolean; output: Record<string, unknown>; error?: string }> {
    const capsuleId = (node.data.capsule_id || node.data.capsule_key || "") as string;

    // Map capsule_id to endpoint
    const endpointMap: Record<string, string> = {
        "teaching.prompt": "/api/v1/teaching/prompt/generate",
        "teaching.prompt.generate": "/api/v1/teaching/prompt/generate",
        "teaching.storyboard": "/api/v1/teaching/storyboard/create",
        "teaching.storyboard.create": "/api/v1/teaching/storyboard/create",
        "teaching.image": "/api/v1/teaching/image/generate",
        "teaching.image.generate": "/api/v1/teaching/image/generate",
        "teaching.reference": "/api/v1/teaching/reference/analyze",
        "teaching.reference.analyze": "/api/v1/teaching/reference/analyze",
    };

    const endpoint = endpointMap[capsuleId];
    if (!endpoint) {
        return { success: false, output: {}, error: `Unknown capsule: ${capsuleId}` };
    }

    try {
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
        };
        if (byokKey) {
            headers["X-Gemini-API-Key"] = byokKey;
        }

        const response = await fetch(endpoint, {
            method: "POST",
            headers,
            body: JSON.stringify(mergedInputs),
        });

        if (!response.ok) {
            const error = await response.text();
            return { success: false, output: {}, error };
        }

        const result = await response.json();
        return { success: true, output: result };
    } catch (error) {
        return { success: false, output: {}, error: String(error) };
    }
}

// ============================================================================
// Hook: usePipelineExecution
// ============================================================================

export function usePipelineExecution() {
    const { getNodes, getEdges, setNodes } = useReactFlow();
    const [isExecuting, setIsExecuting] = useState(false);
    const abortRef = useRef(false);

    const executePipeline = useCallback(
        async (startNodeId?: string, byokKey?: string): Promise<PipelineResult> => {
            setIsExecuting(true);
            abortRef.current = false;

            const nodes = getNodes() as PipelineNode[];
            const edges = getEdges();
            const results: ExecutionResult[] = [];
            const context: Record<string, unknown> = {};

            try {
                // 1. Topological sort for execution order
                const executionOrder = topologicalSort(nodes, edges, startNodeId);

                // 2. Sequential execution
                for (const nodeId of executionOrder) {
                    if (abortRef.current) break;

                    const node = nodes.find((n) => n.id === nodeId);
                    if (!node) continue;

                    // 3. Get upstream outputs
                    const upstreamData = getUpstreamOutputs(nodeId, edges, nodes);
                    const nodeInputs = (node.data.inputs || {}) as Record<string, unknown>;
                    const mergedInputs = { ...nodeInputs, ...upstreamData };

                    // 4. Execute node
                    const result = await executeNode(node, mergedInputs, byokKey);

                    // 5. Update context
                    context[nodeId] = result.output;

                    // 6. Update node state
                    setNodes((prevNodes: Node[]) =>
                        prevNodes.map((n: Node) =>
                            n.id === nodeId
                                ? {
                                    ...n,
                                    data: {
                                        ...(n.data as Record<string, unknown>),
                                        output: result.output,
                                        executed: result.success,
                                    },
                                }
                                : n
                        )
                    );

                    results.push({
                        nodeId,
                        success: result.success,
                        output: result.output,
                        error: result.error,
                    });
                }

                return {
                    success: results.every((r) => r.success),
                    executedCount: results.length,
                    results,
                    context,
                };
            } finally {
                setIsExecuting(false);
            }
        },
        [getNodes, getEdges, setNodes]
    );

    const stopExecution = useCallback(() => {
        abortRef.current = true;
    }, []);

    return {
        executePipeline,
        stopExecution,
        isExecuting,
    };
}

// ============================================================================
// Hook: useNodeExecution
// ============================================================================

export function useNodeExecution() {
    const { setNodes } = useReactFlow();
    const [isExecuting, setIsExecuting] = useState(false);

    const executeNodeById = useCallback(
        async (
            nodeId: string,
            capsuleId: string,
            inputs: Record<string, unknown>,
            byokKey?: string
        ): Promise<ExecutionResult> => {
            setIsExecuting(true);

            try {
                const node = {
                    id: nodeId,
                    position: { x: 0, y: 0 },
                    data: {
                        capsule_id: capsuleId,
                        display_name: "",
                        inputs,
                        output: {},
                        executed: false,
                    } as NodeData,
                } as PipelineNode;

                const result = await executeNode(node, inputs, byokKey);

                // Update node state
                setNodes((prevNodes: Node[]) =>
                    prevNodes.map((n: Node) =>
                        n.id === nodeId
                            ? {
                                ...n,
                                data: {
                                    ...(n.data as Record<string, unknown>),
                                    output: result.output,
                                    executed: result.success,
                                },
                            }
                            : n
                    )
                );

                return {
                    nodeId,
                    success: result.success,
                    output: result.output,
                    error: result.error,
                };
            } finally {
                setIsExecuting(false);
            }
        },
        [setNodes]
    );

    return {
        executeNodeById,
        isExecuting,
    };
}

// ============================================================================
// Hook: useAutoPosition
// ============================================================================

export function useAutoPosition() {
    const { getNodes } = useReactFlow();

    const calculateAutoPosition = useCallback((): { x: number; y: number } => {
        const nodes = getNodes() as PipelineNode[];

        if (nodes.length === 0) {
            return { x: 100, y: 100 };
        }

        // Find rightmost node
        const rightmost = nodes.reduce(
            (max: { x: number; y: number }, node: PipelineNode) =>
                (node.position.x > max.x ? node.position : max),
            { x: 0, y: 0 }
        );

        return {
            x: rightmost.x + 350,
            y: rightmost.y,
        };
    }, [getNodes]);

    return { calculateAutoPosition };
}
