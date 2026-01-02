"use client";

/**
 * Studio Page - Opal-Style Unified UI
 * 
 * Chat at bottom center, Canvas fills the rest.
 * Expert mode shows additional tools and scene list.
 */

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Copy, RefreshCcw, XCircle, ChevronRight, ChevronLeft, Maximize2, Minimize2, MessageSquare } from "lucide-react";
import { ReactFlowProvider } from "@xyflow/react";
import AppShell from "@/components/AppShell";
import PageStatus from "@/components/PageStatus";
import ChatPanel from "@/components/agent/ChatPanel";
import SceneCard from "@/components/agent/SceneCard";
import StudioCanvas from "@/components/studio/StudioCanvas";
import StudioEmptyState from "@/components/studio/StudioEmptyState";
import { useAgentChat } from "@/hooks/useAgentChat";
import type { AgentToolResultEvent, AgentNodeCreatedEvent } from "@/hooks/useAgentChat";
import { useLanguage } from "@/contexts/LanguageContext";
import { copyToClipboard } from "@/lib/clipboard";
import type { WorkflowPlanResponse } from "@/lib/api";
import { formatDateTime } from "@/lib/formatters";

const resolveStatusTone = (status?: string | null) => {
  if (!status) return "border-white/10 bg-white/5 text-slate-300";
  const normalized = status.toLowerCase();
  if (normalized.includes("reject") || normalized.includes("fail")) {
    return "border-rose-500/40 bg-rose-500/10 text-rose-200";
  }
  if (normalized.includes("approve") || normalized.includes("complete")) {
    return "border-emerald-500/40 bg-emerald-500/10 text-emerald-200";
  }
  return "border-amber-500/40 bg-amber-500/10 text-amber-200";
};

const isValidNode = (node: unknown): node is { id: string; type: string; position: { x: number; y: number } } => {
  if (!node || typeof node !== "object") return false;
  const n = node as Record<string, unknown>;
  return (
    typeof n.id === "string" &&
    typeof n.type === "string" &&
    n.position != null &&
    typeof (n.position as Record<string, unknown>).x === "number" &&
    typeof (n.position as Record<string, unknown>).y === "number"
  );
};

const coerceWorkflowPlan = (output: Record<string, unknown>): WorkflowPlanResponse | null => {
  // Check for flat structure
  if (Array.isArray(output.nodes) && Array.isArray(output.edges)) {
    // Validate first node has expected structure
    if (output.nodes.length > 0 && !isValidNode(output.nodes[0])) {
      console.warn("[coerceWorkflowPlan] nodes array has invalid structure");
      return null;
    }
    return output as unknown as WorkflowPlanResponse;
  }

  // Check for nested structure (output.plan or output.workflow)
  const nested = (output.plan || output.workflow) as Record<string, unknown>;
  if (nested && Array.isArray(nested.nodes) && Array.isArray(nested.edges)) {
    if (nested.nodes.length > 0 && !isValidNode(nested.nodes[0])) {
      console.warn("[coerceWorkflowPlan] nested nodes array has invalid structure");
      return null;
    }
    return nested as unknown as WorkflowPlanResponse;
  }

  // Last resort: check if output ITSELF is the plan (if fields are missing but structure looks ok)
  if (Array.isArray(output.nodes)) {
    if (output.nodes.length > 0 && !isValidNode(output.nodes[0])) {
      console.warn("[coerceWorkflowPlan] fallback nodes array has invalid structure");
      return null;
    }
    return {
      nodes: output.nodes as WorkflowPlanResponse["nodes"],
      edges: (output.edges as WorkflowPlanResponse["edges"]) || [],
      workflow_id: (output.workflow_id as string) || "generated",
      narrative_dna: (output.narrative_dna as WorkflowPlanResponse["narrative_dna"]) || null,
      agent_assignments: (output.agent_assignments as Record<string, string>) || {},
      estimated_duration_sec: (output.estimated_duration_sec as number) || 60,
      capsule_id: (output.capsule_id as string) || null,
      logic_vector: (output.logic_vector as Record<string, number>) || null,
      persona_vector: (output.persona_vector as Record<string, number>) || null,
    };
  }

  return null;
};

