"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ReactFlow,
  addEdge,
  Background,
  Connection,
  Edge,
  Node,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  Panel,
  MiniMap,
  useReactFlow,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle,
  Info,
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
  XCircle,
  X,
  ChevronLeft,
  CreditCard,
} from "lucide-react";

import {
  CanvasNode,
  CanvasNodeData,
  CanvasNodeKind,
} from "@/components/canvas/CustomNodes";
import { Inspector } from "@/components/canvas/Inspector";
import { PreviewPanel } from "@/components/canvas/PreviewPanel";
import { GenerationPreviewPanel } from "@/components/canvas/GenerationPreviewPanel";
import {
  api,
  CapsuleRunStreamController,
  Canvas,
  GenerationRun,
  GenerationRunFeedbackRequest,
  StoryboardPreview,
} from "@/lib/api";
import { useAdminAccess } from "@/hooks/useAdminAccess";
import { normalizeAllowedType } from "@/lib/graph";
import { normalizeApiError } from "@/lib/errors";
import { withViewTransition } from "@/lib/viewTransitions";
import { useUndoRedo } from "@/hooks/useUndoRedo";
import { useNodeLifecycle } from "@/hooks/useNodeLifecycle";
import { useLanguage } from "@/contexts/LanguageContext";
import AppShell from "@/components/AppShell";
import EmptyCanvasOverlay from "@/components/EmptyCanvasOverlay";
import { useRouter } from "next/navigation";
import { useCreditBalance } from "@/hooks/useCreditBalance";
import { useSessionContext } from "@/contexts/SessionContext";
import LoginRequiredModal from "@/components/LoginRequiredModal";
import { useDirectorPackState } from "@/hooks/useDirectorPackState";
import { CanvasDirectorPackPanel } from "@/components/canvas/CanvasDirectorPackPanel";
import { useNarrativeArcState } from "@/hooks/useNarrativeArcState";
import { CanvasNarrativePanel } from "@/components/canvas/CanvasNarrativePanel";

const nodeTypes = {
  input: CanvasNode,
  style: CanvasNode,
  customization: CanvasNode,
  processing: CanvasNode,
  output: CanvasNode,
  capsule: CanvasNode,
};

// Initial nodes removed from global scope to be defined inside component with translations

const initialEdges: Edge[] = [];

const createNodeId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `node-${Date.now()}`;
};

