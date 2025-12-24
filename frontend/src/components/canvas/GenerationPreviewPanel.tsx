"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Clapperboard, X, ListChecks, PanelsTopLeft } from "lucide-react";
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
  const storyboard = Array.isArray(run?.spec?.storyboard) ? run?.spec?.storyboard : [];

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
          </div>
        )}

        {run && (
          <div className="p-4 border-t border-white/10 text-[10px] text-slate-500 text-center">
            {t("runId")}: {run.id} • {run.status}
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}

export default GenerationPreviewPanel;
