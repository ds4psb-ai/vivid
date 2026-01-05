"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
    Sparkles, Copy, Play, Star, Zap, Loader2, AlertCircle, RefreshCw, X
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, SingularityTemplate } from "@/lib/api";
import { useToast } from "@/components/Toast";

// Template type alias for local use
type Template = SingularityTemplate;


// =============================================================================
// DIMENSION FLOW DISPLAY - 차원 조합 시각화
// =============================================================================

const DIMENSION_COLORS: Record<string, { bg: string; text: string; glow: string }> = {
    "1D": { bg: "bg-violet-500/20", text: "text-violet-400", glow: "shadow-violet-500/30" },
    "2D": { bg: "bg-cyan-500/20", text: "text-cyan-400", glow: "shadow-cyan-500/30" },
    "3D": { bg: "bg-emerald-500/20", text: "text-emerald-400", glow: "shadow-emerald-500/30" },
    "4D": { bg: "bg-amber-500/20", text: "text-amber-400", glow: "shadow-amber-500/30" },
    "5D": { bg: "bg-lime-400/20", text: "text-lime-400", glow: "shadow-lime-400/30" },
};

function DimensionFlow({ dimensions }: { dimensions: string[] }) {
    if (!dimensions?.length) return null;

    return (
        <div className="flex items-center gap-1">
            {dimensions.map((dim, i) => {
                const colors = DIMENSION_COLORS[dim] || DIMENSION_COLORS["1D"];
                return (
                    <React.Fragment key={dim}>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${colors.bg} ${colors.text}`}>
                            {dim}
                        </span>
                        {i < dimensions.length - 1 && (
                            <span className="text-slate-600 text-xs">→</span>
                        )}
                    </React.Fragment>
                );
            })}
        </div>
    );
}

// =============================================================================
// BLACKHOLE VISUAL - 블랙홀 비주얼
// =============================================================================

function BlackholeVisual() {
    return (
        <div className="relative w-full h-[400px] flex items-center justify-center overflow-hidden">
            {/* Gravitational Lensing Effect */}
            <div className="absolute inset-0 bg-gradient-radial from-transparent via-transparent to-black/80" />

            {/* Accretion Disk - Outer */}
            <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
                className="absolute w-[600px] h-[600px] rounded-full"
                style={{
                    background: "conic-gradient(from 0deg, transparent, rgba(139,92,246,0.1), transparent, rgba(6,182,212,0.1), transparent)",
                }}
            />

            {/* Accretion Disk - Inner */}
            <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
                className="absolute w-[400px] h-[400px] rounded-full"
                style={{
                    background: "conic-gradient(from 180deg, transparent, rgba(139,92,246,0.2), rgba(236,72,153,0.1), transparent)",
                }}
            />

            {/* Event Horizon */}
            <div className="absolute w-48 h-48 rounded-full bg-black shadow-[0_0_100px_40px_rgba(0,0,0,0.9),0_0_60px_20px_rgba(139,92,246,0.3)]" />

            {/* Photon Sphere */}
            <motion.div
                animate={{ scale: [1, 1.05, 1], opacity: [0.5, 0.8, 0.5] }}
                transition={{ duration: 3, repeat: Infinity }}
                className="absolute w-56 h-56 rounded-full border border-violet-500/30"
            />

            {/* Singularity */}
            <div className="absolute w-4 h-4 rounded-full bg-white/10" />

            {/* Content Overlay */}
            <div className="relative z-10 text-center px-8">
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-4xl md:text-6xl font-black tracking-tight text-white mb-4"
                >
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 via-fuchsia-400 to-cyan-400">
                        차원의 특이점
                    </span>
                </motion.h1>
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="text-slate-400 text-lg max-w-xl mx-auto"
                >
                    여러 차원을 관통한 워크플로우가 이곳으로 수렴합니다
                </motion.p>
            </div>
        </div>
    );
}

// =============================================================================
// TAG FILTER - 태그 기반 필터
// =============================================================================

const POPULAR_TAGS = ["콘텐츠", "마케팅", "스토리", "비주얼", "브랜딩"];

function TagFilter({
    selectedTag,
    onTagChange,
    featuredOnly,
    onFeaturedChange
}: {
    selectedTag: string;
    onTagChange: (tag: string) => void;
    featuredOnly: boolean;
    onFeaturedChange: (v: boolean) => void;
}) {
    return (
        <div className="flex flex-wrap items-center justify-center gap-2 mb-12">
            <button
                onClick={() => onTagChange("")}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${!selectedTag
                    ? "bg-white text-black shadow-lg"
                    : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                    }`}
            >
                전체
            </button>
            {POPULAR_TAGS.map(tag => (
                <button
                    key={tag}
                    onClick={() => onTagChange(tag === selectedTag ? "" : tag)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${tag === selectedTag
                        ? "bg-violet-500 text-white shadow-lg shadow-violet-500/25"
                        : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                        }`}
                >
                    #{tag}
                </button>
            ))}
            <button
                onClick={() => onFeaturedChange(!featuredOnly)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${featuredOnly
                    ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    : "bg-white/5 text-slate-400 hover:bg-white/10"
                    }`}
            >
                <Star className="w-4 h-4" />
                추천
            </button>
        </div>
    );
}

// =============================================================================
// TEMPLATE CARD - 개선된 템플릿 카드
// =============================================================================

function TemplateCard({
    template,
    onClick,
    index
}: {
    template: Template;
    onClick: () => void;
    index: number;
}) {
    const thumbnail = template.thumbnail_url || "/images/placeholder.png";

    return (
        <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
            whileHover={{ y: -8, scale: 1.02 }}
            onClick={onClick}
            className="group relative bg-gradient-to-b from-white/[0.04] to-transparent border border-white/10 rounded-3xl overflow-hidden cursor-pointer
                       hover:border-violet-500/40 hover:shadow-[0_0_60px_rgba(139,92,246,0.15)] transition-all duration-500"
        >
            {/* Featured Glow */}
            {template.is_featured && (
                <div className="absolute inset-0 bg-gradient-to-br from-amber-500/5 via-transparent to-transparent pointer-events-none" />
            )}

            {/* Thumbnail */}
            <div className="relative h-52 overflow-hidden">
                <img
                    src={thumbnail}
                    alt={template.title}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                    onError={(e) => { (e.target as HTMLImageElement).src = "/images/placeholder.png"; }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent" />

                {/* Play Button */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300">
                    <motion.div
                        whileHover={{ scale: 1.1 }}
                        className="w-16 h-16 rounded-full bg-white/90 backdrop-blur flex items-center justify-center shadow-2xl"
                    >
                        <Play className="w-7 h-7 text-black ml-1" />
                    </motion.div>
                </div>

                {/* Featured Badge */}
                {template.is_featured && (
                    <div className="absolute top-4 right-4 px-3 py-1 rounded-full bg-amber-500 text-[10px] font-bold text-black tracking-wide">
                        ⭐ 추천
                    </div>
                )}

                {/* Dimension Flow - Bottom of Image */}
                <div className="absolute bottom-4 left-4">
                    <DimensionFlow dimensions={template.dimension_sequence} />
                </div>
            </div>

            {/* Content */}
            <div className="p-6">
                <h3 className="text-lg font-bold text-white mb-2 group-hover:text-violet-300 transition-colors line-clamp-1">
                    {template.title}
                </h3>
                <p className="text-sm text-slate-500 mb-4 line-clamp-2 leading-relaxed">
                    {template.description}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-1.5 mb-4">
                    {template.tags.slice(0, 3).map(tag => (
                        <span key={tag} className="px-2 py-0.5 rounded-full bg-white/5 text-[10px] text-slate-500">
                            #{tag}
                        </span>
                    ))}
                </div>

                {/* Stats */}
                <div className="flex items-center justify-between text-xs text-slate-600">
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                            <Star className="w-3.5 h-3.5 text-amber-500" />
                            {template.rating_avg.toFixed(1)}
                        </span>
                        <span className="flex items-center gap-1">
                            <Zap className="w-3.5 h-3.5" />
                            {template.use_count.toLocaleString()}회
                        </span>
                    </div>
                    <span className="text-slate-500">{template.creator_name}</span>
                </div>
            </div>
        </motion.div>
    );
}

// =============================================================================
// TEMPLATE MODAL - 상세 모달
// =============================================================================

function TemplateModal({
    template,
    onClose,
    onApply,
    isApplying
}: {
    template: Template | null;
    onClose: () => void;
    onApply: (t: Template) => void;
    isApplying: boolean;
}) {
    const [rating, setRating] = useState(0);
    const [hasRated, setHasRated] = useState(false);

    if (!template) return null;

    const thumbnail = template.thumbnail_url || "/images/placeholder.png";

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-xl"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.9, opacity: 0, y: 20 }}
                onClick={e => e.stopPropagation()}
                className="w-full max-w-2xl bg-slate-950 border border-white/10 rounded-3xl overflow-hidden shadow-2xl"
            >
                {/* Hero Image */}
                <div className="relative h-64">
                    <img src={thumbnail} alt={template.title} className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/50 to-transparent" />
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 p-2 rounded-full bg-black/50 hover:bg-black/70 transition-colors"
                    >
                        <X className="w-5 h-5 text-white" />
                    </button>

                    {/* Dimension Flow */}
                    <div className="absolute bottom-6 left-6">
                        <DimensionFlow dimensions={template.dimension_sequence} />
                    </div>
                </div>

                {/* Content */}
                <div className="p-8">
                    <h2 className="text-3xl font-bold text-white mb-3">{template.title}</h2>
                    <p className="text-slate-400 mb-6 leading-relaxed">{template.description}</p>

                    {/* Tool Sequence */}
                    {template.tool_names && template.tool_names.length > 0 && (
                        <div className="mb-6 p-4 rounded-2xl bg-white/5 border border-white/10">
                            <div className="text-xs text-slate-500 mb-2">사용된 도구 흐름</div>
                            <div className="flex flex-wrap gap-2">
                                {template.tool_names.map((tool, i) => (
                                    <span key={i} className="px-3 py-1 rounded-lg bg-violet-500/10 text-violet-300 text-sm">
                                        {tool}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Tags */}
                    <div className="flex flex-wrap gap-2 mb-6">
                        {template.tags.map(tag => (
                            <span key={tag} className="px-3 py-1 rounded-full bg-white/5 text-xs text-slate-400">
                                #{tag}
                            </span>
                        ))}
                    </div>

                    {/* Stats */}
                    <div className="flex items-center gap-6 text-sm text-slate-400 mb-8 pb-6 border-b border-white/10">
                        <span className="flex items-center gap-1.5">
                            <Star className="w-4 h-4 text-amber-500" />
                            {template.rating_avg.toFixed(1)}
                        </span>
                        <span className="flex items-center gap-1.5">
                            <Zap className="w-4 h-4" />
                            {template.use_count.toLocaleString()}회 사용
                        </span>
                        <span>by {template.creator_name}</span>
                    </div>

                    {/* Rating */}
                    <div className="mb-8">
                        <div className="text-xs text-slate-500 mb-3">이 워크플로우를 평가해주세요</div>
                        <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map(star => (
                                <button
                                    key={star}
                                    onClick={() => { setRating(star); setHasRated(true); }}
                                    disabled={hasRated}
                                    className={`w-10 h-10 rounded-xl transition-all ${star <= rating
                                        ? "bg-amber-500 text-black font-bold"
                                        : "bg-white/5 text-slate-500 hover:bg-white/10"
                                        } ${hasRated ? "cursor-not-allowed" : ""}`}
                                >
                                    {star}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-4">
                        <button
                            onClick={() => onApply(template)}
                            disabled={isApplying}
                            className="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 disabled:opacity-50 text-white font-bold rounded-2xl transition-all shadow-lg shadow-violet-500/25"
                        >
                            {isApplying ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Copy className="w-5 h-5" />
                            )}
                            {isApplying ? "적용 중..." : "이 워크플로우 적용하기"}
                        </button>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
}

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function SingularityPage() {
    const router = useRouter();
    const toast = useToast();
    const [templates, setTemplates] = useState<Template[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
    const [isApplying, setIsApplying] = useState(false);
    const [selectedTag, setSelectedTag] = useState("");
    const [featuredOnly, setFeaturedOnly] = useState(false);

    const loadTemplates = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.listSingularityTemplates({
                tag: selectedTag || undefined,
                featured_only: featuredOnly
            });
            setTemplates(response.items);
        } catch (err) {
            setError(err instanceof Error ? err.message : "워크플로우를 불러오는데 실패했습니다");
        } finally {
            setLoading(false);
        }
    }, [selectedTag, featuredOnly]);

    useEffect(() => {
        loadTemplates();
    }, [loadTemplates]);

    const handleApply = async (template: Template) => {
        setIsApplying(true);
        try {
            await api.useSingularityTemplate(template.id);
            setSelectedTemplate(null);
            router.push(`/flow?template=${template.id}`);
        } catch (err) {
            const message = err instanceof Error ? err.message : "템플릿 적용에 실패했습니다";
            toast.error(message);
        } finally {
            setIsApplying(false);
        }
    };

    return (
        <AppShell>
            <div className="min-h-screen bg-black">
                {/* Blackhole Visual Header */}
                <BlackholeVisual />

                {/* Content */}
                <div className="max-w-7xl mx-auto px-6 pb-24">
                    {/* Tag Filter */}
                    <TagFilter
                        selectedTag={selectedTag}
                        onTagChange={setSelectedTag}
                        featuredOnly={featuredOnly}
                        onFeaturedChange={setFeaturedOnly}
                    />

                    {/* Loading */}
                    {loading && (
                        <div className="flex flex-col items-center justify-center py-20">
                            <Loader2 className="w-10 h-10 text-violet-400 animate-spin mb-4" />
                            <p className="text-slate-500">워크플로우를 불러오는 중...</p>
                        </div>
                    )}

                    {/* Error */}
                    {error && !loading && (
                        <div className="flex flex-col items-center justify-center py-20">
                            <AlertCircle className="w-10 h-10 text-red-400 mb-4" />
                            <p className="text-red-400 mb-4">{error}</p>
                            <button
                                onClick={loadTemplates}
                                className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg text-white hover:bg-white/20"
                            >
                                <RefreshCw className="w-4 h-4" />
                                다시 시도
                            </button>
                        </div>
                    )}

                    {/* Empty */}
                    {!loading && !error && templates.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-20">
                            <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-6">
                                <Sparkles className="w-8 h-8 text-slate-600" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">아직 수렴된 워크플로우가 없습니다</h3>
                            <p className="text-slate-500 mb-4">
                                차원 여행을 시작하고 첫 번째 워크플로우를 만들어보세요
                            </p>
                            <button
                                onClick={() => router.push("/dimension")}
                                className="px-6 py-3 bg-violet-500 hover:bg-violet-400 text-white font-semibold rounded-xl transition-colors"
                            >
                                차원문 열기
                            </button>
                        </div>
                    )}

                    {/* Grid */}
                    {!loading && !error && templates.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {templates.map((template, i) => (
                                <TemplateCard
                                    key={template.id}
                                    template={template}
                                    onClick={() => setSelectedTemplate(template)}
                                    index={i}
                                />
                            ))}
                        </div>
                    )}
                </div>

                {/* Modal */}
                <AnimatePresence>
                    {selectedTemplate && (
                        <TemplateModal
                            template={selectedTemplate}
                            onClose={() => setSelectedTemplate(null)}
                            onApply={handleApply}
                            isApplying={isApplying}
                        />
                    )}
                </AnimatePresence>
            </div>
        </AppShell>
    );
}
