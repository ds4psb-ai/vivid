import { motion, AnimatePresence } from "framer-motion";
import { X, Palette, Layers, Clock, Eye, Sparkles, Link } from "lucide-react";
import type { StoryboardPreview, ScenePreview } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

interface PreviewPanelProps {
    preview: StoryboardPreview | null;
    isLoading: boolean;
    onClose: () => void;
}

export function PreviewPanel({ preview, isLoading, onClose }: PreviewPanelProps) {
    const { t } = useLanguage();

    if (!preview && !isLoading) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, x: 300 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 300 }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="fixed right-0 top-0 h-full w-[400px] bg-gradient-to-b from-gray-900/95 to-gray-950/95 backdrop-blur-xl border-l border-white/10 z-50 overflow-hidden flex flex-col"
            >
                {/* Header */}
                <div className="flex items-center justify-between p-5 border-b border-white/10">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/20 to-cyan-500/20 flex items-center justify-center">
                            <Eye className="w-5 h-5 text-violet-400" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">{t("storyboardPreview")}</h2>
                            <p className="text-xs text-gray-400">{t("generatedDesc")}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                {/* Loading State */}
                {isLoading && (
                    <div className="flex-1 flex items-center justify-center">
                        <div className="text-center">
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                            >
                                <Sparkles className="w-12 h-12 text-violet-400 mx-auto mb-4" />
                            </motion.div>
                            <p className="text-gray-400">{t("generating")}</p>
                        </div>
                    </div>
                )}

                {/* Content */}
                {preview && !isLoading && (
                    <div className="flex-1 overflow-y-auto p-5 space-y-6">
                        {/* Palette Section */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Palette className="w-4 h-4 text-violet-400" />
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
                                <Layers className="w-4 h-4 text-cyan-400" />
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
                                <Sparkles className="w-4 h-4 text-amber-400" />
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
                                            className="flex-1 bg-gradient-to-t from-violet-600 to-violet-400 rounded-t"
                                        />
                                    ))}
                                </div>
                                <div className="mt-2 text-xs text-gray-500 text-center">
                                    16-dimensional style embedding
                                </div>
                            </div>
                        </section>

                        {/* Evidence Section */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Link className="w-4 h-4 text-emerald-400" />
                                <h3 className="text-sm font-medium text-white">{t("evidenceRefs")}</h3>
                            </div>
                            {preview.evidence_refs.length === 0 ? (
                                <div className="text-xs text-gray-500">No evidence refs returned.</div>
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
                        </section>
                    </div>
                )}

                {/* Footer */}
                {preview && (
                    <div className="p-5 border-t border-white/10 bg-gray-900/50">
                        <div className="text-xs text-gray-500 text-center">
                            {t("runId")}: {preview.run_id} • {preview.capsule_id}
                        </div>
                    </div>
                )}
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
                    <span className="w-6 h-6 rounded-full bg-gradient-to-br from-violet-600 to-cyan-600 flex items-center justify-center text-xs font-bold text-white">
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
