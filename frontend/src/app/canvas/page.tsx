"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
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
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { motion, AnimatePresence } from "framer-motion";
import {
  Save,
  FolderOpen,
  Plus,
  Undo,
  Redo,
  Maximize2,
  ZoomIn,
  ZoomOut,
  Play,
  Sparkles,
  Box,
  X,
} from "lucide-react";

import {
  CanvasNode,
  CanvasNodeData,
  CanvasNodeKind,
} from "@/components/canvas/CustomNodes";
import { Inspector } from "@/components/canvas/Inspector";
import { PreviewPanel } from "@/components/canvas/PreviewPanel";
import { GenerationPreviewPanel } from "@/components/canvas/GenerationPreviewPanel";
import { api, Canvas, GenerationRun, StoryboardPreview } from "@/lib/api";
import { useUndoRedo } from "@/hooks/useUndoRedo";
import { useLanguage } from "@/contexts/LanguageContext";


const nodeTypes = {
  input: CanvasNode,
  style: CanvasNode,
  customization: CanvasNode,
  processing: CanvasNode,
  output: CanvasNode,
  capsule: CanvasNode,
};

const initialNodes: Node<CanvasNodeData>[] = [
  {
    id: "input-1",
    type: "input",
    position: { x: 100, y: 300 },
    data: { label: "Prompt Input", subtitle: "User request" },
  },
  {
    id: "processing-1",
    type: "processing",
    position: { x: 450, y: 300 },
    data: { label: "Reasoning Core", subtitle: "LLM + GA" },
  },
  {
    id: "output-1",
    type: "output",
    position: { x: 800, y: 300 },
    data: { label: "Final Response", subtitle: "Rendered Output" },
  },
];

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
  const { t } = useLanguage();

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
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
  const [generationRun, setGenerationRun] = useState<GenerationRun | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<string | null>(null);
  const generationPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [showGenerationPanel, setShowGenerationPanel] = useState(false);

  const { takeSnapshot, undo, redo, canUndo, canRedo } = useUndoRedo();

  const updateOutputNodes = useCallback(
    (data: Partial<CanvasNodeData>) => {
      setNodes((current) =>
        current.map((node) =>
          node.type === "output"
            ? { ...node, data: { ...node.data, ...data } }
            : node
        )
      );
      setSelectedNode((current) =>
        current && current.type === "output"
          ? ({ ...current, data: { ...current.data, ...data } } as Node<CanvasNodeData>)
          : current
      );
    },
    [setNodes]
  );

  useEffect(() => {
    return () => {
      if (generationPollRef.current) {
        clearInterval(generationPollRef.current);
      }
    };
  }, []);

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
    generationPollRef.current = setInterval(async () => {
      try {
        const run = await api.getGenerationRun(runId);
        setGenerationRun(run);
        setGenerationStatus(run.status);
        if (run.status === "done") {
          const beatSheet = Array.isArray(run.spec?.beat_sheet) ? run.spec.beat_sheet : [];
          const storyboard = Array.isArray(run.spec?.storyboard) ? run.spec.storyboard : [];
          updateOutputNodes({
            status: "success",
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
          setShowGenerationPanel(true);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch run status");
        updateOutputNodes({ status: "error" });
        stopGenerationPolling();
        setIsGenerating(false);
      }
    }, 1500);
  }, [stopGenerationPolling, updateOutputNodes]);

  const handleRun = useCallback(async () => {
    setIsOptimizing(true);
    setError(null);
    try {
      const processingNode = nodes.find((node) => node.type === "processing");
      const targetProfile =
        typeof processingNode?.data?.params?.target_profile === "string"
          ? (processingNode.data.params.target_profile as string)
          : "balanced";
      const result = await api.optimizeParams(nodes, edges, targetProfile);
      setRecommendations(result.recommendations);
      setShowRecommendations(true);

      // Also run capsule and get preview for any capsule nodes
      const capsuleNode = nodes.find((n) => n.type === "capsule");
      if (capsuleNode && capsuleNode.data.capsuleId) {
        setIsPreviewLoading(true);
        setShowPreviewPanel(true);
        try {
          const runResult = await api.runCapsule({
            canvas_id: canvasId || undefined,
            node_id: capsuleNode.id,
            capsule_id: capsuleNode.data.capsuleId,
            capsule_version: capsuleNode.data.capsuleVersion || "latest",
            inputs: {},
            params: capsuleNode.data.params || {},
          });
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
          const preview = await api.getStoryboardPreview(
            capsuleNode.data.capsuleId,
            runResult.run_id,
            3
          );
          setStoryboardPreview(preview);
        } catch (previewErr) {
          console.error("Preview error:", previewErr);
        } finally {
          setIsPreviewLoading(false);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Optimization failed");
    } finally {
      setIsOptimizing(false);
    }
  }, [nodes, edges, canvasId, setNodes]);

  const handleGenerate = useCallback(async () => {
    if (!canvasId) {
      setError("Save the canvas before generating.");
      return;
    }
    setIsGenerating(true);
    updateOutputNodes({ status: "running", generationPreview: undefined });
    setError(null);
    try {
      const run = await api.createGenerationRun(canvasId);
      setGenerationRun(run);
      setGenerationStatus(run.status);
      setShowGenerationPanel(true);
      startGenerationPolling(run.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed to start");
      updateOutputNodes({ status: "error" });
      setIsGenerating(false);
    }
  }, [canvasId, startGenerationPolling, updateOutputNodes]);

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
          takeSnapshot(loaded.graph_data.nodes, loaded.graph_data.edges);
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : "Failed to load canvas");
        })
        .finally(() => setIsLoading(false));
    }
  }, [urlCanvasId, canvasId, setNodes, setEdges, takeSnapshot]);

  // Initial snapshot (only if not loading from URL)
  useEffect(() => {
    if (!urlCanvasId) {
      takeSnapshot(initialNodes, initialEdges);
    }
  }, [takeSnapshot, urlCanvasId]);

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
      const newNode: Node<CanvasNodeData> = {
        id: createNodeId(),
        type: kind,
        position: {
          x: 400 + Math.random() * 100,
          y: 300 + Math.random() * 100,
        },
        data: {
          label: `New ${kind}`,
          subtitle: "Configure in inspector",
        },
      };
      const nextNodes = [...nodes, newNode];
      setNodes(nextNodes);
      takeSnapshot(nextNodes, edges);
    },
    [edges, nodes, setNodes, takeSnapshot]
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
      const nextNodes = nodes.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...data } }
          : node
      );
      setNodes(nextNodes);
      setSelectedNode((current) =>
        current && current.id === nodeId
          ? ({ ...current, data: { ...current.data, ...data } } as Node<CanvasNodeData>)
          : current
      );
    },
    [nodes, setNodes]
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
    setIsSaving(true);
    setError(null);
    try {
      const payload = {
        title,
        graph_data: { nodes, edges },
        is_public: isPublic,
      };
      const saved = canvasId
        ? await api.updateCanvas(canvasId, payload)
        : await api.createCanvas(payload);
      setCanvasId(saved.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setIsSaving(false);
    }
  }, [canvasId, edges, isPublic, nodes, title]);

  const handleOpenLoad = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const list = await api.listCanvases();
      setCanvases(list);
      setShowLoadModal(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setIsLoading(false);
    }
  }, []);

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
        stopGenerationPolling();
        setGenerationRun(null);
        setGenerationStatus(null);
        setIsGenerating(false);
        setShowLoadModal(false);
        takeSnapshot(loaded.graph_data.nodes, loaded.graph_data.edges);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Load failed");
      } finally {
        setIsLoading(false);
      }
    },
    [setEdges, setNodes, takeSnapshot, stopGenerationPolling]
  );

  const handleNewCanvas = useCallback(() => {
    setCanvasId(null);
    setTitle(t("newProject"));
    setIsPublic(false);
    setNodes(initialNodes);
    setEdges(initialEdges);
    setSelectedNode(null);
    stopGenerationPolling();
    setGenerationRun(null);
    setGenerationStatus(null);
    setIsGenerating(false);
    takeSnapshot(initialNodes, initialEdges);
  }, [setEdges, setNodes, takeSnapshot, stopGenerationPolling, t]);

  const toolbarButtons = useMemo(
    () =>
      [
        { kind: "input", label: t("nodeInput") },
        { kind: "style", label: t("nodeStyle") },
        { kind: "customization", label: t("nodeCustom") },
        { kind: "processing", label: t("nodeProcess") },
        { kind: "output", label: t("nodeOutput") },
      ] as const,
    [t]
  );

  return (
    <div className="h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden relative">
      {/* --- HEADER --- */}
      <header className="absolute top-0 left-0 right-0 z-10 px-6 py-4 flex items-center justify-between pointer-events-none">
        <div className="pointer-events-auto flex items-center gap-4 bg-slate-950/50 backdrop-blur-md p-2 rounded-2xl border border-white/10 shadow-xl">
          <div className="flex flex-col px-2">
            <span className="text-[10px] uppercase tracking-widest text-sky-400 font-bold">
              {t("appName")}
            </span>
            <input
              className="bg-transparent text-sm font-bold text-slate-100 focus:outline-none w-40"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Project Name"
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
          {/* Custom Controls Positioned Bottom Right */}
          <Panel position="bottom-right" className="mb-8 mr-8 flex flex-col gap-2">
            <button className="bg-slate-900/80 p-2 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:bg-white/10" title="Zoom In">
              <ZoomIn className="h-5 w-5" />
            </button>
            <button className="bg-slate-900/80 p-2 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:bg-white/10" title="Zoom Out">
              <ZoomOut className="h-5 w-5" />
            </button>
            <button className="bg-slate-900/80 p-2 rounded-lg border border-white/10 text-slate-400 hover:text-white hover:bg-white/10" title="Fit View">
              <Maximize2 className="h-5 w-5" />
            </button>
          </Panel>
        </ReactFlow>
      </div>

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
            >
              <div className="h-8 w-8 rounded bg-slate-800 group-hover:bg-sky-500/20 group-hover:text-sky-400 flex items-center justify-center transition-colors text-slate-400 mb-1">
                <Box className="h-5 w-5" />
              </div>
              <span className="text-[10px] font-medium text-slate-400 group-hover:text-slate-100">
                {btn.label}
              </span>

              {/* Tooltip hint could go here */}
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
      />

      {/* --- PREVIEW PANEL --- */}
      {showPreviewPanel && (
        <PreviewPanel
          preview={storyboardPreview}
          isLoading={isPreviewLoading}
          onClose={() => {
            setShowPreviewPanel(false);
            setStoryboardPreview(null);
          }}
        />
      )}

      {showGenerationPanel && (
        <GenerationPreviewPanel
          run={generationRun}
          isLoading={isGenerating}
          onClose={() => setShowGenerationPanel(false)}
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
    </div>
  );
}

import { Suspense } from "react";

function CanvasPageContent() {
  return (
    <ReactFlowProvider>
      <CanvasFlow />
    </ReactFlowProvider>
  );
}

export default function CanvasPage() {
  return (
    <Suspense fallback={<div className="h-screen w-screen flex items-center justify-center bg-slate-950 text-slate-400">Loading canvas...</div>}>
      <CanvasPageContent />
    </Suspense>
  );
}
