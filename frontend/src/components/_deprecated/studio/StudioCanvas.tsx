"use client";

/**
 * StudioCanvas - Reusable canvas component for workflow visualization
 * 
 * Extracted from canvas/page.tsx to enable embedding in Studio page.
 * Supports both "full" mode (standalone canvas page) and "embedded" mode (within Studio).
 */

import { useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
    ReactFlow,
    addEdge,
    Background,
    Connection,
    Edge,
    Node,
    useEdgesState,
    useNodesState,
    Panel,
    MiniMap,
    useReactFlow,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";
import { motion, AnimatePresence } from "framer-motion";
import {
    Save,
    FileInput,
    FileOutput,
    Palette,
    Sliders,
    FolderOpen,
    Plus,
    Undo,
    Redo,
    Maximize2,
    ZoomIn,
    ZoomOut,
    Play,
    Sparkles,
    Workflow,
    History,
    X,
    ChevronLeft,
    CreditCard,
    LayoutGrid,
    Video,
    Wand2,
} from "lucide-react";
import { getLayoutedElements } from "@/lib/layout";

import {
    CanvasNode,
    CanvasNodeData,
    CanvasNodeKind,
} from "@/components/canvas/CustomNodes";
import { TeachingCapsuleNode } from "@/components/canvas/DimensionCapsuleNode";
import { Inspector } from "@/components/canvas/Inspector";
import { PreviewPanel } from "@/components/canvas/PreviewPanel";
import { GenerationPreviewPanel } from "@/components/_deprecated/canvas/GenerationPreviewPanel";
import { usePipelineExecution } from "@/hooks/usePipelineExecution";
import {
    api,
    CapsuleRunStreamController,
    Canvas,
    GenerationRun,
    GenerationRunFeedbackRequest,
    NarrativeDNA,
    StoryboardPreview,
} from "@/lib/api";
import type { WorkflowPlanResponse } from "@/lib/api";
import { useAdminAccess } from "@/hooks/useAdminAccess";
import { normalizeAllowedType } from "@/lib/graph";
import { normalizeApiError } from "@/lib/errors";
import { withViewTransition } from "@/lib/viewTransitions";
import { useUndoRedo } from "@/hooks/useUndoRedo";
import { useNodeLifecycle } from "@/hooks/useNodeLifecycle";
import { useLanguage } from "@/contexts/LanguageContext";
import { useCanvasSyncChannel } from "@/hooks/useCanvasSyncChannel";
import EmptyCanvasOverlay from "@/components/EmptyCanvasOverlay";
import { NodeDetailPanel } from "@/components/studio/NodeDetailPanel";
import { useRouter } from "next/navigation";
import { useCreditBalance } from "@/hooks/useCreditBalance";
import { useSessionContext } from "@/contexts/SessionContext";
import LoginRequiredModal from "@/components/LoginRequiredModal";
import { buildCanvasSnapshot, readAutoApplySetting, writeAutoApplySetting } from "@/lib/canvasSync";
import type { CanvasSyncEvent } from "@/lib/canvasSync";
import { useDirectorPackState } from "@/hooks/_deprecated/useDirectorPackState";
import { CanvasDirectorPackPanel } from "@/components/_deprecated/canvas/CanvasDirectorPackPanel";
import { useNarrativeArcState } from "@/hooks/useNarrativeArcState";

import { CanvasNarrativePanel } from "@/components/_deprecated/canvas/CanvasNarrativePanel";
import VibeBoard, { VibeInput } from "@/components/canvas/VibeBoard";
import ProactiveAssistant, { ProactiveSuggestion } from "@/components/canvas/ProactiveAssistant";
import { formatNumber } from "@/lib/formatters";

// ============================================================================
// Types
// ============================================================================

export interface StudioCanvasProps {
    /** Display mode: "full" for standalone, "embedded" for within Studio */
    mode: "full" | "embedded";
    /** Workflow plan from external source (e.g., chat tool result) */
    externalWorkflow?: WorkflowPlanResponse | null;
    /** Callback when workflow changes */
    onWorkflowChange?: (plan: WorkflowPlanResponse) => void;
    /** Show top toolbar */
    showToolbar?: boolean;
    /** Show minimap */
    showMinimap?: boolean;
    /** Show run log panel */
    showRunLog?: boolean;
    /** Initial canvas ID to load */
    initialCanvasId?: string | null;
    /** Ref to expose addExternalNode function for Agent integration */
    canvasRef?: React.RefObject<{ addExternalNode: (nodeSpec: Record<string, unknown>) => void } | null>;
}

// ============================================================================
// Constants
// ============================================================================

const nodeTypes = {
    input: CanvasNode,
    source: CanvasNode,  // Backend uses 'source' for story input nodes
    style: CanvasNode,
    customization: CanvasNode,
    processing: CanvasNode,
    output: CanvasNode,
    capsule: CanvasNode,
    asset: CanvasNode,
    teaching_capsule: TeachingCapsuleNode,  // Agent-generated teaching nodes
};

const initialEdges: Edge[] = [];

const CONNECTION_RULES: Record<string, string[]> = {
    text: ["text", "any"],
    image: ["image", "video", "any"],
    video: ["video", "any"],
    audio: ["audio", "video", "any"],
    dna: ["dna", "text", "any"],
    metadata: ["metadata", "text", "any"],
    any: ["text", "image", "video", "audio", "dna", "metadata", "any"],
};

const createNodeId = () => {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
        return crypto.randomUUID();
    }
    return `node-${Date.now()}`;
};

