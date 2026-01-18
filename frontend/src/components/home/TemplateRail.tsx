"use client";

/**
 * TemplateRail - Horizontal scrolling template recommendations
 * 
 * Displays Singularity templates in a horizontally scrollable rail.
 * Uses the same API as /singularity for consistency.
 */

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ChevronRight, Sparkles, Play, Loader2, Star, Zap } from "lucide-react";
import { api, SingularityTemplate } from "@/lib/api";
import { StarRating } from "@/components/ui/StarRating";
import { useLanguage } from "@/contexts/LanguageContext";
import { FLOW_ENABLED } from "@/lib/feature-flags";
import { dimensionIdToCode, getDimensionToken } from "@/lib/tokens";

// Dimension tones for flow badges (token-driven, synced with /singularity)
type DimensionTone = { bg: string; text: string };

const getDimensionTone = (dimension: string): DimensionTone => {
    const code = dimensionIdToCode(dimension);
    if (code) {
        const token = getDimensionToken(code);
        const key = token.tailwindKey;
        return { bg: `bg-${key}/20`, text: `text-${key}` };
    }
    const fallbackToken = getDimensionToken("1d");
    const fallbackKey = fallbackToken.tailwindKey;
    return { bg: `bg-${fallbackKey}/20`, text: `text-${fallbackKey}` };
};

const BRAND_PRIMARY = {
    text: "text-[var(--color-brand-primary)]",
    borderHover: "hover:border-[var(--color-brand-primary)]/40",
    ring: "focus:ring-[var(--color-brand-primary)]/50",
    shadowHover: "hover:shadow-[0_0_40px] hover:shadow-dimension-1d/20",
};

const BRAND_ACCENT = {
    bg: "bg-[var(--color-brand-accent)]",
};

function DimensionFlow({ dimensions }: { dimensions: string[] }) {
    if (!dimensions?.length) return null;
    return (
        <div className="flex items-center gap-1">
            {dimensions.map((dim, i) => {
                const colors = getDimensionTone(dim);
                return (
                    <span key={`${dim}-${i}`}>
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${colors.bg} ${colors.text}`}>
                            {dim}
                        </span>
                        {i < dimensions.length - 1 && (
                            <span className="text-slate-600 text-[10px] mx-0.5">→</span>
                        )}
                    </span>
                );
            })}
        </div>
    );
}

interface TemplateRailProps {
    maxItems?: number;
    title?: string;
    showSeeAll?: boolean;
}

export function TemplateRail({ maxItems = 6, title, showSeeAll = true }: TemplateRailProps) {
    const router = useRouter();
    const { language } = useLanguage();
    const [templates, setTemplates] = useState<SingularityTemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const [applying, setApplying] = useState<string | null>(null);

    useEffect(() => {
        // Use the same API as /singularity page
        api.listSingularityTemplates({ featured_only: true })
            .then((result) => {
                setTemplates(result.items.slice(0, maxItems));
            })
            .catch(() => {
                // Fallback: try all templates if featured fails
                api.listSingularityTemplates({})
                    .then((result) => setTemplates(result.items.slice(0, maxItems)))
                    .catch(() => setTemplates([]));
            })
            .finally(() => setLoading(false));
    }, [maxItems]);

    const handleApply = async (template: SingularityTemplate) => {
        // Flow is disabled - redirect to singularity page instead
        if (!FLOW_ENABLED) {
            router.push(`/singularity?template=${template.id}`);
            return;
        }

        setApplying(template.id);
        try {
            await api.useSingularityTemplate(template.id);
            router.push(`/flow?template=${template.id}`);
        } catch {
            setApplying(null);
        }
    };

    if (loading) {
        return (
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <div className="h-6 w-40 bg-white/5 rounded animate-pulse" />
                </div>
                <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
                    {Array.from({ length: 4 }).map((_, i) => (
                        <div
                            key={i}
                            className="flex-shrink-0 w-80 h-48 rounded-2xl bg-white/5 animate-pulse"
                        />
                    ))}
                </div>
            </div>
        );
    }

    if (templates.length === 0) return null;

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Sparkles className={`h-5 w-5 ${BRAND_PRIMARY.text}`} />
                    <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                        {title || (language === "ko" ? "차원 템플릿" : "Dimension Templates")}
                    </h2>
                </div>
                {showSeeAll && (
                    <Link
                        href="/singularity"
                        className="flex items-center gap-1 text-sm text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                    >
                        {language === "ko" ? "더보기" : "See all"}
                        <ChevronRight className="h-4 w-4" />
                    </Link>
                )}
            </div>

            {/* Horizontal Scroll Rail */}
            <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide -mx-2 px-2">
                {templates.map((template, idx) => {
                    const thumbnail = template.thumbnail_url || "/images/placeholder.png";
                    return (
                        <motion.div
                            key={template.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.08 }}
                            className="flex-shrink-0 w-80"
                        >
                            <div
                                onClick={() => !applying && handleApply(template)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); !applying && handleApply(template); } }}
                                className={`group relative w-full rounded-2xl overflow-hidden border border-gray-200 dark:border-white/10 bg-gradient-to-b from-gray-50 dark:from-white/[0.04] to-transparent ${BRAND_PRIMARY.borderHover} ${BRAND_PRIMARY.shadowHover} transition-all text-left cursor-pointer focus:outline-none focus:ring-2 ${BRAND_PRIMARY.ring} ${applying === template.id ? 'opacity-50 pointer-events-none' : ''}`}
                            >
                                {/* Thumbnail */}
                                <div className="relative h-36 overflow-hidden">
                                    <img
                                        src={thumbnail}
                                        alt={template.title}
                                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                                        onError={(e) => { (e.target as HTMLImageElement).src = "/images/placeholder.png"; }}
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />

                                    {/* Featured Badge */}
                                    {template.is_featured && (
                                        <div className={`absolute top-3 right-3 px-2 py-0.5 rounded-full ${BRAND_ACCENT.bg} text-[9px] font-bold text-black`}>
                                            ⭐ 추천
                                        </div>
                                    )}

                                    {/* Play overlay */}
                                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                        {applying === template.id ? (
                                            <Loader2 className="h-10 w-10 text-white animate-spin" />
                                        ) : (
                                            <div className="h-12 w-12 rounded-full bg-white/90 backdrop-blur flex items-center justify-center shadow-2xl">
                                                <Play className="h-5 w-5 text-black ml-0.5" />
                                            </div>
                                        )}
                                    </div>

                                    {/* Dimension Flow */}
                                    <div className="absolute bottom-3 left-3">
                                        <DimensionFlow dimensions={template.dimension_sequence} />
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="p-4">
                                    <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-[var(--color-brand-primary)] transition-colors line-clamp-1">
                                        {template.title}
                                    </h3>
                                    <p className="text-xs text-gray-500 dark:text-slate-500 mt-1 line-clamp-2">
                                        {template.description}
                                    </p>

                                    {/* Stats */}
                                    <div className="flex items-center gap-3 mt-3 text-[10px] text-slate-500">
                                        <span className="flex items-center gap-1">
                                            <StarRating value={Math.round(template.rating_avg)} readonly size="sm" />
                                            <span className="ml-1">{template.rating_avg.toFixed(1)}</span>
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <Zap className="w-3 h-3" />
                                            {template.use_count.toLocaleString()}회
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
}
