"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Copy, RefreshCcw, XCircle } from "lucide-react";
import AppShell from "@/components/AppShell";
import PageStatus from "@/components/PageStatus";
import ChatPanel from "@/components/agent/ChatPanel";
import SceneCard from "@/components/agent/SceneCard";
import { useAgentChat } from "@/hooks/useAgentChat";
import type { AgentToolResultEvent } from "@/hooks/useAgentChat";
import { useCanvasSyncChannel } from "@/hooks/useCanvasSyncChannel";
import { useLanguage } from "@/contexts/LanguageContext";
import { copyToClipboard } from "@/lib/clipboard";
import type { CanvasSnapshot, CanvasSyncEvent } from "@/lib/canvasSync";
import { readAutoApplySetting, writeAutoApplySetting } from "@/lib/canvasSync";
import type { WorkflowPlanResponse } from "@/lib/api";

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

const coerceWorkflowPlan = (output: Record<string, unknown>): WorkflowPlanResponse | null => {
  const nodes = output.nodes;
  const edges = output.edges;
  if (!Array.isArray(nodes) || !Array.isArray(edges)) return null;
  return output as WorkflowPlanResponse;
};

export default function StudioPage() {
  const { t } = useLanguage();
  const searchParams = useSearchParams();
  const sessionParam = searchParams.get("session");
  const sessionIdRef = useRef<string | null>(sessionParam);
  const [studioMode, setStudioMode] = useState<"simple" | "expert">("simple");
  const [canvasSnapshot, setCanvasSnapshot] = useState<CanvasSnapshot | null>(null);
  const [autoApplyChatWorkflow, setAutoApplyChatWorkflow] = useState(false);
  const sendCanvasSync = useCanvasSyncChannel((event: CanvasSyncEvent) => {
    if (event.type === "canvas_snapshot" && event.payload.source === "canvas") {
      setCanvasSnapshot(event.payload);
      return;
    }
    if (event.type === "canvas_settings" && event.payload.source === "canvas") {
      const incomingId = event.payload.canvasId ?? null;
      const currentId = canvasSnapshot?.canvasId ?? null;
      if (incomingId !== currentId) {
        return;
      }
      setAutoApplyChatWorkflow(event.payload.autoApplyChatWorkflow);
    }
  });
  const handleToolResult = useCallback(
    (event: AgentToolResultEvent) => {
      if (event.name !== "compile_workflow") return;
      const plan = coerceWorkflowPlan(event.output);
      if (!plan) return;
      const resolvedSessionId = event.sessionId ?? sessionIdRef.current ?? sessionParam;
      sendCanvasSync({
        type: "workflow_plan",
        payload: {
          source: "studio",
          sessionId: resolvedSessionId,
          plan,
        },
      });
    },
    [sendCanvasSync, sessionParam]
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
  } = useAgentChat({ sessionId: sessionParam, onToolResult: handleToolResult });
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

  useEffect(() => {
    if (typeof window === "undefined") return;
    const saved = window.localStorage.getItem("vivid.studio.mode");
    if (saved === "expert" || saved === "simple") {
      setStudioMode(saved);
    }
  }, []);

  useEffect(() => {
    sessionIdRef.current = session?.sessionId ?? sessionParam;
  }, [session?.sessionId, sessionParam]);

  useEffect(() => {
    if (!canvasSnapshot) return;
    setAutoApplyChatWorkflow(readAutoApplySetting(canvasSnapshot.canvasId));
  }, [canvasSnapshot]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem("vivid.studio.mode", studioMode);
  }, [studioMode]);

  const handleToggleAutoApply = () => {
    const next = !autoApplyChatWorkflow;
    setAutoApplyChatWorkflow(next);
    writeAutoApplySetting(canvasSnapshot?.canvasId, next);
    sendCanvasSync({
      type: "canvas_settings",
      payload: {
        source: "studio",
        canvasId: canvasSnapshot?.canvasId ?? null,
        autoApplyChatWorkflow: next,
      },
    });
  };

  const handleSend = (content: string) => {
    const override = modelTouched ? modelOverride.trim() : "";
    const metadata = canvasSnapshot ? { canvas_snapshot: canvasSnapshot } : undefined;
    const extra =
      override || metadata
        ? {
            model: override || undefined,
            metadata,
          }
        : undefined;
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

  const gridClassName = isExpertMode
    ? "grid gap-6 xl:grid-cols-[260px_minmax(0,1fr)_320px]"
    : "grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]";

  return (
    <AppShell showTopBar={false}>
      <div className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-2xl font-semibold text-slate-100">{t("studioTitle")}</div>
              <p className="text-sm text-slate-400">{t("studioSubtitle")}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                {t("studioModeLabel")}
              </span>
              <div className="flex rounded-full border border-white/10 bg-white/5 p-1">
                <button
                  type="button"
                  onClick={() => setStudioMode("simple")}
                  className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.2em] transition ${
                    studioMode === "simple"
                      ? "bg-sky-500/20 text-sky-100"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {t("studioModeSimple")}
                </button>
                <button
                  type="button"
                  onClick={() => setStudioMode("expert")}
                  className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.2em] transition ${
                    studioMode === "expert"
                      ? "bg-amber-500/20 text-amber-100"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {t("studioModeExpert")}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <PageStatus
              variant="error"
              title={t("studioErrorTitle")}
              message={error}
              className="mb-6"
            />
          )}

          <div className={gridClassName}>
            {isExpertMode && (
              <div className="order-2 xl:order-1">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-semibold text-slate-100">{t("studioScenes")}</div>
                  <span className="text-xs text-slate-500">{scenes.length}</span>
                </div>
                <div className="mt-4 space-y-3 overflow-y-auto pr-1 xl:max-h-[calc(100vh-240px)]">
                  {scenes.length === 0 && (
                    <div className="rounded-2xl border border-dashed border-white/10 bg-slate-900/30 p-4 text-xs text-slate-400">
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
              </div>
            )}

            <div className={`${isExpertMode ? "order-1 xl:order-2" : "order-1"} min-h-[640px]`}>
              <ChatPanel
                messages={messages}
                isStreaming={isStreaming}
                onSend={handleSend}
                onStop={stop}
                placeholder={t("studioChatPlaceholder")}
                showTools={isExpertMode}
              />
            </div>

            <div className={`${isExpertMode ? "order-3" : "order-2"} space-y-6`}>
              <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-semibold text-slate-100">{t("studioSessionPanel")}</div>
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
                {!session && (
                  <div className="mt-3 text-xs text-slate-400">{t("studioNoSession")}</div>
                )}
                {session && (
                  <div className="mt-4 space-y-3 text-xs text-slate-400">
                    <div>
                      <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                        {t("studioSessionId")}
                      </div>
                      <div className="mt-2 flex items-center gap-2 rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-xs text-slate-200">
                        <span className="truncate font-mono">{session.sessionId}</span>
                        <button
                          type="button"
                          onClick={() => {
                            void copyToClipboard(session.sessionId);
                          }}
                          className="ml-auto rounded-full border border-white/10 px-2 py-1 text-[10px] text-slate-300 hover:border-white/20 hover:text-white"
                        >
                          <Copy className="h-3 w-3" aria-hidden="true" />
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
                {canvasSnapshot && (
                  <div className="mt-4 rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-xs text-slate-300">
                    <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                      {t("studioCanvasLinked")}
                    </div>
                    <div className="mt-2 flex items-center justify-between gap-2">
                      <span className="truncate">
                        {canvasSnapshot.title || canvasSnapshot.canvasId || t("studioCanvasUntitled")}
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {new Date(canvasSnapshot.updatedAt).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="mt-3 flex items-center justify-between gap-2">
                      <span className="text-[11px] text-slate-400">{t("canvasChatAutoApply")}</span>
                      <button
                        type="button"
                        onClick={handleToggleAutoApply}
                        title={t("canvasChatAutoApplyHint")}
                        aria-pressed={autoApplyChatWorkflow}
                        className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[10px] uppercase tracking-[0.2em] transition ${
                          autoApplyChatWorkflow
                            ? "border-emerald-400/60 bg-emerald-500/15 text-emerald-100"
                            : "border-white/10 bg-white/5 text-slate-300 hover:border-white/20 hover:bg-white/10"
                        }`}
                      >
                        <span
                          className={`h-2 w-2 rounded-full ${
                            autoApplyChatWorkflow ? "bg-emerald-400" : "bg-slate-500"
                          }`}
                        />
                        {autoApplyChatWorkflow ? "ON" : "OFF"}
                      </button>
                    </div>
                  </div>
                )}
                <div className="mt-4 space-y-2">
                  <label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                    {t("studioLoadSession")}
                  </label>
                  <div className="flex gap-2">
                    <input
                      value={sessionInput}
                      onChange={(event) => setSessionInput(event.target.value)}
                      placeholder={t("studioSessionId")}
                      className="flex-1 rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:border-sky-500/40 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={handleLoadSession}
                      className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-200 hover:border-white/20 hover:bg-white/10"
                    >
                      {t("studioLoad")}
                    </button>
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  <label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">
                    {t("studioNotePlaceholder")}
                  </label>
                  <textarea
                    value={decisionNote}
                    onChange={(event) => setDecisionNote(event.target.value)}
                    placeholder={t("studioNotePlaceholder")}
                    rows={2}
                    className="w-full resize-none rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:border-sky-500/40 focus:outline-none"
                  />
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={handleApprove}
                      disabled={!session?.sessionId}
                      className="inline-flex items-center gap-2 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-100 transition hover:border-emerald-500/70 hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                      {t("studioApprove")}
                    </button>
                    <button
                      type="button"
                      onClick={handleReject}
                      disabled={!session?.sessionId}
                      className="inline-flex items-center gap-2 rounded-full border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-100 transition hover:border-rose-500/70 hover:bg-rose-500/20 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
                      {t("studioReject")}
                    </button>
                    <button
                      type="button"
                      onClick={handleResetSession}
                      className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:border-white/20 hover:bg-white/10"
                    >
                      <RefreshCcw className="h-3.5 w-3.5" aria-hidden="true" />
                      {t("studioNewSession")}
                    </button>
                  </div>
                  <div className="text-[11px] text-slate-500">{t("studioStatusHint")}</div>
                </div>
              </div>

              {isExpertMode && (
                <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                  <div className="text-sm font-semibold text-slate-100">{t("studioScenePreview")}</div>
                  <div className="mt-4">
                    {selectedScene ? (
                      <SceneCard scene={selectedScene} variant="detail" />
                    ) : (
                      <div className="rounded-2xl border border-dashed border-white/10 bg-slate-900/30 p-4 text-xs text-slate-400">
                        {t("studioSceneEmpty")}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
