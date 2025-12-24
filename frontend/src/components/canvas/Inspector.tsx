"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Node } from "@xyflow/react";
import { CanvasNodeData, CanvasNodeKind } from "./CustomNodes";
import { api, CapsuleRun, CapsuleRunHistoryItem, CapsuleSpec } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { X, Trash2, Sliders, Play, Lock } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface InspectorProps {
  selectedNode: Node<CanvasNodeData> | null;
  onClose: () => void;
  onUpdate: (nodeId: string, data: Partial<CanvasNodeData>) => void;
  onDelete?: (nodeId: string) => void;
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
    iterations: { type: "number", min: 1, max: 50, step: 1, default: 10 },
    temperature: { type: "number", min: 0.1, max: 1.0, step: 0.05, default: 0.7 },
  },
};

export function Inspector({
  selectedNode,
  onClose,
  onUpdate,
  onDelete,
}: InspectorProps) {
  const { t } = useLanguage();
  const [capsuleSpec, setCapsuleSpec] = useState<CapsuleSpec | null>(null);
  const [capsuleError, setCapsuleError] = useState<string | null>(null);
  const [capsuleLoading, setCapsuleLoading] = useState(false);
  const [runStatus, setRunStatus] = useState<
    "idle" | "running" | "success" | "error"
  >("idle");
  const [runError, setRunError] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<CapsuleRun | null>(null);
  const [runHistory, setRunHistory] = useState<CapsuleRunHistoryItem[]>([]);
  const [runHistoryLoading, setRunHistoryLoading] = useState(false);
  const [runHistoryError, setRunHistoryError] = useState<string | null>(null);

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
        setCapsuleError(err instanceof Error ? err.message : "Failed to load capsule spec");
      })
      .finally(() => {
        if (isActive) setCapsuleLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, [selectedNode]);

  useEffect(() => {
    setRunStatus("idle");
    setRunError(null);
    setRunResult(null);
  }, [selectedNode?.id]);

  const exposedParams = useMemo(() => {
    const spec = capsuleSpec?.spec as { exposedParams?: Record<string, ParamDef> } | undefined;
    return spec?.exposedParams || null;
  }, [capsuleSpec]);

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
  const capsuleVersion =
    selectedNode?.data?.capsuleVersion || capsuleSpec?.version || "latest";

  const renderParamControl = (key: string, def: ParamDef) => {
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
          className="w-full rounded border border-white/10 bg-slate-900/50 px-2 py-1.5 text-xs text-slate-100"
        >
          {(def.options || []).map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
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
          className={`w-full rounded border px-2 py-1.5 text-xs ${currentValue
            ? "border-emerald-400/40 bg-emerald-500/10 text-emerald-200"
            : "border-white/10 bg-slate-900/50 text-slate-400"
            }`}
        >
          {currentValue ? "Enabled" : "Disabled"}
        </button>
      );
    }

    if (def.type === "number") {
      return (
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
          className="w-full accent-rose-400"
        />
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
        className="w-full rounded border border-white/10 bg-slate-900/50 px-2 py-1.5 text-xs text-slate-100"
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
      setRunHistoryError(err instanceof Error ? err.message : "Failed to load run history");
    } finally {
      setRunHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!selectedNode || selectedNode.type !== "capsule" || !selectedNode.data.capsuleId) return;
    refreshRunHistory(selectedNode.data.capsuleId);
  }, [selectedNode, refreshRunHistory]);

  const handleRunCapsule = async () => {
    if (!selectedNode || selectedNode.type !== "capsule" || !selectedNode.data.capsuleId) {
      return;
    }

    setRunStatus("running");
    setRunError(null);
    onUpdate(selectedNode.id, { status: "running" });

    if (!selectedNode.data.capsuleVersion && capsuleSpec?.version) {
      onUpdate(selectedNode.id, { capsuleVersion: capsuleSpec.version });
    }

    try {
      const result = await api.runCapsule({
        capsule_id: selectedNode.data.capsuleId,
        capsule_version: capsuleVersion,
        inputs: {},
        params: params as Record<string, unknown>,
        node_id: selectedNode.id,
      });
      setRunResult(result);
      setRunStatus("success");
      onUpdate(selectedNode.id, {
        status: "success",
        capsuleVersion:
          selectedNode.data.capsuleVersion || result.version || capsuleVersion,
      });
      await refreshRunHistory(selectedNode.data.capsuleId);
    } catch (err) {
      setRunError(err instanceof Error ? err.message : "Capsule run failed");
      setRunStatus("error");
      onUpdate(selectedNode.id, { status: "error" });
    }
  };

  return (
    <AnimatePresence>
      {selectedNode && (
        <motion.aside
          initial={{ x: "100%", opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: "100%", opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="absolute right-0 top-0 h-full w-80 border-l border-white/10 bg-slate-950/80 p-6 backdrop-blur-2xl shadow-2xl z-20"
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
                    disabled={runStatus === "running"}
                    className="w-full rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-100 hover:bg-rose-500/20 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {runStatus === "running" ? (
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-rose-200 border-t-transparent" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                    {runStatus === "running" ? t("running") : t("runCapsule")}
                  </button>
                  {runError && <div className="text-xs text-rose-300">{runError}</div>}
                  {runResult && (
                    <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-emerald-200">{t("runSummary")}</span>
                        <span className="text-slate-400 uppercase">{runResult.status}</span>
                      </div>
                      {runResult.cached && (
                        <div className="mt-1 text-[10px] text-emerald-300 uppercase">{t("cachedResult")}</div>
                      )}
                      <div className="mt-2 text-slate-200">
                        {String(runResult.summary?.message ?? t("generating"))}
                      </div>
                      <div className="mt-2 text-[10px] text-slate-400">
                        {t("runId")}: {runResult.run_id}
                      </div>
                      <div className="mt-2 space-y-1 text-[10px] text-slate-500">
                        <div>{t("evidenceRefs")}: {runResult.evidence_refs?.length ?? 0}</div>
                        {(runResult.evidence_refs || []).map((ref) => (
                          <div key={ref} className="rounded border border-white/5 bg-black/20 px-2 py-1 text-slate-300">
                            {ref}
                          </div>
                        ))}
                      </div>
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