function StudioPageContent() {
  const { t } = useLanguage();
  const searchParams = useSearchParams();
  const sessionParam = searchParams.get("session");
  const sessionIdRef = useRef<string | null>(sessionParam);

  // Mode state - initialized from localStorage
  const [studioMode, setStudioMode] = useState<"simple" | "expert">("simple");
  const [isExpertPanelOpen, setIsExpertPanelOpen] = useState(true);
  const [isChatMaximized, setIsChatMaximized] = useState(false);

  // Workflow state - direct connection (no BroadcastChannel)
  const [externalWorkflow, setExternalWorkflow] = useState<WorkflowPlanResponse | null>(null);
  const [showEmptyState, setShowEmptyState] = useState(true);
  const [workflowNotice, setWorkflowNotice] = useState<{
    nodes: number;
    edges: number;
    receivedAt: string;
  } | null>(null);

  // Handle tool results - capture compile_workflow results
  const handleToolResult = useCallback(
    (event: AgentToolResultEvent) => {
      console.log("[Studio] Tool result received:", event.name, event);
      if (event.name !== "compile_workflow") return;
      console.log("[Studio] compile_workflow output:", event.output);
      const plan = coerceWorkflowPlan(event.output);
      console.log("[Studio] Coerced plan:", plan);
      if (!plan) {
        console.warn("[Studio] coerceWorkflowPlan returned null - output may not have nodes/edges");
        return;
      }

      // Direct state update - no BroadcastChannel needed
      setExternalWorkflow(plan);
      setShowEmptyState(false);
      setWorkflowNotice({
        nodes: plan.nodes.length,
        edges: plan.edges.length,
        receivedAt: new Date().toISOString(),
      });
    },
    []
  );

  // Ref to StudioCanvas for adding nodes from Agent Chat
  const canvasRef = useRef<{ addExternalNode: (nodeSpec: Record<string, unknown>) => void } | null>(null);

  // Handle node created events from Agent Chat (Teaching tools)
  const handleNodeCreated = useCallback(
    (event: AgentNodeCreatedEvent) => {
      console.log("[Studio] Node created event:", event);
      const { nodeSpec, action } = event;

      if (action === "add_to_canvas" && canvasRef.current) {
        canvasRef.current.addExternalNode(nodeSpec);
        setShowEmptyState(false);
      }
    },
    []
  );

  const {
    session,
    messages,
    scenes,
    isStreaming,
    error,
    loadSession,
    resetSession,
    sendMessage,
    stop,
    approveSession,
    rejectSession,
  } = useAgentChat({ sessionId: sessionParam, onToolResult: handleToolResult, onNodeCreated: handleNodeCreated });

  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null);
  const [modelOverride, setModelOverride] = useState("");
  const [modelTouched, setModelTouched] = useState(false);
  const [sessionInput, setSessionInput] = useState(sessionParam ?? "");
  const [decisionNote, setDecisionNote] = useState("");

  const resolvedSceneId = useMemo(() => {
    if (selectedSceneId && scenes.some((scene) => scene.sceneId === selectedSceneId)) {
      return selectedSceneId;
    }
    return scenes[0]?.sceneId ?? null;
  }, [scenes, selectedSceneId]);

  const selectedScene = useMemo(
    () => scenes.find((scene) => scene.sceneId === resolvedSceneId) ?? null,
    [scenes, resolvedSceneId]
  );

  const modelValue = modelTouched ? modelOverride : session?.agentModel ?? "";
  const isExpertMode = studioMode === "expert";

  // Load mode from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("vivid.studio.mode");
    if (saved === "expert" || saved === "simple") {
      setStudioMode(saved);
    }
  }, []);

  // Persist mode to localStorage
  useEffect(() => {
    localStorage.setItem("vivid.studio.mode", studioMode);
  }, [studioMode]);

  // Update session ref
  useEffect(() => {
    sessionIdRef.current = session?.sessionId ?? sessionParam;
  }, [session?.sessionId, sessionParam]);

  const handleSend = (content: string) => {
    const override = modelTouched ? modelOverride.trim() : "";
    const extra = override ? { model: override } : undefined;
    void sendMessage(content, extra);
  };

  const handleLoadSession = () => {
    const value = sessionInput.trim();
    if (!value) return;
    void loadSession(value);
  };

  const handleResetSession = () => {
    setModelTouched(false);
    setModelOverride("");
    setDecisionNote("");
    setSelectedSceneId(null);
    setWorkflowNotice(null);
    setExternalWorkflow(null);
    resetSession();
  };

  const handleApprove = () => {
    if (!session?.sessionId) return;
    void approveSession(session.sessionId, decisionNote.trim() || undefined);
  };

  const handleReject = () => {
    if (!session?.sessionId) return;
    void rejectSession(session.sessionId, decisionNote.trim() || undefined);
  };

  const workflowTime = workflowNotice ? formatDateTime(workflowNotice.receivedAt) : null;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-950">
      {/* Header */}
      <header className="flex-none border-b border-white/10 bg-slate-950/80 px-4 py-3 backdrop-blur-sm">
        <div className="mx-auto flex max-w-[1800px] items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-100">{t("studioTitle")}</h1>
            <p className="text-xs text-slate-400">{t("studioSubtitle")}</p>
          </div>
          <div className="flex items-center gap-3">
            {/* Mode toggle */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                {t("studioModeLabel")}
              </span>
              <div className="flex rounded-full border border-white/10 bg-white/5 p-1">
                <button
                  type="button"
                  onClick={() => setStudioMode("simple")}
                  className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.2em] transition ${studioMode === "simple"
                    ? "bg-sky-500/20 text-sky-100"
                    : "text-slate-400 hover:text-slate-200"
                    }`}
                >
                  {t("studioModeSimple")}
                </button>
                <button
                  type="button"
                  onClick={() => setStudioMode("expert")}
                  className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.2em] transition ${studioMode === "expert"
                    ? "bg-amber-500/20 text-amber-100"
                    : "text-slate-400 hover:text-slate-200"
                    }`}
                >
                  {t("studioModeExpert")}
                </button>
              </div>
            </div>

            {/* Session status */}
            {session?.status && (
              <span
                className={`rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.2em] ${resolveStatusTone(
                  session.status
                )}`}
              >
                {session.status}
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main content area */}
      <div className="relative flex flex-1 min-h-0">
        {/* Canvas area - fills available space */}
        <div className={`relative flex-1 min-w-0 ${isExpertMode && isExpertPanelOpen ? 'mr-80' : ''} transition-all duration-300`}>
          <ReactFlowProvider>
            <StudioCanvas
              mode="embedded"
              externalWorkflow={externalWorkflow}
              showToolbar={!showEmptyState}
              showMinimap={!showEmptyState}
              showRunLog={isExpertMode && !showEmptyState}
              canvasRef={canvasRef}
            />
          </ReactFlowProvider>

          {/* Chat-first empty state overlay */}
          {showEmptyState && (
            <StudioEmptyState
              onSendPrompt={(prompt) => {
                setShowEmptyState(false);
                handleSend(prompt);
              }}
            />
          )}
        </div>

        {/* Expert panel - slides in from right */}
        {isExpertMode && (
          <>
            {/* Toggle button */}
            <button
              onClick={() => setIsExpertPanelOpen(!isExpertPanelOpen)}
              className={`absolute top-4 z-20 flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-slate-900/90 text-slate-400 backdrop-blur-sm transition hover:text-white ${isExpertPanelOpen ? 'right-[316px]' : 'right-4'
                }`}
            >
              {isExpertPanelOpen ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
            </button>

            {/* Panel content */}
            <aside
              className={`absolute right-0 top-0 bottom-0 w-80 overflow-y-auto border-l border-white/10 bg-slate-950/95 backdrop-blur-sm transition-transform duration-300 ${isExpertPanelOpen ? 'translate-x-0' : 'translate-x-full'
                }`}
            >
              <div className="p-4 space-y-4">
                {/* Session panel */}
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="text-sm font-semibold text-slate-100">{t("studioSessionPanel")}</div>
                  {session && (
                    <div className="mt-3 space-y-3 text-xs text-slate-400">
                      <div>
                        <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                          {t("studioSessionId")}
                        </div>
                        <div className="mt-2 flex items-center gap-2 rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-xs text-slate-200">
                          <span className="max-w-[140px] truncate font-mono text-[11px]" title={session.sessionId}>
                            {session.sessionId}
                          </span>
                          <button
                            type="button"
                            onClick={() => void copyToClipboard(session.sessionId)}
                            className="ml-auto shrink-0 rounded-md border border-white/10 p-1.5 text-slate-400 hover:border-white/20 hover:text-white hover:bg-white/5 transition-colors"
                            title="Copy Session ID"
                          >
                            <Copy className="h-3.5 w-3.5" aria-hidden="true" />
                          </button>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                          {t("studioModel")}
                        </label>
                        <input
                          value={modelValue}
                          onChange={(event) => {
                            setModelTouched(true);
                            setModelOverride(event.target.value);
                          }}
                          placeholder={t("studioModelPlaceholder")}
                          className="w-full rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:border-sky-500/40 focus:outline-none"
                        />
                      </div>
                    </div>
                  )}
                  {!session && (
                    <div className="mt-3 text-xs text-slate-400">{t("studioNoSession")}</div>
                  )}
                </div>

                {/* Scenes panel */}
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-semibold text-slate-100">{t("studioScenes")}</div>
                    <span className="text-xs text-slate-500">{scenes.length}</span>
                  </div>
                  <div className="mt-3 space-y-2 max-h-[300px] overflow-y-auto">
                    {scenes.length === 0 && (
                      <div className="rounded-xl border border-dashed border-white/10 bg-slate-900/30 p-3 text-xs text-slate-400">
                        {t("studioSceneEmpty")}
                      </div>
                    )}
                    {scenes.map((scene) => (
                      <SceneCard
                        key={scene.sceneId}
                        scene={scene}
                        isSelected={scene.sceneId === resolvedSceneId}
                        onSelect={setSelectedSceneId}
                      />
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <textarea
                    value={decisionNote}
                    onChange={(event) => setDecisionNote(event.target.value)}
                    placeholder={t("studioNotePlaceholder")}
                    rows={2}
                    className="w-full resize-none rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:border-sky-500/40 focus:outline-none"
                  />
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={handleApprove}
                      disabled={!session?.sessionId}
                      className="inline-flex items-center gap-1 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-100 transition hover:border-emerald-500/70 hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
                      {t("studioApprove")}
                    </button>
                    <button
                      type="button"
                      onClick={handleReject}
                      disabled={!session?.sessionId}
                      className="inline-flex items-center gap-1 rounded-full border border-rose-500/40 bg-rose-500/10 px-3 py-1.5 text-xs font-semibold text-rose-100 transition hover:border-rose-500/70 hover:bg-rose-500/20 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <XCircle className="h-3 w-3" aria-hidden="true" />
                      {t("studioReject")}
                    </button>
                    <button
                      type="button"
                      onClick={handleResetSession}
                      className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-200 transition hover:border-white/20 hover:bg-white/10"
                    >
                      <RefreshCcw className="h-3 w-3" aria-hidden="true" />
                      {t("studioNewSession")}
                    </button>
                  </div>
                </div>
              </div>
            </aside>
          </>
        )}
      </div>

      {/* Bottom chat - Resizable accordion style */}
      <div className={`flex-none border-t border-white/10 bg-slate-950/95 backdrop-blur-sm relative z-30 transition-all duration-300 ease-in-out ${isChatMaximized ? "h-[75vh]" : "h-20"
        }`}>
        {/* Toggle button */}
        <button
          onClick={() => setIsChatMaximized(!isChatMaximized)}
          className="absolute -top-8 left-1/2 -translate-x-1/2 flex items-center gap-1.5 px-3 py-1.5 rounded-t-lg border border-b-0 border-white/10 bg-slate-900/95 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors text-xs backdrop-blur-sm"
          title={isChatMaximized ? "채팅창 줄이기" : "채팅창 크게 보기"}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span className="font-medium">Chat</span>
          {isChatMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
        </button>

        <div className="h-full mx-auto max-w-4xl px-4 py-4 flex flex-col">
          {/* Error display */}
          {error && (
            <PageStatus
              variant="error"
              title={t("studioErrorTitle")}
              message={error}
              className="mb-3"
            />
          )}

          {/* Workflow notice */}
          {workflowNotice && (
            <div className="mb-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-400">
              <span className="text-emerald-400">●</span>{" "}
              {workflowNotice.nodes} nodes · {workflowNotice.edges} edges
              {workflowTime && <span className="ml-2 text-slate-500">{workflowTime}</span>}
            </div>
          )}

          {/* Chat input */}
          <ChatPanel
            messages={messages}
            isStreaming={isStreaming}
            onSend={handleSend}
            onStop={stop}
            placeholder={t("studioChatPlaceholder")}
            showTools={isExpertMode}
            isMinimized={!isChatMaximized}
          />
        </div>
      </div>
    </div>
  );
}

export default function StudioPage() {
  return (
    <AppShell showTopBar={false}>
      <Suspense fallback={<div className="h-screen w-screen flex items-center justify-center bg-slate-950 text-slate-400">Loading studio...</div>}>
        <StudioPageContent />
      </Suspense>
    </AppShell>
  );
}
