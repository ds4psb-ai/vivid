"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Clapperboard, X, ListChecks, PanelsTopLeft, Copy } from "lucide-react";
import type { GenerationRun } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

interface GenerationPreviewPanelProps {
  run: GenerationRun | null;
  isLoading: boolean;
  onClose: () => void;
}

export function GenerationPreviewPanel({
  run,
  isLoading,
  onClose,
}: GenerationPreviewPanelProps) {
  const { t } = useLanguage();

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

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: -300 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -300 }}
        transition={{ type: "spring", damping: 25, stiffness: 200 }}
        className="fixed left-0 top-0 h-full w-[420px] bg-gradient-to-b from-emerald-950/95 to-slate-950/95 backdrop-blur-xl border-r border-white/10 z-50 overflow-hidden flex flex-col"
      >
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
                            {continuity.map((tag: unknown) => (
                              <span
                                key={String(tag)}
                                className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5"
                              >
                                {String(tag)}
                              </span>
                            ))}
                          </div>
                        )}
                        {shot.dialogue && (
                          <div className="mt-2 text-[10px] text-slate-400">
                            {t("dialogue")}: {String(shot.dialogue)}
                          </div>
                        )}
                      </div>
                    );
                  })}
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
      </motion.div>
    </AnimatePresence>
  );
}

export default GenerationPreviewPanel;
