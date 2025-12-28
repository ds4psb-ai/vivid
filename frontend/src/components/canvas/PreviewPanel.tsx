import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Palette, Layers, Clock, Eye, Sparkles, Link, Square, Music, Share2, FileText, Clapperboard } from "lucide-react";
import type { StoryboardPreview, ScenePreview } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { getStoryboardLabel, getStoryboardShotType } from "@/lib/narrative";

interface PreviewPanelProps {
    preview: StoryboardPreview | null;
    isLoading: boolean;
    showCancel?: boolean;
    onCancel?: () => void;
    statusNotice?: { tone: "info" | "warning" | "error"; message: string };
    outputLanguage?: string;
    availableLanguages?: string[];
    onLanguageChange?: (language: string) => void;
    onClose: () => void;
    isAdminView?: boolean;
}

export function PreviewPanel({
    preview,
    isLoading,
    showCancel,
    onCancel,
    statusNotice,
    outputLanguage,
    availableLanguages,
    onLanguageChange,
    onClose,
    isAdminView = false,
}: PreviewPanelProps) {
    const { t } = useLanguage();
    const [activeOutput, setActiveOutput] = useState<"storyboard" | "audio" | "mindmap">(
        "storyboard"
    );
    const evidenceWarnings = Array.isArray(preview?.evidence_warnings)
        ? preview?.evidence_warnings
        : [];
    const outputWarnings = Array.isArray(preview?.output_warnings)
        ? preview?.output_warnings
        : [];
    const patternVersion = preview?.pattern_version;
    const sourceId = preview?.source_id;
    const sequenceLen =
        typeof preview?.sequence_len === "number" ? preview.sequence_len : undefined;
    const contextMode =
        typeof preview?.context_mode === "string" ? preview.context_mode : undefined;
    const creditCost =
        typeof preview?.credit_cost === "number" ? preview.credit_cost : undefined;
    const latencyMs =
        typeof preview?.latency_ms === "number" ? preview.latency_ms : undefined;
    const tokenUsage =
        preview?.token_usage && typeof preview.token_usage === "object"
            ? (preview.token_usage as { input?: number; output?: number; total?: number })
            : null;
    const summaryText = typeof preview?.summary === "string" ? preview?.summary : null;
    const storyboardCards = Array.isArray(preview?.storyboard_cards)
        ? preview?.storyboard_cards
        : [];
    const previewLanguages = Array.isArray(availableLanguages)
        ? availableLanguages
        : Array.isArray(preview?.available_languages)
            ? preview?.available_languages
            : [];
    const activeLanguage = outputLanguage || preview?.output_language;
    const showLanguageSwitch = previewLanguages.length > 1;
    const handleLanguageClick = (language: string) => {
        if (language === activeLanguage) return;
        onLanguageChange?.(language);
    };
    const seqSummary =
        isAdminView && sequenceLen !== undefined && preview?.scenes?.length
            ? {
                  first: preview.scenes[0]?.composition,
                  last: preview.scenes[preview.scenes.length - 1]?.composition,
              }
            : null;

    if (!preview && !isLoading) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: 240 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 240 }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="fixed bottom-0 left-0 right-0 h-[360px] md:h-[420px] bg-gradient-to-b from-gray-900/95 to-gray-950/95 backdrop-blur-xl border-t border-white/10 z-50 overflow-hidden rounded-t-2xl panel-container"
            >
                <div className="mx-auto flex h-full w-full max-w-5xl flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-5 border-b border-white/10">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500/20 to-amber-500/20 flex items-center justify-center">
                            <Eye className="w-5 h-5 text-sky-300" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">{t("storyboardPreview")}</h2>
                            <p className="text-xs text-gray-400">{t("generatedDesc")}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {showLanguageSwitch && (
                            <div className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 p-1 text-[10px] text-gray-300">
                                <span className="px-2 text-gray-400">{t("outputLanguage")}</span>
                                {previewLanguages.map((language) => (
                                    <button
                                        key={language}
                                        onClick={() => handleLanguageClick(language)}
                                        className={`rounded-full px-2 py-0.5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/40 ${
                                            activeLanguage === language
                                                ? "bg-sky-500/20 text-sky-200"
                                                : "text-gray-400 hover:text-gray-200"
                                        }`}
                                    >
                                        {language.toUpperCase()}
                                    </button>
                                ))}
                            </div>
                        )}
                        {showCancel && onCancel && (
                            <button
                                onClick={onCancel}
                                className="flex items-center gap-1 rounded-lg border border-rose-500/30 bg-rose-500/10 px-2 py-1 text-[11px] font-semibold text-rose-200 hover:bg-rose-500/20 transition-colors"
                            >
                                <Square className="w-3 h-3" />
                                {t("cancel")}
                            </button>
                        )}
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                        >
                            <X className="w-5 h-5 text-gray-400" />
                        </button>
                    </div>
                </div>

                {statusNotice && (
                    <div
                        className={`mx-5 mt-4 rounded-lg border px-3 py-2 text-[11px] font-semibold ${statusNotice.tone === "error"
                            ? "border-rose-500/30 bg-rose-500/10 text-rose-200"
                            : statusNotice.tone === "warning"
                                ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
                                : "border-sky-500/30 bg-sky-500/10 text-sky-200"
                            }`}
                    >
                        {statusNotice.message}
                    </div>
                )}

                {/* Loading State */}
                {isLoading && (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center">
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                            >
                                <Sparkles className="w-12 h-12 text-sky-300 mx-auto mb-4" />
                            </motion.div>
                            <p className="text-gray-400">{t("generating")}</p>
                        </div>
                    </div>
                )}

                {/* Content */}
                {preview && !isLoading && (
                    <div className="flex-1 overflow-y-auto p-5 space-y-6">
                        {/* Output Tabs */}
                        <section>
                            <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 p-1 text-[11px] text-gray-300">
                                {[
                                    { id: "storyboard", label: t("outputStoryboard"), icon: Layers },
                                    { id: "audio", label: t("outputAudio"), icon: Music },
                                    { id: "mindmap", label: t("outputMindMap"), icon: Share2 },
                                ].map((tab) => (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveOutput(tab.id as typeof activeOutput)}
                                        className={`flex flex-1 items-center justify-center gap-1 rounded-full px-3 py-1 transition-colors ${
                                            activeOutput === tab.id
                                                ? "bg-sky-500/20 text-sky-200"
                                                : "text-gray-400 hover:text-gray-200"
                                        }`}
                                    >
                                        <tab.icon className="h-3 w-3" />
                                        {tab.label}
                                    </button>
                                ))}
                            </div>
                        </section>

                        {activeOutput === "audio" && (
                            <section>
                                <div className="flex items-center gap-2 mb-3">
                                    <Music className="w-4 h-4 text-emerald-300" />
                                    <h3 className="text-sm font-medium text-white">{t("audioOverview")}</h3>
                                </div>
                                {preview.audio_overview ? (
                                    <div className="rounded-xl border border-white/10 bg-gray-900/50 p-4 space-y-2 text-xs text-gray-300">
                                        <div>{t("audioMood")}: <span className="text-gray-200">{preview.audio_overview.mood}</span></div>
                                        <div>{t("audioTempo")}: <span className="text-gray-200">{preview.audio_overview.tempo}</span></div>
                                        <div>{t("audioNotes")}: <span className="text-gray-200">{preview.audio_overview.notes}</span></div>
                                    </div>
                                ) : (
                                    <div className="text-xs text-gray-400">{t("noAudioOverview")}</div>
                                )}
                            </section>
                        )}

                        {activeOutput === "mindmap" && (
                            <section>
                                <div className="flex items-center gap-2 mb-3">
                                    <Share2 className="w-4 h-4 text-amber-300" />
                                    <h3 className="text-sm font-medium text-white">{t("mindMap")}</h3>
                                </div>
                                {Array.isArray(preview.mind_map) && preview.mind_map.length > 0 ? (
                                    <div className="space-y-2">
                                        {preview.mind_map.map((node, idx) => (
                                            <div
                                                key={`${node.label}-${idx}`}
                                                className="rounded-lg border border-white/10 bg-gray-900/50 px-3 py-2 text-xs"
                                            >
                                                <div className="text-gray-200 font-semibold">{node.label}</div>
                                                <div className="text-gray-400 mt-1">{node.note}</div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-xs text-gray-400">{t("noMindMap")}</div>
                                )}
                            </section>
                        )}

                        {activeOutput !== "storyboard" ? null : (
                            <>
                        {summaryText && (
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <FileText className="w-4 h-4 text-emerald-300" />
                                <h3 className="text-sm font-medium text-white">{t("previewSummary")}</h3>
                            </div>
                            <div className="rounded-xl border border-white/10 bg-gray-900/60 p-3 text-sm text-gray-200 leading-relaxed">
                                {summaryText}
                            </div>
                        </section>
                        )}

                        {storyboardCards.length > 0 && (
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Clapperboard className="w-4 h-4 text-indigo-300" />
                                <h3 className="text-sm font-medium text-white">{t("storyboardCards")}</h3>
                            </div>
                            <div className="grid gap-3 sm:grid-cols-2">
                                {storyboardCards.slice(0, 6).map((card, idx) => {
                                    const label = getStoryboardLabel(card);
                                    const shotType = getStoryboardShotType(card);
                                    const tone = idx % 2 === 0 ? "from-indigo-500/10" : "from-slate-500/10";
                                    return (
                                        <div
                                            key={`card-${idx}`}
                                            className={`rounded-xl border border-white/10 bg-gradient-to-br ${tone} to-gray-950/80 p-3`}
                                        >
                                            <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-slate-400">
                                                <span>{t("shot")} {idx + 1}</span>
                                                {shotType && (
                                                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[9px] text-slate-300">
                                                        {shotType}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="mt-2 text-xs text-slate-200 line-clamp-3">
                                                {label || t("outputComingSoon")}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </section>
                        )}

                        {/* Palette Section */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Palette className="w-4 h-4 text-sky-300" />
                                <h3 className="text-sm font-medium text-white">{t("colorPalette")}</h3>
                            </div>
                            <div className="flex gap-2">
                                {preview.palette.map((color, idx) => (
                                    <motion.div
                                        key={idx}
                                        initial={{ scale: 0 }}
                                        animate={{ scale: 1 }}
                                        transition={{ delay: idx * 0.1 }}
                                        className="group relative"
                                    >
                                        <div
                                            className="w-12 h-12 rounded-xl shadow-lg cursor-pointer transition-transform hover:scale-110"
                                            style={{ backgroundColor: color }}
                                        />
                                        <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 px-2 py-1 bg-gray-800 rounded text-[10px] text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                                            {color}
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </section>

                        {/* Scenes Section */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Layers className="w-4 h-4 text-amber-300" />
                                <h3 className="text-sm font-medium text-white">{t("sceneBreakdown")}</h3>
                            </div>
                            <div className="space-y-3">
                                {preview.scenes.map((scene, idx) => (
                                    <SceneCard key={idx} scene={scene} index={idx} t={t as (key: string) => string} />
                                ))}
                            </div>
                        </section>

                        {/* Style Vector Visualization */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Sparkles className="w-4 h-4 text-emerald-300" />
                                <h3 className="text-sm font-medium text-white">{t("styleSignature")}</h3>
                            </div>
                            <div className="bg-gray-800/50 rounded-xl p-4">
                                <div className="flex gap-1 h-16 items-end">
                                    {preview.style_vector.slice(0, 12).map((val, idx) => (
                                        <motion.div
                                            key={idx}
                                            initial={{ height: 0 }}
                                            animate={{ height: `${val * 100}%` }}
                                            transition={{ delay: idx * 0.05, type: "spring" }}
                                            className="flex-1 bg-gradient-to-t from-sky-600 to-emerald-400 rounded-t"
                                        />
                                    ))}
                                </div>
                                <div className="mt-2 text-xs text-gray-500 text-center">
                                    {t("styleEmbeddingNote")}
                                </div>
                            </div>
                        </section>
                            </>
                        )}

                        {/* Evidence Section */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Link className="w-4 h-4 text-emerald-400" />
                                <h3 className="text-sm font-medium text-white">{t("evidenceRefs")}</h3>
                            </div>
                            {patternVersion && (
                                <div className="mb-2 text-[11px] text-emerald-200/80">
                                    {t("patternVersion")}: {patternVersion}
                                </div>
                            )}
                            {sourceId && (
                                <div className="mb-2 text-[11px] text-emerald-200/80">
                                    {t("sourceId")}: {sourceId}
                                </div>
                            )}
                            {evidenceWarnings.length > 0 && (
                                <div className="mb-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] font-semibold text-amber-200">
                                    {t("evidenceWarnings")}: {evidenceWarnings.length}
                                </div>
                            )}
                            {outputWarnings.length > 0 && (
                                <div className="mb-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[11px] font-semibold text-amber-200">
                                    {t("outputWarnings")}: {outputWarnings.length}
                                </div>
                            )}
                            {preview.evidence_refs.length === 0 ? (
                                <div className="text-xs text-gray-500">{t("noEvidenceRefs")}</div>
                            ) : (
                                <div className="space-y-2">
                                    {preview.evidence_refs.map((ref, idx) => (
                                        <div
                                            key={idx}
                                            className="rounded-lg border border-white/5 bg-gray-900/50 px-3 py-2 text-[11px] text-gray-300"
                                        >
                                            {ref}
                                        </div>
                                    ))}
                                </div>
                            )}
                            {outputWarnings.length > 0 && (
                                <div className="mt-3 space-y-2">
                                    {outputWarnings.map((warning) => (
                                        <div
                                            key={warning}
                                            className="rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2 text-[11px] text-amber-100/80"
                                        >
                                            {warning}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </section>
                    </div>
                )}

                {/* Footer */}
                {preview && (
                    <div className="border-t border-white/10 bg-gray-900/50">
                        <div className="px-5 pt-4 pb-3">
                            <div className="flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-widest text-gray-400">
                                <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">
                                    {t("runId")}:
                                    <span className="ml-1 font-mono text-gray-200">{preview.run_id}</span>
                                </span>
                                <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">
                                    {preview.capsule_id}
                                </span>
                                {patternVersion && (
                                    <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-emerald-200">
                                        {t("patternVersion")}: {patternVersion}
                                    </span>
                                )}
                                {typeof creditCost === "number" && (
                                    <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-1 text-sky-200">
                                        {t("creditsCost")}: {creditCost}
                                    </span>
                                )}
                                {typeof latencyMs === "number" && (
                                    <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-amber-200">
                                        {t("latency")}: {latencyMs}ms
                                    </span>
                                )}
                                {sequenceLen !== undefined && (
                                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">
                                        seq: {sequenceLen}
                                    </span>
                                )}
                                {isAdminView && contextMode && (
                                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">
                                        context: {contextMode}
                                    </span>
                                )}
                                {seqSummary?.first && seqSummary?.last && (
                                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">
                                        first: {seqSummary.first} • last: {seqSummary.last}
                                    </span>
                                )}
                            </div>
                            {tokenUsage && (
                                <div className="mt-2 text-[11px] text-gray-400">
                                    {t("tokenUsage")}: {tokenUsage.input ?? 0} / {tokenUsage.output ?? 0} (
                                    {tokenUsage.total ?? (tokenUsage.input ?? 0) + (tokenUsage.output ?? 0)})
                                </div>
                            )}
                        </div>
                    </div>
                )}
                </div>
            </motion.div>
        </AnimatePresence>
    );
}

interface SceneCardProps {
    scene: ScenePreview;
    index: number;
    t: (key: string) => string;
}

function SceneCard({ scene, index, t }: SceneCardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-gray-800/50 rounded-xl p-4 border border-white/5"
        >
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-gradient-to-br from-sky-500 to-emerald-500 flex items-center justify-center text-xs font-bold text-white">
                        {scene.scene_number}
                    </span>
                    <span className="text-sm font-medium text-white">{scene.composition}</span>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-400">
                    <Clock className="w-3 h-3" />
                    {scene.duration_hint}
                </div>
            </div>

            <div className="flex gap-2 mb-3">
                <div className="flex items-center gap-1">
                    <div
                        className="w-4 h-4 rounded border border-white/20"
                        style={{ backgroundColor: scene.dominant_color }}
                    />
                    <span className="text-[10px] text-gray-500">{t("primary")}</span>
                </div>
                <div className="flex items-center gap-1">
                    <div
                        className="w-4 h-4 rounded border border-white/20"
                        style={{ backgroundColor: scene.accent_color }}
                    />
                    <span className="text-[10px] text-gray-500">{t("accent")}</span>
                </div>
            </div>

            <div className="text-xs text-gray-400 bg-gray-900/50 rounded-lg px-3 py-2">
                {scene.pacing_note}
            </div>
        </motion.div>
    );
}

export default PreviewPanel;
