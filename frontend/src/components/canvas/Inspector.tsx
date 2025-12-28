"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Node } from "@xyflow/react";
import { CanvasNodeData, CanvasNodeKind } from "./CustomNodes";
import { api, CapsuleRun, CapsuleRunHistoryItem, CapsuleRunStreamController, CapsuleSpec } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { X, Trash2, Sliders, Play, Lock } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { normalizeAllowedType } from "@/lib/graph";
import { useCapsuleNodeFSM } from "@/hooks/useCapsuleNodeFSM";
import { normalizeApiError } from "@/lib/errors";
import { getBeatLabel, getStoryboardLabel } from "@/lib/narrative";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface InspectorProps {
  selectedNode: Node<CanvasNodeData> | null;
  onClose: () => void;
  onUpdate: (nodeId: string, data: Partial<CanvasNodeData>) => void;
  onDelete?: (nodeId: string) => void;
  onToast?: (tone: "info" | "warning" | "error", message: string) => void;
  getInputValues?: () => Record<string, unknown>;
  getUpstreamContext?: (nodeId: string, contextMode?: "aggregate" | "sequential") => Record<string, unknown>;
  getConnectedCapsules?: (nodeId: string) => Array<{
    nodeId: string;
    capsuleId: string;
    capsuleVersion?: string;
  }>;
  canvasId?: string | null;
  isAdminView?: boolean;
}

type ParamDef = {
  type: "enum" | "number" | "boolean" | "string";
  options?: string[];
  min?: number;
  max?: number;
  step?: number;
  default?: unknown;
  visibility?: "public" | "admin";
};

const NODE_PARAM_DEFS: Partial<Record<CanvasNodeKind, Record<string, ParamDef>>> = {
  input: {
    source_id: { type: "string", default: "" },
    scene_summary: { type: "string", default: "" },
    duration_sec: { type: "number", min: 1, max: 600, step: 1, default: 60 },
  },
  style: {
    style_intensity: { type: "number", min: 0.4, max: 1.0, step: 0.05, default: 0.6 },
    color_bias: { type: "enum", options: ["cool", "neutral", "warm"], default: "neutral" },
    composition: {
      type: "enum",
      options: ["symmetry", "rule_of_thirds", "centered", "leading_lines"],
      default: "rule_of_thirds",
    },
    pacing: { type: "enum", options: ["slow", "medium", "fast"], default: "medium" },
  },
  customization: {
    tone: {
      type: "enum",
      options: ["hopeful", "tense", "melancholic", "playful"],
      default: "hopeful",
    },
    music_mood: {
      type: "enum",
      options: ["ambient", "orchestral", "electronic", "acoustic"],
      default: "ambient",
    },
    personal_theme: { type: "string", default: "" },
    motif: { type: "string", default: "" },
  },
  processing: {
    mode: { type: "enum", options: ["auto", "ga", "rl"], default: "auto" },
    target_profile: {
      type: "enum",
      options: ["balanced", "cinematic", "experimental"],
      default: "balanced",
    },
    objective: {
      type: "enum",
      options: ["balanced", "quality", "efficient", "cost", "latency"],
      default: "balanced",
    },
    iterations: { type: "number", min: 1, max: 50, step: 1, default: 10 },
    temperature: { type: "number", min: 0.1, max: 1.0, step: 0.05, default: 0.7 },
  },
};

