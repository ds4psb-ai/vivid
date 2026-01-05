"use client";

/**
 * Template Card Component
 * 
 * Premium card for displaying template with preview, badges, and actions.
 * Extracted from page.tsx for maintainability.
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Sparkles,
    Film,
    Palette,
    Music,
    Zap,
    Coffee,
    Clapperboard,
    ArrowRight,
    History as HistoryIcon,
    Check,
} from "lucide-react";
import { Template, CanvasGraph } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { getBeatLabel, getStoryboardLabel } from "@/lib/narrative";

// Icon mapping for each auteur
const AUTEUR_ICONS: Record<string, React.ElementType> = {
    "tmpl-auteur-bong": Film,
    "tmpl-auteur-park": Palette,
    "tmpl-auteur-shinkai": Sparkles,
    "tmpl-auteur-leejunho": Music,
    "tmpl-auteur-na": Zap,
    "tmpl-auteur-hong": Coffee,
    "tmpl-production-stage": Clapperboard,
};

const AUTEUR_COLORS: Record<string, { gradient: string; glow: string }> = {
    "tmpl-auteur-bong": { gradient: "from-sky-400 to-blue-600", glow: "shadow-sky-500/30" },
    "tmpl-auteur-park": { gradient: "from-amber-400 to-orange-600", glow: "shadow-amber-500/30" },
    "tmpl-auteur-shinkai": { gradient: "from-cyan-400 to-teal-600", glow: "shadow-cyan-500/30" },
    "tmpl-auteur-leejunho": { gradient: "from-emerald-400 to-teal-600", glow: "shadow-emerald-500/30" },
    "tmpl-auteur-na": { gradient: "from-rose-400 to-red-600", glow: "shadow-rose-500/30" },
    "tmpl-auteur-hong": { gradient: "from-slate-400 to-zinc-600", glow: "shadow-slate-500/30" },
    "tmpl-production-stage": { gradient: "from-lime-400 to-emerald-600", glow: "shadow-emerald-500/30" },
};

const isVideoPreview = (url?: string | null) => {
    if (!url) return false;
    const clean = url.split("?")[0].toLowerCase();
    return [".mp4", ".webm", ".mov"].some((ext) => clean.endsWith(ext));
};

export const getNarrativeSeeds = (graphData?: CanvasGraph) => {
    const meta = graphData?.meta;
    const narrativeSeeds =
        meta && typeof meta === "object"
            ? (meta.narrative_seeds as Record<string, unknown>) || {}
            : {};
    const storyBeats = Array.isArray(narrativeSeeds.story_beats)
        ? narrativeSeeds.story_beats
        : [];
    const storyboardCards = Array.isArray(narrativeSeeds.storyboard_cards)
        ? narrativeSeeds.storyboard_cards
        : [];
    const beatSnippet = getBeatLabel(storyBeats[0]);
    const storyboardSnippet = getStoryboardLabel(storyboardCards[0]);
    return {
        storyBeats,
        storyboardCards,
        beatSnippet,
        storyboardSnippet,
        hasSeeds: storyBeats.length > 0 || storyboardCards.length > 0,
    };
};

export const isProductionTemplateGraph = (graphData?: CanvasGraph) => {
    const meta = graphData?.meta;
    if (!meta || typeof meta !== "object") return false;
    const production = meta.production_contract as Record<string, unknown> | undefined;
    if (!production || typeof production !== "object") return false;
    const shotContracts = Array.isArray(production.shot_contracts) ? production.shot_contracts : [];
    const storyboardRefs = Array.isArray(production.storyboard_refs) ? production.storyboard_refs : [];
    return shotContracts.length > 0 || storyboardRefs.length > 0;
};

interface TemplateCardProps {
    template: Template;
    onSelect: () => void;
    onOpenVersions: () => void;
    isCreating: boolean;
}

export function TemplateCard({ template, onSelect, onOpenVersions, isCreating }: TemplateCardProps) {
    const { t } = useLanguage();
    const Icon = AUTEUR_ICONS[template.slug] || Sparkles;
    const colors = AUTEUR_COLORS[template.slug] || { gradient: "from-slate-400 to-slate-600", glow: "shadow-slate-500/20" };
    const [isHovered, setIsHovered] = useState(false);
    const graphMeta = (template.graph_data?.meta || {}) as Record<string, unknown>;
    const evidenceRefs = Array.isArray(graphMeta.evidence_refs) ? graphMeta.evidence_refs : [];
    const evidenceCount = evidenceRefs.length;
    const isProductionTemplate = isProductionTemplateGraph(template.graph_data);
    const seeds = getNarrativeSeeds(template.graph_data);
    const guideSources = Array.isArray(graphMeta.guide_sources) ? graphMeta.guide_sources : [];
    const guideTypeSet = new Set<string>();
    guideSources.forEach((source) => {
        if (!source || typeof source !== "object") return;
        const guideTypes = (source as { guide_types?: unknown }).guide_types;
        if (!Array.isArray(guideTypes)) return;
        guideTypes.forEach((type) => {
            if (typeof type === "string" && type.trim()) {
                guideTypeSet.add(type.trim());
            }
        });
    });
    const guideLabelMap: Record<string, string> = {
        summary: t("guideSummary"),
        homage: t("guideHomage"),
        variation: t("guideVariation"),
        template_fit: t("guideTemplateFit"),
        persona: t("guidePersona"),
        synapse: t("guideSynapse"),
        story: t("guideStory"),
        beat_sheet: t("guideBeatSheet"),
        storyboard: t("guideStoryboard"),
    };
    const guideLabels = Array.from(guideTypeSet).map((type) => guideLabelMap[type] || type.toUpperCase());
    const visibleGuideLabels = guideLabels.slice(0, 3);
    const extraGuideCount = guideLabels.length - visibleGuideLabels.length;
    const springConfig = { type: "spring" as const, stiffness: 400, damping: 28 };

    return (
        <motion.article
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -12 }}
            whileTap={{ scale: 0.98 }}
            transition={springConfig}
            onHoverStart={() => setIsHovered(true)}
            onHoverEnd={() => setIsHovered(false)}
            onClick={onSelect}
            role="button"
            tabIndex={0}
            aria-label={`${template.title} - ${template.description}`}
            onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelect();
                }
            }}
            className="group relative cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg-0)] rounded-[var(--card-radius)]"
        >
            <div
                className="relative flex flex-col overflow-hidden rounded-[var(--card-radius)] border backdrop-blur-xl transition-all duration-300 ease-out"
                style={{
                    background: isHovered ? 'var(--card-bg-hover)' : 'var(--card-bg)',
                    borderColor: isHovered ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.1)',
                    boxShadow: isHovered ? 'var(--card-shadow-hover)' : 'var(--card-shadow)',
                }}
            >
                {/* Thumbnail Section */}
                <div className="relative m-[var(--card-padding)] aspect-[16/10] overflow-hidden rounded-[var(--card-inner-radius)] bg-gradient-to-br from-slate-900/90 to-slate-800/60">
                    <AnimatePresence mode="wait">
                        {template.preview_video_url ? (
                            isVideoPreview(template.preview_video_url) ? (
                                <motion.video
                                    key="video"
                                    src={template.preview_video_url}
                                    muted
                                    autoPlay={isHovered}
                                    loop
                                    playsInline
                                    preload="metadata"
                                    initial={{ scale: 1, opacity: 0.85 }}
                                    animate={{ scale: isHovered ? 1.06 : 1, opacity: isHovered ? 1 : 0.85, filter: isHovered ? 'brightness(1.05)' : 'brightness(0.95)' }}
                                    transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
                                    className="absolute inset-0 h-full w-full object-cover"
                                />
                            ) : (
                                <motion.img
                                    key="image"
                                    src={template.preview_video_url}
                                    alt={template.title}
                                    loading="lazy"
                                    initial={{ scale: 1, opacity: 0.85 }}
                                    animate={{ scale: isHovered ? 1.06 : 1, opacity: isHovered ? 1 : 0.85, filter: isHovered ? 'brightness(1.05)' : 'brightness(0.95)' }}
                                    transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
                                    className="absolute inset-0 h-full w-full object-cover"
                                />
                            )
                        ) : (
                            <motion.div
                                className={`absolute inset-0 bg-gradient-to-br ${colors.gradient}`}
                                initial={{ opacity: 0.25 }}
                                animate={{ opacity: isHovered ? 0.35 : 0.25 }}
                            >
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <motion.div
                                        animate={{ scale: isHovered ? 1.15 : 1, rotate: isHovered ? 5 : 0 }}
                                        transition={springConfig}
                                        className={`h-16 w-16 rounded-2xl bg-gradient-to-br ${colors.gradient} flex items-center justify-center shadow-2xl ring-1 ring-white/10`}
                                    >
                                        <Icon className="h-8 w-8 text-white drop-shadow-lg" strokeWidth={1.5} />
                                    </motion.div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                    <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent opacity-60 group-hover:opacity-80 transition-opacity duration-300" />

                    {/* Badges */}
                    <div className="absolute top-2.5 left-2.5 flex flex-wrap gap-1.5">
                        {template.slug.startsWith("tmpl-auteur-") && (
                            <motion.span initial={{ opacity: 0, x: -8, scale: 0.9 }} animate={{ opacity: 1, x: 0, scale: 1 }} transition={{ delay: 0.05, ...springConfig }}
                                className={`inline-flex items-center gap-1 rounded-full bg-gradient-to-r ${colors.gradient} px-2.5 py-1 text-[10px] font-bold text-white shadow-lg ${colors.glow} backdrop-blur-sm ring-1 ring-white/20`}>
                                <Sparkles className="h-3 w-3" />DNA
                            </motion.span>
                        )}
                        {evidenceCount > 0 && (
                            <motion.span initial={{ opacity: 0, x: -8, scale: 0.9 }} animate={{ opacity: 1, x: 0, scale: 1 }} transition={{ delay: 0.1, ...springConfig }}
                                className="inline-flex items-center gap-1 rounded-full bg-emerald-500/95 px-2.5 py-1 text-[10px] font-bold text-white shadow-lg shadow-emerald-500/30 backdrop-blur-sm">
                                <Check className="h-3 w-3" />{t("templateVerified")}
                            </motion.span>
                        )}
                        {isProductionTemplate && (
                            <motion.span initial={{ opacity: 0, x: -8, scale: 0.9 }} animate={{ opacity: 1, x: 0, scale: 1 }} transition={{ delay: 0.2, ...springConfig }}
                                className="inline-flex items-center gap-1 rounded-full bg-sky-500/95 px-2.5 py-1 text-[10px] font-bold text-white shadow-lg shadow-sky-500/30 backdrop-blur-sm">
                                <Clapperboard className="h-3 w-3" />{t("productionTemplate")}
                            </motion.span>
                        )}
                    </div>

                    {template.version !== undefined && (
                        <motion.span initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.15 }}
                            className="absolute top-2.5 right-2.5 rounded-full bg-black/60 px-2.5 py-1 text-[10px] font-semibold text-white/90 backdrop-blur-md shadow-lg">
                            v{template.version}
                        </motion.span>
                    )}

                    {/* Hover CTA */}
                    <motion.div initial={{ opacity: 0, y: 12, scale: 0.92 }} animate={{ opacity: isHovered ? 1 : 0, y: isHovered ? 0 : 12, scale: isHovered ? 1 : 0.92 }}
                        transition={{ duration: 0.25, ease: "easeOut" }} className="absolute inset-0 flex items-center justify-center">
                        <div className="flex items-center gap-2.5 rounded-full bg-white px-6 py-3 text-sm font-bold text-slate-900 shadow-2xl shadow-black/30 ring-1 ring-white/20">
                            <Sparkles className="h-4 w-4 text-[var(--accent)]" />{t("createCanvas")}<ArrowRight className="h-4 w-4 opacity-60" />
                        </div>
                    </motion.div>
                </div>

                {/* Content */}
                <div className="flex flex-1 flex-col px-5 pb-5">
                    <h3 className="text-[15px] font-semibold leading-tight text-white/95 group-hover:text-white transition-colors duration-200 line-clamp-1">{template.title}</h3>
                    <p className="mt-2 text-[13px] leading-relaxed text-white/50 group-hover:text-white/70 transition-colors duration-200 line-clamp-2">{template.description}</p>

                    {seeds.hasSeeds && (
                        <div className="mt-3 flex items-center gap-2">
                            <span className="inline-flex items-center gap-1.5 rounded-md bg-white/[0.04] px-2 py-1 text-[10px] font-medium text-white/50 ring-1 ring-white/[0.06]">
                                <span className="opacity-70">📝</span>{seeds.storyBeats.length} {t("beats") || "beats"}
                            </span>
                            <span className="inline-flex items-center gap-1.5 rounded-md bg-white/[0.04] px-2 py-1 text-[10px] font-medium text-white/50 ring-1 ring-white/[0.06]">
                                <span className="opacity-70">🎬</span>{seeds.storyboardCards.length} {t("shots") || "shots"}
                            </span>
                        </div>
                    )}

                    {visibleGuideLabels.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1.5">
                            {visibleGuideLabels.map((label, i) => (
                                <motion.span key={label} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 + i * 0.05 }}
                                    className="rounded-full bg-white/[0.05] px-2.5 py-1 text-[10px] font-medium text-white/55 ring-1 ring-white/[0.06]">{label}</motion.span>
                            ))}
                            {extraGuideCount > 0 && (<span className="rounded-full bg-white/[0.03] px-2.5 py-1 text-[10px] font-medium text-white/35">+{extraGuideCount}</span>)}
                        </div>
                    )}

                    {/* Footer */}
                    <div className="mt-auto pt-4">
                        <div className="flex items-center justify-between border-t border-white/[0.06] pt-3">
                            <div className="flex items-center gap-1.5 overflow-hidden">
                                {template.tags.slice(0, 2).map((tag) => (
                                    <span key={tag} className="truncate rounded bg-white/[0.04] px-2 py-0.5 text-[10px] font-medium text-white/40 ring-1 ring-white/[0.05]">{tag}</span>
                                ))}
                                {template.tags.length > 2 && <span className="text-[9px] text-white/25">+{template.tags.length - 2}</span>}
                            </div>
                            <div className="flex items-center gap-2">
                                <motion.button whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}
                                    onClick={(event) => { event.stopPropagation(); onOpenVersions(); }}
                                    className="rounded-full border border-white/10 bg-white/[0.04] p-2 text-white/50 hover:bg-white/10 hover:text-white/90 hover:border-white/20 transition-all duration-200"
                                    title={t("versions")} aria-label={t("versions")}>
                                    <HistoryIcon className="h-3.5 w-3.5" />
                                </motion.button>
                                <motion.div initial={{ width: 0, opacity: 0 }} animate={{ width: isHovered ? 28 : 0, opacity: isHovered ? 1 : 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
                                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--accent)]/20"><ArrowRight className="h-4 w-4 text-[var(--accent)]" /></div>
                                </motion.div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Glow */}
                <div className="pointer-events-none absolute -inset-px rounded-[var(--card-radius)] opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                    style={{ boxShadow: colors.glow.includes('sky') ? 'var(--glow-sky)' : colors.glow.includes('amber') ? 'var(--glow-amber)' : colors.glow.includes('rose') ? 'var(--glow-rose)' : colors.glow.includes('emerald') ? 'var(--glow-emerald)' : 'var(--glow-violet)' }} />
            </div>

            {/* Creating Overlay */}
            <AnimatePresence>
                {isCreating && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 z-20 flex items-center justify-center rounded-[var(--card-radius)] bg-black/85 backdrop-blur-md">
                        <div className="flex flex-col items-center gap-3">
                            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }} className="h-8 w-8 rounded-full border-2 border-[var(--accent)] border-t-transparent" />
                            <span className="text-sm font-medium text-white/90">{t("creating")}</span>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.article>
    );
}
