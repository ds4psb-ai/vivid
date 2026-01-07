"use client";

/**
 * Template Versions Modal
 * Shows version history for a template with use/revert actions.
 */

import { motion } from "framer-motion";
import { X, Check, RefreshCcw, History as HistoryIcon } from "lucide-react";
import { Template, TemplateVersion } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { formatDateTime } from "@/lib/formatters";
import { getNarrativeSeeds } from "./TemplateCard";
import { translations } from "@/lib/translations";

// Helper component for translations
const TemplateCardText = ({ tKey }: { tKey: keyof typeof translations.ko }) => {
    const { t } = useLanguage();
    return <>{t(tKey)}</>;
};

interface VersionsModalProps {
    template: Template;
    versions: TemplateVersion[];
    currentVersion: number | null;
    isLoading: boolean;
    error: string | null;
    actionId: string | null;
    onClose: () => void;
    onUseVersion: (version: TemplateVersion) => void;
    onRevertVersion: (version: TemplateVersion) => void;
}

export function VersionsModal({
    template,
    versions,
    currentVersion,
    isLoading,
    error,
    actionId,
    onClose,
    onUseVersion,
    onRevertVersion,
}: VersionsModalProps) {
    const { t } = useLanguage();

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="w-full max-w-2xl rounded-2xl border border-white/10 bg-slate-950 shadow-2xl overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-center justify-between p-6 border-b border-white/5">
                    <div>
                        <div className="text-xs uppercase tracking-widest text-slate-400">{t("templateVersions")}</div>
                        <div className="text-lg font-semibold text-white">{template.title}</div>
                    </div>
                    <button onClick={onClose} className="text-slate-400 hover:text-white">
                        <X className="h-4 w-4" />
                    </button>
                </div>

                <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
                    {isLoading && <div className="text-sm text-slate-400">{t("loadingVersions")}</div>}
                    {error && <div className="text-sm text-rose-300">{error}</div>}
                    {!isLoading && versions.length === 0 && <div className="text-sm text-slate-500">{t("noVersions")}</div>}

                    {versions.map((version) => {
                        const isCurrent = currentVersion === version.version;
                        const seeds = getNarrativeSeeds(version.graph_data);

                        return (
                            <div key={version.id} className="rounded-xl border border-white/10 bg-slate-900/50 p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <div className="text-sm font-semibold text-slate-100">
                                            v{version.version} {isCurrent ? `(${t("currentVersion")})` : ""}
                                        </div>
                                        <div className="text-xs text-slate-500 mt-1">
                                            {formatDateTime(version.created_at) ?? ""}
                                        </div>
                                        {version.notes && <div className="text-xs text-slate-400 mt-1">{version.notes}</div>}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => onUseVersion(version)}
                                            disabled={actionId === version.id}
                                            className="inline-flex items-center gap-1 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-[10px] uppercase tracking-widest text-sky-300 hover:bg-sky-500/20 disabled:opacity-50"
                                        >
                                            <Check className="h-3 w-3" />{t("useVersion")}
                                        </button>
                                        <button
                                            onClick={() => onRevertVersion(version)}
                                            disabled={actionId === `revert-${version.id}` || isCurrent}
                                            className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-[10px] uppercase tracking-widest text-amber-300 hover:bg-amber-500/20 disabled:opacity-50"
                                        >
                                            <RefreshCcw className="h-3 w-3" />{t("revertVersion")}
                                        </button>
                                    </div>
                                </div>

                                {seeds.hasSeeds && (
                                    <div className="mt-3 rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2 text-[11px] text-slate-300">
                                        <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-slate-400">
                                            <span>{t("narrativeSeeds")}</span>
                                            <span>
                                                {t("beatSheet")}: {seeds.storyBeats.length} · {t("storyboard")}: {seeds.storyboardCards.length}
                                            </span>
                                        </div>
                                        {seeds.beatSnippet && (
                                            <div className="mt-2 line-clamp-1 text-[11px] text-slate-200">
                                                {t("beat")} 1: {seeds.beatSnippet}
                                            </div>
                                        )}
                                        {seeds.storyboardSnippet && (
                                            <div className="mt-1 line-clamp-1 text-[11px] text-slate-400">
                                                {t("shot")} 1: {seeds.storyboardSnippet}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                <div className="p-4 border-t border-white/10 text-[10px] text-slate-500 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <HistoryIcon className="h-3 w-3" />
                        <TemplateCardText tKey="latestHistory" />
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
}
