"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { Clapperboard, X, ListChecks, PanelsTopLeft, Copy, Package, FileText, AlertCircle, CheckCircle2, MessageSquare } from "lucide-react";
import type { GenerationRun } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

interface ShotFeedbackEntry {
  shot_id: string;
  rating?: number | null;
  note?: string | null;
  tags?: string[];
}

interface GenerationPreviewPanelProps {
  run: GenerationRun | null;
  isLoading: boolean;
  onClose: () => void;
  onSubmitFeedback?: (payload: { shots: ShotFeedbackEntry[] }) => void;
}

export function GenerationPreviewPanel({
  run,
  isLoading,
  onClose,
  onSubmitFeedback,
}: GenerationPreviewPanelProps) {
  const { t } = useLanguage();
  const [feedbackEntries, setFeedbackEntries] = useState<Record<string, ShotFeedbackEntry>>({});
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);

  if (!run && !isLoading) return null;

  const beatSheet = Array.isArray(run?.spec?.beat_sheet) ? run?.spec?.beat_sheet : [];
  const storyboardSpec = Array.isArray(run?.spec?.storyboard) ? run?.spec?.storyboard : [];
  const storyboardOutput = Array.isArray(run?.outputs?.storyboard_cards) ? run?.outputs?.storyboard_cards : [];
  const storyboard = storyboardOutput.length ? storyboardOutput : storyboardSpec;
  const scriptText = typeof run?.outputs?.script_text === "string" ? run.outputs.script_text : "";
  const shotContracts = Array.isArray(run?.spec?.shot_contracts)
    ? run?.spec?.shot_contracts
    : Array.isArray(run?.outputs?.shot_contracts)
      ? run?.outputs?.shot_contracts
      : [];
  const promptContracts = Array.isArray(run?.spec?.prompt_contracts)
    ? run?.spec?.prompt_contracts
    : Array.isArray(run?.outputs?.prompt_contracts)
      ? run?.outputs?.prompt_contracts
      : [];
  const promptContractVersion =
    run?.spec?.prompt_contract_version ||
    run?.outputs?.prompt_contract_version ||
    run?.spec?.promptContractVersion;
  const patternVersion =
    run?.spec?.pattern_version ||
    run?.spec?.patternVersion;
  const creditCost =
    typeof run?.spec?.credit_cost === "number" ? run?.spec?.credit_cost : null;
  const productionContract =
    run?.spec?.production_contract && typeof run.spec.production_contract === "object"
      ? run.spec.production_contract
      : run?.outputs?.production_contract && typeof run.outputs.production_contract === "object"
        ? run.outputs.production_contract
        : null;
  const runLabel = run?.id ? `run-${run.id}` : "run";
  const copyToClipboard = (text: string) => {
    if (!text) return;
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      void navigator.clipboard.writeText(text);
    }
  };

  const handleCopyScript = () => copyToClipboard(scriptText);

  const downloadJson = (filename: string, payload: unknown) => {
    if (typeof document === "undefined") return;
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
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
    if (typeof document === "undefined") return;
    if (!rows.length) return;
    const headers = Object.keys(rows[0]);
    const lines = [headers.map(toCsvValue).join(",")];
    rows.forEach((row) => {
      lines.push(headers.map((key) => toCsvValue(row[key])).join(","));
    });
    const blob = new Blob([lines.join("\n")], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadPackage = () => {
    const payload = {
      run_id: run?.id,
      canvas_id: run?.canvas_id,
      status: run?.status,
      pattern_version: patternVersion,
      prompt_contract_version: promptContractVersion,
      spec: run?.spec,
      outputs: run?.outputs,
      production_contract: productionContract,
      shot_contracts: shotContracts,
      prompt_contracts: promptContracts,
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
        aspect_ratio: shot.aspect_ratio,
        lens: shot.lens,
        film_stock: shot.film_stock,
        lighting: shot.lighting,
        time_of_day: shot.time_of_day,
        mood: shot.mood,
        character_name: character.name,
        wardrobe: character.wardrobe,
        pose_motion: shot.pose_motion,
        dialogue: shot.dialogue,
        foreground: env.foreground,
        midground: env.midground,
        background: env.background,
        duration_sec: shot.duration_sec,
        palette_primary: palette.primary,
        palette_accent: palette.accent,
        continuity_tags: Array.isArray(shot.continuity_tags)
          ? shot.continuity_tags.join("|")
          : shot.continuity_tags,
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
      [shotId]: {
        shot_id: shotId,
        ...prev[shotId],
        ...patch,
      },
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

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 240 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 240 }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed bottom-0 left-0 right-0 h-[360px] md:h-[420px] bg-gradient-to-b from-emerald-950/95 to-slate-950/95 backdrop-blur-xl border-t border-white/10 z-40 overflow-hidden rounded-t-2xl panel-container"
      >
        <div className="mx-auto flex h-full w-full max-w-5xl flex-col">
          <div className="flex items-center justify-between p-5 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/15 flex items-center justify-center">
                <Clapperboard className="w-5 h-5 text-emerald-300" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">{t("generationPreview")}</h2>
                <p className="text-xs text-slate-400">{t("beatSheetStoryboardDesc")}</p>
              </div>
            </div>
            <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/10 transition-colors">
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          {isLoading && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                >
                  <PanelsTopLeft className="w-10 h-10 text-emerald-300 mx-auto mb-4" />
                </motion.div>
                <p className="text-slate-400">{t("generating")}</p>
              </div>
            </div>
          )}

          {/* Sticky Action Bar + Summary Chips */}
          {!isLoading && run && (
            <div className="sticky top-0 z-10 bg-gradient-to-b from-emerald-950/98 to-emerald-950/95 backdrop-blur-md border-b border-white/10 px-5 py-3">
              <div className="flex flex-wrap items-center gap-3">
                {/* Pipeline End Badge */}
                <div className="flex items-center gap-1.5 rounded-full bg-emerald-500/20 border border-emerald-500/30 px-2.5 py-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-[10px] font-semibold text-emerald-200 uppercase tracking-wider">{t("pipelineEnd") || "Pipeline End"}</span>
                </div>

                {/* Summary Chips */}
                <div className="flex items-center gap-2 text-[10px] text-slate-400">
                  {beatSheet.length > 0 && (
                    <span className="rounded-md bg-slate-800/80 px-2 py-1 border border-white/5">
                      {t("beats") || "Beats"}: {beatSheet.length}
                    </span>
                  )}
                  {storyboard.length > 0 && (
                    <span className="rounded-md bg-slate-800/80 px-2 py-1 border border-white/5">
                      {t("storyboard")}: {storyboard.length}
                    </span>
                  )}
                  {shotContracts.length > 0 && (
                    <span className="rounded-md bg-slate-800/80 px-2 py-1 border border-white/5">
                      {t("shots") || "Shots"}: {shotContracts.length}
                    </span>
                  )}
                  {promptContracts.length > 0 && (
                    <span className="rounded-md bg-slate-800/80 px-2 py-1 border border-white/5">
                      {t("prompts") || "Prompts"}: {promptContracts.length}
                    </span>
                  )}
                </div>

                {/* Export Actions */}
                <div className="ml-auto flex items-center gap-2">
                  <button
                    onClick={handleDownloadPackage}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/15 px-3 py-1.5 text-[11px] font-medium text-emerald-100 transition-colors hover:bg-emerald-500/25"
                  >
                    <Package className="w-3.5 h-3.5" />
                    {t("productionPackage")}
                  </button>
                  {shotContracts.length > 0 && (
                    <button
                      onClick={handleDownloadShotCsv}
                      className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2.5 py-1.5 text-[10px] text-slate-300 transition-colors hover:bg-white/10"
                    >
                      <FileText className="w-3 h-3" />
                      {t("shotCsv") || "Shot CSV"}
                    </button>
                  )}
                  {promptContracts.length > 0 && (
                    <button
                      onClick={handleDownloadPromptCsv}
                      className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2.5 py-1.5 text-[10px] text-slate-300 transition-colors hover:bg-white/10"
                    >
                      <FileText className="w-3 h-3" />
                      {t("promptCsv") || "Prompt CSV"}
                    </button>
                  )}
                  {scriptText && (
                    <button
                      onClick={handleCopyScript}
                      className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2.5 py-1.5 text-[10px] text-slate-300 transition-colors hover:bg-white/10"
                    >
                      <Copy className="w-3 h-3" />
                      {t("copyScript")}
                    </button>
                  )}
                </div>
              </div>

              {/* Feedback Callout */}
              {shotContracts.length > 0 && onSubmitFeedback && !feedbackSent && (
                <div className="mt-3 flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2">
                  <MessageSquare className="w-4 h-4 text-amber-300 flex-shrink-0" />
                  <span className="text-[11px] text-amber-100">{t("feedbackCallout") || "Your feedback improves the next template version"}</span>
                  <button
                    onClick={() => {
                      const el = document.getElementById("feedback-section");
                      el?.scrollIntoView({ behavior: "smooth" });
                    }}
                    className="ml-auto text-[10px] font-medium text-amber-200 underline underline-offset-2 hover:text-amber-100"
                  >
                    {t("giveFeedback") || "Give Feedback →"}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Failed/Empty State Card */}
          {!isLoading && run && (run.status === "failed" || (shotContracts.length === 0 && promptContracts.length === 0 && beatSheet.length === 0)) && (
            <div className="mx-5 my-4 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-rose-200">
                    {run.status === "failed" ? (t("generationFailed") || "Generation Failed") : (t("noOutputs") || "No Outputs Generated")}
                  </h4>
                  <p className="mt-1 text-[11px] text-rose-300/80">
                    {run.status === "failed"
                      ? (t("generationFailedHint") || "Check capsule inputs and evidence references, then retry.")
                      : (t("noOutputsHint") || "This may indicate missing inputs or template configuration issues.")}
                  </p>
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={onClose}
                      className="inline-flex items-center gap-1 rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-[10px] text-rose-200 hover:bg-rose-500/20"
                    >
                      {t("reviewInputs") || "Review Inputs"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {!isLoading && run && (
            <div className="flex-1 overflow-y-auto p-5 space-y-6">
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <ListChecks className="w-4 h-4 text-emerald-300" />
                  <h3 className="text-sm font-medium text-white">{t("beatSheet")}</h3>
                  {scriptText && (
                    <button
                      onClick={handleCopyScript}
                      className="ml-auto inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1 text-[10px] text-slate-300 transition-colors hover:bg-white/10"
                      aria-label={t("copyScript")}
                    >
                      <Copy className="h-3 w-3" />
                      {t("copyScript")}
                    </button>
                  )}
                </div>
                {beatSheet.length === 0 ? (
                  <div className="text-xs text-slate-500">{t("noBeatSheet")}</div>
                ) : (
                  <div className="space-y-2">
                    {beatSheet.map((beat: Record<string, unknown>, idx: number) => (
                      <div
                        key={`${String(beat.beat)}-${idx}`}
                        className="rounded-lg border border-white/5 bg-slate-900/50 px-3 py-2 text-xs"
                      >
                        <div className="text-slate-200 font-semibold">{String(beat.beat || `Beat ${idx + 1}`)}</div>
                        <div className="text-slate-400 mt-1">{String(beat.note)}</div>
                      </div>
                    ))}
                  </div>
                )}
                {scriptText && (
                  <div className="mt-3 rounded-lg border border-white/5 bg-slate-900/40 p-3 text-[11px] text-slate-300 whitespace-pre-line">
                    {scriptText}
                  </div>
                )}
              </section>

              <section>
                <div className="flex items-center gap-2 mb-3">
                  <Clapperboard className="w-4 h-4 text-sky-300" />
                  <h3 className="text-sm font-medium text-white">{t("storyboard")}</h3>
                </div>
                {storyboard.length === 0 ? (
                  <div className="text-xs text-slate-500">{t("noStoryboard")}</div>
                ) : (
                  <div className="space-y-2">
                    {storyboard.map((shot: Record<string, unknown>, idx: number) => (
                      <div
                        key={`${String(shot.shot)}-${idx}`}
                        className="rounded-lg border border-white/5 bg-slate-900/50 px-3 py-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-slate-200 font-semibold">{t("shot")} {String(shot.shot || idx + 1)}</span>
                          <span className="text-[10px] text-slate-500">{String(shot.pacing_note)}</span>
                        </div>
                        <div className="mt-1 text-slate-400">{String(shot.composition)}</div>
                        <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-500">
                          <span className="h-3 w-3 rounded-full border border-white/10" style={{ backgroundColor: String(shot.dominant_color) }} />
                          <span className="h-3 w-3 rounded-full border border-white/10" style={{ backgroundColor: String(shot.accent_color) }} />
                          <span>{String(shot.dominant_color)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section>
                <div className="flex items-center gap-2 mb-3">
                  <ListChecks className="w-4 h-4 text-amber-300" />
                  <h3 className="text-sm font-medium text-white">{t("shotContracts")}</h3>
                  <button
                    onClick={handleDownloadPackage}
                    className="ml-auto inline-flex items-center gap-1 rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[10px] text-emerald-100 transition-colors hover:bg-emerald-500/20"
                  >
                    {t("productionPackage")}
                  </button>
                  {shotContracts.length > 0 && (
                    <button
                      onClick={() => downloadJson(`${runLabel}-shot-contracts.json`, shotContracts)}
                      className="ml-2 inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1 text-[10px] text-slate-300 transition-colors hover:bg-white/10"
                    >
                      {t("downloadJson")}
                    </button>
                  )}
                  {shotContracts.length > 0 && (
                    <button
                      onClick={handleDownloadShotCsv}
                      className="ml-2 inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1 text-[10px] text-slate-300 transition-colors hover:bg-white/10"
                    >
                      {t("downloadCsv")}
                    </button>
                  )}
                </div>
                {shotContracts.length === 0 ? (
                  <div className="text-xs text-slate-500">{t("noShotContracts")}</div>
                ) : (
                  <div className="space-y-2">
                    {shotContracts.map((shot: Record<string, unknown>, idx: number) => {
                      const env = shot.environment_layers as Record<string, unknown> | undefined;
                      const character = shot.character as Record<string, unknown> | undefined;
                      const continuity = Array.isArray(shot.continuity_tags) ? shot.continuity_tags : [];
                      const shotId = String(shot.shot_id || idx + 1);
                      const feedback = feedbackEntries[shotId] || { shot_id: shotId };
                      return (
                        <div
                          key={`${String(shot.shot_id || idx)}`}
                          className="rounded-lg border border-white/5 bg-slate-900/50 px-3 py-2 text-xs"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-slate-200 font-semibold">
                              {t("shot")} {String(shot.shot_id || idx + 1)}
                            </span>
                            <span className="text-[10px] text-slate-500">
                              {String(shot.shot_type || "")} • {String(shot.duration_sec || "")}s
                            </span>
                          </div>
                          <div className="mt-1 text-slate-400">
                            {t("lens")}: {String(shot.lens || "-")} · {t("aspectRatio")}: {String(shot.aspect_ratio || "-")}
                          </div>
                          <div className="mt-1 text-slate-500">
                            {t("filmStock")}: {String(shot.film_stock || "-")} · {t("lighting")}: {String(shot.lighting || "-")}
                          </div>
                          <div className="mt-1 text-slate-500">
                            {t("mood")}: {String(shot.mood || "-")}
                          </div>
                          <div className="mt-1 text-slate-500">
                            {t("character")}: {String(character?.name || "-")} · {t("poseMotion")}: {String(shot.pose_motion || "-")}
                          </div>
                          <div className="mt-2 text-[10px] text-slate-500">
                            {t("environmentLayers")}: {String(env?.foreground || "-")} / {String(env?.midground || "-")} / {String(env?.background || "-")}
                          </div>
                          {continuity.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1 text-[10px] text-emerald-200/80">
                              {(continuity as string[]).map((tag: string) => (
                                <span
                                  key={tag}
                                  className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                          {shot.dialogue && (
                            <div className="mt-2 text-[10px] text-slate-400">
                              {t("dialogue")}: {String(shot.dialogue)}
                            </div>
                          )}
                          <div className="mt-3 rounded-md border border-white/10 bg-slate-950/60 p-2">
                            <div className="flex items-center gap-2 text-[10px] text-slate-400">
                              <span className="uppercase tracking-widest">{t("feedback")}</span>
                              <div className="ml-auto flex items-center gap-1">
                                {[1, 2, 3, 4, 5].map((rating) => (
                                  <button
                                    key={rating}
                                    onClick={() => updateFeedbackEntry(shotId, { rating })}
                                    className={`h-5 w-5 rounded-full border text-[10px] transition-colors ${feedback.rating === rating
                                      ? "border-emerald-400 bg-emerald-500/20 text-emerald-200"
                                      : "border-white/10 text-slate-400 hover:border-emerald-400/60"
                                      }`}
                                    type="button"
                                  >
                                    {rating}
                                  </button>
                                ))}
                              </div>
                            </div>
                            <textarea
                              value={feedback.note ?? ""}
                              onChange={(event) =>
                                updateFeedbackEntry(shotId, { note: event.target.value })
                              }
                              placeholder={t("feedbackNotePlaceholder")}
                              className="mt-2 w-full rounded-md border border-white/10 bg-slate-900/70 p-2 text-[11px] text-slate-200 placeholder:text-slate-500 focus:border-emerald-400/60 focus:outline-none"
                              rows={2}
                            />
                          </div>
                        </div>
                      );
                    })}
                    {onSubmitFeedback && (
                      <div id="feedback-section" className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <button
                          onClick={handleSubmitFeedback}
                          className="inline-flex items-center justify-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-xs font-semibold text-emerald-100 transition-colors hover:bg-emerald-500/20"
                          type="button"
                        >
                          {t("submitFeedback")}
                        </button>
                        <div className="text-[10px] text-slate-500">
                          {feedbackSent ? t("feedbackSaved") : feedbackError ?? ""}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </section>

              <section>
                <div className="flex items-center gap-2 mb-3">
                  <PanelsTopLeft className="w-4 h-4 text-emerald-300" />
                  <h3 className="text-sm font-medium text-white">{t("promptContracts")}</h3>
                  {promptContractVersion && (
                    <span className="ml-auto text-[10px] text-emerald-200/80">
                      {t("promptContractVersion")}: {String(promptContractVersion)}
                    </span>
                  )}
                  {promptContracts.length > 0 && (
                    <button
                      onClick={() => downloadJson(`${runLabel}-prompt-contracts.json`, promptContracts)}
                      className="ml-2 inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1 text-[10px] text-slate-300 transition-colors hover:bg-white/10"
                    >
                      {t("downloadJson")}
                    </button>
                  )}
                  {promptContracts.length > 0 && (
                    <button
                      onClick={handleDownloadPromptCsv}
                      className="ml-2 inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1 text-[10px] text-slate-300 transition-colors hover:bg-white/10"
                    >
                      {t("downloadCsv")}
                    </button>
                  )}
                </div>
                {promptContracts.length === 0 ? (
                  <div className="text-xs text-slate-500">{t("noPromptContracts")}</div>
                ) : (
                  <div className="space-y-2">
                    {promptContracts.map((prompt: Record<string, unknown>, idx: number) => {
                      const promptText = typeof prompt.prompt === "string" ? prompt.prompt : "";
                      return (
                        <div
                          key={`${String(prompt.shot_id || idx)}`}
                          className="rounded-lg border border-white/5 bg-slate-900/50 px-3 py-2 text-xs"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-slate-200 font-semibold">
                              {t("shot")} {String(prompt.shot_id || idx + 1)}
                            </span>
                            <button
                              onClick={() => copyToClipboard(promptText)}
                              className="inline-flex items-center gap-1 rounded-md border border-white/10 px-2 py-1 text-[10px] text-slate-300 transition-colors hover:bg-white/10"
                              aria-label={t("copyPrompt")}
                            >
                              <Copy className="h-3 w-3" />
                              {t("copyPrompt")}
                            </button>
                          </div>
                          <div className="mt-2 text-[11px] text-slate-400 whitespace-pre-line">
                            {promptText || "-"}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            </div>
          )}

          {run && (
            <div className="p-4 border-t border-white/10 text-[10px] text-slate-500 text-center">
              {t("runId")}: {run.id} • {run.status}
              {patternVersion && (
                <span> • {t("patternVersion")}: {String(patternVersion)}</span>
              )}
              {creditCost !== null && (
                <span> • {t("creditsCost")}: {creditCost}</span>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

export default GenerationPreviewPanel;
