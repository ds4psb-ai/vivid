"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useState, useMemo, useEffect } from "react";
import {
  Clapperboard, X, ListChecks, PanelsTopLeft, Copy, Package,
  FileText, AlertCircle, CheckCircle2, MessageSquare, Play,
  Film, Download, ChevronRight, Sparkles, Music, Network, Shield
} from "lucide-react";
import type { GenerationRun } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { getStoryboardLabel, getStoryboardShotType } from "@/lib/narrative";
import DNAComplianceViewer, { BatchComplianceReport, ShotComplianceReport } from "@/components/DNAComplianceViewer";

/**
 * Premium UI Design - 2025 Refinement
 * -----------------------------------
 * - Glassmorphism: Backdrop blur-xl, border-white/10
 * - Layout: Tabbed interface (Storyboard, Video, Audio, Mind Map, Data)
 * - Typography: Space Grotesk (via globals)
 * - Animation: Framer Motion spring physics
 */

interface ShotFeedbackEntry {
  shot_id: string;
  rating?: number | null;
  note?: string | null;
  tags?: string[];
}

interface VideoResult {
  shot_id: string;
  status: string;
  video_url: string | null;
  iteration: number;
  model_version: string;
  error?: string | null;
}

interface GenerationPreviewPanelProps {
  run: GenerationRun | null;
  isLoading: boolean;
  onClose: () => void;
  onSubmitFeedback?: (payload: { shots: ShotFeedbackEntry[] }) => void;
}

type Tab = "story" | "video" | "audio" | "mindmap" | "data" | "dna";