function CanvasFlow() {
  const searchParams = useSearchParams();
  const urlCanvasId = searchParams.get("id");
  const { t, language } = useLanguage();
  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const router = useRouter();
  const { session, isLoading: isSessionLoading } = useSessionContext();
  const { isAdmin } = useAdminAccess();
  const [showLoginModal, setShowLoginModal] = useState(false);

  // Empty state overlay - show when no nodes or starting fresh
  const [showEmptyOverlay, setShowEmptyOverlay] = useState(!urlCanvasId);

  const initialNodes = useMemo<Node<CanvasNodeData>[]>(() => [
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
  ], [t]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [graphMeta, setGraphMeta] = useState<Record<string, unknown>>({});
  const [selectedNode, setSelectedNode] = useState<Node<CanvasNodeData> | null>(
    null
  );

  const [canvasId, setCanvasId] = useState<string | null>(null);
  const [title, setTitle] = useState(t("untitledProject"));
  const [isPublic, setIsPublic] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [canvases, setCanvases] = useState<Canvas[]>([]);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
  const generationPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [showGenerationPanel, setShowGenerationPanel] = useState(false);
  const [generationFeedbackStatus, setGenerationFeedbackStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const capsuleStreamRef = useRef<CapsuleRunStreamController | null>(null);
  const [previewRunId, setPreviewRunId] = useState<string | null>(null);
  const previewCancelFallbackRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isPreviewLoadingRef = useRef(false);
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
  const lastGenerationStatusRef = useRef<string | null>(null);
  const lastGenerationRunIdRef = useRef<string | null>(null);
  const previewCapsuleIdRef = useRef<string | null>(null);

  const { takeSnapshot, undo, redo, canUndo, canRedo } = useUndoRedo();
  const { updateNodeData, updateNodesByType } = useNodeLifecycle(setNodes, setSelectedNode);
  const { balance: creditBalance } = useCreditBalance();

  // DirectorPack state for multi-scene DNA consistency
  const capsuleNode = useMemo(() => nodes.find((n) => n.type === "capsule"), [nodes]);
  const directorPackState = useDirectorPackState(capsuleNode?.data?.capsuleId);

  // NarrativeArc state for Story-First generation
  const narrativeArcState = useNarrativeArcState();

  const openPreviewPanel = useCallback(() => {
    withViewTransition(() => setShowPreviewPanel(true));
  }, [setShowPreviewPanel]);

  const closePreviewPanel = useCallback(() => {
    withViewTransition(() => {
      setShowPreviewPanel(false);
      setStoryboardPreview(null);
      setPreviewNotice(null);
      setPreviewLanguage(null);
    });
  }, [setPreviewLanguage, setPreviewNotice, setShowPreviewPanel, setStoryboardPreview]);

  // Seed graph creation based on selected template
  const handleSelectSeed = useCallback((seedId: string) => {
    let newNodes: Node<CanvasNodeData>[] = [];
    const newEdges: Edge[] = [];

    switch (seedId) {
      case "youtube":
        newNodes = [
          { id: createNodeId(), type: "input", position: { x: 100, y: 200 }, data: { label: t("seedYoutubeVideo"), subtitle: t("seedYoutubeSubtitle") } },
          { id: createNodeId(), type: "capsule", position: { x: 400, y: 150 }, data: { label: t("seedTranscription"), subtitle: t("seedTranscriptionSubtitle"), locked: true } },
          { id: createNodeId(), type: "capsule", position: { x: 400, y: 300 }, data: { label: t("seedSceneAnalysis"), subtitle: t("seedSceneAnalysisSubtitle"), locked: true } },
          { id: createNodeId(), type: "processing", position: { x: 700, y: 200 }, data: { label: t("seedShortCreator"), subtitle: t("seedShortCreatorSubtitle") } },
          { id: createNodeId(), type: "output", position: { x: 1000, y: 200 }, data: { label: t("seedShortsOutput"), subtitle: t("seedShortsOutputSubtitle") } },
        ];
        break;
      case "document":
        newNodes = [
          { id: createNodeId(), type: "input", position: { x: 100, y: 250 }, data: { label: t("seedDocumentUpload"), subtitle: t("seedDocumentSubtitle") } },
          { id: createNodeId(), type: "capsule", position: { x: 400, y: 250 }, data: { label: t("seedDocumentParser"), subtitle: t("seedDocumentParserSubtitle"), locked: true } },
          { id: createNodeId(), type: "processing", position: { x: 700, y: 250 }, data: { label: t("seedAnalysisEngine"), subtitle: t("seedAnalysisEngineSubtitle") } },
          { id: createNodeId(), type: "output", position: { x: 1000, y: 250 }, data: { label: t("seedAnalysisReport"), subtitle: t("seedAnalysisReportSubtitle") } },
        ];
        break;
      case "blank":
      default:
        newNodes = [
          { id: createNodeId(), type: "input", position: { x: 200, y: 300 }, data: { label: t("seedInput"), subtitle: t("seedDataInput") } },
          { id: createNodeId(), type: "capsule", position: { x: 500, y: 300 }, data: { label: t("seedCapsule"), subtitle: t("seedProcessData"), locked: true } },
          { id: createNodeId(), type: "output", position: { x: 800, y: 300 }, data: { label: t("seedOutput"), subtitle: t("seedFinalResult") } },
        ];
        break;
    }

    // Create edges between consecutive nodes
    for (let i = 0; i < newNodes.length - 1; i++) {
      newEdges.push({
        id: `edge-${newNodes[i].id}-${newNodes[i + 1].id}`,
        source: newNodes[i].id,
        target: newNodes[i + 1].id,
      });
    }

    setNodes(newNodes);
    setEdges(newEdges);
    setShowEmptyOverlay(false);
    setTitle(
      seedId === "youtube"
        ? t("seedOptionYoutubeTitle")
        : seedId === "document"
          ? t("seedOptionDocumentTitle")
          : t("untitledProject")
    );
    takeSnapshot(newNodes, newEdges);
    setTimeout(() => fitView({ padding: 0.2 }), 100);
  }, [setNodes, setEdges, takeSnapshot, fitView, t]);

  const handleNavigateToTemplates = useCallback(() => {
    router.push("/");
  }, [router]);

  const updateOutputNodes = useCallback(
    (data: Partial<CanvasNodeData>) => {
      updateNodesByType("output", data);
    },
    [updateNodesByType]
  );

  const removeToast = useCallback((toastId: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== toastId));
    const timeout = toastTimersRef.current.get(toastId);
    if (timeout) {
      clearTimeout(timeout);
      toastTimersRef.current.delete(toastId);
    }
  }, []);

  const pushRunLog = useCallback(
    (
      tone: "info" | "warning" | "error" | "success",
      message: string,
      context?: { kind?: "capsule" | "generation" | "system"; runId?: string; capsuleId?: string },
      metrics?: { latencyMs?: number; costUsd?: number }
    ) => {
      if (!message) return;
      const id =
        typeof crypto !== "undefined" && "randomUUID" in crypto
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

  const pushToast = useCallback(
    (tone: "info" | "warning" | "error", message: string, ttl: number = 3200) => {
      if (!message) return;
      const id =
        typeof crypto !== "undefined" && "randomUUID" in crypto
          ? crypto.randomUUID()
          : `toast-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      setToasts((current) => [...current, { id, tone, message }]);
      if (tone !== "info") {
        pushRunLog(tone === "warning" ? "warning" : "error", message);
      }
      const timeout = setTimeout(() => removeToast(id), ttl);
      toastTimersRef.current.set(id, timeout);
    },
    [pushRunLog, removeToast]
  );

  useEffect(() => {
    const toastTimers = toastTimersRef.current;
    return () => {
      if (generationPollRef.current) {
        clearInterval(generationPollRef.current);
      }
      if (capsuleStreamRef.current) {
        capsuleStreamRef.current.close();
      }
      if (previewCancelFallbackRef.current) {
        clearTimeout(previewCancelFallbackRef.current);
      }
      toastTimers.forEach((timeout) => clearTimeout(timeout));
      toastTimers.clear();
    };
  }, []);

  useEffect(() => {
    isPreviewLoadingRef.current = isPreviewLoading;
  }, [isPreviewLoading]);

  const stopGenerationPolling = useCallback(() => {
    if (generationPollRef.current) {
      clearInterval(generationPollRef.current);
      generationPollRef.current = null;
    }
  }, []);

  const startGenerationPolling = useCallback((runId: string) => {
    if (generationPollRef.current) {
      clearInterval(generationPollRef.current);
    }
    const runContext = { kind: "generation" as const, runId };
    generationPollRef.current = setInterval(async () => {
      try {
        const run = await api.getGenerationRun(runId);
        setGenerationRun(run);
        setGenerationStatus(run.status);
        if (run.status !== lastGenerationStatusRef.current) {
          lastGenerationStatusRef.current = run.status;
          if (run.status === "done") {
            pushRunLog("success", t("runGenerationDone"), runContext);
          } else if (run.status === "failed") {
            pushRunLog("error", t("runGenerationFailed"), runContext);
          }
        }
        if (run.status === "done") {
          const beatSheet = Array.isArray(run.spec?.beat_sheet) ? run.spec.beat_sheet : [];
          const storyboard = Array.isArray(run.spec?.storyboard) ? run.spec.storyboard : [];
          updateOutputNodes({
            status: "complete",
            generationPreview: {
              beat_sheet: beatSheet,
              storyboard: storyboard,
            },
          });
        } else if (run.status === "failed") {
          updateOutputNodes({ status: "error" });
        }
        if (run.status === "done" || run.status === "failed") {
          stopGenerationPolling();
          setIsGenerating(false);
          closePreviewPanel();
          setPreviewRunId(null);
          withViewTransition(() => setShowGenerationPanel(true));
        }
      } catch (err) {
        setError(normalizeApiError(err, t("runStatusLoadError")));
        updateOutputNodes({ status: "error" });
        stopGenerationPolling();
        setIsGenerating(false);
      }
    }, 1500);
  }, [closePreviewPanel, pushRunLog, stopGenerationPolling, t, updateOutputNodes]);

  const buildUpstreamContext = useCallback(
    (targetId: string, contextMode?: "aggregate" | "sequential") => {
      const incoming = new Map<string, string[]>();
      edges.forEach((edge) => {
        if (!edge.target || !edge.source) return;
        const list = incoming.get(edge.target) ?? [];
        list.push(edge.source);
        incoming.set(edge.target, list);
      });

      const visited = new Set<string>();
      const stack = [targetId];
      while (stack.length > 0) {
        const current = stack.pop();
        if (!current) break;
        const parents = incoming.get(current) ?? [];
        for (const parent of parents) {
          if (!visited.has(parent)) {
            visited.add(parent);
            stack.push(parent);
          }
        }
      }

      const upstreamNodes = nodes
        .filter((node) => visited.has(node.id))
        .map((node) => ({
          id: node.id,
          type: node.type,
          label: node.data.label,
          subtitle: node.data.subtitle,
          params: node.data.params ?? {},
          capsuleId: node.data.capsuleId,
          capsuleVersion: node.data.capsuleVersion,
        }));

      const upstreamEdges = edges
        .filter((edge) => visited.has(edge.source) && visited.has(edge.target))
        .map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
        }));

      if (contextMode === "sequential") {
        const nodeIds = upstreamNodes.map((node) => node.id);
        const nodeIdSet = new Set(nodeIds);
        const adjacency = new Map<string, string[]>();
        const indegree = new Map<string, number>();
        nodeIds.forEach((id) => {
          adjacency.set(id, []);
          indegree.set(id, 0);
        });
        upstreamEdges.forEach((edge) => {
          if (!nodeIdSet.has(edge.source) || !nodeIdSet.has(edge.target)) return;
          const list = adjacency.get(edge.source) ?? [];
          list.push(edge.target);
          adjacency.set(edge.source, list);
          indegree.set(edge.target, (indegree.get(edge.target) ?? 0) + 1);
        });
        const queue = [...nodeIds].filter((id) => (indegree.get(id) ?? 0) === 0).sort();
        const ordered: string[] = [];
        while (queue.length > 0) {
          const current = queue.shift();
          if (!current) break;
          ordered.push(current);
          const neighbors = (adjacency.get(current) ?? []).sort();
          neighbors.forEach((neighbor) => {
            indegree.set(neighbor, (indegree.get(neighbor) ?? 0) - 1);
            if ((indegree.get(neighbor) ?? 0) === 0) {
              queue.push(neighbor);
            }
          });
        }
        if (ordered.length < nodeIds.length) {
          nodeIds.forEach((id) => {
            if (!ordered.includes(id)) ordered.push(id);
          });
        }
        const payloadMap = new Map(upstreamNodes.map((node) => [node.id, node]));
        const sequence = ordered.map((id) => payloadMap.get(id)).filter(Boolean);
        return { nodes: upstreamNodes, edges: upstreamEdges, mode: "sequential", sequence };
      }

      if (contextMode === "aggregate") {
        return { nodes: upstreamNodes, edges: upstreamEdges, mode: "aggregate" };
      }

      return { nodes: upstreamNodes, edges: upstreamEdges };
    },
    [edges, nodes]
  );

  const getConnectedCapsules = useCallback(
    (startId: string) => {
      const nodeMap = new Map(nodes.map((node) => [node.id, node]));
      const outgoing = new Map<string, string[]>();
      edges.forEach((edge) => {
        if (!edge.source || !edge.target) return;
        const list = outgoing.get(edge.source) ?? [];
        list.push(edge.target);
        outgoing.set(edge.source, list);
      });

      const visited = new Set<string>([startId]);
      const queue = [startId];
      const capsules: Array<{
        nodeId: string;
        capsuleId: string;
        capsuleVersion?: string;
      }> = [];

      while (queue.length > 0) {
        const current = queue.shift();
        if (!current) break;
        const targets = outgoing.get(current) ?? [];
        for (const target of targets) {
          if (visited.has(target)) continue;
          visited.add(target);
          queue.push(target);
          const node = nodeMap.get(target);
          if (node?.type === "capsule" && node.data?.capsuleId) {
            capsules.push({
              nodeId: node.id,
              capsuleId: node.data.capsuleId,
              capsuleVersion: node.data.capsuleVersion || "latest",
            });
          }
        }
      }

      return capsules;
    },
    [edges, nodes]
  );

  const buildInputValues = useCallback(() => {
    const inputNode = nodes.find((node) => node.type === "input");
    if (!inputNode || typeof inputNode.data !== "object") {
      return {};
    }
    const params = (inputNode.data.params ?? {}) as Record<string, unknown>;
    const inputs: Record<string, unknown> = {};
    const sourceId = params.source_id ?? params.sourceId;
    if (typeof sourceId === "string" && sourceId.trim()) {
      inputs.source_id = sourceId.trim();
    }
    const sceneSummary = params.scene_summary;
    if (typeof sceneSummary === "string" && sceneSummary.trim()) {
      inputs.scene_summary = sceneSummary.trim();
    }
    const durationSec = params.duration_sec;
    if (typeof durationSec === "number" && Number.isFinite(durationSec)) {
      inputs.duration_sec = durationSec;
    }
    const emotionCurve = params.emotion_curve;
    if (
      Array.isArray(emotionCurve) &&
      emotionCurve.every((item) => typeof item === "number" && Number.isFinite(item))
    ) {
      inputs.emotion_curve = emotionCurve;
    }
    return inputs;
  }, [nodes]);

  const handleRun = useCallback(async () => {
    // Wait for session to load before checking auth
    if (isSessionLoading) return;
    if (!session?.authenticated) {
      setShowLoginModal(true);
      return;
    }
    setIsOptimizing(true);
    setError(null);
    try {
      const processingNode = nodes.find((node) => node.type === "processing");
      const targetProfile =
        typeof processingNode?.data?.params?.target_profile === "string"
          ? (processingNode.data.params.target_profile as string)
          : "balanced";
      const objective =
        typeof processingNode?.data?.params?.objective === "string"
          ? (processingNode.data.params.objective as string)
          : undefined;
      const result = await api.optimizeParams(nodes, edges, targetProfile, {
        objective,
      });
      setRecommendations(result.recommendations);
      setShowRecommendations(true);

      // Also run capsule and get preview for any capsule nodes
      const capsuleNode = nodes.find((n) => n.type === "capsule");
      if (capsuleNode && capsuleNode.data.capsuleId) {
        setIsPreviewLoading(true);
        openPreviewPanel();
        setPreviewNotice(null);
        setPreviewLanguage((current) => current ?? language);
        updateNodeData(capsuleNode.id, { status: "loading", streamingData: undefined });
        try {
          let contextMode: "aggregate" | "sequential" | undefined;
          let inputContracts: { contextMode?: string; maxUpstream?: number; allowedTypes?: string[] } | undefined;
          if (!canvasId) {
            try {
              const spec = await api.getCapsuleSpec(
                capsuleNode.data.capsuleId,
                capsuleNode.data.capsuleVersion
              );
              inputContracts =
                spec?.spec && typeof spec.spec === "object"
                  ? (spec.spec as { inputContracts?: { contextMode?: string } }).inputContracts
                  : undefined;
              const rawMode = inputContracts?.contextMode;
              if (rawMode === "aggregate" || rawMode === "sequential") {
                contextMode = rawMode;
              }
              if (inputContracts) {
                const strictContracts = {
                  ...inputContracts,
                  contextMode: (inputContracts.contextMode === "aggregate" || inputContracts.contextMode === "sequential")
                    ? (inputContracts.contextMode as "aggregate" | "sequential")
                    : undefined
                };
                updateNodeData(capsuleNode.id, { inputContracts: strictContracts });
              }
            } catch {
              contextMode = undefined;
            }
          }
          if (!inputContracts && capsuleNode.data?.inputContracts) {
            inputContracts = capsuleNode.data.inputContracts;
          }
          const rawMaxUpstream = inputContracts?.maxUpstream;
          const maxUpstream =
            typeof rawMaxUpstream === "number" && Number.isFinite(rawMaxUpstream)
              ? rawMaxUpstream
              : undefined;
          if (maxUpstream && maxUpstream > 0) {
            const upstream = buildUpstreamContext(capsuleNode.id, contextMode);
            const upstreamCount = Array.isArray(upstream?.nodes) ? upstream.nodes.length : 0;
            if (upstreamCount > maxUpstream) {
              const message = `Upstream nodes exceed maxUpstream (${upstreamCount} > ${maxUpstream})`;
              updateNodeData(capsuleNode.id, { status: "error", streamingData: undefined });
              setPreviewNotice({ tone: "error", message });
              pushToast("warning", message);
              setIsPreviewLoading(false);
              return;
            }
          }
          const rawAllowed = inputContracts?.allowedTypes;
          if (rawAllowed && Array.isArray(rawAllowed) && rawAllowed.length > 0) {
            const allowed = rawAllowed
              .map((value) => normalizeAllowedType(String(value)))
              .filter((value): value is string => Boolean(value));
            const inputs = buildInputValues();
            const sourceIdRaw = inputs.source_id ?? inputs.sourceId;
            if (
              isAdmin &&
              allowed.length > 0 &&
              typeof sourceIdRaw === "string" &&
              sourceIdRaw.trim()
            ) {
              try {
                const asset = await api.getRawAsset(sourceIdRaw.trim());
                const normalized = normalizeAllowedType(asset.source_type || "");
                if (normalized && !allowed.includes(normalized)) {
                  const message = `source_type '${asset.source_type}' not allowed (allowed: ${allowed.join(", ")})`;
                  updateNodeData(capsuleNode.id, { status: "error", streamingData: undefined });
                  setPreviewNotice({ tone: "error", message });
                  pushToast("warning", message);
                  setIsPreviewLoading(false);
                  return;
                }
              } catch (err) {
                const message = normalizeApiError(err, t("sourceTypeLoadError"));
                if (!message.toLowerCase().includes("admin")) {
                  updateNodeData(capsuleNode.id, { status: "error", streamingData: undefined });
                  setPreviewNotice({ tone: "error", message });
                  pushToast("warning", message);
                  setIsPreviewLoading(false);
                  return;
                }
              }
            }
          }
          // Get DirectorPack payload if enabled
          const dnaPayload = directorPackState.getApiPayload();
          // Get Story-First payload (NarrativeArc + HookVariant)
          const storyPayload = narrativeArcState.getApiPayload();
          const runResult = await api.runCapsule({
            canvas_id: canvasId || undefined,
            node_id: capsuleNode.id,
            capsule_id: capsuleNode.data.capsuleId,
            capsule_version: capsuleNode.data.capsuleVersion || "latest",
            inputs: buildInputValues(),
            params: capsuleNode.data.params || {},
            upstream_context: canvasId
              ? undefined
              : buildUpstreamContext(capsuleNode.id, contextMode),
            async_mode: true,
            // DirectorPack DNA for multi-scene consistency
            director_pack: dnaPayload.director_pack,
            scene_overrides: dnaPayload.scene_overrides,
            // Story-First: NarrativeArc + HookVariant
            narrative_arc: storyPayload.narrative_arc || undefined,
            hook_variant: storyPayload.hook_variant || undefined,
          });
          const runContext = {
            kind: "capsule" as const,
            runId: runResult.run_id,
            capsuleId: capsuleNode.data.capsuleId,
          };
          previewCapsuleIdRef.current = capsuleNode.data.capsuleId;
          pushRunLog("info", `${t("runCapsuleQueued")} · ${capsuleNode.data.capsuleId}`, runContext);
          setPreviewRunId(runResult.run_id);
          if (runResult.version && capsuleNode.data.capsuleVersion !== runResult.version) {
            setNodes((current) =>
              current.map((node) =>
                node.id === capsuleNode.id
                  ? {
                    ...node,
                    data: {
                      ...node.data,
                      capsuleVersion: runResult.version,
                    },
                  }
                  : node
              )
            );
          }

          const capsuleNodeId = capsuleNode.id;
          const capsuleKey = capsuleNode.data.capsuleId;
          let isFirstChunk = true;

          if (capsuleStreamRef.current) {
            capsuleStreamRef.current.close();
          }
          capsuleStreamRef.current = api.streamCapsuleRun(runResult.run_id, {
            onEvent: async (event) => {
              const payload = event.payload || {};
              if (
                event.type === "run.queued" ||
                event.type === "run.started" ||
                event.type === "run.progress" ||
                event.type === "run.partial"
              ) {
                if (event.type === "run.started") {
                  pushRunLog("info", t("runCapsuleStarted"), runContext);
                }
                const message =
                  typeof payload.message === "string"
                    ? payload.message
                    : typeof payload.text === "string"
                      ? payload.text
                      : "Working...";
                const progress =
                  typeof payload.progress === "number" ? payload.progress : undefined;
                updateNodeData(capsuleNodeId, {
                  status: "streaming",
                  streamingData: {
                    partialText: message,
                    progress: progress ?? (isFirstChunk ? 10 : 0),
                  },
                });
                isFirstChunk = false;
                return;
              }

              if (event.type === "run.completed") {
                updateNodeData(capsuleNodeId, { status: "complete", streamingData: undefined });
                const latencyMs =
                  typeof payload.latency_ms === "number" ? payload.latency_ms : undefined;
                const costUsd =
                  typeof payload.cost_usd_est === "number" ? payload.cost_usd_est : undefined;
                pushRunLog("success", t("runCapsuleCompleted"), runContext, {
                  latencyMs,
                  costUsd,
                });
                const requestedLanguage = previewLanguage ?? language;
                const preview = await api.getStoryboardPreview(
                  capsuleKey,
                  runResult.run_id,
                  3,
                  requestedLanguage
                );
                setStoryboardPreview(preview);
                setPreviewLanguage(preview.output_language ?? requestedLanguage ?? null);
                updateNodeData(capsuleNodeId, {
                  evidence_refs: Array.isArray(preview.evidence_refs) ? preview.evidence_refs : [],
                });
                setIsPreviewLoading(false);
                setPreviewRunId(null);
                previewCapsuleIdRef.current = null;
                setPreviewNotice(null);
                if (previewCancelFallbackRef.current) {
                  clearTimeout(previewCancelFallbackRef.current);
                  previewCancelFallbackRef.current = null;
                }
                if (capsuleStreamRef.current) {
                  capsuleStreamRef.current.close();
                  capsuleStreamRef.current = null;
                }
                return;
              }

              if (event.type === "run.failed") {
                const message =
                  typeof payload.error === "string" ? payload.error : "Preview run failed";
                updateNodeData(capsuleNodeId, { status: "error", streamingData: undefined });
                setError(message);
                setPreviewNotice({ tone: "error", message });
                pushRunLog("error", `${t("runCapsuleFailed")}: ${message}`, runContext);
                setIsPreviewLoading(false);
                setPreviewRunId(null);
                previewCapsuleIdRef.current = null;
                if (previewCancelFallbackRef.current) {
                  clearTimeout(previewCancelFallbackRef.current);
                  previewCancelFallbackRef.current = null;
                }
                if (capsuleStreamRef.current) {
                  capsuleStreamRef.current.close();
                  capsuleStreamRef.current = null;
                }
              }

              if (event.type === "run.cancelled") {
                const message =
                  typeof payload.message === "string" ? payload.message : "Preview cancelled";
                updateNodeData(capsuleNodeId, { status: "cancelled", streamingData: undefined });
                setError(message);
                setPreviewNotice({ tone: "warning", message: t("cancelled") });
                pushToast("warning", t("cancelled"));
                pushRunLog("warning", t("runCapsuleCancelled"), runContext);
                setIsPreviewLoading(false);
                setPreviewRunId(null);
                previewCapsuleIdRef.current = null;
                if (previewCancelFallbackRef.current) {
                  clearTimeout(previewCancelFallbackRef.current);
                  previewCancelFallbackRef.current = null;
                }
                if (capsuleStreamRef.current) {
                  capsuleStreamRef.current.close();
                  capsuleStreamRef.current = null;
                }
              }
            },
            onError: (streamError) => {
              updateNodeData(capsuleNodeId, { status: "error", streamingData: undefined });
              setError(streamError.message);
              setPreviewNotice({ tone: "error", message: streamError.message });
              pushRunLog("error", `${t("runCapsuleFailed")}: ${streamError.message}`, runContext);
              setIsPreviewLoading(false);
              setPreviewRunId(null);
              previewCapsuleIdRef.current = null;
              if (previewCancelFallbackRef.current) {
                clearTimeout(previewCancelFallbackRef.current);
                previewCancelFallbackRef.current = null;
              }
              if (capsuleStreamRef.current) {
                capsuleStreamRef.current.close();
                capsuleStreamRef.current = null;
              }
            },
          });
        } catch (previewErr) {
          console.error("Preview error:", previewErr);
          updateNodeData(capsuleNode.id, { status: "error", streamingData: undefined });
          previewCapsuleIdRef.current = null;
        } finally {
          if (!capsuleStreamRef.current) {
            setIsPreviewLoading(false);
          }
        }
      }
    } catch (err) {
      setError(normalizeApiError(err, t("optimizationFailed")));
    } finally {
      setIsOptimizing(false);
    }
  }, [
    nodes,
    edges,
    canvasId,
    setNodes,
    buildUpstreamContext,
    buildInputValues,
    updateNodeData,
    t,
    language,
    isAdmin,
    pushRunLog,
    pushToast,
    openPreviewPanel,
    previewLanguage,
  ]);

  const previewCapsuleKey = storyboardPreview?.capsule_id;

  const handleCancelPreviewRun = useCallback(() => {
    if (!previewRunId) {
      return;
    }
    if (capsuleStreamRef.current) {
      pushToast("info", t("cancelling"));
      setPreviewNotice({ tone: "info", message: t("cancelling") });
      pushRunLog("info", t("runCancelRequested"), {
        kind: "capsule",
        runId: previewRunId,
        capsuleId: previewCapsuleIdRef.current ?? undefined,
      });
      capsuleStreamRef.current.cancel();
      if (previewCancelFallbackRef.current) {
        clearTimeout(previewCancelFallbackRef.current);
      }
      previewCancelFallbackRef.current = setTimeout(() => {
        if (isPreviewLoadingRef.current) {
          void api.cancelCapsuleRun(previewRunId).catch(() => undefined);
        }
      }, 1200);
      return;
    }
    pushRunLog("info", t("runCancelRequested"), {
      kind: "capsule",
      runId: previewRunId,
      capsuleId: previewCapsuleIdRef.current ?? undefined,
    });
    void api.cancelCapsuleRun(previewRunId).catch((err) => {
      setError(normalizeApiError(err, t("cancelRunError")));
    });
  }, [previewRunId, setError, t, pushRunLog, pushToast]);

  const handlePreviewLanguageChange = useCallback(
    async (language: string) => {
      const capsuleKey = previewCapsuleIdRef.current ?? previewCapsuleKey;
      if (!previewRunId || !capsuleKey) {
        return;
      }
      setPreviewLanguage(language);
      setIsPreviewLoading(true);
      setPreviewNotice(null);
      try {
        const preview = await api.getStoryboardPreview(capsuleKey, previewRunId, 3, language);
        setStoryboardPreview(preview);
        setPreviewLanguage(preview.output_language ?? language);
      } catch (err) {
        const message = normalizeApiError(err, t("previewLoadError"));
        setPreviewNotice({ tone: "error", message });
      } finally {
        setIsPreviewLoading(false);
      }
    },
    [previewCapsuleKey, previewRunId, t]
  );

  const handleGenerate = useCallback(async () => {
    if (!canvasId) {
      setError(t("saveBeforeGenerate"));
      return;
    }
    setIsGenerating(true);
    lastGenerationStatusRef.current = null;
    updateOutputNodes({ status: "loading", generationPreview: undefined });
    setError(null);
    try {
      const run = await api.createGenerationRun(canvasId);
      setGenerationRun(run);
      setGenerationStatus(run.status);
      lastGenerationRunIdRef.current = run.id;
      lastGenerationStatusRef.current = run.status;
      const runContext = { kind: "generation" as const, runId: run.id };
      pushRunLog("info", t("runGenerationStarted"), runContext);
      closePreviewPanel();
      setPreviewRunId(null);
      withViewTransition(() => setShowGenerationPanel(true));
      startGenerationPolling(run.id);
    } catch (err) {
      setError(normalizeApiError(err, t("generationStartFailed")));
      updateOutputNodes({ status: "error" });
      setIsGenerating(false);
    }
  }, [canvasId, closePreviewPanel, pushRunLog, startGenerationPolling, t, updateOutputNodes]);

  const handleOpenGenerationPanel = useCallback(() => {
    if (!generationRun) return;
    withViewTransition(() => setShowGenerationPanel(true));
  }, [generationRun]);

  const handleGenerationFeedback = useCallback(
    async (payload: GenerationRunFeedbackRequest) => {
      if (!generationRun?.id) {
        return;
      }
      setGenerationFeedbackStatus("saving");
      try {
        const updated = await api.submitGenerationFeedback(generationRun.id, payload);
        setGenerationRun(updated);
        setGenerationFeedbackStatus("saved");
      } catch (err) {
        setGenerationFeedbackStatus("error");
        setError(normalizeApiError(err, t("feedbackSaveFailed")));
      }
    },
    [generationRun?.id, setError, t]
  );

  const applyRecommendation = useCallback(
    (params: Record<string, unknown>) => {
      // Find capsule nodes and update their params
      const nextNodes = nodes.map((node) => {
        if (node.type === "capsule") {
          return {
            ...node,
            data: {
              ...node.data,
              params: { ...node.data.params, ...params },
            },
          };
        }
        return node;
      });
      setNodes(nextNodes);
      takeSnapshot(nextNodes, edges);
      setShowRecommendations(false);
    },
    [nodes, edges, setNodes, takeSnapshot]
  );

  // Load canvas from URL param (from template flow)
  useEffect(() => {
    if (urlCanvasId && !canvasId) {
      setIsLoading(true);
      api.loadCanvas(urlCanvasId)
        .then((loaded) => {
          setCanvasId(loaded.id);
          setTitle(loaded.title);
          setIsPublic(loaded.is_public);
          setNodes(loaded.graph_data.nodes as Node<CanvasNodeData>[]);
          setEdges(loaded.graph_data.edges);
          setGraphMeta(loaded.graph_data.meta ?? {});
          takeSnapshot(loaded.graph_data.nodes, loaded.graph_data.edges);
        })
        .catch((err) => {
          setError(normalizeApiError(err, t("canvasLoadError")));
        })
        .finally(() => setIsLoading(false));
    }
  }, [urlCanvasId, canvasId, setNodes, setEdges, takeSnapshot, t]);

  // Initial snapshot (only if not loading from URL)
  useEffect(() => {
    if (!urlCanvasId) {
      takeSnapshot(initialNodes, initialEdges);
    }
  }, [takeSnapshot, urlCanvasId, initialNodes]);

  useEffect(() => {
    if (!canvasId || isLoading) return;
    let active = true;
    const hydrateLastRun = async () => {
      try {
        const runs = await api.listGenerationRuns({ canvas_id: canvasId, limit: 1 });
        if (!active) return;
        const [latest] = runs;
        if (!latest) {
          return;
        }
        if (lastGenerationRunIdRef.current === latest.id) {
          return;
        }
        lastGenerationRunIdRef.current = latest.id;
        lastGenerationStatusRef.current = latest.status;
        setGenerationRun(latest);
        setGenerationStatus(latest.status);
        if (latest.status === "done") {
          const beatSheet = Array.isArray(latest.spec?.beat_sheet) ? latest.spec.beat_sheet : [];
          const storyboard = Array.isArray(latest.spec?.storyboard) ? latest.spec.storyboard : [];
          updateOutputNodes({
            status: "complete",
            generationPreview: {
              beat_sheet: beatSheet,
              storyboard: storyboard,
            },
          });
          setIsGenerating(false);
        } else if (latest.status === "failed") {
          updateOutputNodes({ status: "error" });
          setIsGenerating(false);
        } else {
          setIsGenerating(true);
          startGenerationPolling(latest.id);
        }
      } catch (err) {
        if (!active) return;
        setError(normalizeApiError(err, t("runStatusLoadError")));
      }
    };
    void hydrateLastRun();
    return () => {
      active = false;
    };
  }, [canvasId, isLoading, setError, startGenerationPolling, t, updateOutputNodes]);

  const onConnect = useCallback(
    (connection: Connection) => {
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
    [nodes, setEdges, takeSnapshot]
  );

  const handleAddNode = useCallback(
    (kind: CanvasNodeKind) => {
      const labelMap: Partial<Record<CanvasNodeKind, string>> = {
        input: t("nodeInput"),
        style: t("nodeStyle"),
        customization: t("nodeCustom"),
        processing: t("nodeProcess"),
        capsule: t("nodeCapsule"),
        output: t("nodeOutput"),
      };
      const newNode: Node<CanvasNodeData> = {
        id: createNodeId(),
        type: kind,
        position: {
          x: 400 + Math.random() * 100,
          y: 300 + Math.random() * 100,
        },
        data: {
          label: labelMap[kind] || `New ${kind}`,
          subtitle: t("configureInInspector"),
          locked: kind === "capsule",
        },
      };
      const nextNodes = [...nodes, newNode];
      setNodes(nextNodes);
      takeSnapshot(nextNodes, edges);
    },
    [edges, nodes, setNodes, takeSnapshot, t]
  );

  const handleUndo = useCallback(() => {
    const previous = undo(nodes, edges);
    if (previous) {
      setNodes(previous.nodes as Node<CanvasNodeData>[]);
      setEdges(previous.edges);
    }
  }, [undo, nodes, edges, setNodes, setEdges]);

  const handleRedo = useCallback(() => {
    const next = redo(nodes, edges);
    if (next) {
      setNodes(next.nodes as Node<CanvasNodeData>[]);
      setEdges(next.edges);
    }
  }, [redo, nodes, edges, setNodes, setEdges]);

  const handleUpdateNode = useCallback(
    (nodeId: string, data: Partial<CanvasNodeData>) => {
      updateNodeData(nodeId, data);
    },
    [updateNodeData]
  );

  const handleDeleteNode = useCallback(
    (nodeId: string) => {
      const nextNodes = nodes.filter((node) => node.id !== nodeId);
      const nextEdges = edges.filter(
        (edge) => edge.source !== nodeId && edge.target !== nodeId
      );
      setNodes(nextNodes);
      setEdges(nextEdges);
      setSelectedNode(null);
      takeSnapshot(nextNodes, nextEdges);
    },
    [edges, nodes, setEdges, setNodes, takeSnapshot]
  );

  const handleSave = useCallback(async () => {
    // Wait for session to load before checking auth
    if (isSessionLoading) return;
    if (!session?.authenticated) {
      setShowLoginModal(true);
      return;
    }
    setIsSaving(true);
    setError(null);
    try {
      const payload = {
        title,
        graph_data: { nodes, edges, meta: graphMeta },
        is_public: isPublic,
      };
      const saved = canvasId
        ? await api.updateCanvas(canvasId, payload)
        : await api.createCanvas(payload);
      setCanvasId(saved.id);
    } catch (err) {
      setError(normalizeApiError(err, t("error")));
    } finally {
      setIsSaving(false);
    }
  }, [canvasId, edges, graphMeta, isPublic, nodes, t, title]);

  const handleOpenLoad = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const list = await api.listCanvases();
      setCanvases(list);
      setShowLoadModal(true);
    } catch (err) {
      setError(normalizeApiError(err, t("error")));
    } finally {
      setIsLoading(false);
    }
  }, [t]);

  const handleLoadCanvas = useCallback(
    async (canvas: Canvas) => {
      setIsLoading(true);
      setError(null);
      try {
        const loaded = await api.loadCanvas(canvas.id);
        setCanvasId(loaded.id);
        setTitle(loaded.title);
        setIsPublic(loaded.is_public);
        setNodes(loaded.graph_data.nodes as Node<CanvasNodeData>[]);
        setEdges(loaded.graph_data.edges);
        setGraphMeta(loaded.graph_data.meta ?? {});
        stopGenerationPolling();
        setGenerationRun(null);
        setGenerationStatus(null);
        setIsGenerating(false);
        lastGenerationRunIdRef.current = null;
        lastGenerationStatusRef.current = null;
        setShowLoadModal(false);
        takeSnapshot(loaded.graph_data.nodes, loaded.graph_data.edges);
      } catch (err) {
        setError(normalizeApiError(err, t("error")));
      } finally {
        setIsLoading(false);
      }
    },
    [setEdges, setNodes, takeSnapshot, stopGenerationPolling, t]
  );

  const handleNewCanvas = useCallback(() => {
    // Optional: Also block new canvas? Or allow clearing?
    // Allowing clearing is fine for guest.
    setCanvasId(null);
    setTitle(t("newProject"));
    setIsPublic(false);
    setNodes(initialNodes);
    setEdges(initialEdges);
    setGraphMeta({});
    setSelectedNode(null);
    stopGenerationPolling();
    setGenerationRun(null);
    setGenerationStatus(null);
    setIsGenerating(false);
    lastGenerationRunIdRef.current = null;
    lastGenerationStatusRef.current = null;
    takeSnapshot(initialNodes, initialEdges);
  }, [setEdges, setNodes, takeSnapshot, stopGenerationPolling, t, initialNodes]);

  const toolbarButtons = useMemo(
    () =>
      [
        {
          kind: "input",
          label: t("nodeInput"),
          icon: FileInput,
          iconClass: "text-sky-200 bg-sky-500/15 group-hover:bg-sky-500/25",
          hotkey: "1",
        },
        {
          kind: "style",
          label: t("nodeStyle"),
          icon: Palette,
          iconClass: "text-amber-200 bg-amber-500/15 group-hover:bg-amber-500/25",
          hotkey: "2",
        },
        {
          kind: "customization",
          label: t("nodeCustom"),
          icon: Sliders,
          iconClass: "text-slate-200 bg-slate-500/15 group-hover:bg-slate-500/25",
          hotkey: "3",
        },
        {
          kind: "processing",
          label: t("nodeProcess"),
          icon: Sparkles,
          iconClass: "text-cyan-200 bg-cyan-500/15 group-hover:bg-cyan-500/25",
          hotkey: "4",
        },
        {
          kind: "capsule",
          label: t("nodeCapsule"),
          icon: Workflow,
          iconClass: "text-rose-200 bg-rose-500/15 group-hover:bg-rose-500/25",
          hotkey: "5",
        },
        {
          kind: "output",
          label: t("nodeOutput"),
          icon: FileOutput,
          iconClass: "text-emerald-200 bg-emerald-500/15 group-hover:bg-emerald-500/25",
          hotkey: "6",
        },
      ] as const,
    [t]
  );

  const toastToneConfig = useMemo(
    () => ({
      info: {
        className: "border-sky-500/30 bg-sky-500/10 text-sky-100",
        icon: Info,
      },
      warning: {
        className: "border-amber-500/30 bg-amber-500/10 text-amber-100",
        icon: AlertTriangle,
      },
      error: {
        className: "border-rose-500/30 bg-rose-500/10 text-rose-100",
        icon: XCircle,
      },
    }),
    []
  );

  const runLogToneConfig = useMemo(
    () => ({
      info: "border-sky-500/30 bg-sky-500/10 text-sky-100",
      warning: "border-amber-500/30 bg-amber-500/10 text-amber-100",
      error: "border-rose-500/30 bg-rose-500/10 text-rose-100",
      success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-100",
    }),
    []
  );

  const filteredRunLog = useMemo(() => {
    return runLog.filter((entry) => {
      if (runLogFilters.errorsOnly && !["warning", "error"].includes(entry.tone)) {
        return false;
      }
      const kind = entry.context?.kind;
      if (kind === "capsule" && !runLogFilters.capsule) {
        return false;
      }
      if (kind === "generation" && !runLogFilters.generation) {
        return false;
      }
      return true;
    });
  }, [runLog, runLogFilters]);

  const runLogOffsetClass =
    showPreviewPanel || showGenerationPanel
      ? "bottom-[380px] md:bottom-[440px]"
      : "bottom-6";

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (showEmptyOverlay) return;
      if (event.defaultPrevented) return;
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if (target) {
        const tagName = target.tagName?.toLowerCase();
        const isEditable =
          tagName === "input" ||
          tagName === "textarea" ||
          tagName === "select" ||
          target.isContentEditable ||
          Boolean(target.closest("[contenteditable='true'], [role='textbox']"));
        if (isEditable) return;
      }
      const keyMap: Record<string, CanvasNodeKind> = {
        "1": "input",
        "2": "style",
        "3": "customization",
        "4": "processing",
        "5": "capsule",
        "6": "output",
      };
      const kind = keyMap[event.key];
      if (!kind) return;
      event.preventDefault();
      handleAddNode(kind);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleAddNode, showEmptyOverlay]);

  return (
    <div className="h-screen w-full bg-slate-950 text-slate-100 overflow-hidden relative">
      {/* --- HEADER --- */}
      <header className="absolute top-0 left-0 right-0 z-10 px-4 md:px-6 py-4 flex flex-wrap items-center justify-between gap-2 pointer-events-none overflow-x-auto">
        <div className="pointer-events-auto flex items-center gap-4 bg-slate-950/50 backdrop-blur-md p-2 rounded-2xl border border-white/10 shadow-xl">
          <Link
            href="/"
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
            aria-label={t("back")}
          >
            <ChevronLeft className="h-4 w-4" />
          </Link>
          <div className="flex flex-col px-2">
            <span className="text-[10px] uppercase tracking-widest text-sky-400 font-bold">
              {t("appName")}
            </span>
            <input
              className="bg-transparent text-sm font-bold text-slate-100 focus:outline-none w-40"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t("projectName")}
            />
          </div>
          <div className="h-6 w-px bg-white/10" />
          <div className="flex gap-1">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="group p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
              title={t("save")}
            >
              <Save
                className={`h-4 w-4 ${isSaving ? "animate-spin" : ""}`}
              />
            </button>
            <button
              onClick={handleOpenLoad}
              disabled={isLoading}
              className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
              title={t("openProject")}
            >
              <FolderOpen className="h-4 w-4" />
            </button>
            <button
              onClick={handleNewCanvas}
              className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
              title={t("newProject")}
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="pointer-events-auto flex gap-2">
          {/* Center or Right aligned controls can go here */}
          <div className="bg-slate-950/50 backdrop-blur-md p-2 rounded-2xl border border-white/10 shadow-xl flex gap-1">
            <button
              onClick={handleUndo}
              disabled={!canUndo}
              className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white disabled:opacity-30"
            >
              <Undo className="h-4 w-4" />
            </button>
            <button
              onClick={handleRedo}
              disabled={!canRedo}
              className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white disabled:opacity-30"
            >
              <Redo className="h-4 w-4" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/credits"
              className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-white/10"
              aria-label={`${creditBalance.toLocaleString()} ${t("credits")}`}
            >
              <CreditCard className="h-4 w-4 text-sky-300" />
              <span>{creditBalance.toLocaleString()}</span>
            </Link>
            {generationRun && (
              <button
                onClick={handleOpenGenerationPanel}
                className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-white/10"
                title={t("generationResult")}
              >
                <History className="h-4 w-4 text-emerald-200" />
                {t("generationResult")}
              </button>
            )}
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="bg-emerald-500 hover:bg-emerald-400 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {isGenerating ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {isGenerating ? t("generating") : t("generate")}
            </button>
            {generationStatus && (
              <span className="text-[10px] uppercase tracking-widest text-emerald-200/80">
                {generationStatus}
              </span>
            )}
          </div>

          <button
            onClick={handleRun}
            disabled={isOptimizing}
            className="bg-sky-500 hover:bg-sky-400 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg shadow-sky-500/20 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {isOptimizing ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <Play className="h-4 w-4 fill-current" />
            )}
            {isOptimizing ? t("optimizing") : t("run")}
          </button>
        </div>
      </header>

      {/* Status Toasts */}
      <AnimatePresence>
        {toasts.length > 0 && (
          <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 pointer-events-none">
            {toasts.map((toast) => {
              const tone = toastToneConfig[toast.tone];
              const ToneIcon = tone.icon;
              return (
                <motion.div
                  key={toast.id}
                  initial={{ opacity: 0, y: -12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold shadow-lg backdrop-blur ${tone.className}`}
                >
                  <ToneIcon className="h-4 w-4" />
                  <span>{toast.message}</span>
                </motion.div>
              );
            })}
          </div>
        )}
      </AnimatePresence>

      {/* Error Toast */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-20 left-1/2 -translate-x-1/2 z-50 bg-rose-500/90 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-medium backdrop-blur"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Run Log Panel */}
      <div className={`fixed left-6 md:left-72 z-30 pointer-events-auto transition-all duration-300 ${runLogOffsetClass} ${showEmptyOverlay || showLoadModal ? "opacity-0 pointer-events-none" : "opacity-100"}`}>
        <button
          onClick={() => setIsRunLogOpen((prev) => !prev)}
          className="flex items-center gap-2 rounded-full border border-white/10 bg-slate-950/70 px-4 py-2 text-xs font-semibold text-slate-200 shadow-lg shadow-black/30 transition-colors hover:bg-white/10"
          aria-expanded={isRunLogOpen}
        >
          {t("runLog")}
          {runLog.length > 0 && (
            <span className="rounded-full bg-sky-500/20 px-2 py-0.5 text-[10px] text-sky-200">
              {runLog.length}
            </span>
          )}
        </button>
        <AnimatePresence>
          {isRunLogOpen && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              className="mt-2 w-80 rounded-2xl border border-white/10 bg-slate-950/80 p-4 shadow-2xl backdrop-blur-xl"
            >
              <div className="mb-3 flex items-center justify-between text-[11px] uppercase tracking-widest text-slate-400">
                <span>{t("runLog")}</span>
                {runLog.length > 0 && (
                  <button
                    onClick={() => setRunLog([])}
                    className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-slate-300 hover:bg-white/10"
                  >
                    {t("runLogClear")}
                  </button>
                )}
              </div>
              <div className="mb-3 flex flex-wrap items-center gap-2 text-[10px]">
                <button
                  onClick={() =>
                    setRunLogFilters((prev) => ({ ...prev, capsule: !prev.capsule }))
                  }
                  aria-pressed={runLogFilters.capsule}
                  className={`rounded-full border px-2 py-1 transition-colors ${runLogFilters.capsule
                    ? "border-sky-500/30 bg-sky-500/10 text-sky-200"
                    : "border-white/10 text-slate-400 hover:bg-white/5"
                    }`}
                >
                  {t("runLogFilterCapsule")}
                </button>
                <button
                  onClick={() =>
                    setRunLogFilters((prev) => ({ ...prev, generation: !prev.generation }))
                  }
                  aria-pressed={runLogFilters.generation}
                  className={`rounded-full border px-2 py-1 transition-colors ${runLogFilters.generation
                    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
                    : "border-white/10 text-slate-400 hover:bg-white/5"
                    }`}
                >
                  {t("runLogFilterGeneration")}
                </button>
                <button
                  onClick={() =>
                    setRunLogFilters((prev) => ({ ...prev, errorsOnly: !prev.errorsOnly }))
                  }
                  aria-pressed={runLogFilters.errorsOnly}
                  className={`rounded-full border px-2 py-1 transition-colors ${runLogFilters.errorsOnly
                    ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
                    : "border-white/10 text-slate-400 hover:bg-white/5"
                    }`}
                >
                  {t("runLogFilterErrors")}
                </button>
                {filteredRunLog.length !== runLog.length && (
                  <span className="text-[10px] text-slate-500">
                    {filteredRunLog.length}/{runLog.length}
                  </span>
                )}
              </div>
              {filteredRunLog.length === 0 ? (
                <div className="text-xs text-slate-500">{t("runLogEmpty")}</div>
              ) : (
                <div className="max-h-48 space-y-2 overflow-y-auto pr-1">
                  {filteredRunLog.map((entry) => (
                    <div
                      key={entry.id}
                      className={`rounded-lg border px-3 py-2 text-[11px] ${runLogToneConfig[entry.tone]}`}
                    >
                      <div className="flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-widest text-slate-400">
                        <span>{entry.time}</span>
                        <span>
                          {entry.context?.kind === "capsule"
                            ? t("runLogKindCapsule")
                            : entry.context?.kind === "generation"
                              ? t("runLogKindGeneration")
                              : t("runLogKindSystem")}
                        </span>
                        {entry.context?.runId && (
                          <span
                            className="rounded bg-white/5 px-1.5 font-mono text-[10px] text-slate-300"
                            title={entry.context.runId}
                          >
                            run:{entry.context.runId.slice(0, 6)}
                          </span>
                        )}
                        {entry.context?.capsuleId && (
                          <span
                            className="max-w-[140px] truncate rounded bg-white/5 px-1.5 text-[10px] text-slate-300"
                            title={entry.context.capsuleId}
                          >
                            capsule:{entry.context.capsuleId}
                          </span>
                        )}
                      </div>
                      <div className="mt-1 text-slate-100">{entry.message}</div>
                      {(entry.metrics?.latencyMs !== undefined ||
                        entry.metrics?.costUsd !== undefined) && (
                          <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] text-slate-300">
                            {entry.metrics?.latencyMs !== undefined && (
                              <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-amber-200">
                                {t("latency")}: {entry.metrics.latencyMs}ms
                              </span>
                            )}
                            {entry.metrics?.costUsd !== undefined && (
                              <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-sky-200">
                                {t("costEstimate")}: ${entry.metrics.costUsd.toFixed(3)}
                              </span>
                            )}
                          </div>
                        )}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* --- CANVAS --- */}
      <div className="absolute inset-0 z-0">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={(_, node) =>
            setSelectedNode(node as Node<CanvasNodeData>)
          }
          fitView
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          nodeTypes={nodeTypes as any}
          proOptions={{ hideAttribution: true }}
          minZoom={0.2}
          maxZoom={2}
          onPaneClick={() => setSelectedNode(null)}
        >
          <Background color="#334155" gap={40} size={1} />
          {/* MiniMap for navigation */}
          <MiniMap
            nodeColor={() => "#38bdf8"}
            maskColor="rgba(0, 0, 0, 0.6)"
            style={{
              backgroundColor: "rgba(15, 23, 42, 0.9)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
            }}
          />
          {/* DirectorPack DNA Panel - Top Right */}
          <Panel position="top-right" className="mt-20 mr-4 w-64">
            <CanvasDirectorPackPanel
              state={directorPackState}
              capsuleId={capsuleNode?.data?.capsuleId}
              defaultCollapsed={true}
            />
            {/* Story-First Narrative Panel */}
            <div className="mt-2">
              <CanvasNarrativePanel
                isEnabled={narrativeArcState.isEnabled}
                arc={narrativeArcState.arc}
                selectedHookVariant={narrativeArcState.selectedHookVariant}
                onToggleEnabled={narrativeArcState.toggleEnabled}
                onSetDissonance={narrativeArcState.setDissonance}
                onSetEmotionCurve={narrativeArcState.setEmotionCurve}
                onSelectHookVariant={narrativeArcState.setHookVariant}
              />
            </div>
          </Panel>
          {/* Custom Controls Positioned Bottom Right */}
          <Panel position="bottom-right" className="mb-8 mr-8 flex flex-col gap-2">
            <button onClick={() => zoomIn()} className="bg-slate-900/80 p-2 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:bg-white/10" title="Zoom In">
              <ZoomIn className="h-5 w-5" />
            </button>
            <button onClick={() => zoomOut()} className="bg-slate-900/80 p-2 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:bg-white/10" title="Zoom Out">
              <ZoomOut className="h-5 w-5" />
            </button>
            <button onClick={() => fitView()} className="bg-slate-900/80 p-2 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:bg-white/10" title="Fit View">
              <Maximize2 className="h-5 w-5" />
            </button>
          </Panel>
        </ReactFlow>

      </div>

      {/* Empty Canvas Overlay */}
      {showEmptyOverlay && (
        <EmptyCanvasOverlay
          onSelectSeed={handleSelectSeed}
          onNavigateToTemplates={handleNavigateToTemplates}
        />
      )}

      {/* --- FLOATING DOCK TOOLBAR --- */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10">
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="flex items-center gap-2 p-2 bg-slate-950/60 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl"
        >
          {toolbarButtons.map((btn) => (
            <button
              key={btn.kind}
              onClick={() => handleAddNode(btn.kind)}
              className="group relative flex flex-col items-center justify-center w-16 h-16 rounded-xl border border-transparent hover:border-white/10 hover:bg-white/5 transition-all"
              title={`${btn.label} · ${btn.hotkey}`}
            >
              <div className={`h-8 w-8 rounded flex items-center justify-center transition-colors mb-1 ${btn.iconClass}`}>
                <btn.icon className="h-5 w-5" />
              </div>
              <span className="text-[10px] font-medium text-slate-400 group-hover:text-slate-100">
                {btn.label}
              </span>
              <span className="text-[9px] uppercase tracking-widest text-slate-500 group-hover:text-slate-300">
                {btn.hotkey}
              </span>

              <span className="pointer-events-none absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md border border-white/10 bg-slate-950/90 px-2 py-1 text-[10px] text-slate-200 opacity-0 transition-opacity group-hover:opacity-100">
                {btn.label} · {btn.hotkey}
              </span>
            </button>
          ))}
        </motion.div>
      </div>

      {/* --- INSPECTOR PANEL --- */}
      <Inspector
        selectedNode={selectedNode}
        onClose={() => setSelectedNode(null)}
        onUpdate={handleUpdateNode}
        onDelete={handleDeleteNode}
        onToast={pushToast}
        getInputValues={buildInputValues}
        getUpstreamContext={buildUpstreamContext}
        getConnectedCapsules={getConnectedCapsules}
        canvasId={canvasId}
        isAdminView={isAdmin}
      />

      {/* --- PREVIEW PANEL --- */}
      {showPreviewPanel && (
        <PreviewPanel
          key={previewRunId ?? storyboardPreview?.run_id ?? "preview-panel"}
          preview={storyboardPreview}
          isLoading={isPreviewLoading}
          showCancel={Boolean(previewRunId) && isPreviewLoading}
          onCancel={handleCancelPreviewRun}
          statusNotice={previewNotice ?? undefined}
          outputLanguage={previewLanguage ?? undefined}
          availableLanguages={storyboardPreview?.available_languages}
          onLanguageChange={handlePreviewLanguageChange}
          onClose={() => {
            if (previewRunId && isPreviewLoading) {
              handleCancelPreviewRun();
            }
            closePreviewPanel();
          }}
          isAdminView={isAdmin}
        />
      )}

      {showGenerationPanel && (
        <GenerationPreviewPanel
          run={generationRun}
          isLoading={isGenerating}
          onClose={() => withViewTransition(() => setShowGenerationPanel(false))}
          onSubmitFeedback={handleGenerationFeedback}
        />
      )}

      {/* --- LOAD MODAL --- */}
      <AnimatePresence>
        {showLoadModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={() => setShowLoadModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-950 shadow-2xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-6 border-b border-white/5">
                <h2 className="text-lg font-semibold text-white">{t("openProject")}</h2>
                <button onClick={() => setShowLoadModal(false)} className="text-slate-400 hover:text-white">
                  <Maximize2 className="h-4 w-4 rotate-45" /> {/* Close Icon */}
                </button>
              </div>
              <div className="p-2 max-h-96 overflow-y-auto">
                {canvases.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    {t("noSavedProjects")}
                  </div>
                ) : (
                  <div className="grid gap-1">
                    {canvases.map((canvas) => (
                      <button
                        key={canvas.id}
                        onClick={() => handleLoadCanvas(canvas)}
                        className="flex items-center justify-between w-full p-4 rounded-xl hover:bg-white/5 text-left border border-transparent hover:border-white/5 transition-all group"
                      >
                        <div>
                          <div className="font-semibold text-slate-200 group-hover:text-sky-400 transition-colors">{canvas.title}</div>
                          <div className="text-xs text-slate-500 mt-1">Updated {new Date(canvas.updated_at).toLocaleDateString()}</div>
                        </div>
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                          <FolderOpen className="h-4 w-4 text-slate-400" />
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Recommendations Modal */}
      <AnimatePresence>
        {showRecommendations && recommendations.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-950/95 p-6 shadow-2xl backdrop-blur-xl"
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-bold text-slate-100">{t("gaRecommendations")}</h2>
                  <p className="text-sm text-slate-400">{t("topRecommendations")}</p>
                </div>
                <button
                  onClick={() => setShowRecommendations(false)}
                  className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-3">
                {recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-white/10 bg-slate-900/50 p-4 hover:border-sky-500/30 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-bold text-sky-400 uppercase">
                        {t("recommendation")} {idx + 1}
                      </span>
                      <span className="text-xs font-mono text-slate-500">
                        {t("score")}: {rec.fitness_score.toFixed(1)}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                      {Object.entries(rec.params).slice(0, 4).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-slate-500">{key.replace(/_/g, " ")}</span>
                          <span className="font-mono text-slate-300">
                            {typeof value === "number" ? value.toFixed(2) : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                    <button
                      onClick={() => applyRecommendation(rec.params)}
                      className="w-full py-2 rounded-lg bg-sky-500/10 text-sky-400 text-xs font-semibold hover:bg-sky-500/20 transition-colors"
                    >
                      Apply This Set
                    </button>
                  </div>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <LoginRequiredModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
      />
    </div>
  );
}

import { Suspense } from "react";

function CanvasPageContent() {
  return (
    <AppShell
      showTopBar={false}
      showBackButton={true}
      backHref="/"
    >
      <ReactFlowProvider>
        <CanvasFlow />
      </ReactFlowProvider>
    </AppShell>
  );
}

export default function CanvasPage() {
  return (
    <Suspense fallback={<div className="h-screen w-screen flex items-center justify-center bg-slate-950 text-slate-400">Loading canvas...</div>}>
      <CanvasPageContent />
    </Suspense>
  );
}