export function Inspector({
  selectedNode,
  onClose,
  onUpdate,
  onDelete,
  onToast,
  getInputValues,
  getUpstreamContext,
  getConnectedCapsules,
  canvasId,
  isAdminView = false,
}: InspectorProps) {
  const { t } = useLanguage();
  const sourceIdValue =
    selectedNode?.data?.params && typeof selectedNode.data.params === "object"
      ? (selectedNode.data.params as Record<string, unknown>).source_id ??
      (selectedNode.data.params as Record<string, unknown>).sourceId
      : undefined;
  const [capsuleSpec, setCapsuleSpec] = useState<CapsuleSpec | null>(null);
  const [capsuleError, setCapsuleError] = useState<string | null>(null);
  const [capsuleLoading, setCapsuleLoading] = useState(false);
  const [runResult, setRunResult] = useState<CapsuleRun | null>(null);
  const [runHistory, setRunHistory] = useState<CapsuleRunHistoryItem[]>([]);
  const [runHistoryLoading, setRunHistoryLoading] = useState(false);
  const [runHistoryError, setRunHistoryError] = useState<string | null>(null);
  const [sourceTypeInfo, setSourceTypeInfo] = useState<{
    status: "idle" | "loading" | "ready" | "error" | "unavailable";
    type?: string;
    title?: string;
    error?: string;
  }>({ status: "idle" });
  const [allowedTypeHints, setAllowedTypeHints] = useState<Array<{
    capsuleId: string;
    types: string[];
  }>>([]);

  const getEvidenceWarnings = (
    summary: Record<string, unknown> | null | undefined
  ): string[] => {
    const raw = summary?.evidence_warnings;
    if (!Array.isArray(raw)) {
      return [];
    }
    return raw.filter((item): item is string => typeof item === "string");
  };
  const getOutputWarnings = (
    summary: Record<string, unknown> | null | undefined
  ): string[] => {
    const raw = summary?.output_warnings;
    if (!Array.isArray(raw)) {
      return [];
    }
    return raw.filter((item): item is string => typeof item === "string");
  };
  const [runNotice, setRunNotice] = useState<{ tone: "info" | "warning"; message: string } | null>(null);
  const streamControllerRef = useRef<CapsuleRunStreamController | null>(null);
  const lastRunParamsRef = useRef<Record<string, unknown> | null>(null);
  const cancelFallbackRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const runStatusRef = useRef<"idle" | "loading" | "streaming" | "complete" | "error" | "cancelled">("idle");

  useEffect(() => {
    if (!selectedNode || selectedNode.type !== "capsule" || !selectedNode.data.capsuleId) {
      setCapsuleSpec(null);
      setCapsuleError(null);
      setCapsuleLoading(false);
      setRunHistory([]);
      setRunHistoryError(null);
      setRunHistoryLoading(false);
      return;
    }

    let isActive = true;
    setCapsuleLoading(true);
    setCapsuleError(null);

    api
      .getCapsuleSpec(
        selectedNode.data.capsuleId,
        selectedNode.data.capsuleVersion
      )
      .then((spec) => {
        if (!isActive) return;
        setCapsuleSpec(spec);
      })
      .catch((err) => {
        if (!isActive) return;
        setCapsuleError(normalizeApiError(err, t("capsuleSpecLoadError")));
      })
      .finally(() => {
        if (isActive) setCapsuleLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, [selectedNode, t]);

  const exposedParams = useMemo(() => {
    const spec = capsuleSpec?.spec as { exposedParams?: Record<string, ParamDef> } | undefined;
    const params = spec?.exposedParams || null;
    if (!params) return null;
    if (isAdminView) return params;
    const filtered = Object.fromEntries(
      Object.entries(params).filter(([, def]) => def.visibility !== "admin")
    );
    return Object.keys(filtered).length > 0 ? filtered : null;
  }, [capsuleSpec, isAdminView]);

  const nodeParamDefs = useMemo(() => {
    if (!selectedNode) return null;
    if (selectedNode.type === "capsule") return exposedParams;
    return NODE_PARAM_DEFS[selectedNode.type as CanvasNodeKind] || null;
  }, [selectedNode, exposedParams]);

  useEffect(() => {
    if (!selectedNode || !nodeParamDefs) return;
    if (selectedNode.data.params) return;

    const defaults: Record<string, unknown> = {};
    Object.entries(nodeParamDefs).forEach(([key, def]) => {
      if (def.default !== undefined) {
        defaults[key] = def.default;
        return;
      }
      if (def.type === "number") {
        defaults[key] = typeof def.min === "number" ? def.min : 0;
      } else if (def.type === "enum") {
        defaults[key] = def.options?.[0] ?? "";
      } else if (def.type === "boolean") {
        defaults[key] = false;
      } else {
        defaults[key] = "";
      }
    });
    onUpdate(selectedNode.id, { params: defaults });
  }, [selectedNode, nodeParamDefs, onUpdate]);

  const params = selectedNode?.data?.params || {};
  const processingSeeds = useMemo(() => {
    if (!selectedNode || selectedNode.type !== "processing") return null;
    const data = selectedNode.data as Record<string, unknown>;
    const seed = data.seed && typeof data.seed === "object" ? (data.seed as Record<string, unknown>) : {};
    const storyBeats = Array.isArray(seed.story_beats)
      ? seed.story_beats
      : Array.isArray(data.story_beats)
        ? data.story_beats
        : [];
    const storyboardCards = Array.isArray(seed.storyboard_cards)
      ? seed.storyboard_cards
      : Array.isArray(data.storyboard_cards)
        ? data.storyboard_cards
        : [];
    return { storyBeats, storyboardCards };
  }, [selectedNode]);
  const capsuleVersion =
    selectedNode?.data?.capsuleVersion || capsuleSpec?.version || "latest";
  const patternVersion =
    selectedNode?.data?.patternVersion ||
    (capsuleSpec?.spec && typeof capsuleSpec.spec === "object"
      ? (capsuleSpec.spec as { patternVersion?: string }).patternVersion
      : undefined);
  const capsuleInputContracts =
    capsuleSpec?.spec && typeof capsuleSpec.spec === "object"
      ? (capsuleSpec.spec as { inputContracts?: Record<string, unknown> }).inputContracts
      : selectedNode?.data?.inputContracts;
  const capsuleOutputContracts =
    capsuleSpec?.spec && typeof capsuleSpec.spec === "object"
      ? (capsuleSpec.spec as { outputContracts?: Record<string, unknown> }).outputContracts
      : undefined;
  const upstreamSequenceSummary = useMemo(() => {
    if (!isAdminView || !selectedNode || selectedNode.type !== "capsule" || !getUpstreamContext) {
      return null;
    }
    const inputContracts =
      capsuleSpec?.spec && typeof capsuleSpec.spec === "object"
        ? (capsuleSpec.spec as { inputContracts?: { contextMode?: string } }).inputContracts
        : selectedNode?.data?.inputContracts;
    const rawMode = inputContracts?.contextMode;
    if (rawMode !== "sequential") {
      return null;
    }
    const upstream = getUpstreamContext(selectedNode.id, "sequential");
    const sequence = Array.isArray((upstream as { sequence?: unknown }).sequence)
      ? ((upstream as { sequence?: Array<{ id?: string; label?: string }> }).sequence ?? [])
      : [];
    if (!sequence || sequence.length === 0) return null;
    const first = sequence[0];
    const last = sequence[sequence.length - 1];
    return {
      length: sequence.length,
      first: first?.label ?? first?.id ?? "n/a",
      firstId: first?.id ?? "n/a",
      last: last?.label ?? last?.id ?? "n/a",
      lastId: last?.id ?? "n/a",
    };
  }, [capsuleSpec?.spec, getUpstreamContext, isAdminView, selectedNode]);



  const summaryContextMode =
    runResult?.summary && typeof runResult.summary === "object"
      ? (runResult.summary as { context_mode?: string }).context_mode
      : undefined;

  useEffect(() => {
    if (!selectedNode || selectedNode.type !== "input") {
      setSourceTypeInfo({ status: "idle" });
      return;
    }
    if (!sourceIdValue || typeof sourceIdValue !== "string" || !sourceIdValue.trim()) {
      setSourceTypeInfo({ status: "idle" });
      return;
    }
    if (!isAdminView) {
      setSourceTypeInfo({ status: "unavailable" });
      return;
    }
    let active = true;
    setSourceTypeInfo({ status: "loading" });
    api
      .getRawAsset(sourceIdValue.trim())
      .then((asset) => {
        if (!active) return;
        setSourceTypeInfo({
          status: "ready",
          type: asset.source_type,
          title: asset.title || undefined,
        });
      })
      .catch((err) => {
        if (!active) return;
        const message = normalizeApiError(err, t("sourceTypeLoadError"));
        setSourceTypeInfo({ status: "error", error: message });
      });
    return () => {
      active = false;
    };
  }, [isAdminView, selectedNode, sourceIdValue, t]);

  useEffect(() => {
    if (!selectedNode || selectedNode.type !== "input" || !getConnectedCapsules) {
      setAllowedTypeHints([]);
      return;
    }
    const capsules = getConnectedCapsules(selectedNode.id);
    if (!capsules.length) {
      setAllowedTypeHints([]);
      return;
    }
    let active = true;
    setAllowedTypeHints([]);
    const loadAllowedTypes = async () => {
      const hints: Array<{ capsuleId: string; types: string[] }> = [];
      for (const capsule of capsules.slice(0, 3)) {
        try {
          const spec = await api.getCapsuleSpec(capsule.capsuleId, capsule.capsuleVersion);
          const inputContracts =
            spec?.spec && typeof spec.spec === "object"
              ? (spec.spec as { inputContracts?: { allowedTypes?: string[] } }).inputContracts
              : undefined;
          const types = Array.isArray(inputContracts?.allowedTypes)
            ? inputContracts?.allowedTypes.map((value) => String(value)).filter((value) => value)
            : [];
          if (types.length > 0) {
            hints.push({ capsuleId: capsule.capsuleId, types });
          }
        } catch {
          continue;
        }
      }
      if (active) {
        setAllowedTypeHints(hints);
      }
    };
    void loadAllowedTypes();
    return () => {
      active = false;
    };
  }, [getConnectedCapsules, selectedNode]);

  const renderParamControl = (key: string, def: ParamDef) => {
    const isRunning = runStatus === "loading" || runStatus === "streaming";
    const fallback =
      def.default ??
      (def.type === "number"
        ? def.min ?? 0
        : def.type === "enum"
          ? def.options?.[0] ?? ""
          : def.type === "boolean"
            ? false
            : "");
    const currentValue = params[key] ?? fallback;

    if (def.type === "enum") {
      return (
        <div className="relative group">
          <select
            value={String(currentValue)}
            onChange={(e) =>
              onUpdate(selectedNode!.id, {
                params: {
                  ...params,
                  [key]: e.target.value,
                },
              })
            }
            disabled={isRunning}
            className="w-full appearance-none rounded-xl border border-white/5 bg-[#0a0a0c]/80 px-4 py-2.5 text-xs font-medium text-slate-200 transition-all duration-200 hover:border-white/10 hover:bg-[#151518] focus:border-sky-500/50 focus:bg-[#0a0a0c] focus:outline-none focus:ring-1 focus:ring-sky-500/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {(def.options || []).map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 transition-colors group-hover:text-slate-300">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      );
    }

    if (def.type === "boolean") {
      return (
        <button
          onClick={() =>
            onUpdate(selectedNode!.id, {
              params: {
                ...params,
                [key]: !currentValue,
              },
            })
          }
          disabled={isRunning}
          className={cn(
            "flex w-full items-center justify-between rounded-xl border px-4 py-3 text-xs font-medium transition-all duration-300 disabled:cursor-not-allowed disabled:opacity-50",
            currentValue
              ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-300 shadow-[0_0_15px_-5px_rgba(16,185,129,0.2)]"
              : "border-white/5 bg-[#0a0a0c]/50 text-slate-400 hover:bg-[#151518] hover:text-slate-300 hover:border-white/10"
          )}
        >
          <span className="tracking-wide uppercase text-[10px] font-bold">{currentValue ? "On" : "Off"}</span>
          <div
            className={cn(
              "h-1.5 w-8 rounded-full transition-colors duration-300 relative",
              currentValue ? "bg-emerald-500/30" : "bg-slate-700/30"
            )}
          >
            <motion.div
              layout
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
              className={cn(
                "absolute top-1/2 -translate-y-1/2 h-2.5 w-2.5 rounded-full shadow-sm",
                currentValue ? "bg-emerald-400 right-0 shadow-[0_0_8px_rgba(52,211,153,0.6)]" : "bg-slate-500 left-0"
              )}
            />
          </div>
        </button>
      );
    }

    if (def.type === "number") {
      return (
        <div className="relative pt-1 pb-1">
          <div className="flex items-center gap-3">
            <div className="relative w-full h-1.5 rounded-full bg-slate-800/50">
              <input
                type="range"
                min={def.min ?? 0}
                max={def.max ?? 1}
                step={def.step ?? 0.05}
                value={Number(currentValue)}
                onChange={(e) =>
                  onUpdate(selectedNode!.id, {
                    params: {
                      ...params,
                      [key]: parseFloat(e.target.value),
                    },
                  })
                }
                disabled={isRunning}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10 disabled:cursor-not-allowed"
              />
              <div
                className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-sky-500 to-indigo-500"
                style={{ width: `${((Number(currentValue) - (def.min ?? 0)) / ((def.max ?? 1) - (def.min ?? 0))) * 100}%` }}
              />
              <div
                className="absolute top-1/2 -translate-y-1/2 h-3 w-3 rounded-full bg-slate-200 shadow-[0_0_10px_rgba(255,255,255,0.3)] transition-transform hover:scale-110 pointer-events-none"
                style={{ left: `${((Number(currentValue) - (def.min ?? 0)) / ((def.max ?? 1) - (def.min ?? 0))) * 100}%` }}
              />
            </div>
            <span className="min-w-[3rem] text-right text-[10px] font-mono font-bold text-slate-300 bg-white/5 rounded px-1.5 py-0.5 border border-white/5">
              {Number(currentValue).toFixed(def.step && def.step < 0.1 ? 2 : 1)}
            </span>
          </div>
        </div>
      );
    }

    return (
      <input
        type="text"
        value={String(currentValue)}
        onChange={(e) =>
          onUpdate(selectedNode!.id, {
            params: {
              ...params,
              [key]: e.target.value,
            },
          })
        }
        disabled={isRunning}
        className="w-full rounded-xl border border-white/5 bg-[#0a0a0c]/80 px-4 py-2.5 text-xs text-slate-200 placeholder-slate-600 transition-all duration-200 hover:border-white/10 hover:bg-[#151518] focus:border-sky-500/50 focus:bg-[#0a0a0c] focus:outline-none focus:ring-1 focus:ring-sky-500/20 disabled:cursor-not-allowed disabled:opacity-50"
      />
    );
  };

  const refreshRunHistory = useCallback(async (capsuleId: string) => {
    setRunHistoryLoading(true);
    setRunHistoryError(null);
    try {
      const history = await api.listCapsuleRuns(capsuleId, 5);
      setRunHistory(history);
    } catch (err) {
      setRunHistoryError(normalizeApiError(err, t("runHistoryLoadError")));
    } finally {
      setRunHistoryLoading(false);
    }
  }, [t]);

  useEffect(() => {
    if (!selectedNode || selectedNode.type !== "capsule" || !selectedNode.data.capsuleId) return;
    refreshRunHistory(selectedNode.data.capsuleId);
  }, [selectedNode, refreshRunHistory]);

  const [inputWarning, setInputWarning] = useState<string | null>(null);

  const runCapsule = useCallback(
    async (
      runParams: Record<string, unknown>,
      helpers: {
        receiveChunk: (text: string, isFirst: boolean, progress?: number) => void;
        complete: (result: unknown) => void;
        error: (message: string) => void;
        cancel: (message: string) => void;
      }
    ) => {
      if (!selectedNode || selectedNode.type !== "capsule" || !selectedNode.data.capsuleId) {
        throw new Error("Capsule node not selected");
      }
      const capsuleId = selectedNode.data.capsuleId;
      lastRunParamsRef.current = runParams;

      if (!selectedNode.data.capsuleVersion && capsuleSpec?.version) {
        onUpdate(selectedNode.id, { capsuleVersion: capsuleSpec.version });
      }

      setInputWarning(null);
      const specObj = capsuleSpec?.spec as Record<string, unknown> | undefined;
      const inputContracts = specObj?.inputContracts as Record<string, unknown> | undefined;

      const rawContextMode = inputContracts?.contextMode as string | undefined;
      const contextMode =
        rawContextMode === "aggregate" || rawContextMode === "sequential"
          ? rawContextMode
          : undefined;

      const rawMaxUpstream = inputContracts?.maxUpstream;
      const maxUpstream =
        typeof rawMaxUpstream === "number" && Number.isFinite(rawMaxUpstream)
          ? rawMaxUpstream
          : undefined;

      if (maxUpstream && maxUpstream > 0 && getUpstreamContext) {
        const upstream = getUpstreamContext(selectedNode.id, contextMode);
        const upstreamNodes = Array.isArray(upstream?.nodes) ? upstream.nodes.length : 0;
        if (upstreamNodes > maxUpstream) {
          const message = `Upstream nodes exceed maxUpstream (${upstreamNodes} > ${maxUpstream})`;
          onToast?.("warning", message);
          setInputWarning(message);
          throw new Error(message);
        }
      }
      if (inputContracts?.allowedTypes) {
        const inputs = getInputValues ? getInputValues() : {};
        const sourceIdRaw = inputs?.source_id ?? inputs?.sourceId;
        if (typeof sourceIdRaw === "string" && sourceIdRaw.trim()) {
          const allowedRaw = inputContracts.allowedTypes;
          const allowed = Array.isArray(allowedRaw)
            ? allowedRaw
              .map((value: unknown) => normalizeAllowedType(String(value)))
              .filter((value: string | null): value is string => Boolean(value))
            : [];
          if (allowed.length > 0) {
            try {
              const asset = await api.getRawAsset(sourceIdRaw.trim());
              const normalized = normalizeAllowedType(asset.source_type || "");
              const isAllowed = normalized ? allowed.includes(normalized) : false;
              if (normalized && !isAllowed) {
                const message = `source_type '${asset.source_type}' not allowed (allowed: ${allowed.join(", ")})`;
                onToast?.("warning", message);
                setInputWarning(message);
                throw new Error(message);
              }
            } catch (err) {
              const message = normalizeApiError(err, t("sourceTypeLoadError"));
              if (message.toLowerCase().includes("admin")) {
                setInputWarning(message);
              } else {
                onToast?.("warning", message);
                setInputWarning(message);
                throw err;
              }
            }
          }
        }
      }

      const result = await api.runCapsule({
        capsule_id: capsuleId,
        capsule_version: capsuleVersion,
        inputs: getInputValues ? getInputValues() : {},
        params: runParams,
        node_id: selectedNode.id,
        canvas_id: canvasId || undefined,
        upstream_context:
          canvasId || !getUpstreamContext
            ? undefined
            : getUpstreamContext(selectedNode.id, contextMode),
        async_mode: true,
      });

      if (result.version && selectedNode.data.capsuleVersion !== result.version) {
        onUpdate(selectedNode.id, { capsuleVersion: result.version });
      }

      setRunResult(result);
      await refreshRunHistory(capsuleId);

      let isFirstChunk = true;
      streamControllerRef.current?.close();
      streamControllerRef.current = api.streamCapsuleRun(result.run_id, {
        onEvent: async (event) => {
          const payload = event.payload || {};
          if (
            event.type === "run.queued" ||
            event.type === "run.started" ||
            event.type === "run.progress" ||
            event.type === "run.partial"
          ) {
            const message =
              typeof payload.message === "string"
                ? payload.message
                : typeof payload.text === "string"
                  ? payload.text
                  : "Working...";
            const progress =
              typeof payload.progress === "number" ? payload.progress : undefined;
            helpers.receiveChunk(message, isFirstChunk, progress);
            isFirstChunk = false;
            return;
          }

          if (event.type === "run.completed") {
            const summary =
              typeof payload.summary === "object" && payload.summary !== null
                ? (payload.summary as Record<string, unknown>)
                : {};
            const evidenceRefs = Array.isArray(payload.evidence_refs)
              ? (payload.evidence_refs as string[])
              : [];
            const finalRun: CapsuleRun = {
              run_id: event.run_id,
              status: "done",
              summary,
              evidence_refs: evidenceRefs,
              version: typeof payload.version === "string" ? payload.version : capsuleVersion,
              token_usage:
                typeof payload.token_usage === "object" && payload.token_usage !== null
                  ? (payload.token_usage as Record<string, unknown>)
                  : undefined,
              latency_ms: typeof payload.latency_ms === "number" ? payload.latency_ms : null,
              cost_usd_est: typeof payload.cost_usd_est === "number" ? payload.cost_usd_est : null,
              cached: false,
            };
            setRunResult(finalRun);
            onUpdate(selectedNode.id, { evidence_refs: evidenceRefs });
            helpers.complete(finalRun);
            void refreshRunHistory(capsuleId);
            setRunNotice(null);
            if (cancelFallbackRef.current) {
              clearTimeout(cancelFallbackRef.current);
              cancelFallbackRef.current = null;
            }
            streamControllerRef.current?.close();
            streamControllerRef.current = null;
            return;
          }

          if (event.type === "run.failed") {
            const message =
              typeof payload.error === "string" ? payload.error : "Capsule run failed";
            helpers.error(message);
            setRunNotice({ tone: "warning", message });
            if (cancelFallbackRef.current) {
              clearTimeout(cancelFallbackRef.current);
              cancelFallbackRef.current = null;
            }
            streamControllerRef.current?.close();
            streamControllerRef.current = null;
          }

          if (event.type === "run.cancelled") {
            const message =
              typeof payload.message === "string" ? payload.message : "Run cancelled";
            setRunResult({
              run_id: event.run_id,
              status: "cancelled",
              summary: { message },
              evidence_refs: [],
              version: capsuleVersion,
            });
            helpers.cancel(message);
            setRunNotice({ tone: "warning", message: t("cancelled") });
            onToast?.("warning", t("cancelled"));
            if (cancelFallbackRef.current) {
              clearTimeout(cancelFallbackRef.current);
              cancelFallbackRef.current = null;
            }
            streamControllerRef.current?.close();
            streamControllerRef.current = null;
          }
        },
        onError: (error) => {
          helpers.error(error.message);
          setRunNotice({ tone: "warning", message: error.message });
          if (cancelFallbackRef.current) {
            clearTimeout(cancelFallbackRef.current);
            cancelFallbackRef.current = null;
          }
          streamControllerRef.current?.close();
          streamControllerRef.current = null;
        },
      });

      return;
    },
    [
      capsuleSpec?.version,
      capsuleSpec?.spec,
      capsuleVersion,
      canvasId,
      getInputValues,
      getUpstreamContext,
      onUpdate,
      refreshRunHistory,
      selectedNode,
      t,
      onToast,
    ]
  );

  const {
    state: runStatus,
    errorMessage: runError,
    run,
    reset,
  } = useCapsuleNodeFSM({
    nodeId: selectedNode?.id || "capsule",
    updateNodeData: onUpdate,
    onRun: runCapsule,
  });

  useEffect(() => {
    streamControllerRef.current?.close();
    streamControllerRef.current = null;
    if (cancelFallbackRef.current) {
      clearTimeout(cancelFallbackRef.current);
      cancelFallbackRef.current = null;
    }
    reset();
    setRunResult(null);
    setRunHistory([]);
    setRunHistoryError(null);
    setRunNotice(null);
  }, [selectedNode?.id, reset]);

  useEffect(() => {
    runStatusRef.current = runStatus;
  }, [runStatus]);

  const handleRunCapsule = async () => {
    if (!selectedNode || selectedNode.type !== "capsule" || !selectedNode.data.capsuleId) {
      return;
    }
    setRunNotice(null);
    setRunResult(null);
    await run(params as Record<string, unknown>);
  };

  const handleCancelCapsule = async () => {
    if (!runResult?.run_id) {
      return;
    }
    if (streamControllerRef.current) {
      onToast?.("info", t("cancelling"));
      setRunNotice({ tone: "info", message: t("cancelling") });
      streamControllerRef.current.cancel();
      if (cancelFallbackRef.current) {
        clearTimeout(cancelFallbackRef.current);
      }
      cancelFallbackRef.current = setTimeout(() => {
        if (runStatusRef.current === "loading" || runStatusRef.current === "streaming") {
          void api.cancelCapsuleRun(runResult.run_id).catch(() => undefined);
        }
      }, 1200);
      return;
    }
    try {
      onToast?.("info", t("cancelling"));
      setRunNotice({ tone: "info", message: t("cancelling") });
      const cancelled = await api.cancelCapsuleRun(runResult.run_id);
      setRunResult({
        run_id: cancelled.run_id,
        status: cancelled.status,
        summary: cancelled.summary,
        evidence_refs: cancelled.evidence_refs,
        version: cancelled.version,
        token_usage: cancelled.token_usage,
        latency_ms: cancelled.latency_ms,
        cost_usd_est: cancelled.cost_usd_est,
        cached: false,
      });
    } catch (err) {
      onToast?.("error", t("error"));
      setRunHistoryError(normalizeApiError(err, t("cancelRunError")));
    }
  };

  const handleRetryCapsule = async () => {
    onToast?.("info", t("retrying"));
    setRunNotice({ tone: "info", message: t("retrying") });
    setRunResult(null);
    const retryParams = lastRunParamsRef.current ?? (params as Record<string, unknown>);
    await run(retryParams);
  };

  return (
    <AnimatePresence>
      {selectedNode && (
        <motion.aside
          initial={{ x: "100%", opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: "100%", opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="absolute right-0 top-0 h-full w-80 border-l border-white/10 bg-slate-950/80 p-6 backdrop-blur-2xl shadow-2xl z-20 panel-container"
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500/20 text-sky-400">
                <Sliders className="h-4 w-4" />
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                  {t("inspectorTitle")}
                </p>
                <p className="text-base font-bold text-slate-100 capitalize">
                  {selectedNode.type} {t("inspectorTitle").replace("Inspector", "Node")}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="rounded-full p-2 text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-6">
            {/* Label Input */}
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                {t("nodeLabel")}
              </label>
              <input
                className="w-full rounded-lg border border-white/10 bg-slate-900/50 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-sky-500/50 focus:outline-none focus:ring-1 focus:ring-sky-500/50 transition-all"
                value={selectedNode.data.label}
                onChange={(event) =>
                  onUpdate(selectedNode.id, { label: event.target.value })
                }
                placeholder={t("nodeLabel")}
              />
            </div>

            {/* Subtitle Input */}
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                {t("nodeSubtitle")}
              </label>
              <textarea
                className="w-full resize-none rounded-lg border border-white/10 bg-slate-900/50 px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-sky-500/50 focus:outline-none focus:ring-1 focus:ring-sky-500/50 transition-all"
                rows={3}
                value={selectedNode.data.subtitle || ""}
                onChange={(event) =>
                  onUpdate(selectedNode.id, { subtitle: event.target.value })
                }
                placeholder={t("nodeSubtitle")}
              />
            </div>

            {/* Read-only Metadata */}
            <div className="rounded-lg bg-black/20 p-4 border border-white/5 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">ID</span>
                <span className="font-mono text-slate-300">{selectedNode.id}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">X, Y</span>
                <span className="font-mono text-slate-300">
                  {Math.round(selectedNode.position.x)},{" "}
                  {Math.round(selectedNode.position.y)}
                </span>
              </div>
            </div>

            {/* Node Params (non-capsule) */}
            {selectedNode.type !== "capsule" && nodeParamDefs && (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <div className="h-1 w-1 rounded-full bg-sky-400" />
                  <span className="text-[10px] font-bold uppercase tracking-widest text-sky-400">
                    {t("nodeParams")}
                  </span>
                </div>

                <div className="rounded-lg border border-white/10 bg-slate-900/40 p-4 space-y-3">
                  {Object.entries(nodeParamDefs).map(([key, def]) => (
                    <div key={key} className="space-y-1">
                      <label className="text-[10px] font-medium text-slate-400 uppercase">
                        {key.replace(/_/g, " ")}
                      </label>
                      {renderParamControl(key, def)}
                    </div>
                  ))}
                </div>
                {selectedNode.type === "input" && (
                  <div className="rounded-lg border border-white/10 bg-slate-900/40 p-3 text-xs text-slate-300">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">{t("sourceType")}</span>
                      <span className="font-mono">
                        {sourceTypeInfo.status === "loading" && t("loading")}
                        {sourceTypeInfo.status === "unavailable" && t("sourceTypeAdminOnly")}
                        {sourceTypeInfo.status === "error" && t("sourceTypeUnknown")}
                        {sourceTypeInfo.status === "idle" && t("sourceTypeUnknown")}
                        {sourceTypeInfo.status === "ready" &&
                          (sourceTypeInfo.type ? sourceTypeInfo.type : t("sourceTypeUnknown"))}
                      </span>
                    </div>
                    {sourceTypeInfo.title && (
                      <div className="mt-2 text-[11px] text-slate-400">
                        {sourceTypeInfo.title}
                      </div>
                    )}
                    {allowedTypeHints.length > 0 && (
                      <div className="mt-3 space-y-1 text-[11px] text-slate-400">
                        {allowedTypeHints.map((hint) => (
                          <div key={hint.capsuleId}>
                            {t("allowedTypes")}: {hint.types.join(", ")} · {hint.capsuleId}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {selectedNode.type === "processing" &&
                  processingSeeds &&
                  (processingSeeds.storyBeats.length > 0 || processingSeeds.storyboardCards.length > 0) && (
                    <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs text-slate-200">
                      <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-emerald-300">
                        <span>{t("narrativeSeeds")}</span>
                        <span>
                          {t("beatSheet")}: {processingSeeds.storyBeats.length} · {t("storyboard")}:{" "}
                          {processingSeeds.storyboardCards.length}
                        </span>
                      </div>
                      {processingSeeds.storyBeats.slice(0, 2).map((beat, idx) => {
                        const label = getBeatLabel(beat);
                        if (!label) return null;
                        return (
                          <div key={`beat-${idx}`} className="mt-2 line-clamp-1 text-[11px] text-slate-300">
                            {t("beat")} {idx + 1}: {String(label)}
                          </div>
                        );
                      })}
                      {processingSeeds.storyboardCards.slice(0, 1).map((card, idx) => {
                        const label = getStoryboardLabel(card);
                        if (!label) return null;
                        return (
                          <div key={`story-${idx}`} className="mt-1 line-clamp-1 text-[11px] text-slate-400">
                            {t("shot")} {idx + 1}: {String(label)}
                          </div>
                        );
                      })}
                    </div>
                  )}
              </div>
            )}

            {/* Capsule Node Params */}
            {selectedNode.type === "capsule" && selectedNode.data.capsuleId && (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <div className="h-1 w-1 rounded-full bg-rose-400" />
                  <span className="text-[10px] font-bold uppercase tracking-widest text-rose-400">
                    Capsule Parameters
                  </span>
                </div>

                <div className="rounded-lg border border-rose-500/20 bg-rose-500/5 p-4 space-y-3">
                  <div className="flex items-start gap-2 rounded-md border border-white/5 bg-black/20 px-3 py-2 text-[11px] text-slate-300">
                    <Lock className="mt-0.5 h-3 w-3 text-rose-300" />
                    <div>
                      <div className="text-slate-200">{t("sealedDesc")}</div>
                      {selectedNode.data.locked && (
                        <div className="text-slate-400">{t("lockedDesc")}</div>
                      )}
                    </div>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Capsule</span>
                    <span className="font-mono text-rose-200">
                      {selectedNode.data.capsuleId}
                    </span>
                  </div>
                  {selectedNode.data.capsuleVersion && (
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">{t("version")}</span>
                      <span className="font-mono text-rose-200">
                        {String(selectedNode.data.capsuleVersion)}
                      </span>
                    </div>
                  )}
                  {patternVersion && (
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">{t("patternVersion")}</span>
                      <span className="font-mono text-rose-200">
                        {String(patternVersion)}
                      </span>
                    </div>
                  )}
                  {isAdminView && capsuleInputContracts && (
                    <div className="rounded-lg border border-white/5 bg-black/20 px-3 py-2 text-[10px] text-slate-300">
                      <div className="mb-1 text-[10px] font-semibold uppercase text-slate-400">
                        Capsule Contract
                      </div>
                      {Array.isArray(capsuleInputContracts.required) && capsuleInputContracts.required.length > 0 && (
                        <div>
                          required: {capsuleInputContracts.required.join(", ")}
                        </div>
                      )}
                      {Array.isArray(capsuleInputContracts.optional) && capsuleInputContracts.optional.length > 0 && (
                        <div>
                          optional: {capsuleInputContracts.optional.join(", ")}
                        </div>
                      )}
                      {typeof capsuleInputContracts.maxUpstream === "number" && (
                        <div>maxUpstream: {capsuleInputContracts.maxUpstream}</div>
                      )}
                      {Array.isArray(capsuleInputContracts.allowedTypes) && capsuleInputContracts.allowedTypes.length > 0 && (
                        <div>allowedTypes: {capsuleInputContracts.allowedTypes.join(", ")}</div>
                      )}
                      {typeof capsuleInputContracts.contextMode === "string" && (
                        <div>contextMode: {capsuleInputContracts.contextMode}</div>
                      )}
                      {capsuleOutputContracts &&
                        Array.isArray(capsuleOutputContracts.types) &&
                        capsuleOutputContracts.types.length > 0 && (
                          <div>outputTypes: {capsuleOutputContracts.types.join(", ")}</div>
                        )}
                      {runResult?.summary && typeof runResult.summary === "object" && (
                        <div className="mt-1 text-slate-400">
                          sequence_len:{" "}
                          {typeof (runResult.summary as { sequence_len?: number }).sequence_len === "number"
                            ? (runResult.summary as { sequence_len?: number }).sequence_len
                            : "n/a"}
                        </div>
                      )}
                      {isAdminView && summaryContextMode && (
                        <div className="mt-1 text-slate-400">
                          context_mode: {summaryContextMode}
                        </div>
                      )}
                      {isAdminView && summaryContextMode && typeof (runResult?.summary as { sequence_len?: number }).sequence_len === "number" && (
                        <div className="mt-2 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] text-slate-300">
                          <span>context: {summaryContextMode}</span>
                          <span>seq: {(runResult?.summary as { sequence_len?: number }).sequence_len}</span>
                        </div>
                      )}
                      {upstreamSequenceSummary && (
                        <div className="mt-1 text-slate-400">
                          seq_nodes: {upstreamSequenceSummary.length} ·
                          first: {upstreamSequenceSummary.first} ({upstreamSequenceSummary.firstId}) ·
                          last: {upstreamSequenceSummary.last} ({upstreamSequenceSummary.lastId})
                        </div>
                      )}
                    </div>
                  )}

                  {capsuleLoading && (
                    <div className="text-xs text-slate-400">Loading capsule spec...</div>
                  )}
                  {capsuleError && (
                    <div className="text-xs text-rose-300">{capsuleError}</div>
                  )}

                  {/* Editable Params */}
                  {exposedParams && (
                    <div className="space-y-3 pt-2 border-t border-white/5">
                      {Object.entries(exposedParams).map(([key, def]) => (
                        <div key={key} className="space-y-1">
                          <label className="text-[10px] font-medium text-slate-400 uppercase">
                            {key.replace(/_/g, " ")}
                          </label>
                          {renderParamControl(key, def)}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <button
                    onClick={handleRunCapsule}
                    disabled={runStatus === "loading" || runStatus === "streaming"}
                    className="w-full rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-100 hover:bg-rose-500/20 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {runStatus === "loading" || runStatus === "streaming" ? (
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-rose-200 border-t-transparent" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                    {runStatus === "loading" || runStatus === "streaming" ? t("running") : t("runCapsule")}
                  </button>
                  <button
                    onClick={handleCancelCapsule}
                    disabled={
                      !runResult?.run_id ||
                      (runStatus !== "loading" && runStatus !== "streaming")
                    }
                    className="w-full rounded-lg border border-slate-500/30 bg-slate-500/10 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-500/20 transition-colors disabled:opacity-50"
                  >
                    {t("cancel")}
                  </button>
                  {(runStatus === "error" || runStatus === "cancelled" || runResult?.status === "cancelled") && (
                    <button
                      onClick={handleRetryCapsule}
                      disabled={runStatus === "loading" || runStatus === "streaming"}
                      className="w-full rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-100 hover:bg-emerald-500/20 transition-colors disabled:opacity-50"
                    >
                      {t("retry")}
                    </button>
                  )}
                  {runNotice && (
                    <div
                      className={`rounded-lg border px-3 py-2 text-[11px] font-semibold ${runNotice.tone === "warning"
                        ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
                        : "border-sky-500/30 bg-sky-500/10 text-sky-200"
                        }`}
                    >
                      {runNotice.message}
                    </div>
                  )}
                  {inputWarning && !runNotice && (
                    <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] font-semibold text-amber-200">
                      {inputWarning}
                    </div>
                  )}
                  {runError && <div className="text-xs text-rose-300">{runError}</div>}
                  {runResult && (
                    <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs">
                      {(() => {
                        const evidenceWarnings = getEvidenceWarnings(runResult.summary);
                        const outputWarnings = getOutputWarnings(runResult.summary);
                        const summaryPatternVersion =
                          (runResult.summary as { pattern_version?: string; patternVersion?: string })
                            .pattern_version ||
                          (runResult.summary as { patternVersion?: string }).patternVersion;
                        const summarySourceId =
                          (runResult.summary as { source_id?: string; sourceId?: string }).source_id ||
                          (runResult.summary as { sourceId?: string }).sourceId;
                        const creditCost =
                          typeof (runResult.summary as { credit_cost?: number }).credit_cost === "number"
                            ? (runResult.summary as { credit_cost?: number }).credit_cost
                            : null;
                        const latencyMs =
                          typeof runResult.latency_ms === "number" ? runResult.latency_ms : null;
                        const costUsd =
                          typeof runResult.cost_usd_est === "number" ? runResult.cost_usd_est : null;
                        const tokenUsage =
                          runResult.token_usage && typeof runResult.token_usage === "object"
                            ? (runResult.token_usage as { input?: number; output?: number; total?: number })
                            : null;
                        const tokenTotal =
                          typeof tokenUsage?.total === "number"
                            ? tokenUsage.total
                            : typeof tokenUsage?.input === "number" && typeof tokenUsage?.output === "number"
                              ? tokenUsage.input + tokenUsage.output
                              : null;
                        return (
                          <>
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-emerald-200">{t("runSummary")}</span>
                              <span className="text-slate-400 uppercase">{runResult.status}</span>
                            </div>
                            {runResult.cached && (
                              <div className="mt-1 text-[10px] text-emerald-300 uppercase">{t("cachedResult")}</div>
                            )}
                            {isAdminView &&
                              summaryContextMode &&
                              typeof (runResult.summary as { sequence_len?: number }).sequence_len === "number" && (
                                <div className="mt-2 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] text-slate-300">
                                  <span>context: {summaryContextMode}</span>
                                  <span>seq: {(runResult.summary as { sequence_len?: number }).sequence_len}</span>
                                </div>
                              )}
                            <div className="mt-2 text-slate-200">
                              {String(runResult.summary?.message ?? t("generating"))}
                            </div>
                            <div className="mt-2 text-[10px] text-slate-400">
                              {t("runId")}: {runResult.run_id}
                            </div>
                            {(creditCost !== null || latencyMs !== null || costUsd !== null || tokenTotal !== null) && (
                              <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] text-slate-400">
                                {creditCost !== null && (
                                  <div>{t("creditsCost")}: {creditCost}</div>
                                )}
                                {latencyMs !== null && (
                                  <div>{t("latency")}: {latencyMs}ms</div>
                                )}
                                {costUsd !== null && (
                                  <div>{t("costEstimate")}: ${costUsd.toFixed(3)}</div>
                                )}
                                {tokenTotal !== null && (
                                  <div>
                                    {t("tokenUsage")}: {tokenTotal}
                                    {typeof tokenUsage?.input === "number" && typeof tokenUsage?.output === "number" && (
                                      <span className="ml-1 text-slate-500">
                                        ({tokenUsage.input}/{tokenUsage.output})
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                            {runResult.summary?.pattern_version && (
                              <div className="mt-1 text-[10px] text-slate-500">
                                {t("patternVersion")}: {String(runResult.summary.pattern_version)}
                              </div>
                            )}
                            <div className="mt-2 space-y-1 text-[10px] text-slate-500">
                              {summaryPatternVersion && (
                                <div>{t("patternVersion")}: {String(summaryPatternVersion)}</div>
                              )}
                              {summarySourceId && (
                                <div>{t("sourceId")}: {String(summarySourceId)}</div>
                              )}
                              <details className="rounded-lg border border-white/5 bg-black/20 px-2 py-1">
                                <summary className="cursor-pointer text-[10px] font-semibold text-slate-300">
                                  {t("evidenceRefs")}: {runResult.evidence_refs?.length ?? 0}
                                </summary>
                                <div className="mt-2 space-y-1">
                                  {(runResult.evidence_refs || []).length === 0 ? (
                                    <div className="text-slate-400">{t("noEvidenceRefs")}</div>
                                  ) : (
                                    (runResult.evidence_refs || []).map((ref) => (
                                      <div
                                        key={ref}
                                        className="rounded border border-white/5 bg-black/30 px-2 py-1 text-slate-200"
                                      >
                                        {ref}
                                      </div>
                                    ))
                                  )}
                                </div>
                              </details>
                            </div>
                            {evidenceWarnings.length > 0 && (
                              <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-2 py-2 text-[10px] text-amber-200">
                                <div className="font-semibold">{t("evidenceWarnings")}: {evidenceWarnings.length}</div>
                                <div className="mt-1 space-y-1 text-amber-100/80">
                                  {evidenceWarnings.map((warning) => (
                                    <div key={warning} className="rounded border border-amber-500/20 bg-amber-500/5 px-2 py-1">
                                      {warning}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {outputWarnings.length > 0 && (
                              <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-2 py-2 text-[10px] text-amber-200">
                                <div className="font-semibold">{t("outputWarnings")}: {outputWarnings.length}</div>
                                <div className="mt-1 space-y-1 text-amber-100/80">
                                  {outputWarnings.map((warning) => (
                                    <div key={warning} className="rounded border border-amber-500/20 bg-amber-500/5 px-2 py-1">
                                      {warning}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-slate-400">
                    <span>{t("runHistory")}</span>
                    {runHistoryLoading && <span className="text-slate-500">{t("loading")}</span>}
                  </div>
                  {runHistoryError && (
                    <div className="text-xs text-rose-300">{runHistoryError}</div>
                  )}
                  {runHistory.length === 0 && !runHistoryLoading && !runHistoryError && (
                    <div className="text-xs text-slate-500">{t("noRuns")}</div>
                  )}
                  {runHistory.map((item) => (
                    <div
                      key={item.run_id}
                      className="rounded-lg border border-white/5 bg-slate-900/50 px-3 py-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-slate-300">
                          {item.run_id.slice(0, 8)}
                        </span>
                        <span className="text-[10px] uppercase text-slate-500">
                          {item.status}
                        </span>
                      </div>
                      <div className="mt-1 text-slate-400">
                        {String(item.summary?.message ?? "Capsule executed")}
                      </div>
                      {typeof item.summary?.pattern_version === "string" && item.summary?.pattern_version && (
                        <div className="mt-1 text-[10px] text-slate-500">
                          {t("patternVersion")}: {String(item.summary.pattern_version)}
                        </div>
                      )}
                      {isAdminView && (
                        <div className="mt-1 text-[10px] text-slate-500">
                          {item.summary && typeof item.summary === "object" && "context_mode" in item.summary && (
                            <span>context: {String((item.summary as Record<string, unknown>).context_mode)}</span>
                          )}
                          {item.summary && typeof item.summary === "object" && "sequence_len" in item.summary && typeof (item.summary as Record<string, unknown>).sequence_len === "number" && (
                            <span>{Boolean((item.summary as Record<string, unknown>).context_mode) ? " • " : ""}seq: {String((item.summary as Record<string, unknown>).sequence_len)}</span>
                          )}
                        </div>
                      )}

                      {/* Spacer to prevent layout jumps */}
                      <div className="h-0" />
                      <div className="mt-1 text-[10px] text-slate-500">
                        {new Date(item.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="absolute bottom-6 left-6 right-6">
            {onDelete && (
              <button
                onClick={() => onDelete(selectedNode.id)}
                className="group flex w-full items-center justify-center gap-2 rounded-lg border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm font-semibold text-rose-200 hover:bg-rose-500/20 hover:border-rose-500/30 transition-all"
              >
                <Trash2 className="h-4 w-4 opacity-70 group-hover:opacity-100" />
                {t("deleteNode")}
              </button>
            )}
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
