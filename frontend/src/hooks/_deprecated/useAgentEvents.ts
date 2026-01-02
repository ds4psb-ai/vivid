"use client";

import { useCallback, useRef, useState } from "react";
import { useReactFlow, Node } from "reactflow";

// ============================================================================
// Types
// ============================================================================

interface TeachingNodeSpec {
    id: string;
    capsule_id: string;
    type: string;
    display_name: string;
    position: { x: number; y: number };
    data: {
        inputs: Record<string, unknown>;
        locked_inputs: string[];
        output: Record<string, unknown>;
        editable: boolean;
    };
    input_ports: string[];
    output_ports: string[];
    icon: string;
    color: string;
    executed: boolean;
}

interface NodeCreatedEvent {
    type: "agent.node_created";
    payload: {
        node_type: "teaching_capsule";
        node_spec: TeachingNodeSpec;
        action: "add_to_canvas";
    };
}

interface NodeUpdatedEvent {
    type: "agent.node_updated";
    payload: {
        node_id: string;
        changes: Record<string, unknown>;
        action: "update_node";
    };
}

interface PipelineCreatedEvent {
    type: "agent.pipeline_created";
    payload: {
        pipeline_spec: {
            pipeline_id: string;
            nodes: TeachingNodeSpec[];
            edges: Array<{
                id: string;
                source: string;
                target: string;
            }>;
        };
        action: "create_pipeline";
    };
}

type AgentEvent = NodeCreatedEvent | NodeUpdatedEvent | PipelineCreatedEvent;

// ============================================================================
// Convert to ReactFlow Node
// ============================================================================

function convertToReactFlowNode(spec: TeachingNodeSpec): Node {
    return {
        id: spec.id,
        type: "teachingCapsule", // Custom node type
        position: spec.position,
        data: {
            ...spec.data,
            capsule_id: spec.capsule_id,
            display_name: spec.display_name,
            icon: spec.icon,
            color: spec.color,
            executed: spec.executed,
            input_ports: spec.input_ports,
            output_ports: spec.output_ports,
        },
    };
}

// ============================================================================
// Hook: useAgentEvents
// ============================================================================

export function useAgentEvents() {
    const { getNodes, setNodes, setEdges } = useReactFlow();
    const [lastEvent, setLastEvent] = useState<AgentEvent | null>(null);

    // Calculate auto position for new nodes
    const calculateAutoPosition = useCallback((): { x: number; y: number } => {
        const nodes = getNodes();

        if (nodes.length === 0) {
            return { x: 100, y: 100 };
        }

        const rightmost = nodes.reduce(
            (max, node) => (node.position.x > max.x ? node.position : max),
            { x: 0, y: 0 }
        );

        return {
            x: rightmost.x + 350,
            y: rightmost.y,
        };
    }, [getNodes]);

    // Handle node created event
    const handleNodeCreated = useCallback(
        (event: NodeCreatedEvent) => {
            const nodeSpec = event.payload.node_spec;

            // Auto position if needed
            if (nodeSpec.position.x === 0 && nodeSpec.position.y === 0) {
                nodeSpec.position = calculateAutoPosition();
            }

            // Convert to ReactFlow node
            const node = convertToReactFlowNode(nodeSpec);

            // Add to canvas
            setNodes((prev) => [...prev, node]);

            setLastEvent(event);

            // Show toast (if available)
            if (typeof window !== "undefined" && (window as unknown as { toast?: (msg: string) => void }).toast) {
                (window as unknown as { toast: (msg: string) => void }).toast(`"${nodeSpec.display_name}" 노드가 생성되었습니다`);
            }
        },
        [calculateAutoPosition, setNodes]
    );

    // Handle node updated event
    const handleNodeUpdated = useCallback(
        (event: NodeUpdatedEvent) => {
            const { node_id, changes } = event.payload;

            setNodes((prev) =>
                prev.map((node) =>
                    node.id === node_id
                        ? {
                            ...node,
                            data: {
                                ...node.data,
                                ...changes,
                            },
                        }
                        : node
                )
            );

            setLastEvent(event);
        },
        [setNodes]
    );

    // Handle pipeline created event
    const handlePipelineCreated = useCallback(
        (event: PipelineCreatedEvent) => {
            const { nodes, edges } = event.payload.pipeline_spec;

            // Convert all nodes
            const reactFlowNodes = nodes.map((spec, index) => {
                // Auto position
                if (spec.position.x === 0 && spec.position.y === 0) {
                    spec.position = {
                        x: 100 + index * 350,
                        y: 100 + index * 50,
                    };
                }
                return convertToReactFlowNode(spec);
            });

            // Add nodes
            setNodes((prev) => [...prev, ...reactFlowNodes]);

            // Add edges
            setEdges((prev) => [
                ...prev,
                ...edges.map((edge) => ({
                    id: edge.id,
                    source: edge.source,
                    target: edge.target,
                    type: "smoothstep",
                })),
            ]);

            setLastEvent(event);
        },
        [setNodes, setEdges]
    );

    // Main event handler
    const handleAgentEvent = useCallback(
        (event: AgentEvent) => {
            switch (event.type) {
                case "agent.node_created":
                    handleNodeCreated(event);
                    break;
                case "agent.node_updated":
                    handleNodeUpdated(event);
                    break;
                case "agent.pipeline_created":
                    handlePipelineCreated(event);
                    break;
            }
        },
        [handleNodeCreated, handleNodeUpdated, handlePipelineCreated]
    );

    return {
        handleAgentEvent,
        lastEvent,
    };
}

// ============================================================================
// Hook: useAgentChatEvents (SSE)
// ============================================================================

export function useAgentChatEvents(sessionId: string | null) {
    const { handleAgentEvent } = useAgentEvents();
    const eventSourceRef = useRef<EventSource | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    const connect = useCallback(() => {
        if (!sessionId || eventSourceRef.current) return;

        const url = `/api/v1/agent/chat?session_id=${sessionId}`;
        const eventSource = new EventSource(url);

        eventSource.onopen = () => {
            setIsConnected(true);
        };

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // Check if it's an agent event
                if (data.type?.startsWith("agent.")) {
                    handleAgentEvent(data as AgentEvent);
                }
            } catch (error) {
                console.error("Failed to parse SSE event:", error);
            }
        };

        eventSource.onerror = () => {
            setIsConnected(false);
            eventSource.close();
            eventSourceRef.current = null;
        };

        eventSourceRef.current = eventSource;
    }, [sessionId, handleAgentEvent]);

    const disconnect = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
            setIsConnected(false);
        }
    }, []);

    return {
        connect,
        disconnect,
        isConnected,
    };
}