// ============================================================================
// Component
// ============================================================================

export default function StudioCanvas({
    mode = "full",
    externalWorkflow,
    onWorkflowChange,
    showToolbar = true,
    showMinimap = true,
    showRunLog = true,
    initialCanvasId,
    canvasRef,
}: StudioCanvasProps) {
    const searchParams = useSearchParams();
    const urlCanvasId = initialCanvasId ?? searchParams.get("id");
    const { t, language } = useLanguage();
    const { zoomIn, zoomOut, fitView } = useReactFlow();
    const router = useRouter();
    const { session, isLoading: isSessionLoading } = useSessionContext();
    const { isAdmin } = useAdminAccess();
    const isAuthenticated = Boolean(session?.authenticated);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const isEmbedded = mode === "embedded";

    // Empty state overlay
    const [showEmptyOverlay, setShowEmptyOverlay] = useState(!urlCanvasId);
    const [pendingWorkflow, setPendingWorkflow] = useState<{
        plan: WorkflowPlanResponse;
        sessionId?: string | null;
        receivedAt: string;
    } | null>(null);
    const [autoApplyChatWorkflow, setAutoApplyChatWorkflow] = useState(false);

    // Initial nodes - empty in embedded mode (Studio handles empty state)
    const initialNodes = useMemo<Node<CanvasNodeData>[]>(() => {
        if (isEmbedded) return []; // No initial nodes in embedded mode
        return [
            {
                id: "input-1",
                type: "input",
                position: { x: 100, y: 300 },
                data: { label: t("promptInput"), subtitle: t("userRequest") },
            },
            {
                id: "processing-1",
                type: "processing",
                position: { x: 450, y: 300 },
                data: { label: t("reasoningCore"), subtitle: t("llmGa") },
            },
            {
                id: "output-1",
                type: "output",
                position: { x: 800, y: 300 },
                data: { label: t("finalResponse"), subtitle: t("renderedOutput") },
            },
        ];
    }, [t, isEmbedded]);

    // Core state
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const [graphMeta, setGraphMeta] = useState<Record<string, unknown>>({});
    const [selectedNode, setSelectedNode] = useState<Node<CanvasNodeData> | null>(null);

    // Canvas management
    const [canvasId, setCanvasId] = useState<string | null>(null);
    const [title, setTitle] = useState(t("untitledProject"));
    const [isPublic, setIsPublic] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [canvases, setCanvases] = useState<Canvas[]>([]);
    const [showLoadModal, setShowLoadModal] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Teaching node callbacks for React Flow state updates
    const handleNodeExecuteComplete = useCallback((nodeId: string, output: Record<string, unknown>) => {
        setNodes((prev) => prev.map((n) =>
            n.id === nodeId
                ? { ...n, data: { ...n.data, output, status: "complete", executed: true } }
                : n
        ));
        console.log("[StudioCanvas] Node execution complete:", nodeId, output);
    }, [setNodes]);

    const handleNodeInputsChange = useCallback((nodeId: string, inputs: Record<string, unknown>) => {
        setNodes((prev) => prev.map((n) =>
            n.id === nodeId
                ? { ...n, data: { ...n.data, inputs } }
                : n
        ));
        console.log("[StudioCanvas] Node inputs changed:", nodeId, inputs);
    }, [setNodes]);
    // Auto Layout Handler
    const handleAutoLayout = useCallback(() => {
        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
            nodes,
            edges,
            { direction: 'LR' }
        );
        setNodes([...layoutedNodes] as Node<CanvasNodeData>[]);
        setEdges([...layoutedEdges]);

        // Fit view after a brief delay to allow rendering
        window.requestAnimationFrame(() => {
            fitView({ padding: 0.2, duration: 800 });
        });
        console.log("[StudioCanvas] Applied auto layout");
    }, [nodes, edges, setNodes, setEdges, fitView]);

    // Expose addExternalNode function via canvasRef for Agent integration
    useImperativeHandle(canvasRef, () => ({
        addExternalNode: (nodeSpec: Record<string, unknown>) => {
            const nodeId = (nodeSpec.id as string) || createNodeId();
            const displayName = (nodeSpec.display_name as string) || "Teaching Capsule";
            const specData = (nodeSpec.data as Record<string, unknown>) || {};

            // Get capsule_key from data object (Backend format) or capsule_id (legacy)
            const capsuleKey = (specData.capsule_key as string) || (nodeSpec.capsule_id as string) || "";

            // Calculate auto position based on existing teaching nodes
            const teachingNodes = nodes.filter(n => n.type === "teaching_capsule");
            const lastNode = teachingNodes[teachingNodes.length - 1];
            const position = (nodeSpec.position as { x: number; y: number }) || {
                x: lastNode ? lastNode.position.x + 350 : 200,
                y: lastNode ? lastNode.position.y : 200,
            };

            // Build TeachingCapsuleNodeData-compatible data structure
            const newNode: Node<CanvasNodeData> = {
                id: nodeId,
                type: "teaching_capsule",
                position,
                data: {
                    // Core fields from Backend
                    capsule_key: capsuleKey,
                    display_name: displayName,
                    category: "teaching" as const,

                    // Schemas from Backend
                    input_schema: (specData.input_schema as Record<string, unknown>) || {},
                    output_schema: (specData.output_schema as Record<string, unknown>) || {},
                    params_schema: (specData.params_schema as Record<string, unknown>) || {},

                    // Current values from Backend
                    inputs: (specData.inputs as Record<string, unknown>) || {},
                    locked_inputs: (specData.locked_inputs as string[]) || [],
                    output: (specData.output as Record<string, unknown>) || {},

                    // Execution state
                    editable: (specData.editable as boolean) ?? true,
                    executed: (nodeSpec.executed as boolean) ?? true,
                    credit_cost: (specData.credit_cost as number) || 0,
                    status: "complete" as const,

                    // Callbacks for node state updates
                    onExecuteComplete: handleNodeExecuteComplete,
                    onInputsChange: handleNodeInputsChange,

                    // Legacy compatibility
                    label: displayName,
                    subtitle: capsuleKey,
                },
            };

            setNodes((prev) => [...prev, newNode]);
            setShowEmptyOverlay(false);
            console.log("[StudioCanvas] Added teaching capsule node:", newNode);
        },
    }), [nodes, setNodes, handleNodeExecuteComplete, handleNodeInputsChange]);

    // Optimization & Preview
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [recommendations, setRecommendations] = useState<
        Array<{
            params: Record<string, unknown>;
            fitness_score: number;
            profile: string;
        }>
    >([]);
    const [showRecommendations, setShowRecommendations] = useState(false);
    const [storyboardPreview, setStoryboardPreview] = useState<StoryboardPreview | null>(null);
    const [isPreviewLoading, setIsPreviewLoading] = useState(false);
    const [showPreviewPanel, setShowPreviewPanel] = useState(false);
    const [previewNotice, setPreviewNotice] = useState<{
        tone: "info" | "warning" | "error";
        message: string;
    } | null>(null);
    const [previewLanguage, setPreviewLanguage] = useState<string | null>(null);
    const [generationRun, setGenerationRun] = useState<GenerationRun | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationStatus, setGenerationStatus] = useState<string | null>(null);
    const [generationFeedbackStatus, setGenerationFeedbackStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
    const [showGenerationPanel, setShowGenerationPanel] = useState(false);

    // Refs
    const generationPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const capsuleStreamRef = useRef<CapsuleRunStreamController | null>(null);
    const previewRunIdRef = useRef<string | null>(null);
    const [previewRunId, setPreviewRunId] = useState<string | null>(null);
    const previewCancelFallbackRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const isPreviewLoadingRef = useRef(false);
    const lastGenerationStatusRef = useRef<string | null>(null);
    const lastGenerationRunIdRef = useRef<string | null>(null);
    const previewCapsuleIdRef = useRef<string | null>(null);
    const canvasSyncTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const lastCanvasSnapshotRef = useRef<string | null>(null);
    const lastAppliedWorkflowIdRef = useRef<string | null>(null);  // Track applied workflow to prevent re-application

    // Toast & Run Log
    const [toasts, setToasts] = useState<
        Array<{ id: string; tone: "info" | "warning" | "error"; message: string }>
    >([]);
    const [runLog, setRunLog] = useState<
        Array<{
            id: string;
            tone: "info" | "warning" | "error" | "success";
            message: string;
            time: string;
            context?: {
                kind?: "capsule" | "generation" | "system";
                runId?: string;
                capsuleId?: string;
            };
            metrics?: {
                latencyMs?: number;
                costUsd?: number;
            };
        }>
    >([]);
    const [isRunLogOpen, setIsRunLogOpen] = useState(true);
    const [runLogFilters, setRunLogFilters] = useState({
        capsule: true,
        generation: true,
        errorsOnly: false,
    });
    const toastTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

    // Hooks
    const { takeSnapshot, undo, redo, canUndo, canRedo } = useUndoRedo();
    const { updateNodeData, updateNodesByType } = useNodeLifecycle(setNodes, setSelectedNode);
    const { balance: creditBalance } = useCreditBalance();

    // DirectorPack state
    const capsuleNode = useMemo(() => nodes.find((n) => n.type === "capsule"), [nodes]);
    const directorPackState = useDirectorPackState(capsuleNode?.data?.capsuleId);

    // NarrativeArc state
    const narrativeArcState = useNarrativeArcState();

    // VibeBoard state
    const [showVibeBoard, setShowVibeBoard] = useState(false);
    const [isVibeParsing, setIsVibeParsing] = useState(false);

    // ProactiveAssistant state
    const [proactiveSuggestions, setProactiveSuggestions] = useState<ProactiveSuggestion[]>([]);
    const [isProactiveMinimized, setIsProactiveMinimized] = useState(false);

    // ============================================================================
    // Callbacks
    // ============================================================================

    const pushRunLog = useCallback(
        (
            tone: "info" | "warning" | "error" | "success",
            message: string,
            context?: { kind?: "capsule" | "generation" | "system"; runId?: string; capsuleId?: string },
            metrics?: { latencyMs?: number; costUsd?: number }
        ) => {
            if (!message) return;
            const id = typeof crypto !== "undefined" && "randomUUID" in crypto
                ? crypto.randomUUID()
                : `runlog-${Date.now()}-${Math.random().toString(16).slice(2)}`;
            const time = new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
            });
            setRunLog((current) => {
                const next = [{ id, tone, message, time, context, metrics }, ...current];
                return next.slice(0, 40);
            });
        },
        []
    );

    const applyWorkflowPlan = useCallback(
        (workflow: WorkflowPlanResponse, source: "vibe" | "chat" | "external") => {
            const newNodes = workflow.nodes.map((n) => ({
                id: n.id,
                type: n.type as CanvasNodeKind,
                position: n.position,
                data: {
                    label: n.label,
                    description: n.description,
                    category: n.category,  // Opal-style category for visual differentiation
                    ai_model: n.ai_model,
                    ...n.data,
                    narrativeDna: workflow.narrative_dna,
                },
            }));

            const newEdges = workflow.edges.map((e) => ({
                id: e.id,
                source: e.source,
                target: e.target,
                sourceHandle: e.source_handle,
                targetHandle: e.target_handle,
            }));

            takeSnapshot(nodes as Node<CanvasNodeData>[], edges as Edge[]);
            setNodes(newNodes as Node<CanvasNodeData>[]);
            setEdges(newEdges);
            setShowVibeBoard(false);
            setShowEmptyOverlay(false);

            const logMessage = source === "chat"
                ? t("canvasChatSyncApplied")
                : source === "external"
                    ? t("canvasChatSyncApplied")
                    : t("canvasWorkflowApplied");
            pushRunLog("info", logMessage, { kind: "system" });

            // Notify parent of workflow change
            if (onWorkflowChange) {
                onWorkflowChange(workflow);
            }
        },
        [edges, nodes, pushRunLog, setEdges, setNodes, setShowEmptyOverlay, setShowVibeBoard, takeSnapshot, t, onWorkflowChange]
    );

    // Apply external workflow when it changes
    useEffect(() => {
        if (externalWorkflow && externalWorkflow.nodes?.length > 0) {
            // Prevent re-application of the same workflow
            const workflowId = externalWorkflow.workflow_id || JSON.stringify(externalWorkflow.nodes.map(n => n.id));
            if (lastAppliedWorkflowIdRef.current === workflowId) {
                return;  // Already applied this workflow
            }
            lastAppliedWorkflowIdRef.current = workflowId;
            applyWorkflowPlan(externalWorkflow, "external");
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [externalWorkflow]);  // Intentionally omit applyWorkflowPlan to prevent infinite loop

    // ============================================================================
    // Canvas Sync (only in full mode)
    // ============================================================================

    useEffect(() => {
        setAutoApplyChatWorkflow(readAutoApplySetting(canvasId));
    }, [canvasId]);

    const sendCanvasSync = useCanvasSyncChannel((event: CanvasSyncEvent) => {
        if (isEmbedded) return; // Skip sync in embedded mode

        if (event.type === "canvas_settings") {
            if (event.payload.source === "canvas") return;
            const incomingId = event.payload.canvasId ?? null;
            const currentId = canvasId ?? null;
            if (incomingId !== currentId) return;
            writeAutoApplySetting(currentId, event.payload.autoApplyChatWorkflow);
            setAutoApplyChatWorkflow(event.payload.autoApplyChatWorkflow);
            return;
        }
        if (event.type !== "workflow_plan") return;
        if (event.payload.source === "canvas") return;
        if (!event.payload.plan?.nodes || !event.payload.plan?.edges) return;
        if (!nodes.length && !edges.length) {
            applyWorkflowPlan(event.payload.plan, "chat");
            return;
        }
        if (autoApplyChatWorkflow) {
            applyWorkflowPlan(event.payload.plan, "chat");
            return;
        }
        setPendingWorkflow({
            plan: event.payload.plan,
            sessionId: event.payload.sessionId,
            receivedAt: new Date().toISOString(),
        });
    });

    // Removed duplicate applyWorkflowPlan definition

    const handleApplyPendingWorkflow = useCallback(() => {
        if (!pendingWorkflow) return;
        applyWorkflowPlan(pendingWorkflow.plan, "chat");
        setPendingWorkflow(null);
    }, [applyWorkflowPlan, pendingWorkflow]);

    const handleDismissPendingWorkflow = useCallback(() => {
        if (!pendingWorkflow) return;
        setPendingWorkflow(null);
        pushRunLog("info", t("canvasChatSyncDismissed"), { kind: "system" });
    }, [pendingWorkflow, pushRunLog, t]);

    const handleToggleAutoApply = useCallback(() => {
        setAutoApplyChatWorkflow((prev) => {
            const next = !prev;
            writeAutoApplySetting(canvasId, next);
            sendCanvasSync({
                type: "canvas_settings",
                payload: {
                    source: "canvas",
                    canvasId,
                    autoApplyChatWorkflow: next,
                },
            });
            return next;
        });
    }, [canvasId, sendCanvasSync]);

    useEffect(() => {
        if (!autoApplyChatWorkflow || !pendingWorkflow) return;
        handleApplyPendingWorkflow();
    }, [autoApplyChatWorkflow, handleApplyPendingWorkflow, pendingWorkflow]);

    // ============================================================================
    // Node Selection
    // ============================================================================

    const handleNodeClick = useCallback(
        (_: React.MouseEvent, node: Node<CanvasNodeData>) => {
            setSelectedNode(node);
        },
        []
    );

    const handlePaneClick = useCallback(() => {
        setSelectedNode(null);
    }, []);

    // ============================================================================
    // Placeholder handlers (to be implemented)
    // ============================================================================

    const handleVibeSelected = useCallback(async (vibe: VibeInput) => {
        setIsVibeParsing(true);
        try {
            const workflow = await api.interpretVibe({
                type: vibe.type,
                preset_id: vibe.presetId,
                custom_description: vibe.customDescription,
                output_type: vibe.outputType,
                target_length_sec: vibe.targetLengthSec,
            });
            applyWorkflowPlan(workflow, "vibe");
        } catch (e) {
            const msg = e instanceof Error ? e.message : "알 수 없는 오류";
            setError(`바이브 해석 실패: ${msg}`);
        } finally {
            setIsVibeParsing(false);
        }
    }, [applyWorkflowPlan]);

    const handleDismissSuggestion = useCallback((id: string) => {
        setProactiveSuggestions((prev) => prev.filter((s) => s.id !== id));
    }, []);

    const handleAcceptSuggestion = useCallback((suggestion: ProactiveSuggestion) => {
        if (suggestion.suggestedAction?.type === "modify_node" && suggestion.targetNodeId) {
            setNodes((nds) =>
                nds.map((n) => {
                    if (n.id === suggestion.targetNodeId) {
                        return {
                            ...n,
                            data: {
                                ...n.data,
                                ...(suggestion.suggestedAction?.params || {}),
                            },
                        };
                    }
                    return n;
                })
            );
        }
        setProactiveSuggestions((prev) => prev.filter((s) => s.id !== suggestion.id));
    }, [setNodes]);

    const handleDismissAllSuggestions = useCallback(() => {
        setProactiveSuggestions([]);
    }, []);

    // ============================================================================
    // Connection validation
    // ============================================================================

    const isValidConnection = useCallback(
        (connection: Connection) => {
            const sourceNode = nodes.find((n) => n.id === connection.source);
            const targetNode = nodes.find((n) => n.id === connection.target);
            if (!sourceNode || !targetNode) return false;

            const sourceHandles = (sourceNode.data.output_handles || []) as Array<{ id: string; type: string }>;
            const targetHandles = (targetNode.data.input_handles || []) as Array<{ id: string; type: string }>;

            const sourceHandle = sourceHandles.find((h) => h.id === connection.sourceHandle);
            const targetHandle = targetHandles.find((h) => h.id === connection.targetHandle);

            if (!sourceHandle || !targetHandle) return true;

            const allowedTypes = CONNECTION_RULES[sourceHandle.type] || [];
            return allowedTypes.includes(targetHandle.type);
        },
        [nodes]
    );

    const onConnect = useCallback(
        (connection: Connection) => {
            if (!isValidConnection(connection)) {
                return;
            }

            setEdges((eds) => {
                const nextEdges = addEdge(
                    {
                        ...connection,
                        animated: true,
                        style: { stroke: "#38bdf8", strokeWidth: 2.5 },
                    },
                    eds
                );
                takeSnapshot(nodes, nextEdges);
                return nextEdges;
            });
        },
        [nodes, setEdges, takeSnapshot, isValidConnection]
    );

    // ============================================================================
    // Render
    // ============================================================================

    const containerStyle = isEmbedded
        ? "relative w-full h-full min-h-[400px]"
        : "relative w-screen h-screen";

    return (
        <div className={containerStyle}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeClick={handleNodeClick}
                onPaneClick={handlePaneClick}
                nodeTypes={nodeTypes}
                proOptions={{ hideAttribution: true }}
                fitView
                minZoom={0.1}
                maxZoom={2}
                defaultEdgeOptions={{
                    animated: true,
                    style: { stroke: "#38bdf8", strokeWidth: 2 },
                }}
            >
                <Background color="#334155" gap={20} />

                {showMinimap && (
                    <MiniMap
                        nodeColor={(node) => {
                            switch (node.type) {
                                case "input": return "#22c55e";
                                case "output": return "#ef4444";
                                case "capsule": return "#3b82f6";
                                case "processing": return "#8b5cf6";
                                default: return "#64748b";
                            }
                        }}
                        maskColor="rgba(15, 23, 42, 0.8)"
                        className="!bg-slate-900/80 !border-white/10"
                    />
                )}

                {/* Toolbar */}
                {showToolbar && !isEmbedded && (
                    <Panel position="top-left" className="flex gap-2">
                        <button
                            onClick={() => setShowVibeBoard(true)}
                            className="flex items-center gap-2 rounded-xl border border-white/10 bg-gradient-to-r from-purple-500/20 to-pink-500/20 px-4 py-2 text-sm font-semibold text-white shadow-lg backdrop-blur-sm transition hover:border-white/20"
                        >
                            <Wand2 className="h-4 w-4" />
                            AI Director
                        </button>
                    </Panel>
                )}

                {/* Pipeline execution and zoom controls */}
                <Panel position="bottom-right" className="flex gap-1">
                    {nodes.filter(n => n.type === "teaching_capsule").length > 0 && (
                        <button
                            onClick={async () => {
                                console.log("[StudioCanvas] Running pipeline...");
                                // Pipeline execution is handled by individual nodes for now
                            }}
                            className="rounded-lg border border-emerald-500/30 bg-emerald-500/20 p-2 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/30 backdrop-blur-sm flex items-center gap-1.5 px-3"
                            title="Run Pipeline"
                        >
                            <Play className="h-4 w-4" />
                            <span className="text-xs font-medium">Run</span>
                        </button>
                    )}
                    <button
                        onClick={handleAutoLayout}
                        className="rounded-lg border border-white/10 bg-slate-900/80 p-2 text-slate-400 hover:text-white backdrop-blur-sm"
                        title="Auto Layout"
                    >
                        <LayoutGrid className="h-4 w-4" />
                    </button>
                    <button
                        onClick={() => zoomIn()}
                        className="rounded-lg border border-white/10 bg-slate-900/80 p-2 text-slate-400 hover:text-white backdrop-blur-sm"
                    >
                        <ZoomIn className="h-4 w-4" />
                    </button>
                    <button
                        onClick={() => zoomOut()}
                        className="rounded-lg border border-white/10 bg-slate-900/80 p-2 text-slate-400 hover:text-white backdrop-blur-sm"
                    >
                        <ZoomOut className="h-4 w-4" />
                    </button>
                    <button
                        onClick={() => fitView({ padding: 0.2 })}
                        className="rounded-lg border border-white/10 bg-slate-900/80 p-2 text-slate-400 hover:text-white backdrop-blur-sm"
                    >
                        <Maximize2 className="h-4 w-4" />
                    </button>
                </Panel>
            </ReactFlow>

            {/* Empty state overlay (only in full mode - embedded mode uses StudioEmptyState) */}
            {showEmptyOverlay && !isEmbedded && (
                <EmptyCanvasOverlay
                    onSelectSeed={(seedId) => {
                        setShowEmptyOverlay(false);
                        // TODO: Implement seed selection
                    }}
                    onNavigateToTemplates={() => router.push("/")}
                />
            )}

            {/* VibeBoard */}
            <VibeBoard
                isOpen={showVibeBoard}
                onClose={() => setShowVibeBoard(false)}
                onVibeSelected={handleVibeSelected}
                isProcessing={isVibeParsing}
            />

            {/* ProactiveAssistant */}
            <ProactiveAssistant
                suggestions={proactiveSuggestions}
                onDismiss={handleDismissSuggestion}
                onAccept={handleAcceptSuggestion}
                onDismissAll={handleDismissAllSuggestions}
                isMinimized={isProactiveMinimized}
                onToggleMinimize={() => setIsProactiveMinimized(!isProactiveMinimized)}
            />

            {/* Node Detail Panel */}
            {selectedNode && (
                <NodeDetailPanel
                    node={selectedNode}
                    onClose={() => setSelectedNode(null)}
                    onExecute={async (nodeId, inputData) => {
                        const node = nodes.find(n => n.id === nodeId);
                        if (!node) return;

                        // Update node status to loading
                        setNodes(nds => nds.map(n =>
                            n.id === nodeId
                                ? { ...n, data: { ...n.data, status: "loading" } }
                                : n
                        ));

                        try {
                            // Call real SSE streaming API
                            const request = {
                                node_id: nodeId,
                                node_type: node.type || "capsule",
                                category: ((node.data?.category as string) || "generate") as "input" | "generate" | "refine" | "validate" | "compose" | "output",
                                input_data: inputData,
                                upstream_results: {},
                                params: (node.data?.data as Record<string, unknown>) || {},
                                ai_model: node.data?.ai_model || "gemini-3-flash-preview",
                            };

                            for await (const event of api.executeNodeStream(request)) {
                                console.log("SSE Event:", event);

                                if (event.type === "status") {
                                    const statusValue = (event.status || "loading") as CanvasNodeData["status"];
                                    setNodes(nds => nds.map(n =>
                                        n.id === nodeId
                                            ? { ...n, data: { ...n.data, status: statusValue } }
                                            : n
                                    ));
                                } else if (event.type === "result") {
                                    setNodes(nds => nds.map(n =>
                                        n.id === nodeId
                                            ? { ...n, data: { ...n.data, status: "complete", generationResult: event.output } }
                                            : n
                                    ));
                                } else if (event.type === "error") {
                                    throw new Error(event.message || "Execution failed");
                                }
                            }
                        } catch (error) {
                            console.error("Node execution error:", error);
                            setNodes(nds => nds.map(n =>
                                n.id === nodeId
                                    ? { ...n, data: { ...n.data, status: "error" } }
                                    : n
                            ));
                            throw error;
                        }
                    }}
                />
            )}

            {/* Login modal */}
            <LoginRequiredModal
                isOpen={showLoginModal}
                onClose={() => setShowLoginModal(false)}
            />
        </div>
    );
}