export function GenerationPreviewPanel({
  run,
  isLoading,
  onClose,
  onSubmitFeedback,
}: GenerationPreviewPanelProps) {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<Tab>("story");
  const [feedbackEntries, setFeedbackEntries] = useState<Record<string, ShotFeedbackEntry>>({});
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [playingVideo, setPlayingVideo] = useState<string | null>(null);

  // Reset tab when run changes
  useEffect(() => {
    if (run?.outputs?.video_results && Array.isArray(run.outputs.video_results) && run.outputs.video_results.length > 0) {
      setActiveTab("video");
    } else {
      setActiveTab("story");
    }
  }, [run?.id, run?.outputs?.video_results]);

  if (!run && !isLoading) return null;

  // Memoize data extraction for performance
  const {
    beatSheet,
    storyboard,
    shotContracts,
    promptContracts,
    videoResults,
    scriptText,
    promptContractVersion,
    patternVersion,
    creditCost,
    productionContract,
    runLabel,
    dnaComplianceReport,
  } = useMemo(() => {
    const outputs = run?.outputs || {};
    const spec = run?.spec || {};

    return {
      beatSheet: Array.isArray(spec.beat_sheet) ? spec.beat_sheet : [],
      storyboard: (Array.isArray(outputs.storyboard_cards) ? outputs.storyboard_cards : Array.isArray(spec.storyboard) ? spec.storyboard : []) as Record<string, any>[],
      shotContracts: (Array.isArray(spec.shot_contracts) ? spec.shot_contracts : Array.isArray(outputs.shot_contracts) ? outputs.shot_contracts : []) as Record<string, any>[],
      promptContracts: (Array.isArray(spec.prompt_contracts) ? spec.prompt_contracts : Array.isArray(outputs.prompt_contracts) ? outputs.prompt_contracts : []) as Record<string, any>[],
      videoResults: (Array.isArray(outputs.video_results) ? outputs.video_results : []) as VideoResult[],
      scriptText: typeof outputs.script_text === "string" ? outputs.script_text : "",
      promptContractVersion: spec.prompt_contract_version || outputs.prompt_contract_version || spec.promptContractVersion,
      patternVersion: spec.pattern_version || spec.patternVersion,
      creditCost: typeof spec.credit_cost === "number" ? spec.credit_cost : null,
      productionContract: spec.production_contract || outputs.production_contract,
      runLabel: run?.id ? `run-${run.id.slice(0, 8)}` : "run",
      // DNA Compliance report
      dnaComplianceReport: outputs.dna_compliance_report as BatchComplianceReport | undefined,
    };
  }, [run]);

  // --- Utilities ---

  const copyToClipboard = (text: string) => {
    if (!text) return;
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      void navigator.clipboard.writeText(text);
    }
  };

  const handleCopyScript = () => copyToClipboard(scriptText);

  const downloadJson = (filename: string, payload: unknown) => {
    if (typeof document === "undefined") return;
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const toCsvValue = (value: unknown) => {
    const text = value === null || value === undefined ? "" : String(value);
    const escaped = text.replace(/"/g, '""');
    return `"${escaped}"`;
  };

  const downloadCsv = (filename: string, rows: Array<Record<string, unknown>>) => {
    if (typeof document === "undefined" || !rows.length) return;
    const headers = Object.keys(rows[0]);
    const lines = [headers.map(toCsvValue).join(",")];
    rows.forEach((row) => lines.push(headers.map((key) => toCsvValue(row[key])).join(",")));
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  // --- Handlers ---

  const handleDownloadPackage = () => {
    const payload = {
      run_id: run?.id,
      canvas_id: run?.canvas_id,
      status: run?.status,
      pattern_version: patternVersion,
      prompt_contract_version: promptContractVersion,
      spec: run?.spec,
      outputs: run?.outputs,
      video_results: videoResults,
    };
    downloadJson(`${runLabel}-production-package.json`, payload);
  };

  const handleDownloadShotCsv = () => {
    if (!shotContracts.length) return;
    const rows = shotContracts.map((shot) => {
      const env = (shot.environment_layers || {}) as Record<string, unknown>;
      const character = (shot.character || {}) as Record<string, unknown>;
      const palette = (shot.palette || {}) as Record<string, unknown>;
      return {
        shot_id: shot.shot_id,
        sequence_id: shot.sequence_id,
        scene_id: shot.scene_id,
        shot_type: shot.shot_type,
        duration_sec: shot.duration_sec,
        mood: shot.mood,
        dialogue: shot.dialogue,
        // ... add other fields as needed
      };
    });
    downloadCsv(`${runLabel}-shot-contracts.csv`, rows);
  };

  const handleDownloadPromptCsv = () => {
    if (!promptContracts.length) return;
    const rows = promptContracts.map((prompt) => ({
      shot_id: prompt.shot_id,
      prompt: prompt.prompt,
    }));
    downloadCsv(`${runLabel}-prompt-contracts.csv`, rows);
  };

  const updateFeedbackEntry = (shotId: string, patch: Partial<ShotFeedbackEntry>) => {
    setFeedbackEntries((prev) => ({
      ...prev,
      [shotId]: { ...prev[shotId], ...patch, shot_id: shotId },
    }));
    setFeedbackSent(false);
    setFeedbackError(null);
  };

  const handleSubmitFeedback = () => {
    if (!onSubmitFeedback) return;
    const shots = Object.values(feedbackEntries).filter((entry) => entry.shot_id);
    if (!shots.length) {
      setFeedbackError(t("feedbackEmpty") ?? "No feedback to submit");
      return;
    }
    onSubmitFeedback({ shots });
    setFeedbackSent(true);
  };

  // --- Components ---

  const TabButton = ({ id, label, icon: Icon, count }: { id: Tab; label: string; icon: any; count?: number }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`
        relative flex items-center gap-2 px-4 py-2 text-xs font-medium transition-all duration-200
        ${activeTab === id ? "text-white" : "text-slate-400 hover:text-slate-200"}
      `}
    >
      <Icon className={`w-3.5 h-3.5 ${activeTab === id ? "text-emerald-400" : ""}`} />
      {label}
      {count !== undefined && count > 0 && (
        <span className={`
          ml-1 rounded-full px-1.5 py-0.5 text-[10px] 
          ${activeTab === id ? "bg-emerald-500/20 text-emerald-300" : "bg-white/5 text-slate-500"}
        `}>
          {count}
        </span>
      )}
      {activeTab === id && (
        <motion.div
          layoutId="activeTab"
          className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500"
        />
      )}
    </button>
  );

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 100 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 100 }}
        transition={{ type: "spring", damping: 30, stiffness: 200 }}
        className="fixed bottom-0 left-0 right-0 z-50 flex flex-col pointer-events-none"
      >
        {/* Floating Controls Area */}
        <div className="mx-auto w-full max-w-5xl px-4 pb-4 pointer-events-auto">
          <div className="bg-[#0A0A0C]/90 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[500px]">

            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/5 bg-white/[0.02]">
              <div className="flex items-center gap-4">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-white/5 shadow-inner">
                  <Sparkles className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-white tracking-tight flex items-center gap-2">
                    {t("generationPreview") || "Generation Preview"}
                    {run?.status === "done" && (
                      <span className="flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3" />
                        Completed
                      </span>
                    )}
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                    {runLabel}
                    <span className="w-1 h-1 rounded-full bg-slate-700" />
                    {shotContracts.length} Shots
                    {videoResults.length > 0 && (
                      <>
                        <span className="w-1 h-1 rounded-full bg-slate-700" />
                        {videoResults.length} Videos
                      </>
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex bg-black/20 rounded-lg p-1 border border-white/5">
                  <TabButton id="story" label={t("storyboard")} icon={Clapperboard} />
                  <TabButton id="video" label="Video" icon={Film} count={videoResults.length} />
                  <TabButton id="dna" label="DNA" icon={Shield} count={dnaComplianceReport?.violation_shots} />
                  <TabButton id="audio" label="Audio" icon={Music} />
                  <TabButton id="mindmap" label="Mind Map" icon={Network} />
                  <TabButton id="data" label="Data" icon={Package} />
                </div>

                <div className="w-px h-6 bg-white/10 mx-2" />

                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto bg-black/20 custom-scrollbar relative">
              {isLoading ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
                  <div className="relative">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
                      className="w-16 h-16 rounded-full border-2 border-emerald-500/20 border-t-emerald-500"
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Sparkles className="w-6 h-6 text-emerald-500 animate-pulse" />
                    </div>
                  </div>
                  <p className="text-sm text-slate-400 font-medium">Generating Masterpiece...</p>
                </div>
              ) : (
                <div className="p-6">
                  {/* STORYBOARD TAB */}
                  {activeTab === "story" && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {storyboard.map((card, idx) => {
                        const cardRecord = card as Record<string, unknown>;
                        const shotType = getStoryboardShotType(card) ?? "N/A";
                        const description =
                          getStoryboardLabel(card) ??
                          String(cardRecord.composition ?? "");
                        const duration =
                          typeof cardRecord.duration_sec === "number"
                            ? Number(cardRecord.duration_sec)
                            : null;
                        const dominant =
                          typeof cardRecord.dominant_color === "string"
                            ? String(cardRecord.dominant_color)
                            : "#334155";
                        return (
                          <div key={idx} className="group relative bg-white/5 rounded-xl border border-white/5 p-4 hover:bg-white/[0.07] transition-all hover:border-white/10">
                            <div className="flex justify-between items-start mb-2">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-slate-400">Shot {idx + 1}</span>
                                <span className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-slate-300">
                                  {shotType}
                                </span>
                              </div>
                              {duration !== null && (
                                <span className="text-[10px] text-slate-500">{duration}s</span>
                              )}
                            </div>
                            <p className="text-sm text-slate-200 leading-snug line-clamp-3">
                              {description}
                            </p>
                            <div className="mt-3 flex flex-wrap gap-1.5 pt-3 border-t border-white/5">
                              <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: dominant }} />
                                {dominant}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* VIDEO TAB */}
                  {activeTab === "video" && (
                    <div className="space-y-8">
                      {videoResults.length === 0 ? (
                        <div className="text-center py-20">
                          <Film className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                          <h3 className="text-slate-300 font-medium">No Videos Generated Yet</h3>
                          <p className="text-slate-500 text-sm mt-1">Run the generation pipeline to create video clips.</p>
                        </div>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {videoResults.map((result, idx) => (
                            <div key={idx} className="bg-black/40 rounded-xl overflow-hidden border border-white/10 group">
                              <div className="aspect-video bg-black relative">
                                {result.video_url ? (
                                  <video
                                    src={result.video_url}
                                    controls
                                    className="w-full h-full object-cover"
                                    poster="/placeholder-video-thumb.jpg"
                                  />
                                ) : (
                                  <div className="absolute inset-0 flex items-center justify-center text-slate-600 bg-white/5">
                                    {result.status === "failed" ? (
                                      <div className="text-center p-4">
                                        <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
                                        <p className="text-xs text-rose-400">{result.error || "Generation Failed"}</p>
                                      </div>
                                    ) : (
                                      <div className="text-center">
                                        <div className="w-8 h-8 border-2 border-slate-600 border-t-emerald-500 rounded-full animate-spin mx-auto mb-2" />
                                        <span className="text-xs">Processing...</span>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                              <div className="p-3 bg-white/[0.02]">
                                <div className="flex justify-between items-center">
                                  <span className="text-xs font-medium text-white">Shot {result.shot_id}</span>
                                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">{result.model_version}</span>
                                </div>
                                <div className="flex justify-between items-center mt-2">
                                  <span className="text-[10px] text-slate-500">{result.iteration} iterations</span>
                                  {result.video_url && (
                                    <a
                                      href={result.video_url}
                                      download
                                      className="text-[10px] flex items-center gap-1 text-emerald-400 hover:text-emerald-300"
                                      target="_blank"
                                      rel="noreferrer"
                                    >
                                      <Download className="w-3 h-3" /> Download
                                    </a>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* AUDIO TAB */}
                  {activeTab === "audio" && (
                    <div className="text-center py-20">
                      <Music className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                      <h3 className="text-slate-300 font-medium">Audio Generation Coming Soon</h3>
                      <p className="text-slate-500 text-sm mt-1">Soundtracks and effects will appear here.</p>
                      {/* Placeholder for future implementation */}
                    </div>
                  )}

                  {/* MINDMAP TAB */}
                  {activeTab === "mindmap" && (
                    <div className="text-center py-20">
                      <Network className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                      <h3 className="text-slate-300 font-medium">Mind Map View</h3>
                      <p className="text-slate-500 text-sm mt-1">Visualize narrative connections and beat structures.</p>
                      {/* Placeholder for future implementation */}
                    </div>
                  )}

                  {/* DNA TAB */}
                  {activeTab === "dna" && (
                    <div className="space-y-4">
                      {dnaComplianceReport ? (
                        <DNAComplianceViewer
                          report={dnaComplianceReport}
                          compact={false}
                          onRegenerateShot={(shotId, suggestions) => {
                            console.log('Regenerate shot:', shotId, suggestions);
                            // TODO: Implement shot regeneration
                          }}
                          onExport={(format) => {
                            if (format === 'json') {
                              const blob = new Blob([JSON.stringify(dnaComplianceReport, null, 2)], { type: 'application/json' });
                              const url = URL.createObjectURL(blob);
                              const a = document.createElement('a');
                              a.href = url;
                              a.download = `${runLabel}-dna-report.json`;
                              a.click();
                              URL.revokeObjectURL(url);
                            }
                          }}
                        />
                      ) : (
                        <div className="text-center py-20">
                          <Shield className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                          <h3 className="text-slate-300 font-medium">DNA Compliance</h3>
                          <p className="text-slate-500 text-sm mt-1">
                            No compliance report available. Enable DirectorPack DNA validation to see compliance results.
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* DATA TAB */}
                  {activeTab === "data" && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="col-span-1 space-y-4">
                        <section className="bg-white/5 rounded-xl p-4 border border-white/5">
                          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                            <FileText className="w-3.5 h-3.5" /> Downloads
                          </h3>
                          <div className="space-y-2">
                            <button onClick={handleDownloadPackage} className="w-full flex items-center justify-between p-2 rounded-lg bg-white/5 hover:bg-emerald-500/10 hover:text-emerald-400 transition-colors text-xs text-slate-300">
                              <span>Production Package</span>
                              <Download className="w-3.5 h-3.5" />
                            </button>
                            <button onClick={handleDownloadShotCsv} className="w-full flex items-center justify-between p-2 rounded-lg bg-white/5 hover:bg-emerald-500/10 hover:text-emerald-400 transition-colors text-xs text-slate-300">
                              <span>Shot List (CSV)</span>
                              <FileText className="w-3.5 h-3.5" />
                            </button>
                            <button onClick={handleDownloadPromptCsv} className="w-full flex items-center justify-between p-2 rounded-lg bg-white/5 hover:bg-emerald-500/10 hover:text-emerald-400 transition-colors text-xs text-slate-300">
                              <span>Prompts (CSV)</span>
                              <FileText className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </section>

                        <section className="bg-white/5 rounded-xl p-4 border border-white/5">
                          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Run Details</h3>
                          <div className="space-y-2 text-xs">
                            <div className="flex justify-between">
                              <span className="text-slate-500">ID</span>
                              <span className="text-slate-300 font-mono">{run?.id.slice(0, 8)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Status</span>
                              <span className={`px-1.5 py-0.5 rounded text-[10px] ${run?.status === 'done' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-300'}`}>
                                {run?.status}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Credits</span>
                              <span className="text-amber-400">{creditCost || '-'}</span>
                            </div>
                          </div>
                        </section>
                      </div>

                      <div className="col-span-1 md:col-span-2 space-y-4">
                        <section className="bg-white/5 rounded-xl p-4 border border-white/5 h-full">
                          <div className="flex items-center justify-between mb-3">
                            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                              <Copy className="w-3.5 h-3.5" /> Script
                            </h3>
                            {scriptText && (
                              <button onClick={handleCopyScript} className="text-[10px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
                                <Copy className="w-3 h-3" /> Copy
                              </button>
                            )}
                          </div>
                          <div className="bg-black/30 rounded-lg p-3 text-xs text-slate-300 font-mono h-[300px] overflow-y-auto custom-scrollbar leading-relaxed whitespace-pre-wrap">
                            {scriptText || "No script generated."}
                          </div>
                        </section>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Feedback Bar */}
            {activeTab === "story" && !isLoading && onSubmitFeedback && (
              <div className="px-5 py-3 border-t border-white/5 bg-white/[0.02] flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <MessageSquare className="w-4 h-4 text-amber-400" />
                  <span>Rate shots to improve the next version</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-slate-500">{Object.keys(feedbackEntries).length} shots rated</span>
                  <button
                    onClick={handleSubmitFeedback}
                    disabled={feedbackSent}
                    className={`
                        px-4 py-1.5 rounded-lg text-xs font-medium transition-all
                        ${feedbackSent
                        ? "bg-emerald-500/20 text-emerald-400 cursor-default"
                        : "bg-emerald-500 hover:bg-emerald-600 text-black shadow-[0_0_15px_rgba(16,185,129,0.4)]"
                      }
                      `}
                  >
                    {feedbackSent ? "Feedback Sent" : "Submit Feedback"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

export default GenerationPreviewPanel;
